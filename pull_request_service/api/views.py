from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from teams.models import Team
from users.models import User
from pull_requests.models import PullRequest
from .serializers import TeamSerializer, UserTeamSerializer, PullRequestSerializer, PullRequestMergeSerializer, PullRequestShortSerializer
from rest_framework.decorators import action
from rest_framework.settings import api_settings
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from django.utils.timezone import now
import random
from django.db.models import Count


class TeamViewSet(viewsets.GenericViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

    def get_success_headers(self, data):
        try:
            return {'Location': str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}

    @action(detail=False, methods=['post'], url_path='add')
    def add_team(self, request, *args, **kwargs):
        team_name = request.data.get('team_name')
        if Team.objects.filter(team_name=team_name).exists():
            return Response(
                {'error': {'code': 'TEAM_EXISTS', 'message': f'{team_name} already exists'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response({'team': serializer.data}, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['get'], url_path='get')
    def get_team(self, request, *args, **kwargs):
        team_name = request.query_params.get('team_name')
        team = get_object_or_404(self.get_queryset(), team_name=team_name)
        serializer = self.get_serializer(team)
        return Response(serializer.data)


class UserViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserTeamSerializer

    @action(detail=False, methods=['post'], url_path='setIsActive')
    def set_active(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        is_active = request.data.get('is_active')
        if user_id is None or is_active is None:
            return Response(
                {'detail': 'user_id и is_active обязательны'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = get_object_or_404(User, pk=user_id)
        user.is_active = is_active
        user.save()

        serializer = self.get_serializer(user)
        return Response({'user': serializer.data}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='getReview')
    def get_review_prs(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {"detail": "user_id обязателен"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = get_object_or_404(User, pk=user_id)
        pull_requests = user.review_assignments.all()
        serializer = PullRequestShortSerializer(pull_requests, many=True)

        return Response({
            'user_id': user_id,
            'pull_requests': serializer.data
        }, status=status.HTTP_200_OK)


class PullRequestViewSet(viewsets.GenericViewSet):
    queryset = PullRequest.objects.all()
    serializer_class = PullRequestSerializer

    @action(detail=False, methods=['post'], url_path='create')
    def create_pull_request(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
        except serializers.ValidationError as e:
            detail = e.detail
            if 'pull_request_name' in detail:
                return Response(
                    {"error": {"code": "PR_EXISTS",
                               "message": detail['pull_request_name']}},
                    status=status.HTTP_409_CONFLICT)
            else:
                return Response(
                    {"error": {"code": "NOT_FOUND",
                               "message": "Author/team not found"}},
                    status=status.HTTP_404_NOT_FOUND)

        return Response({'pr': serializer.data}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='merge')
    def merge_pull_request(self, request, *args, **kwargs):
        pull_request_id = request.data.get('pull_request_id')
        if not pull_request_id:
            return Response(
                {"error": {"code": "BAD_REQUEST",
                           "message": "pull_request_id is required"}},
                status=status.HTTP_400_BAD_REQUEST
            )

        pull_request = get_object_or_404(PullRequest, pk=pull_request_id)

        if pull_request.status == 'MERGED':
            serializer = PullRequestMergeSerializer(pull_request)
            return Response({'pr': serializer.data}, status=status.HTTP_200_OK)

        pull_request.status = 'MERGED'
        pull_request.merged_at = now()
        pull_request.save()

        serializer = PullRequestMergeSerializer(pull_request)
        return Response({'pr': serializer.data}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='reassign')
    def reassign_reviewer(self, request, *args, **kwargs):
        pull_request_id = request.data.get('pull_request_id')
        old_user_id = request.data.get('old_user_id')

        if not pull_request_id or not old_user_id:
            return Response(
                {"error": {"code": "BAD_REQUEST",
                           "message": "pull_request_id and old_user_id are required"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pull_request = get_object_or_404(PullRequest, pk=pull_request_id)

        if pull_request.status == 'MERGED':
            return Response(
                {"error": {"code": "PR_MERGED", "message": "cannot reassign on merged PR"}},
                status=status.HTTP_409_CONFLICT,
            )

        old_reviewer = get_object_or_404(User, pk=old_user_id)

        if old_reviewer not in pull_request.assigned_reviewers.all():
            return Response(
                {"error": {"code": "NOT_ASSIGNED",
                           "message": "reviewer is not assigned to this PR"}},
                status=status.HTTP_409_CONFLICT,
            )

        candidates = list(
            old_reviewer.team.members.filter(is_active=True)
            .exclude(pk__in=[old_reviewer.pk] + list(pull_request.assigned_reviewers.values_list('pk', flat=True)))
        )

        if not candidates:
            return Response(
                {"error": {"code": "NO_CANDIDATE",
                           "message": "no active replacement candidate in team"}},
                status=status.HTTP_409_CONFLICT,
            )

        new_reviewer = random.choice(candidates)

        pull_request.assigned_reviewers.remove(old_reviewer)
        pull_request.assigned_reviewers.add(new_reviewer)
        pull_request.save()

        serializer = self.get_serializer(pull_request)
        return Response({'pr': serializer.data, 'replaced_by': new_reviewer.pk}, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_user_statistics(request):
    stats = User.objects.annotate(assignments_count=Count(
        'review_assignments')).values('pk', 'username', 'assignments_count')

    data = [
        {
            'user_id': user['pk'],
            'username': user['username'],
            'assignments_count': user['assignments_count']
        } for user in stats
    ]
    return Response(data)


@api_view(['GET'])
def get_pr_statistics(request):
    stats = PullRequest.objects.annotate(reviewers_count=Count(
        'assigned_reviewers')).values('pk', 'pull_request_name', 'reviewers_count')

    data = [
        {
            'pull_request_id': pr['pk'],
            'pull_request_name': pr['pull_request_name'],
            'reviewers_count': pr['reviewers_count']
        } for pr in stats
    ]
    return Response(data)

from rest_framework import viewsets, status
from rest_framework.response import Response
from teams.models import Team
from users.models import User
from pull_requests.models import PullRequest
from .serializers import TeamSerializer, UserTeamSerializer, PullRequestSerializer
from rest_framework.decorators import action
from rest_framework.settings import api_settings
from django.shortcuts import get_object_or_404
from rest_framework import serializers


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
                {'error': {'code': 'TEAM_EXISTS', 'message': 'team_name уже существует'}},
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
                    {"error": {"code": "PR_EXISTS", "message": detail['pull_request_name']}},
                    status=status.HTTP_409_CONFLICT)
            else:
                return Response(
                    {"error": {"code": "NOT_FOUND", "message": "Автор/команда не найдены"}},
                    status=status.HTTP_404_NOT_FOUND)

        return Response({'pr': serializer.data}, status=status.HTTP_201_CREATED)

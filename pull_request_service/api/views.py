from rest_framework import viewsets, status
from rest_framework.response import Response
from teams.models import Team
from .serializers import TeamSerializer
from rest_framework.decorators import action
from rest_framework.settings import api_settings


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
        try:
            team = self.get_queryset().get(team_name=team_name)
        except Team.DoesNotExist:
            return Response(
                {'error': {'code': 'NOT_FOUND', 'message': 'Команда не найдена'}},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(team)
        return Response(serializer.data)

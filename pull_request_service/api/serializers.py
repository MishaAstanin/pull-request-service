import random

from teams.models import Team
from users.models import User
from pull_requests.models import PullRequest

from django.db import transaction
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = User
        fields = ('user_id', 'username', 'is_active')


class UserTeamSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='id', read_only=True)
    team = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = User
        fields = ('user_id', 'username', 'team', 'is_active')


class TeamSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True)

    class Meta:
        model = Team
        fields = ('team_name', 'members')

    def create(self, validated_data):
        members = validated_data.pop('members')

        with transaction.atomic():
            team = Team.objects.create(**validated_data)

            for user in members:
                User.objects.create(team=team, **user)

        return team


class PullRequestSerializer(serializers.ModelSerializer):
    pull_request_id = serializers.IntegerField(source='id', read_only=True)
    author_id = serializers.PrimaryKeyRelatedField(source='author', queryset=User.objects.all())

    class Meta:
        model = PullRequest
        fields = ('pull_request_id', 'pull_request_name', 'author_id',
                  'status', 'assigned_reviewers')
        read_only_fields = ('status', 'assigned_reviewers')

    def create(self, validated_data):
        author = validated_data.pop('author')

        if PullRequest.objects.filter(pull_request_name=validated_data['pull_request_name']).exists():
            raise serializers.ValidationError(
                {"pull_request_name": "PR already exists"})

        with transaction.atomic():
            pull_request = PullRequest.objects.create(
                author=author, status='OPEN', **validated_data)

            team_members = list(author.team.members.filter(
                is_active=True).exclude(pk=author.pk))
            assigned_reviewers = random.sample(
                team_members, k=min(2, len(team_members)))

            pull_request.assigned_reviewers.set(assigned_reviewers)
            pull_request.save()
        return pull_request


class PullRequestMergeSerializer(serializers.ModelSerializer):
    pull_request_id = serializers.IntegerField(source='id', read_only=True)
    author_id = serializers.PrimaryKeyRelatedField(source='author', queryset=User.objects.all())

    class Meta:
        model = PullRequest
        fields = ('pull_request_id', 'pull_request_name', 'author_id',
                  'status', 'assigned_reviewers', 'merged_at')
        read_only_fields = ('status', 'assigned_reviewers', 'merged_at')


class PullRequestShortSerializer(serializers.ModelSerializer):
    pull_request_id = serializers.IntegerField(source='id', read_only=True)
    author_id = serializers.PrimaryKeyRelatedField(source='author', queryset=User.objects.all())

    class Meta:
        model = PullRequest
        fields = ('pull_request_id', 'pull_request_name', 'author_id', 'status')
        read_only_fields = ('status',)

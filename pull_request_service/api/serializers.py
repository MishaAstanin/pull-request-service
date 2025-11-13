from rest_framework import serializers
from teams.models import Team
from users.models import User
from pull_requests.models import PullRequest
import random


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'is_active')

class UserTeamSerializer(serializers.ModelSerializer):
    team = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'team', 'is_active')


class TeamSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True)

    class Meta:
        model = Team
        fields = ('id', 'team_name', 'members') 
    
    def create(self, validated_data):
        members = validated_data.pop('members')

        team = Team.objects.create(**validated_data)

        for user in members:
            User.objects.create(team=team, **user)

        return team
    
class PullRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = PullRequest
        fields = ('id', 'pull_request_name', 'author', 'status', 'assigned_reviewers')
        read_only_fields = ('status', 'assigned_reviewers')

    def create(self, validated_data):
        author = validated_data.pop('author')
        
        if PullRequest.objects.filter(pull_request_name=validated_data['pull_request_name']).exists():
            raise serializers.ValidationError({"pull_request_name": "PR уже существует"})

        pull_request = PullRequest.objects.create(author=author, status='OPEN', **validated_data)
        
        team_members = list(author.team.members.filter(is_active=True).exclude(pk=author.pk))
        assigned_reviewers = random.sample(team_members, k=min(2, len(team_members)))

        pull_request.assigned_reviewers.set(assigned_reviewers)
        pull_request.save()
        return pull_request    
    
class PullRequestMergeSerializer(serializers.ModelSerializer):

    class Meta:
        model = PullRequest
        fields = ('id', 'pull_request_name', 'author', 'status', 'assigned_reviewers', 'merged_at')
        read_only_fields = ('status', 'assigned_reviewers', 'merged_at')
    
class PullRequestShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = PullRequest
        fields = ('id', 'pull_request_name', 'author', 'status')
        read_only_fields = ('status',)

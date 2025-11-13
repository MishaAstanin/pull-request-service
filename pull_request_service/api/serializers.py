from rest_framework import serializers
from teams.models import Team
from users.models import User


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

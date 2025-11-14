import json

from rest_framework import status
from rest_framework.test import APITestCase

from pull_requests.models import PullRequest
from teams.models import Team
from users.models import User


class TeamAPITestCase(APITestCase):
    def setUp(self):
        self.team_data = {
            "team_name": "TestTeam",
            "members": [
                {"username": "Alice", "is_active": True},
                {"username": "Bob", "is_active": True}
            ]
        }

    def test_add_team_success(self):
        response = self.client.post(
            '/api/team/add/', data=json.dumps(self.team_data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Team.objects.filter(team_name='TestTeam').exists())
        team = Team.objects.get(team_name='TestTeam')
        self.assertEqual(team.members.count(), 2)

    def test_add_team_already_exists(self):
        Team.objects.create(team_name='TestTeam')
        response = self.client.post(
            '/api/team/add/', data=json.dumps(self.team_data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_team_success(self):
        Team.objects.create(team_name='TestTeam')
        response = self.client.get('/api/team/get/', {'team_name': 'TestTeam'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('team_name'), 'TestTeam')

    def test_get_team_not_found(self):
        response = self.client.get('/api/team/get/', {'team_name': 'NoTeam'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class UserAPITestCase(APITestCase):
    def setUp(self):
        self.team = Team.objects.create(team_name='Team1')
        self.user = User.objects.create(
            username='user1', team=self.team, is_active=True)
        self.team2 = Team.objects.create(team_name='Team2')

    def test_set_active_user(self):
        response = self.client.post('/api/users/setIsActive/', data=json.dumps(
            {'user_id': self.user.id, 'is_active': False}), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_set_active_missing_fields(self):
        response = self.client.post(
            '/api/users/setIsActive/', data=json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_review_prs_missing_user_id(self):
        response = self.client.get('/api/users/getReview/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_review_prs_success(self):
        pr = PullRequest.objects.create(
            pull_request_name='pr1', author=self.user, status='OPEN')
        pr.assigned_reviewers.add(self.user)
        response = self.client.get(
            '/api/users/getReview/', {'user_id': self.user.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(str(self.user.id), data['user_id'])
        self.assertTrue(len(data['pull_requests']) >= 1)

    def test_change_team_success(self):
        response = self.client.post('/api/users/changeTeam/', data=json.dumps(
            {'user_id': self.user.id, 'team_name': self.team2.team_name}), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.team, self.team2)

    def test_change_team_missing_fields(self):
        response = self.client.post(
            '/api/users/changeTeam/', data=json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_team_with_open_pr(self):
        pr = PullRequest.objects.create(
            pull_request_name='pr1', author=self.user, status='OPEN')
        pr.assigned_reviewers.add(self.user)
        response = self.client.post('/api/users/changeTeam/', data=json.dumps(
            {'user_id': self.user.id, 'team_name': self.team2.team_name}), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)


class PullRequestAPITestCase(APITestCase):
    def setUp(self):
        self.team = Team.objects.create(team_name='Team1')
        self.user = User.objects.create(
            username='user1', team=self.team, is_active=True)
        self.user2 = User.objects.create(
            username='user2', team=self.team, is_active=True)

    def test_create_pull_request_success(self):
        data = {'pull_request_name': 'PR1',
                'author_id': self.user.id, 'status': 'OPEN'}
        response = self.client.post(
            '/api/pullRequest/create/', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PullRequest.objects.filter(
            pull_request_name='PR1').exists())

    def test_create_pull_request_conflict(self):
        PullRequest.objects.create(
            pull_request_name='PR1', author=self.user, status='OPEN')
        data = {'pull_request_name': 'PR1',
                'author_id': self.user.id, 'status': 'OPEN'}
        response = self.client.post(
            '/api/pullRequest/create/', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_merge_pull_request_success(self):
        pr = PullRequest.objects.create(
            pull_request_name='PR1', author=self.user, status='OPEN')
        response = self.client.post('/api/pullRequest/merge/', data=json.dumps(
            {'pull_request_id': pr.id}), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pr.refresh_from_db()
        self.assertEqual(pr.status, 'MERGED')

    def test_merge_pull_request_no_id(self):
        response = self.client.post(
            '/api/pullRequest/merge/', data=json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reassign_reviewer_success(self):
        pr = PullRequest.objects.create(
            pull_request_name='PR1', author=self.user, status='OPEN')
        pr.assigned_reviewers.set([self.user, self.user2])
        data = {'pull_request_id': pr.id, 'old_user_id': self.user.id}
        response = self.client.post(
            '/api/pullRequest/reassign/', data=json.dumps(data), content_type='application/json')
        self.assertIn(response.status_code, [
                      status.HTTP_200_OK, status.HTTP_409_CONFLICT])

    def test_reassign_reviewer_no_candidates(self):
        pr = PullRequest.objects.create(
            pull_request_name='PR1', author=self.user, status='OPEN')
        pr.assigned_reviewers.set([self.user])
        self.user.team.members.exclude(pk=self.user.pk).delete()

        data = {'pull_request_id': pr.id, 'old_user_id': self.user.id}
        response = self.client.post(
            '/api/pullRequest/reassign/', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)


class StatisticsAPITestCase(APITestCase):
    def setUp(self):
        self.team = Team.objects.create(team_name='Team1')
        self.user = User.objects.create(
            username='user1', team=self.team, is_active=True)
        self.pr = PullRequest.objects.create(
            pull_request_name='PR1', author=self.user, status='OPEN')
        self.pr.assigned_reviewers.add(self.user)

    def test_get_user_statistics(self):
        response = self.client.get('/api/statisticsUser/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            any(item['user_id'] == self.user.id for item in response.json()))

    def test_get_pr_statistics(self):
        response = self.client.get('/api/statisticsPR/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(item['pull_request_id'] ==
                        self.pr.id for item in response.json()))

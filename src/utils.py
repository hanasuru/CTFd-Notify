from helper import limit, run_in_thread
from bs4 import BeautifulSoup as bs

import config
import requests
import database

import queue

API_ENDPOINT = {
    'login': '/login',
    'chall': '/api/v1/challenges',
    'challid': '/api/v1/challenges/{}',
    'solve': '/api/v1/challenges/{}/solves',
    'scoreboard': '/api/v1/scoreboard',
    'teams': '/api/v1/teams',
    'users': '/api/v1/users'
}


class Request(object):
    def __init__(self, username, password, proxy, url):
        self.current_submission = dict()
        self.challenges = dict()
        self.teams = dict()

        self.username = username
        self.password = password
        self.proxy = proxy
        self.url = url

        self.create_session()

    def create_session(self):
        self.ses = requests.session()
        self.ses.proxies.update(self.proxy)

        self.login()

    def get_csrf_token(self, target_url):
        response = self.ses.get(target_url)
        response_soup = bs(response.text, 'lxml')

        nonce = response_soup.find(
            'input', {'name':'nonce'}
        )

        return nonce.get('value')

    def login(self):
        target_url = self.url + API_ENDPOINT.get('login')
        csrf_token = self.get_csrf_token(target_url)
    
        auth_data = {
            'name': self.username,
            'password': self.password,
            'nonce': csrf_token
        }

        post_response = self.ses.post(target_url, data=auth_data)

        assert('incorrect' not in post_response.text)

    def get_scoreboards(self):
        target_url = self.url + API_ENDPOINT.get('scoreboard')
        response = self.ses.get(target_url).json()['data']

        scoreboard_data = []
        for data in response:
            position = data.get('pos')
            team_id = data.get('account_id')
            score = data.get('score')

            scoreboard_data.append({
                'rank': position,
                'team_name': self.teams[team_id],
                'score': score
            })

        return scoreboard_data

    def get_teams(self):
        target_url = self.url + API_ENDPOINT.get(config.MODE)
        response = self.ses.get(target_url)

        try:
            teams_data = response.json()['data']
        except ValueError:
            pass
        else:
            for team in teams_data:
                team_id = team.get('id')
                team_name = team.get('name')

                database.add_team(team_id, team_name)
                self.teams[team_id] = team_name

    def get_update_challenges(self):
        target_url = self.url + API_ENDPOINT.get('chall')
        response = self.ses.get(target_url)
        
        challenges = dict()

        try:
            challenges_data = response.json()['data']
        except ValueError as e:
            print(str(e))
        else:
            for data in challenges_data:
                challenges_id = data.get('id')
                challenges_name = data.get('name')
                challenges_value = data.get('value')
                challenges_category = data.get('category')

                status = database.add_challenge(
                    challenges_id,
                    challenges_name,
                    challenges_value,
                    challenges_category
                )

                if status:
                    challenges[challenges_id] = f'**{challenges_category}** challenge: `{challenges_name}`'
                
                self.challenges[challenges_id] = challenges_name

        return challenges

    @limit(config.WORKER)
    @run_in_thread
    def get_submission_by_id(self, challenge_id):
        target_url = self.url + API_ENDPOINT.get('solve').format(challenge_id)
        response = self.ses.get(target_url)
        
        self.parse_submission_data(
            challenge_id,
            response.json().get('data', list())
        )


    @limit(config.WORKER)
    def get_submissions(self):
        for challenge in self.challenges.items():
            challenge_id, challenge_name = challenge
            self.get_submission_by_id(challenge_id)
        
    def parse_submission_data(self, challenge_id, submission_data):

        for enum, data in enumerate(submission_data):
            team_id = data.get('account_id')
            team_name = data.get('name')
            timestamp = data.get('date')
            
            status = database.add_submission(challenge_id, team_id, timestamp)
            if status:
                value = self.current_submission.get(timestamp, list())

                if not value:
                    self.current_submission[timestamp] = value

                if len(submission_data) == 1 or enum == 0:
                    first_blood_status = True
                else:
                    first_blood_status = False

                value.append({
                    'team_name': team_name,
                    'challenge_name': self.challenges[challenge_id],
                    'first_blood_status': first_blood_status
                })


def get_session():
    instance = Request(
        config.USERNAME,
        config.PASSWORD,
        config.PROXY,
        config.CTFD_URL
    )

    return instance
# TODO: add requirements.txt
import pandas as pd
import requests
from datetime import datetime
from requests_paginator import RequestsPaginator


BASE_URL = 'https://api.github.com'
DATETIME_FMT = '%Y-%m-%dT%H:%M:%SZ'


class Repo:
    def __init__(self, repo_id, name, url, default_branch):
        self.id = repo_id
        self.name = name
        self.url = url
        self.default_branch = default_branch

# TODO: Request branches
class Branch:
    def __init__(self, branch_name):
        self.name = branch_name

class Commit:
    def __init__(self, sha, author_name, author_email, message, date: datetime,
                 additions, deletions, url):
        self.sha = sha
        self.author_name = author_name
        self.author_email = author_email
        self.commit_message = message
        self.commit_date = date
        self.additions = additions
        self.deletions = deletions
        self.url = url


class GitHubExtractor:
    def __init__(self, user, api_token):
        self.user = user
        self.api_token = api_token

    def __github_request(self, url):
        """Make a request to GitHub's API using the given URL. 
        If response is paginated, make a request to each page.
        Returns API response as a dict, or list of dicts if multiple JSON objects 
        returned."""
        response = []

        if self.api_token == "":
            headers = None
        else:
            headers = {
                'Authorization': 'Bearer '+self.api_token,
            }

        class GitHubPaginator(RequestsPaginator):
            """Updates RequestsPaginator with necessary authorization."""
            def __iter__(self):
                while self.next_page:
                    r = requests.get(self.next_page, headers=headers)
                    this_page = self.next_page
                    yield r
                    self.next_page = self.get_next_page(r)
    
        def get_next_page(page):
            """get_next_page method for GitHubPaginator instance."""
            body = page.json()
            if 'message' in body and body['message'] != '':  # invalid request
                raise Exception(body['message'])
            try:
                next_page = page.links['next']['url']
                print(next_page)
            except KeyError:
                next_page = None
            if next_page:
                return page.links['next']['url']
            return None
    
        pages = GitHubPaginator(
            url,
            get_next_page
        )
    
        for page in pages:
            page_json = page.json()
            if type(page_json) is list:
                response.extend(page.json())
            else:
                return page_json
    
        return response
    
    # TODO: Find a way to a list all repositories (public and private) that a
    # user has contributed to (not just has membership of)
    def get_repos(self):
        """Request the given user's public repositories.
        Returns a list of Repo objects."""
        repos = []
        url = BASE_URL + '/users/{}/repos'.format(self.user)

        print('Requesting repo data...')
        response = self.__github_request(url)

        for repo in response:
            repos.append(
                Repo(repo['id'], repo['name'], repo['html_url'],
                      repo['default_branch'])
                )

        return repos

    # TODO: See if you can limit commits to just those authored by the given user
    def get_commits(self, repo):
        """Request the given user's commits to a given repository.
        Returns a list of commit objects."""
        commits = []
        url = BASE_URL + '/repos/{}/{}/commits'.format(self.user, repo)
        
        print('Requesting commit data for {}...'.format(repo))
        response = self.__github_request(url)
        
        for commit in response:
            commits.append(
                self.get_commit_data(repo, commit['sha'])
                )

        return commits
    
    def get_commit_data(self, repo, commit):
        url = BASE_URL + '/repos/{}/{}/commits/{}'.format(self.user, repo, commit)
        response = self.__github_request(url)
        
        return Commit(
            response['sha'],
            response['commit']['author']['name'],
            response['commit']['author']['email'],
            response['commit']['message'],
            datetime.strptime(response['commit']['author']['date'],
                              DATETIME_FMT),
            response['stats']['additions'],
            response['stats']['deletions'],
            response['html_url']
            )
        
    # TODO: Export repositories and commits to csv
    def export_to_csv(self, obj_list):
        """Convert a list of objects into a dataframe and export that dataframe
        to a csv file."""
        pass

# TODO: Error handling for incorrectly spelled/nonexistent users and tokens
if __name__ == "__main__":
    username = input("Enter GitHub username: ")
    api_token = input("Enter API token, or press Enter if no token: ")

    # testing
    github_extractor = GitHubExtractor(username, api_token)
    repos = github_extractor.get_repos()
    print([repo.name for repo in repos])

    # TODO: For each repo, get the commits for that repo
    for repo in repos:
        commits = github_extractor.get_commits(repo.name)
        print([commit.sha for commit in commits])
    
    # TODO: Once repo and commit data are both stored, export to csv

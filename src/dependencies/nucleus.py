import json

import aiohttp

# import config


class CookiesExpired(Exception):
    """Raised when the account cookies are detected to be expired"""


class Nucleus:
    domain = 'https://nucleus.amcspsgtech.in'
    login_url = f'{domain}/oauth'
    server_url = f'{domain}/server'
    oauth_path = '/oauth'
    class_path = '/class'
    resources_path = '/resources'
    assignments_path = '/assignment'
    schedule_path = '/schedule/schedule'

    def __init__(self, username: str, cookies: dict = None):
        self.username = username
        self.cookies = cookies

    async def __get_request_to_server__(self,  headers: dict = None):
        async with aiohttp.ClientSession(cookies=self.cookies) as session:
            async with session.get(url=Nucleus.server_url, headers=headers) as resp:
                response_bin = await resp.read()
                response_str = response_bin.decode()
                try:
                    response_dict = json.loads(response_str)
                    return response_dict
                except json.JSONDecodeError:
                    return {}

    @staticmethod
    async def login(username, password):
        print(f'Logging in as {username}')
        auth_credentials = {
            "rollNo": username,
            "password": password
        }
        headers = {"path": Nucleus.oauth_path}
        async with aiohttp.ClientSession() as session:
            async with session.post(url=Nucleus.login_url, data=auth_credentials, headers=headers) as resp:
                response_bin = await resp.read()
                response_str = response_bin.decode()
                try:
                    response_dict = json.loads(response_str)
                    print(response_dict)
                    cookies_dict = {}
                    for cookie in session.cookie_jar:
                        cookies_dict[cookie.key] = cookie.value
                    return Nucleus(username, cookies_dict)
                except json.JSONDecodeError:
                    return None

    @staticmethod
    async def check_for_expiry(cookies: dict):
        raise NotImplementedError

    def schedule(self, date: str):
        headers = {"path": f'{Nucleus.schedule_path}/{date}', "referrer": f'{Nucleus.domain}/schedule'}
        return self.__get_request_to_server__(headers)

    def assignments(self, course_id: str = 'all'):
        headers = {"path": f'{Nucleus.assignments_path}?courseId={course_id}&submissionDetails=true',
                   "referrer": f'{Nucleus.domain}/assignments'}
        return self.__get_request_to_server__(headers)

    def resources(self, course_id: str):
        headers = {"path": f'{Nucleus.resources_path}?courseId={course_id}',
                   "referrer": f'{Nucleus.domain}/resources?courseId={course_id}'}
        return self.__get_request_to_server__(headers)

    def class_details(self, class_id: str):
        headers = {"path": f'{Nucleus.class_path}/{class_id}',
                   "referrer": f'{Nucleus.domain}/class?classId={class_id}'}
        return self.__get_request_to_server__(headers)

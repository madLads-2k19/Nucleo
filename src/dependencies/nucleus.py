import json
from datetime import datetime

import aiohttp

from dependencies.database import Database

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
    profile_path = '/profile'

    def __init__(self, username: str, cookies: dict = None):
        self.username = username
        self.cookies = cookies

    async def __get_request_to_server__(self, headers: dict = None):
        async with aiohttp.request('GET', Nucleus.server_url, headers=headers, cookies=self.cookies) as resp:
            try:
                response_bin = await resp.read()
                response_str = response_bin.decode()
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

    def get_profile(self):
        headers = {"path": f'{Nucleus.profile_path}',
                   "referrer": f'{Nucleus.domain}/profile'}
        return self.__get_request_to_server__(headers)

    async def update_database(self, db: Database, discord_id: int, discord_username: str, admin=False):
        # TODO: Check if cookies expire
        response = await self.get_profile()
        user_details = response['data']
        first_name = user_details['firstName']
        last_name = user_details['lastName']
        email = user_details['email']
        mobile = user_details['mobileNo']
        class_id = user_details['classId']
        year = user_details['year']
        cookies = json.dumps(self.cookies)

        # user = db.get_user(user_id=self.username)
        try:
            discord_user = await db.get_discord_user(discord_id=discord_id)

            if admin:
                core_courses = user_details['courses']['core']
                elective_courses = user_details['courses']['elective']
                db_courses = await db.get_nucleus_course(class_id)
                for core in core_courses:
                    if core['courseId'] not in db_courses:
                        await db.add_nucleus_course(class_id, core['courseId'], core['courseName'], False)

                for elective in elective_courses:
                    if elective['courseId'] not in db_courses:
                        await db.add_nucleus_course(class_id, elective['courseId'], elective['courseName'], True)
            elif discord_user:
                await db.update_nucleus_user(self.username, first_name, last_name, email, mobile, class_id, year,
                                             cookies, datetime.now(), discord_id)

            else:
                await db.add_discord_user(discord_id, discord_username)
                await db.add_nucleus_user(self.username, first_name, last_name, email, mobile, class_id, year,
                                          cookies, datetime.now(), discord_id)

        except Exception as err:
            print(err)

async def main():
    acc = await Nucleus.login('19PW22', 'pritam222')
    res = await acc.assignments()
    # resp = await acc.get_profile()
    print(res)


if __name__ == '__main__':
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

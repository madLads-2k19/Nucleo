import json
import random
import re
import time
from datetime import datetime, timedelta
from typing import Optional, Union

import dateparser
from discord import Embed
from discord.ext import commands, tasks
from discord.ext.commands import Context

from dependencies.database import Database
from dependencies.nucleus import Nucleus
from . import bot_checks
from ..bot_utils import generate_embed, emoji_selection_detector

NUMERIC_EMOTES = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣', '0⃣']


def generate_assignment_embed(assignment: dict, description: str):
    utc_deadline = datetime.strptime(assignment['targetDateTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
    deadline = utc_deadline + timedelta(hours=5, minutes=30)
    color = random.randint(0, 16777215)
    embed_dict = {
        "color": color,
        "title": assignment['title'],
        "description": description,
        "url": assignment['question']['details']['previewLink'],
        "fields": [
            {
                "name": "Course Name",
                "value": assignment['courseName'],
                "inline": True
            },
            {
                "name": "Course ID",
                "value": assignment['courseId'],
                "inline": True
            },
            {
                "name": "Description",
                "value": assignment['description']
            },
            {
                "name": "Due Date",
                "value": deadline.strftime("%d/%m/%Y"),
                "inline": True
            },
            {
                "name": "Due Time",
                "value": deadline.strftime("%H:%M:%S"),
                "inline": True
            }
        ]
    }
    return Embed.from_dict(embed_dict)


def generate_schedule_embed(schedule: dict, date: datetime, meet_urls: dict):
    fields = []
    for timing in schedule:
        for class_ in schedule[timing]:
            field = {
                'name': timing + ' - ' + class_['title'],
                'value': ''
            }
            if 'type' in class_:
                if class_['type'] == 'gmeet':
                    field['value'] = f"[Meet Link]({meet_urls[class_['courseId']]})"
                    field['value'] += ' Extra Class :pencil:'
                elif class_['type'] == 'assignment':
                    field['value'] += ' Assignment Deadline :notepad_spiral:'
                elif class_['type'] == 'announcement':
                    field['value'] += ' Announcement :speech_balloon:'
            else:
                field['value'] = f"[Meet Link]({meet_urls[class_['courseId']]})"

            fields.append(field)
    date_string = date.strftime("%Y-%m-%d")
    description = 'No classes scheduled, Have a great day :wink:' if fields == [] else ''
    color = random.randint(0, 16777215)
    embed_dict = {
        "color": color,
        "title": f'Schedule for {date_string}',
        "description": description,
        "url": f'https://nucleus.amcspsgtech.in/schedule?date={date_string}',
        "fields": fields
    }
    return Embed.from_dict(embed_dict)


def generate_submitted_assignment_embed(submitted: list, color: int):
    fields = []
    for assignment in submitted:
        assignment_added_on_time = assignment['addedOn']
        submission_added_on_time = assignment['submissions']['submissionDetails']["details"]['addedOn']

        assignment_preview_link = assignment["question"]["details"]["previewLink"]
        submission_preview_link = assignment["submissions"]["submissionDetails"]["details"]["previewLink"]

        added_on = datetime.strptime(assignment_added_on_time, '%Y-%m-%dT%H:%M:%S.%fZ')
        added_on += timedelta(hours=5, minutes=30)
        submitted_date = datetime.strptime(submission_added_on_time, '%Y-%m-%dT%H:%M:%S.%fZ')
        submitted_date += timedelta(hours=5, minutes=30)
        field = {
            'name': assignment['title'],
            'value': assignment["courseName"],
            'inline': True
        }
        field_left = {
            'name': 'Added On',
            'value': f'[{added_on.strftime("%d/%m/%Y")}]({assignment_preview_link})',
            'inline': True
        }
        field_right = {
            'name': 'Submitted On',
            'value': f'[{submitted_date.strftime("%d/%m/%Y")}]({submission_preview_link})',
            'inline': True
        }
        fields.append(field)
        fields.append(field_left)
        fields.append(field_right)

    embed_dict = {
        "color": color,
        "title": f'Assignments',
        "description": 'Submitted assignments',
        "url": f'https://nucleus.amcspsgtech.in/assignments',
        "fields": fields
    }

    return Embed.from_dict(embed_dict)


def generate_resources_embed(resources: list, color: int):
    fields = []
    course_id = resources[0]['courseId']
    for resource in resources:
        added_on_time = resource["details"]['addedOn']
        preview_link = resource["details"]["previewLink"]

        added_on = datetime.strptime(added_on_time, '%Y-%m-%dT%H:%M:%S.%fZ')
        added_on += timedelta(hours=5, minutes=30)
        if 'type' in resource:
            if resource['type'] == 'book':
                title_emote = ':books:'
            elif resource['type'] == 'questions':
                title_emote = ':question:'
            elif resource['type'] == 'notes':
                title_emote = ':page_facing_up:'
            elif resource['type'] == 'presentation':
                title_emote = ':bookmark_tabs:'
            elif resource['type'] == 'homework':
                title_emote = ':pencil:'
            elif resource['type'] == 'worksheet':
                title_emote = ':bookmark:'
        else:
            title_emote = ''

        field = {
            'name': title_emote + ' ' + resource['name'],
            'value': f'[{added_on.strftime("%d/%m/%Y")}]({preview_link})',
        }
        fields.append(field)

    embed_dict = {
        "color": color,
        "title": course_id,
        "description": 'Resources',
        "url": f'https://nucleus.amcspsgtech.in/resources?courseId={course_id}',
        "fields": fields
    }

    return Embed.from_dict(embed_dict)


def generate_resource_embed(resource: dict, description: str):
    added_on = datetime.strptime(resource['details']['addedOn'], '%Y-%m-%dT%H:%M:%S.%fZ')
    added_on += timedelta(hours=5, minutes=30)
    color = random.randint(0, 16777215)
    tags = '| '.join(resource['tags'])

    embed_dict = {
        "color": color,
        "title": resource['name'],
        "description": description,
        "url": resource['details']['previewLink'],
        "fields": [
            {
                "name": "Course ID",
                "value": resource['courseId'],
                "inline": True
            },
            {
                "name": "Added On",
                "value": added_on.strftime("%d/%m/%Y"),
                "inline": True
            },
            {
                "name": "Type",
                "value": resource['type'].capitalize(),
                "inline": True
            },
            {
                "name": "Tags",
                "value": tags,
                # "inline": True
            }
        ]
    }
    return Embed.from_dict(embed_dict)


class NucleusCog(commands.Cog):
    class_regex_check = r'[12][0-9][A-Z]{2}'

    def __init__(self, bot):
        self.bot = bot
        self.db: Database = bot.db
        self.assignments_detector.add_exception_type(Exception)
        self.assignments_detector.start()

    @staticmethod
    def __get_date_from_date_string(date_string: str) -> Union[datetime, str]:
        date = datetime.now()
        if date_string:
            date = dateparser.parse(date_string)
            if date is None:
                return f"Can't parse out a date from `{date_string}`"
        return date

    @staticmethod
    async def __interactive_course_selection(ctx: Context, user: Nucleus) -> Optional[str]:
        user_profile = await user.get_profile()
        user_courses = user_profile['data']['courses']
        core_courses = user_courses['core']
        elective_courses = user_courses['elective']
        courses = []
        courses.extend(core_courses)
        courses.extend(elective_courses)

        color = random.randint(0, 16777215)
        description = 'React for the course that you want resources'
        embed = generate_embed(f'Course Selection for {user.username}', ctx.author, description=description, color=color)
        i = 0
        for course in courses:
            if course['courseId'].endswith('SEM') or course['courseId'].endswith('TWM'):
                continue
            name = f"{NUMERIC_EMOTES[i]} - {course['courseId']}"
            value = course['courseName'].capitalize()
            i += 1
            embed.add_field(name=name, value=value)

        chosen_emote = await emoji_selection_detector(ctx, NUMERIC_EMOTES[:i], embed, 30)
        if chosen_emote is None:
            return None
        selected_course = courses[NUMERIC_EMOTES.index(chosen_emote)]
        return selected_course['courseId']

    async def __get_nucleus_user_by_discord_id(self, discord_id: int) -> Union[str, Nucleus]:
        discord_user = await self.db.get_user_by_discord_id(discord_id)
        if not discord_user:
            return 'Login to perform this command.'
        cookies = json.loads(discord_user[8])
        user_id = discord_user[0]
        user = Nucleus(user_id, cookies)
        if await user.is_expired():
            return 'Session expired, Please login to perform this command.'
        return user

    @bot_checks.is_whitelist(allow_dm=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(brief='Generates nucleus schedule for the given date(defaults to today)')
    async def schedule(self, ctx: Context, *date_string):
        """
        Generates an embed of the nucleus schedule for the given date(defaults to today in case not specified).

        Date String: str -  Date for which the schedule is to be generated.
                            We use [dataparser](https://pypi.org/project/dateparser/) to parse the dates.
                            Examples: tomorrow, next friday, 23(for 23rd of this month), 8-8 (for 8th August)

        You need to be logged in to use this command.
        """
        # TODO: use a better aliasing mechanism
        user_string = ' '.join(date_string).replace('tom', 'tomorrow').replace('yest', 'yesterday')

        date = self.__get_date_from_date_string(user_string)
        if isinstance(date, str):
            return await ctx.send(date)
        user = await self.__get_nucleus_user_by_discord_id(ctx.author.id)
        if isinstance(user, str):
            return await ctx.send(user)

        schedule_response = await user.schedule(date.strftime("%Y-%m-%d"))
        schedule = schedule_response['data']['schedule']
        meet_urls = schedule_response['data']['meetUrls']
        embed = generate_schedule_embed(schedule, date, meet_urls)
        await ctx.send(embed=embed)

    @bot_checks.is_whitelist(allow_dm=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(brief='Generates nucleus user assignments (unsubmitted assignments by default)')
    async def assignments(self, ctx: Context, option: Optional[str] = ''):
        """
        Generates an Embed that contains logged in user's assignments (defaults to unsubmitted assignments only).

        Option: str - Option that allows to generate submitted/unsubmitted assignments when set to 'all'.

        You need to be logged in to use this command.
        """
        try:
            if option != '' and option != 'all':
                return await ctx.send('Invalid option!')

            user = await self.__get_nucleus_user_by_discord_id(ctx.author.id)
            if isinstance(user, str):
                return await ctx.send(user)
            not_submitted = []
            submitted = []
            assignments_response = await user.assignments()
            assignments = assignments_response['data']['assignments']
            if not assignments:
                return await ctx.message.author.send('No assignments uploaded.')
            for assignment in assignments:
                if assignment['submissions']['submissionDetails'] == {}:
                    not_submitted.append(assignment)
                else:
                    submitted.append(assignment)

            if option == 'all':
                counter = 0
                color = random.randint(0, 16777215)
                if not submitted:
                    await ctx.message.author.send('You have not submitted any assignments.')
                while counter < len(submitted):
                    assignments_iter = submitted[counter:counter + 8]
                    embed_s = generate_submitted_assignment_embed(assignments_iter, color)
                    await ctx.message.author.send(embed=embed_s)
                    counter += 8
            if not not_submitted:
                return await ctx.message.author.send('You have submitted all assignments till date.')

            for assignment in not_submitted:
                embed_uns = generate_assignment_embed(assignment, 'Assignments not Submitted')
                await ctx.message.author.send(embed=embed_uns)

        except Exception as err:
            print(err)

    @bot_checks.is_whitelist(allow_dm=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(brief='Generates nucleus course resources')
    async def resources(self, ctx: Context, course_id: Optional[str] = None):
        """
        Generates an Embed that contains logged in user's resources.

        course_id: str - Option that allows to generate course's resources when set, generates reaction specific
        message by default.

        You need to be logged in to use this command.
        """
        try:
            user = await self.__get_nucleus_user_by_discord_id(ctx.author.id)
            if isinstance(user, str):
                return await ctx.send(user)

            if course_id == '' or course_id is None:
                course_id = await self.__interactive_course_selection(ctx, user)
                if course_id is None:
                    return

            course_match = re.match(r'[12][0-9][A-Za-z]{2,3}[0-9]{2}', course_id)
            if course_match is None:
                return await ctx.reply('Invalid courseId!')

            resources_response = await user.resources(course_id)
            resources = resources_response['data']
            if not resources:
                return await ctx.message.author.send(f'{course_id} - No resources uploaded.')

            counter = 0
            color = random.randint(0, 16777215)

            while counter < len(resources):
                resource_iter = resources[counter:counter + 8]
                embed_r = generate_resources_embed(resource_iter, color)
                await ctx.message.author.send(embed=embed_r)
                counter += 8

        except Exception as err:
            print(err)

    @tasks.loop(seconds=600)
    async def assignments_detector(self):
        print(f'Detector Running! - {datetime.now()}')
        try:
            alert_accounts = await self.db.get_alert_accounts()
            for username, cookies_str, class_id, password in alert_accounts:
                cookies = json.loads(cookies_str)
                user = Nucleus(username, cookies)
                user_response = await user.get_profile()
                if user_response == {}:
                    user = await Nucleus.login(username, password)
                    if user:
                        await self.db.update_alert_account(user.username, json.dumps(user.cookies), password)
                    else:
                        admin_channel = self.bot.get_channel(755021030489325638)
                        await admin_channel.send(f'@everyone Account cookie refresh failed - `{username}`')
                        time.sleep(3600)
                        continue

                assignments_response = await user.assignments()
                assignments = assignments_response["data"]["assignments"]

                new_assignments = []
                nucleus_courses = await self.db.get_assignments_last_checked(class_id)

                for assignment in assignments:
                    course_id = assignment['courseId']
                    added_on_str = assignment['addedOn']
                    added_on = datetime.strptime(added_on_str, '%Y-%m-%dT%H:%M:%S.%fZ')
                    for course in nucleus_courses:
                        if course_id == course[0]:
                            last_checked = course[1]
                            if added_on > last_checked:
                                new_assignments.append(assignment)
                                await self.db.update_assignments_last_uploaded(class_id, course_id, added_on)

                new_resources = []
                nucleus_courses = await self.db.get_resources_last_checked(class_id)

                for course in nucleus_courses:
                    course_response = await user.resources(course[0])
                    for resource in course_response['data']:
                        added_on_str = resource['details']['addedOn']
                        last_checked = course[1]
                        added_on = datetime.strptime(added_on_str, '%Y-%m-%dT%H:%M:%S.%fZ')
                        if added_on > last_checked:
                            new_resources.append(resource)
                            await self.db.update_resouces_last_uploaded(class_id, resource['courseId'], added_on)

                if len(new_assignments) != 0 or len(new_resources) != 0:
                    try:
                        alert_details = await self.db.get_alert_details(class_id)
                        for channel_id, guild_id, role_id in alert_details:
                            guild = self.bot.get_guild(guild_id)
                            channel = guild.get_channel(channel_id)
                            role = guild.get_role(role_id)
                            if role:
                                if new_assignments and new_resources:
                                    alert_type = 'Assignments + Resources'
                                else:
                                    alert_type = 'Assignments' if new_assignments else 'Resources'
                                await channel.send(f'{role.mention} - {alert_type}')

                            for assignment in new_assignments:
                                embed = generate_assignment_embed(assignment, description='New Assignment Detected!')
                                await channel.send(embed=embed)

                            for resource in new_resources:
                                if resource['type'] != 'assignment':
                                    embed = generate_resource_embed(resource, description='New resource uploaded!')
                                    await channel.send(embed=embed)

                    except Exception as err:
                        print('Error inside loop', err)

        except Exception as err:
            print(f'Error outside loop {err}')

    @assignments_detector.before_loop
    async def before_detection(self):
        await self.bot.wait_until_ready()

    @bot_checks.is_whitelist()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(brief='Generate nucleus login cookies for the current discord user')
    async def login(self, ctx: Context, user_id: str):
        """
        Login as a nucleus user and generate the cookies. Passwords are not cached and are removed immediately after the
        login request. [Source](https://github.com/madLads-2k19/Nucleo/blob/master/src/bot/cogs/nucleus_cog.py) can be
        found here.

        User ID: str - Nuclues user ID to login as.
        """

        def dm_check(message):
            if message.channel.id == ctx.author.dm_channel.id and message.author == ctx.author:
                return True

        user_match = re.match(r'[12][0-9][A-Z]{2}[0-9]{2}', user_id)
        if user_match is None:
            return await ctx.reply('Invalid UserName!, ex: 17PD39')

        await ctx.message.author.send('Please send me the password...')
        pass_message = await self.bot.wait_for('message', check=dm_check, timeout=30)
        password = pass_message.content
        if password == '':
            return await ctx.message.author.send('Please try logging in again.')

        user = await Nucleus.login(user_match.string, password)
        if type(user) is str:
            return await ctx.author.send(f'`Login failed due to {user}`')
        elif type(user) is None:
            return await ctx.author.send('`Login failed due to unknown reasons. Please contact the devs....`')
        await ctx.message.author.send('`Login Succeeded!`')
        try:
            await user.update_database(self.db, ctx.message.author.id, ctx.message.author.name)
        except Exception as err:
            print(err)

    @bot_checks.is_whitelist()
    @bot_checks.check_permission_level(8)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(brief='Add privileged accounts for assignment detector')
    async def alert_account(self, ctx: Context, user_id: str):
        """
        Adds nuclues user accounts which are used for detecting assignments when added by teachers. Passwords are stored
        into database to refresh cookies.

        User ID: str - Nuclues user ID to login as.
        """

        def dm_check(message):
            if message.channel.id == ctx.author.dm_channel.id and message.author == ctx.author:
                return True

        user_match = re.match(r'[12][0-9][A-Z]{2}[0-9]{2}', user_id)
        if user_match is None:
            return await ctx.reply('Invalid UserName!, ex: 17PD39')

        await ctx.message.author.send('Please send me the password...')
        pass_message = await self.bot.wait_for('message', check=dm_check, timeout=30)
        password = pass_message.content
        if password == '':
            return await ctx.message.author.send('Please try logging in again.')

        user = await Nucleus.login(user_match.string, password)
        if type(user) is str:
            return await ctx.author.send(f'`Login failed due to {user}`')
        elif type(user) is None:
            return await ctx.author.send('`Login failed due to unknown reasons. Please contact the devs....`')
        await ctx.message.author.send('`Login Succeeded!`')
        try:
            await user.update_alert_accounts(self.db, password)
            await ctx.send('Alert account updated!')
        except Exception as err:
            print(err)

    @bot_checks.is_whitelist()
    @bot_checks.check_permission_level(8)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(brief='Creates a new nucleus class')
    async def add_class(self, ctx: Context, class_id: str):
        """
        Creates new nucleus class which is referenced for nuclues users, courses and alert channel IDs.

        Class ID: str - Nucleus class ID

        """
        class_match = re.match(self.class_regex_check, class_id)
        if class_match == '':
            return await ctx.reply('Invalid Classname!')
        try:
            await self.db.add_nucleus_class(class_id)
            await ctx.send(f'Class {class_id} Added!')
        except Exception as err:
            await ctx.reply(err)

    @bot_checks.is_whitelist()
    @bot_checks.check_permission_level(8)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(brief='Channels are added with respective roles to ping when a new assignment is detected')
    async def add_alert(self, ctx: Context, class_id: str, role_id: Optional[int] = None,
                        channel_id: Optional[int] = None,
                        guild_id: Optional[int] = None):

        """
        Creates new alert entry with channel ID and role ID which pings the role when a new assignment in detected.

        Class ID: str - Nucleus class ID
        Role ID: int - Discord Role ID to ping
        Channel ID: int - Discord channel ID (defaults to channel where the command is invoked)
        Guild ID: int - Discord Server ID (defaults to server where the command is invoked)

        """
        class_match = re.match(self.class_regex_check, class_id).group(0)
        if class_match == '':
            return await ctx.reply('Invalid Classname!')

        class_ids = await self.db.get_nucleus_class()
        if class_match not in class_ids:
            return await ctx.reply('Class not found in DB!')

        if guild_id is None:
            guild_id = ctx.message.guild.id
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return await ctx.reply('Invalid Server ID')

        if role_id:
            role = guild.get_role(role_id)
            if role is None:
                return await ctx.send('Invalid Role!')

        if channel_id is None:
            channel_id = ctx.message.channel.id
        channel = guild.get_channel(channel_id)
        if channel is None:
            return await ctx.reply('Invalid Channel ID')
        try:
            await self.db.add_class_alert(class_id, role_id, channel.id, guild.id)
            return await ctx.send('Class Alert Added!')
        except Exception as error:
            print(error)
            return await ctx.reply(error)


def setup(bot):
    cog = NucleusCog(bot)
    bot.add_cog(cog)

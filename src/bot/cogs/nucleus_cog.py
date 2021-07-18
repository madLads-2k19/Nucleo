import json
import random
import re
from datetime import datetime
from typing import Optional

import dateparser
from discord import Embed
from discord.ext import commands, tasks
from discord.ext.commands import Context

from dependencies.database import Database
from dependencies.nucleus import Nucleus
from . import bot_checks


def generate_assignment_embed(assignment: dict, description: str):
    deadline = datetime.strptime(assignment['targetDateTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
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


def generate_schedule_embed(schedule: dict, date: datetime):
    fields = []
    for timing in schedule:
        for class_ in schedule[timing]:
            field = {
                'name': timing,
                'value': class_['title']
            }
            if 'type' in class_:
                if class_['type'] == 'gmeet':
                    field['name'] += ' Extra Class :pencil:'
                elif class_['type'] == 'assignment':
                    field['name'] += ' Assignment Deadline :notepad_spiral:'

            fields.append(field)
    date_string = date.strftime("%Y-%m-%d")
    description = 'No classes scheduled, Have a good day :wink:' if fields == [] else ''
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
        added_on = datetime.strptime(assignment['addedOn'], '%Y-%m-%dT%H:%M:%S.%fZ')
        submitted_date = datetime.strptime(assignment['submissions']['submissionDetails']["details"]['addedOn'], '%Y'
                                                                                                                 '-%m-%dT%H:%M:%S.%fZ')
        field = {
            'name': assignment['title'],
            'value': assignment["courseName"],
            'inline': True
        }
        field_left = {
            'name': 'Added On',
            'value': f'[{added_on.strftime("%d/%m/%Y")}]({assignment["question"]["details"]["previewLink"]})',
            'inline': True
        }
        field_right = {
            'name': 'Submitted On',
            'value': f'[{submitted_date.strftime("%d/%m/%Y")}]({assignment["submissions"]["submissionDetails"]["details"]["previewLink"]})',
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


class NucleusCog(commands.Cog):
    class_regex_check = r'[12][0-9][A-Z]{2}'

    def __init__(self, bot):
        self.bot = bot
        self.db: Database = bot.db
        self.assignments_detector.add_exception_type(Exception)
        self.assignments_detector.start()

    @commands.command()
    async def schedule(self, ctx: Context, date_string: Optional[str] = None):
        try:
            discord_user = await self.db.get_user_by_discord_id(ctx.message.author.id)
            if not discord_user:
                return await ctx.send('Login to perform this command.')
            cookies = json.loads(discord_user[8])
            user_id = discord_user[0]
            user = Nucleus(user_id, cookies)
            if await user.is_expired():
                return await ctx.message.author.send('Session expired, Please login to perform this command.')
            if date_string:
                date = dateparser.parse(date_string)
            else:
                date = datetime.now()
            schedule_response = await user.schedule(date.strftime("%Y-%m-%d"))
            schedule = schedule_response['data']['schedule']
            # meet_urls = schedule_response['data']['meetUrls']
            embed = generate_schedule_embed(schedule, date)
            await ctx.send(embed=embed)

        except Exception as err:
            print(err)

    @commands.command()
    async def assignments(self, ctx: Context, option: Optional[str] = ''):
        try:
            if option != '' and option != 'all':
                return await ctx.send('Invalid option!')
            discord_user = await self.db.get_user_by_discord_id(ctx.message.author.id)
            if not discord_user:
                return await ctx.send('Login to perform this command.')
            cookies = json.loads(discord_user[8])
            user_id = discord_user[0]
            user = Nucleus(user_id, cookies)
            if await user.is_expired():
                return await ctx.message.author.send('Session expired, Please login to perform this command.')
            unsubmitted = []
            submitted = []
            assignments_response = await user.assignments()
            assignments = assignments_response['data']['assignments']
            if not assignments:
                return await ctx.message.author.send('No assignments uploaded.')
            for assignment in assignments:
                if assignment['submissions']['submissionDetails'] == {}:
                    unsubmitted.append(assignment)
                else:
                    submitted.append(assignment)

            if option == 'all':
                counter = 0
                color = random.randint(0, 16777215)
                if not submitted:
                    await ctx.message.author.send('You have not submitted any assignments.')
                while counter < len(submitted):
                    assignments_iter = submitted[counter:counter+8]
                    embed_s = generate_submitted_assignment_embed(assignments_iter, color)
                    await ctx.message.author.send(embed=embed_s)
                    counter += 8
            if not unsubmitted:
                return await ctx.message.author.send('You have submitted all assignments till date.')

            for assignment in unsubmitted:
                embed_uns = generate_assignment_embed(assignment, 'Unsubmitted Assignment')
                await ctx.message.author.send(embed=embed_uns)

        except Exception as err:
            print(err)

    @tasks.loop(seconds=600)
    async def assignments_detector(self):
        print(f'Assignments Detector Running! - {datetime.now()}')
        try:
            alert_accounts = await self.db.get_alert_accounts()
            for username, cookies_str, class_id, password in alert_accounts:
                cookies = json.loads(cookies_str)
                user = Nucleus(username, cookies)
                user_response = await user.get_profile()
                if user_response == {}:
                    await user.login(username, password)
                    await self.db.update_alert_account(user.username, json.dumps(user.cookies), password)

                assignments_response = await user.assignments()
                assignments = assignments_response["data"]["assignments"]

                new_assignments = []
                nucleus_courses = await self.db.get_last_checked(class_id)

                for assignment in assignments:
                    course_id = assignment['courseId']
                    added_on_str = assignment['addedOn']
                    added_on = datetime.strptime(added_on_str, '%Y-%m-%dT%H:%M:%S.%fZ')
                    for course in nucleus_courses:
                        if course_id == course[0]:
                            last_checked = course[1]
                            if added_on > last_checked:
                                new_assignments.append(assignment)
                                await self.db.update_last_checked(class_id, course_id, added_on)

                if len(new_assignments) != 0:
                    try:
                        alert_details = await self.db.get_alert_details(class_id)
                        for channel_id, guild_id, role_id in alert_details:
                            guild = self.bot.get_guild(guild_id)
                            channel = guild.get_channel(channel_id)
                            role = guild.get_role(role_id)
                            if role:
                                await channel.send(role.mention)
                            for assignment in new_assignments:
                                embed = generate_assignment_embed(assignment, description='New Assignment Detected!')
                                await channel.send(embed=embed)
                    except Exception as err:
                        print('Error inside loop', err)

        except Exception as err:
            print(f'Error outside loop {err}')

    @assignments_detector.before_loop
    async def before_detection(self):
        await self.bot.wait_until_ready()

    @commands.command()
    @bot_checks.is_whitelist()
    @bot_checks.check_permission_level(2)
    async def login(self, ctx: Context, user_id: str):
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
        if user is None:
            return await ctx.author.send('Invalid Credentials!\nLogin failed....')
        await ctx.message.author.send('Login Succeeded!')
        try:
            await user.update_database(self.db, ctx.message.author.id, ctx.message.author.name)
        except Exception as err:
            print(err)

    @commands.command()
    @bot_checks.is_whitelist()
    @bot_checks.check_permission_level(8)
    async def alert_account(self, ctx: Context, user_id: str):
        def dm_check(message):
            if message.channel.id == ctx.author.dm_channel.id and message.author == ctx.author:
                return True

        user_match = re.match(r'[12][0-9][A-Z]{2}[0-9]{2}', user_id).group(0)
        if user_match is None:
            return await ctx.reply('Invalid UserName!, ex: 17PD39')

        await ctx.message.author.send('Please send me the password...')
        pass_message = await self.bot.wait_for('message', check=dm_check, timeout=30)
        password = pass_message.content
        if password == '':
            return await ctx.message.author.send('Please try logging in again.')

        user = await Nucleus.login(user_match, password)
        if user is None:
            return await ctx.author.send('Invalid Credentials!\nLogin failed....')
        await ctx.message.author.send('Login Succeeded!')
        try:
            await user.update_alert_accounts(self.db, password)
            await ctx.send('Alert account updated!')
        except Exception as err:
            print(err)

    @commands.command()
    @bot_checks.is_whitelist()
    @bot_checks.check_permission_level(8)
    async def add_class(self, ctx: Context, class_id: str):
        class_match = re.match(self.class_regex_check, class_id)
        if class_match == '':
            return await ctx.reply('Invalid Classname!')
        try:
            await self.db.add_nucleus_class(class_id)
            await ctx.send(f'Class {class_id} Added!')
        except Exception as err:
            await ctx.reply(err)

    @commands.command()
    @bot_checks.is_whitelist()
    @bot_checks.check_permission_level(8)
    async def add_alert(self, ctx: Context, class_id: str, role_id: Optional[int] = None,
                        channel_id: Optional[int] = None,
                        guild_id: Optional[int] = None):
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

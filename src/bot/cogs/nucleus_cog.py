from typing import Union, Optional
import re
import json

import dateparser
from discord.ext import commands, tasks
from discord.ext.commands import Context
from discord import Embed
from datetime import datetime

from bot import bot_exceptions
from dependencies.nucleus import Nucleus
from dependencies.database import Database, DatabaseDuplicateEntry
from . import bot_checks


async def generate_assignment_embed(assignments: list, bot, channel_id: int, guild_id: int, role_id: int):
    try:
        guild = bot.get_guild(guild_id)
        channel = guild.get_channel(channel_id)
        role = guild.get_role(role_id)
        if role:
            await channel.send(role.mention)

        for assignment in assignments:
            deadline = datetime.strptime(assignment['targetDateTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
            embed_dict = {
                "color": 15874618,
                "title": assignment['title'],
                "description": "New Assignment Detected.",
                "url": assignment['question']['details']['downloadLink'],
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
            embed = Embed.from_dict(embed_dict)
            await channel.send(embed=embed)

    except Exception as err:
        print(err)


class NucleusCog(commands.Cog):
    class_regex_check = r'[12][0-9][A-Z]{2}'

    def __init__(self, bot):
        self.bot = bot
        self.db: Database = bot.db
        self.assignments_detector.add_exception_type(Exception)
        self.assignments_detector.start()

    @commands.command()
    @bot_checks.is_whitelist()
    async def schedule(self, ctx: Context, date_string: str):
        date = dateparser.parse(date_string)

    @tasks.loop(seconds=600)
    async def assignments_detector(self):
        print('Assignments Detector Running!')
        try:
            admin_accounts = await self.db.get_admin_accounts()
            for username, cookies_str, class_id in admin_accounts:
                cookies = json.loads(cookies_str)
                user = Nucleus(username, cookies)
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

                # new_assignments = assignments

                if len(new_assignments) != 0:
                    alert_details = await self.db.get_alert_details(class_id)
                    for channel_id, guild_id, role_id in alert_details:
                        await generate_assignment_embed(new_assignments, self.bot, channel_id, guild_id, role_id)

        except Exception as err:
            print(f'{err}')

    @assignments_detector.before_loop
    async def before_detection(self):
        await self.bot.wait_until_ready()

    @commands.command()
    @bot_checks.is_whitelist()
    async def login(self, ctx: Context, user_id: str):
        def dm_check(message):
            if message.channel.id == ctx.author.dm_channel.id and message.author == ctx.author:
                return True

        user_match = re.match(r'[12][0-9][A-Z]{2}[0-9]{2}', user_id)
        if user_match == '':
            return await ctx.reply('Invalid Username!')
        await ctx.message.author.send('Please send me the password...')
        pass_message = await self.bot.wait_for('message', check=dm_check, timeout=30)
        user = await Nucleus.login(user_match.string, pass_message.content)
        if user is None:
            return await ctx.author.send('Invalid Credentials!\nLogin failed....')
        await ctx.message.author.send('Login Succeeded!')
        try:
            await user.update_database(self.db, ctx.message.author.id, ctx.message.author.name)
        except Exception as err:
            print(err)

    @commands.command()
    @bot_checks.is_whitelist()
    @bot_checks.check_permission_level(9)
    async def add_admin(self, ctx: Context, user_id: str):
        user_match = re.match(r'[12][0-9][A-Z]{2}[0-9]{2}', user_id).group(0)
        if user_match == '':
            return await ctx.reply('Invalid UserName!')

        user_ids = await self.db.get_nucleus_user_ids()
        if user_match not in user_ids:
            return await ctx.send('UserId not found in DB!')
        try:
            await self.db.update_to_admin(user_id)
            await ctx.send('Admin Added!')
            user_data = await self.db.get_user(user_id)
            cookies = json.loads(user_data[8])
            user = Nucleus(user_id, cookies)
            await user.update_database(self.db, admin=True)
            await ctx.send('Updated Courses!')
        except Exception as err:
            return await ctx.send(f'{err}')

    @commands.command()
    @bot_checks.is_whitelist()
    async def add_class(self, ctx: Context, class_id: str):
        class_match = re.match(self.class_regex_check, class_id)
        if class_match == '':
            return await ctx.reply('Invalid Classname!')
        try:
            await self.db.add_nucleus_class(class_id)
            await ctx.reply(f'Class {class_id} Added!')
        except Exception as err:
            await ctx.reply(err)

    @commands.command()
    @bot_checks.is_whitelist()
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

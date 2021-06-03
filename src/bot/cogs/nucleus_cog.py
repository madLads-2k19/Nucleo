from typing import Union, Optional
import re
import json

import dateparser
from discord.ext import commands, tasks
from discord.ext.commands import Context
from datetime import datetime

from bot import bot_exceptions
from dependencies.nucleus import Nucleus
from dependencies.database import Database, DatabaseDuplicateEntry
from . import bot_checks


def generate_assignment_embed(assignments: list):
    pass


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
        accounts = await self.db.get_accounts()
        try:
            for username, cookies_str, class_id in accounts:
                cookies = json.loads(cookies_str)
                user = Nucleus(username, cookies)

                assignments = await user.assignments()
                assignments = assignments["data"]["assignments"]

                result = await self.db.get_lastchecked(class_id)
                last_checked = datetime.timestamp(result)

                new_assignments = []
                for assignment in assignments:
                    time = datetime.timestamp(datetime.strptime(assignment["addedOn"], '%Y-%m-%dT%H:%M:%S.%fZ'))
                    if time > last_checked:
                        new_assignments.append(assignment)

                if len(new_assignments) != 0:
                    last_checked = datetime.timestamp(assignments[-1]["addedOn"])
                    await self.db.update_lastchecked(class_id, last_checked)

        except Exception as err:
            print(err)

    @assignments_detector.before_loop
    async def before_detection(self):
        await self.bot.wait_until_ready()

    @commands.command()
    @bot_checks.is_whitelist()
    async def add_user(self, ctx: Context, user_id: str):
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
        await user.update_database(self.db, add_user=True)

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
    async def add_alert_channel(self, ctx: Context, class_id: str, channel_id: Optional[int] = None,
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

        if channel_id is None:
            channel_id = ctx.message.channel.id
        channel = guild.get_channel(channel_id)
        if channel is None:
            return await ctx.reply('Invalid Channel ID')
        try:
            await self.db.add_class_alert(class_id, channel.id, guild.id)
            return await ctx.send('Class Alert Added!')
        except Exception as error:
            print(error)
            return await ctx.reply(error)


def setup(bot):
    cog = NucleusCog(bot)
    bot.add_cog(cog)

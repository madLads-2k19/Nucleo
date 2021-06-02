from typing import Union
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


class NucleusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db: Database = bot.db
        self.assignments_detector.add_exception_type(Exception)
        self.assignments_detector.start()

    @commands.command()
    @bot_checks.is_whitelist()
    async def schedule(self, ctx: Context, date_string: str):
        date = dateparser.parse(date_string)

    @tasks.loop(seconds=600.0)
    async def assignments_detector(self):
        accounts = await self.db.get_accounts()
        for username, cookies_str, class_id in accounts:
            cookies = json.loads(cookies_str)
            user = Nucleus(username, cookies)
            assignments = await user.assignments()
            assignments = assignments["data"]["assignments"]
            result = await self.db.get_lastchecked_time(class_id)
            detector_flag = False
            print(result)
            for assignment in assignments:
                time = datetime.timestamp(assignment["addedOn"])
                print(time, result)
                if time > result:
                    detector_flag = True

            if detector_flag:
                last_checked = datetime.strptime(assignments[-1]["addedOn"], '%Y-%m-%dT%H:%M:%SZ')
                await self.db.update_lastchecked_time(class_id, last_checked)

    @assignments_detector.before_loop
    async def before_detection(self):
        await self.bot.wait_until_ready()

    @commands.command()
    @bot_checks.is_whitelist()
    async def add_user(self, ctx: Context, user_id: str):
        def dm_check(message):
            if message.channel.id == ctx.author.dm_channel.id and message.author == ctx.author:
                return True

        user_match = re.match(r'[12][0-9][A-Za-z]{2}[0-9]{2}', user_id)
        if user_match == '':
            return await ctx.reply('Invalid Username!')
        await ctx.message.author.send('Please send me the password...')
        pass_message = await self.bot.wait_for('message', check=dm_check, timeout=30)
        user = await Nucleus.login(user_match.string, pass_message.content)
        if user is None:
            return await ctx.author.send('Invalid Credentials!\nLogin failed....')
        await ctx.message.author.send('Login Succeeded!')
        await user.update_database(self.db, add_user=True)


def setup(bot):
    cog = NucleusCog(bot)
    bot.add_cog(cog)

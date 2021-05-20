from typing import Union
import re

import dateparser
from discord.ext import commands, tasks
from discord.ext.commands import Context

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

    @tasks.loop(seconds=3600)
    async def assignments_detector(self):
        accounts = await self.db.get_accounts()
        for username, cookies in accounts:
            user = Nucleus(username, cookies)

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

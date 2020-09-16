from typing import Union

import discord
from discord.ext import commands
from discord.ext.commands import Context

from bot import bot_exceptions
from dependencies.database import Database
from . import bot_checks


class ModCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db: Database = bot.db

    @commands.command()
    @bot_checks.check_permission_level(8)
    async def purge(self, ctx: Context, count: int = 1, user: Union[discord.member.User, discord.guild.Role] = None):
        def user_check(message):
            return user is None or user.id == message.author.id

        if ctx.channel.guild is None:
            await ctx.send("This is not a Text channel")
            return
        if count > 100:
            count = 100
        await ctx.message.delete()
        deleted = await ctx.channel.purge(limit=count, check=user_check)
        await ctx.send('Deleted {} message(s)'.format(len(deleted)), delete_after=5)


def setup(bot):
    cog = ModCommands(bot)
    bot.add_cog(cog)
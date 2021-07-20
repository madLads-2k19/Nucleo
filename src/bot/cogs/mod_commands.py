import discord
from discord.ext import commands
from discord.ext.commands import Context

from dependencies.database import Database
from . import bot_checks


class ModCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db: Database = bot.db

    @commands.command(brief='Deletes discord messages')
    @bot_checks.check_permission_level(8)
    async def purge(self, ctx: Context, number_of_msg: int = 5, user: discord.member.User = None):
        """
        Deletes messages
        :param ctx: Discord context object
        :param number_of_msg: Messages to be deleted
        :param user: User whose message is to be deleted
        :return:
        """
        if isinstance(user, discord.member.User):
            count = int(number_of_msg)
        else:
            user = None
            count = int(number_of_msg)

        def user_check(message):
            return user is None or user.id == message.author.id

        if ctx.channel.guild is None:
            await ctx.send("This is not a Text channel")
            return
        if count > 500:
            count = 500
        deleted = await ctx.channel.purge(limit=count + 1, check=user_check)
        await ctx.send('Deleted {} message(s)'.format(len(deleted)), delete_after=5)


def setup(bot):
    cog = ModCommands(bot)
    bot.add_cog(cog)

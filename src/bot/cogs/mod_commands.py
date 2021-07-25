from typing import Optional, Union

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

    @commands.command(brief='Send the message content to the corresponding channel')
    @bot_checks.check_permission_level(8)
    async def say(self, ctx: Context, channel_id: int):
        if channel_id:
            try:
                channel: discord.TextChannel = self.bot.get_channel(channel_id)
            except discord.NotFound:
                return await ctx.reply("Invalid Channel ID")
        else:
            channel = ctx.channel
        m = await ctx.reply('Please send the message....')

        def author_check(message):
            if message.channel.id == ctx.channel.id and message.author == ctx.author:
                return True

        try:
            msg = await self.bot.wait_for('message', check=author_check, timeout=30)
            await channel.send(msg.content)
            await ctx.reply("Message sent")
        except TimeoutError:
            await ctx.reply("Timed out!")
        await m.delete()

    @commands.command(brief='Reacts to a message')
    @bot_checks.check_permission_level(8)
    async def react(self, ctx: Context, emoji: Union[discord.PartialEmoji, str], message_id: int, channel_id: Optional[int]):
        if channel_id:
            try:
                channel: discord.TextChannel = self.bot.get_channel(channel_id)
            except discord.NotFound:
                return await ctx.reply("Invalid Channel ID")
        else:
            channel = ctx.channel

        try:
            msg = await channel.fetch_message(message_id)
            await msg.add_reaction(emoji)
        except discord.NotFound:
            await ctx.reply(f"Cannot find message with ID: `{message_id}`")
        except discord.Forbidden:
            await ctx.reply(f"I dont have enough Permissions!")


def setup(bot):
    cog = ModCommands(bot)
    bot.add_cog(cog)

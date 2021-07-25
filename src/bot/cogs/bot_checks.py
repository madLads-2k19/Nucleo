import discord
from discord.ext import commands
from discord.ext.commands import Context

from bot import bot_exceptions
from dependencies.database import Database


async def get_author_permission(ctx: Context) -> int:
    db: Database = ctx.bot.db
    author: discord.Member = ctx.author
    if hasattr(author, "roles"):
        ids = [author.id, *[role.id for role in author.roles]]
    else:
        ids = [author.id]
    perm = await db.permission_retriever(*ids)
    if perm is None:
        perm = 0
    return perm


def check_permission_level(required_level: int = 0):
    async def check(ctx: Context):
        is_god: bool = await ctx.bot.is_owner(ctx.author)
        perm = await get_author_permission(ctx)
        if perm >= required_level or is_god:
            return True
        raise bot_exceptions.NotEnoughPerms(f"{ctx.author} does not have enough permission to run the command")

    return commands.check(check)


def is_whitelist(allow_dm=False):
    async def check(ctx: Context):
        if allow_dm is True and ctx.channel.type is discord.ChannelType.private:
            return True
        db: Database = ctx.bot.db
        channel_id: int = ctx.channel.id
        server_id: int = ctx.guild.id
        data = await db.whitelist_check(server_id, channel_id)
        if data:
            return data
        raise bot_exceptions.NotOnWhiteList

    return commands.check(check)

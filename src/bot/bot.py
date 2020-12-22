# import asyncio
import datetime
import sys
import traceback
import os
from collections import deque, defaultdict

import aiohttp
import discord
from discord.ext import commands

from config import Settings
from dependencies.database import Database

# initial_extensions = ('bot.cogs.permission_management', 'bot.cogs.mod_commands')
exceptions_cogs = ['__init__.py', 'bot_checks.py']


def _custom_prefix_adder(*args):
    def _prefix_callable(bot, msg):
        """returns a list of strings which will be used as command prefixes"""
        user_id = bot.user.id
        base = [f'<@!{user_id}> ', f'<@{user_id}> ']
        base.extend(args)
        return base

    return _prefix_callable


class Bot(commands.AutoShardedBot):
    def __init__(self):
        self.configs = Settings()
        super().__init__(command_prefix=_custom_prefix_adder(self.configs.bot_prefix),
                         description=self.configs.bot_description, pm_help=None, help_attrs=dict(hidden=True),
                         fetch_offline_members=False, heartbeat_timeout=150.0)
        self.bot_token = self.configs.bot_token
        self.db = Database(self.configs.db_host, self.configs.db_name, self.configs.db_user, self.configs.db_password,
                           self.configs.db_port, self.configs.min_db_conns, self.configs.max_db_conns, loop=self.loop)

        self.uptime: datetime.datetime = datetime.datetime.now()

        # Cogs loader
        for extension in os.listdir('./bot/cogs'):
            try:
                if extension.endswith('.py') and extension not in exceptions_cogs:
                    self.load_extension(f'bot.cogs.{extension[:-3]}')
            except Exception as e:
                print(f'failed to load extension because of:  {e}, type:  {type(e)}')
                traceback.print_exc()
                # TODO probably log it

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.errors.CommandInvokeError):
            await ctx.send(f"What you are attempting to do isn't implemented by the lazy devs 😱 | error: {error}")
        elif isinstance(error, commands.DisabledCommand):
            await ctx.send('Sorry. This command is disabled and cannot be used.')
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send('This command cannot be used in private messages.')
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"You are missing required arguments in the command. :frowning:")
        elif isinstance(error, commands.CommandInvokeError):
            original = error.original
            if not isinstance(original, discord.HTTPException):
                print(f'In {ctx.command.qualified_name}:', file=sys.stderr)
                traceback.print_tb(original.__traceback__)
                print(f'{original.__class__.__name__}: {original}', file=sys.stderr)
        elif isinstance(error, commands.ArgumentParsingError):
            await ctx.send(error)

    # TODO check if this is needed
    def get_guild_prefixes(self, guild, *, local_inject=_custom_prefix_adder()):
        proxy_msg = discord.Object(id=0)
        proxy_msg.guild = guild
        return local_inject(self, proxy_msg)

    # TODO: use guild prefixes with db
    # async def set_guild_prefixes(self, guild, prefixes):
    #     if len(prefixes) == 0:
    #         await self.prefixes.put(guild.id, [])
    #     elif len(prefixes) > 10:
    #         raise RuntimeError('Cannot have more than 10 custom prefixes.')
    #     else:
    #         await self.prefixes.put(guild.id, sorted(set(prefixes), reverse=True))

    async def on_ready(self):
        if not hasattr(self, 'uptime'):
            self.uptime = datetime.datetime.utcnow()

        print(f'Ready: {self.user} (ID: {self.user.id})')

    async def on_message(self, message):
        if message.author.bot:  # can be edited to allow message from feather
            return
        await self.process_commands(message)

    async def close(self):
        await super().close()

    def run(self):
        try:
            super().run(self.configs.bot_token, reconnect=True)
        except Exception as e:
            print(f"Error at start!  error: {e},  type:  {type(e)}")

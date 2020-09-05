# import asyncio
import datetime
import sys
import traceback
from collections import deque, defaultdict

import aiohttp
import discord
from discord.ext import commands

from config import Settings
from dependencies.database import Database

initial_extensions = ('bot.cogs.permission_management',)


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

        # TODO change implementation to a non deprecated form, unknown if possible
        self.session = aiohttp.ClientSession(loop=self.loop)

        self._prev_events = deque(maxlen=10)

        # shard_id: List[datetime.datetime]
        # shows the last attempted IDENTIFYs and RESUMEs
        self.resumes = defaultdict(list)
        self.identifies = defaultdict(list)  # TODO check if it is still used

        # Cogs loader
        for extension in initial_extensions:
            try:
                self.load_extension(extension)
            except Exception as e:
                print(f'failed to load extension because of:  {e}, type:  {type(e)}')
                traceback.print_exc()
                # TODO probably log it

    def _clear_gateway_data(self):
        one_week_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        for shard_id, dates in self.identifies.items():
            to_remove = [index for index, dt in enumerate(dates) if dt < one_week_ago]
            for index in reversed(to_remove):
                del dates[index]

        # checks resume instead of identifies
        for shard_id, dates in self.resumes.items():
            to_remove = [index for index, dt in enumerate(dates) if dt < one_week_ago]
            for index in reversed(to_remove):
                del dates[index]

    async def on_socket_response(self, msg):
        self._prev_events.append(msg)

    async def before_identify_hook(self, shard_id, *, initial):
        self._clear_gateway_data()
        self.identifies[shard_id].append(datetime.datetime.utcnow())
        await super().before_identify_hook(shard_id, initial=initial)

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

    # Unknown if needed
    # def get_raw_guild_prefixes(self, guild_id):
    #     return self.prefixes.get(guild_id, ['?', '!'])
    #
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

    async def on_shard_resumed(self, shard_id):
        print(f'Shard ID {shard_id} has resumed...')
        self.resumes[shard_id].append(datetime.datetime.utcnow())

    @property
    def stats_webhook(self):
        wh_id, wh_token = self.config.stat_webhook
        hook = discord.Webhook.partial(id=wh_id, token=wh_token, adapter=discord.AsyncWebhookAdapter(self.session))
        return hook

    #  can be used in case more precise control wants to be used
    ####
    # async def process_commands(self, message):
    #     ctx = await self.get_context(message)
    #
    #     if ctx.command is None:
    #         return
    #
    #     # if ctx.author.id in self.blacklist:
    #     #     return
    #
    #     # if ctx.guild is not None and ctx.guild.id in self.blacklist:
    #     #     return
    #
    #     bucket = self.spam_control.get_bucket(message)
    #     current = message.created_at.replace(tzinfo=datetime.timezone.utc).timestamp()
    #     retry_after = bucket.update_rate_limit(current)
    #     author_id = message.author.id
    #     if retry_after and author_id != self.owner_id:
    #         self._auto_spam_count[author_id] += 1
    #         if self._auto_spam_count[author_id] >= 5:
    #             await self.add_to_blacklist(author_id)
    #             del self._auto_spam_count[author_id]
    #             await self.log_spammer(ctx, message, retry_after, autoblock=True)
    #         else:
    #             self.log_spammer(ctx, message, retry_after)
    #         return
    #     else:
    #         self._auto_spam_count.pop(author_id, None)
    #
    #     try:
    #         await self.invoke(ctx)
    #     finally:
    #         # Just in case we have any outstanding DB connections
    #         await ctx.release()

    async def on_message(self, message):
        if message.author.bot:  # can be edited to allow message from feather
            return
        await self.process_commands(message)

    async def close(self):
        await super().close()
        await self.session.close()

    # probably won't be manually implemented
    def run(self):
        try:
            super().run(self.configs.bot_token, reconnect=True)
        except Exception as e:
            print(f"Error at start!  error: {e},  type:  {type(e)}")
        # finally:
        #     with open('prev_events.log', 'w', encoding='utf-8') as fp:
        #         for data in self._prev_events:
        #             try:
        #                 x = json.dumps(data, ensure_ascii=True, indent=4)
        #             except:
        #                 fp.write(f'{data}\n')
        #             else:
        #                 fp.write(f'{x}\n')

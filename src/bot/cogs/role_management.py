import discord
from discord.ext import commands

from . import bot_checks


class ReactionRoles(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        message_id = payload.message_id
        if message_id == 790495628932808714:
            guild_id = payload.guild_id
            guild = discord.utils.find(lambda g: g.id == guild_id, self.client.guilds)

            if payload.emoji.name == '🟣':
                role = discord.utils.get(guild.roles, name='purple')
            elif payload.emoji.name == '⚫':
                role = discord.utils.get(guild.roles, name='black')
            else:
                role = discord.utils.get(guild.roles, name=payload.emoji.name)

            if role is not None:
                member = discord.utils.find(lambda m: m.id == payload.user_id, guild.members)
                if member is not None:
                    await member.add_roles(role)
                    print('Role added.')
                else:
                    print('Member not found!')
            else:
                print('Role not found.')

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        message_id = payload.message_id
        if message_id == 790495628932808714:
            guild_id = payload.guild_id
            guild = discord.utils.find(lambda g: g.id == guild_id, self.client.guilds)

            if payload.emoji.name == '🟣':
                role = discord.utils.get(guild.roles, name='purple')
            elif payload.emoji.name == '⚫':
                role = discord.utils.get(guild.roles, name='black')
            else:
                role = discord.utils.get(guild.roles, name=payload.emoji.name)

            if role is not None:
                member = discord.utils.find(lambda m: m.id == payload.user_id, guild.members)
                if member is not None:
                    await member.remove_roles(role)
                    print('Role removed.')
                else:
                    print('Member not found!')
            else:
                print('Role not found.')

        def is_it_dev(ctx):
            return ctx.message.author.server_permissons.manage_roles

        @commands.command()
        @bot_checks.is_whitelist()
        @commands.check(is_it_dev)
        async def create_role(self, ctx):
            pass

        @commands.command()
        @bot_checks.is_whitelist()
        @commands.check(is_it_dev)
        async def delete_role(self, ctx):
            pass

        @commands.command()
        @bot_checks.is_whitelist()
        @bot_checks.check_permission_level(6)
        async def add_opt_role(self, ctx, role_id, emote_id):
            pass

        @commands.command()
        @bot_checks.is_whitelist()
        @bot_checks.check_permission_level(6)
        async def remove_opt_role(self, ctx, role_id, emote_id):
            pass


def setup(bot):
    bot.add_cog(ReactionRoles(bot))

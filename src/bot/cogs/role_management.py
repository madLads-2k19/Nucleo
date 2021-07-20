"""
This module provides a discord.py Cog `RoleManagement`.
"""

import re

import discord
from discord.ext import commands

from . import bot_checks
from ..bot_utils import generate_embed


class RoleManagement(commands.Cog):
    """
    A discord.Cog that is used for Role Management.
    """
    welcome_role_message_id = 867076357321785385

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        message_id = payload.message_id
        if message_id == RoleManagement.welcome_role_message_id:
            guild_id = payload.guild_id
            guild = discord.utils.find(lambda g: g.id == guild_id, self.client.guilds)

            if payload.emoji.name == '🇩':
                role = discord.utils.get(guild.roles, name='DS')
            elif payload.emoji.name == '🇸':
                role = discord.utils.get(guild.roles, name='SS')
            elif payload.emoji.name == '🇹':
                role = discord.utils.get(guild.roles, name='TCS')
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
        if message_id == RoleManagement.welcome_role_message_id:
            guild_id = payload.guild_id
            guild = discord.utils.find(lambda g: g.id == guild_id, self.client.guilds)

            if payload.emoji.name == '🇩':
                role = discord.utils.get(guild.roles, name='DS')
            elif payload.emoji.name == '🇸':
                role = discord.utils.get(guild.roles, name='SS')
            elif payload.emoji.name == '🇹':
                role = discord.utils.get(guild.roles, name='TCS')
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

    @commands.command()
    @bot_checks.is_whitelist()
    @bot_checks.check_permission_level(8)
    async def create_role(self, ctx, name, color):
        """
            Used to create roles with a specific colour.
        :param ctx: The context object of the message
        :type ctx: discord.Context
        :param name: Name of the role to be created
        :type name: str
        :param color: A Hex coded colour prefixed with a #
        :type color: str
        """
        if re.match("^#[0-9A-F]{6}$", color):
            color = discord.Color(color)
            guild = ctx.guild
            try:
                await guild.create_role(name=name, color=color)
                description = f'Role name = {name} Color = {color}'
                embed = generate_embed('Role Added', ctx.author, description=description, color=discord.Color.red())
                embed.set_footer(text='Have a great day! :)')
                await self.client.send_message(ctx.message.channel, embed=embed)
            except discord.Forbidden as e:
                print(f'create_role name={name} color={color} failed with error :{e}')
        else:
            await ctx.send('Invalid color argument.')

    @commands.command()
    @bot_checks.is_whitelist()
    @bot_checks.check_permission_level(8)
    async def delete_role(self, ctx, name):
        role = discord.utils.get(ctx.message.server.roles, name=name)
        if role:
            try:
                await self.client.delete_role(ctx.message.server, role)
                description = f'Role name = {name} Author = {role.color}'
                embed = generate_embed('Role Deleted!', ctx.author, description=description, color=discord.Color.red())
                embed.set_footer(text='Have a great day! :)')
                await self.client.send_message(ctx.message.channel, embed=embed)
            except discord.Forbidden:
                await ctx.send("Missing Permissions to delete this role!")
        else:
            await ctx.send("The role doesn't exist!")

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
    bot.add_cog(RoleManagement(bot))

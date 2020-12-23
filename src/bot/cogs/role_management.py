import discord
from discord.ext import commands
import re

from . import bot_checks

class RoleManagement(commands.Cog):

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

    @commands.command(pass_context=True)
    @bot_checks.is_whitelist()
    @commands.check(is_it_dev)
    async def create_role(self, ctx, name, color):
        if re.match("/^#[0-9A-F]{6}$/", color):
            color = discord.Color(color)
            guild = ctx.guild
            try:
                await guild.create_role(name=name, color=color)
                embed = discord.Embed(title='Role Added', description=f'Role name = {name} Color = {color}', color=discord.Color.red())
                embed.add_field(name='Wanna add role to DB?')
                embed.add_field(name='Yes', value='yeah ofc')
                embed.add_field(name='No', value='nope')
                embed.set_footer(text='Have a great day! :)')
                await self.client.send_message(ctx.message.channel, embed=embed)
            except Exception as e:
                print(f'create_role name={name} color={color} failed with error :{e}')
        else:
            await ctx.send('```Invalid color argument.```')

    @commands.command(pass_context=True)
    @bot_checks.is_whitelist()
    @commands.check(is_it_dev)
    async def delete_role(self, ctx, name):
        role = discord.utils.get(ctx.message.server.roles, name=name)
        if role:
            try:
                await self.client.delete_role(ctx.message.server, role)
                embed = discord.Embed(title='Role Deleted', description=f'Role name = {name} Author = {ctx.author.name}', color=discord.Color.red())
                embed.set_footer(text='Have a great day! :)')
                await self.client.send_message(ctx.message.channel, embed=embed)
            except discord.Forbidden:
                await ctx.send("Missing Permissions to delete this role!")
        else:
            await ctx.send("The role doesn't exist!")

    @commands.command(pass_context=True)
    @bot_checks.is_whitelist()
    @bot_checks.check_permission_level(6)
    async def add_opt_role(self, ctx, role_id, emote_id):
        pass

    @commands.command(pass_context=True)
    @bot_checks.is_whitelist()
    @bot_checks.check_permission_level(6)
    async def remove_opt_role(self, ctx, role_id, emote_id):
        pass


def setup(bot):
    bot.add_cog(RoleManagement(bot))

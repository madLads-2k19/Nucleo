from typing import Optional

from discord import Embed
from discord.utils import get
from discord.ext import menus, commands

from .bot_checks import get_author_permission

def syntax(command: commands.command):
    cmd_and_aliases = "|".join([str(command), *command.aliases])
    params = []

    for key, value in command.params.items():
        if key not in ("self", "ctx"):
            params.append(f"[{key}]" if "NoneType" in str(
                value) else f"<{key}>")

    params = " ".join(params)

    return f"`{cmd_and_aliases} {params}`"


class HelpMenu(menus.ListPageSource):
    def __init__(self, ctx, data):
        self.ctx = ctx

        super().__init__(data, per_page=3)

    async def write_page(self, menu, fields=None):
        if fields is None:
            fields = []
        offset = (menu.current_page*self.per_page) + 1
        len_data = len(self.entries)

        embed = Embed(title="Help",
                      description="Nucleo help dialog!",
                      colour=self.ctx.author.colour)
        embed.set_thumbnail(url=self.ctx.guild.me.avatar_url)
        embed.set_footer(
            text=f"{offset:,} - {min(len_data, offset+self.per_page-1):,} of {len_data:,} commands.")

        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)

        return embed

    async def format_page(self, menu, entries):
        fields = []

        for entry in entries:
            fields.append((entry.brief or "No description", syntax(entry)))

        return await self.write_page(menu, fields)


async def cmd_help(ctx: commands.Context, command):
    embed = Embed(title=f"Help with `{command}`",
                  description=syntax(command),
                  colour=ctx.author.colour)
    embed.add_field(name="Command description", value=command.help)
    await ctx.send(embed=embed)


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command("help")

    @commands.command(name="help", brief='Shows help dialog for Nucleo')
    async def show_help(self, ctx: commands.Context, cmd: Optional[str]):
        """Shows this message."""
        command_levels = {
            'assignments': 0,
            'schedule': 0,
            'login': 0,
            'resources': 0,
            'alert_account': 8,
            'add_class': 8,
            'add_alert': 8
        }
        user_prem = await get_author_permission(ctx)
        commands_allowed = [command for command in command_levels if command_levels[command] <= user_prem]
        commands_list = [command for command in list(self.bot.commands) if command.name in commands_allowed]
        if cmd is None:

            menu = menus.MenuPages(source=HelpMenu(ctx, list(commands_list)),
                                   delete_message_after=True,
                                   timeout=45.0)
            await menu.start(ctx)

        else:
            if command := get(commands_list, name=cmd):
                await cmd_help(ctx, command)

            else:
                await ctx.send("That command does not exist.")


def setup(bot):
    bot.add_cog(HelpCog(bot))

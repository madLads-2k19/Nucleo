from typing import Union

from discord import Color, Member, Embed


def generate_embed(title: str, author: Member, *, description: str, color: Union[Color, int]) -> Embed:
    return Embed(
        title=title,
        color=color,
        description=description
    ).set_footer(text=author.display_name, icon_url=author.avatar_url)
from discord.ext.commands import CommandError


class NotImplementedFunction(CommandError):
    """Raised when a command or part of a command is not implemented"""


class NotEnoughPerms(CommandError):
    """Raised when a user doesn't have enough permissions to run the command"""


class NotOnWhiteList(CommandError):
    """Raised When a channel isn't on the whitelist"""

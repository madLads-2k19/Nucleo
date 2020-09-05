class DatabaseInitError(Exception):
    """raised when the database fails to init"""


class DatabaseMissingArguments(Exception):
    """raised when a method of the database is missing arguments"""


class DatabaseDuplicateEntry(Exception):
    """raised when a method of the database fails because an similar entry already exists"""

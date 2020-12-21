class SettingsNotConfigured(Exception):
    """Is raised when the settings file is missing information"""

    def __init__(self, missing_setting: str = 'Unknown', comment: str = 'None'):
        self.missing = missing_setting
        self.comment = comment

    def __str__(self):
        if self.missing != 'Unknown':
            return_string = f"The settings file is missing the setting for {self.missing}"
            if self.comment != 'None':
                return ', '.join([return_string, self.comment])
            return return_string
        return f"The settings file is missing a setting for an unspecified section"


class EmptySettingsFile(Exception):
    """Raised when a settings file is empty or just created"""

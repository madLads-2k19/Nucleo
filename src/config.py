from ast import literal_eval
from configparser import ConfigParser

import exceptions


class Settings:
    def __read_settings_file(self):
        config = self.config
        config.read('../settings.ini')
        self.__test_settings()

    def __test_settings(self):
        settings_file = self.config
        try:
            database_section = settings_file['database']
        except KeyError:
            self.__write_default_settings_values()
            raise exceptions.EmptySettingsFile()
        if database_section['host'] == '' or database_section['password'] == '' or database_section['user'] == '':
            raise exceptions.SettingsNotConfigured('database')
        misc_section = settings_file['misc']
        try:
            use_test = literal_eval(misc_section['use-test'])
            if type(use_test) != bool:
                raise exceptions.SettingsNotConfigured('use-test','The value is not a bool')
        except ValueError:
            raise exceptions.SettingsNotConfigured('use-test', 'The value is not a selection of "True" or "False"')
        self.use_test = use_test
        if use_test is False:
            bot_section = settings_file['main bot']
        else:
            bot_section = settings_file['test bot']
        self.bot_section = bot_section
        if bot_section['token'] == '':
            raise exceptions.SettingsNotConfigured('token', 'Corresponding Bot Token is missing')

    def __write_default_settings_values(self):
        config = self.config
        config['main bot'] = {'token': '', 'prefix': '!', 'description': 'A bot'}
        config['test bot'] = {'token': '', 'prefix': '?', 'description': 'A test bot'}
        config['database'] = {'host': '', 'name': '', 'user': '', 'port': '3306', 'password': '', 'min conns': '1',
                              'max conns': '5'}
        config['misc'] = {'use-test': 'False'}
        with open('../settings.ini', 'w') as settings_file:
            config.write(settings_file)

    def __load_values_to_attribute(self):
        config_file = self.config
        bot_section = self.bot_section
        self.bot_token = bot_section['token']
        self.bot_prefix = bot_section['prefix']
        self.bot_description = bot_section['description']
        db_section = config_file['database']
        self.db_host = db_section['host']
        self.db_name = db_section['name']
        self.db_user = db_section['user']
        self.db_password = db_section['password']
        self.db_port: int = literal_eval(db_section['port'])
        self.min_db_conns: int = literal_eval(db_section['min conns'])
        self.max_db_conns: int = literal_eval(db_section['max conns'])

    def __init__(self):
        self.bot_section = None
        self.config = ConfigParser()
        self.__read_settings_file()
        self.use_test: bool = literal_eval(self.config['misc']['use-test'])
        self.bot_token = ''
        self.bot_description = ''
        self.bot_prefix = ''
        self.db_host = ''
        self.db_name = ''
        self.db_user = ''
        self.db_port = 3306
        self.db_password = ''
        self.min_db_conns = 0
        self.max_db_conns = 0
        self.__load_values_to_attribute()

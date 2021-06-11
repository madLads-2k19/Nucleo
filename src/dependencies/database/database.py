import asyncio
from datetime import datetime
from typing import Optional
import asyncpg

from .database_exceptions import DatabaseDuplicateEntry, DatabaseInitError, DatabaseMissingArguments


class Database:
    def __init__(self, database_host: str, database_name: str, database_user: str, database_password,
                 database_port: int = 5432, min_conns: int = 3, max_conns: int = 10,
                 loop: asyncio.AbstractEventLoop = None):
        self.db_connections = {}
        self.db_pool: asyncpg.pool.Pool
        self.running = False
        self._database_data = {'dsn': f'postgres://{database_user}:{database_password}'
                                      f'@{database_host}:{database_port}/{database_name}', 'min_size': min_conns,
                               'max_size': max_conns}

        self.loop = loop
        if self.loop is None:
            self.loop = asyncio.get_event_loop()

        self.__async_init_task = self.loop.create_task(self.__pool_starter__())

    async def __pool_starter__(self):
        try:
            self.db_pool: asyncpg.pool.Pool = await asyncpg.create_pool(**self._database_data)
            self.running = True
            await self.__database_initializer__()
            return True
        except Exception as e:
            raise DatabaseInitError(f'Database Initialization Error: {type(e)}: {e}') from e

    async def __init_check__(self):
        if self.running:
            return
        await self.__async_init_task

    async def test(self):
        await self.__init_check__()
        data = await self.db_pool.fetch('SELECT version();')
        print(data)

    async def __database_initializer__(self):
        try:
            with open('./dependencies/database/database_initialization.sql') as file:
                query = file.read()
                await self.db_pool.execute(query)
        except FileNotFoundError:
            print('Please run the the launcher with the repository as the working directory.')

    async def permission_retriever(self, *ids, with_name=False):
        await self.__init_check__()
        if len(ids) == 0:
            raise DatabaseMissingArguments('Missing arguments at the permission retriever')
        if with_name:
            query = f'SELECT MAX("LEVEL"), "NAME" FROM "USER_AUTH" INNER JOIN "PERMISSIONS_NAMES" USING ("LEVEL") ' \
                    f'WHERE "ITEM_ID" IN({", ".join(f"${x + 1}" for x in range(len(ids)))})'
        else:
            query = f'SELECT MAX("LEVEL") FROM "USER_AUTH" WHERE "ITEM_ID" IN ' \
                    f'({", ".join(f"${x + 1}" for x in range(len(ids)))}) '
        data = await self.db_pool.fetchrow(query, *ids)
        permission_level = data[0]
        if with_name:
            return permission_level, data[1]
        return permission_level

    async def auth_retriever(self, include_roles: bool = False):
        await self.__init_check__()
        query = 'SELECT "ITEM_ID", "LEVEL", "NAME", "ROLE" FROM "USER_AUTH" ' \
                'INNER JOIN "PERMISSIONS_NAMES" USING ("LEVEL") '
        if include_roles is False:
            query = ' '.join((query, 'AND USER_AUTH.`ROLE` = 0'))

        data = await self.db_pool.fetch(query)
        return [{'id': item[0], 'level': item[1], 'nick': item[2], 'role': bool(item[3])} for item in data]

    async def auth_adder(self, target_id: int, level: int, role: bool = False, server_id: int = 0):
        await self.__init_check__()
        query = 'INSERT INTO "USER_AUTH" ("ITEM_ID", "LEVEL", "ROLE", "SERVER_ID") VALUES ($1, $2, $3, $4)'
        try:
            await self.db_pool.execute(query, target_id, level, int(role), server_id)
        except asyncpg.IntegrityConstraintViolationError:
            raise DatabaseDuplicateEntry('USER_AUTH has duplicates!') from asyncpg.IntegrityConstraintViolationError

    async def auth_changer(self, target_id: int, level: int):
        await self.__init_check__()
        query = 'UPDATE "USER_AUTH" set "LEVEL" = $1 where "ITEM_ID" = $2'
        await self.db_pool.execute(query, level, target_id)

    async def whitelist_check(self, server_id: int, channel_id: int) -> int:
        await self.__init_check__()
        query = 'SELECT "WHITELIST_LEVEL" FROM "CHANNEL_AUTH" WHERE "SERVER_ID" = $1 AND "CHANNEL_ID" = $2'
        data = await self.db_pool.fetchval(query, server_id, channel_id)
        return data

    async def whitelist_add(self, server_id: int, channel_id: int, whitelist_level: int = 1):
        await self.__init_check__()
        query = 'INSERT INTO "CHANNEL_AUTH" ("SERVER_ID", "CHANNEL_ID", "WHITELIST_LEVEL") VALUES ($1, $2, $3)'
        try:
            await self.db_pool.execute(query, server_id, channel_id, whitelist_level)
        except asyncpg.IntegrityConstraintViolationError:
            raise DatabaseDuplicateEntry('CHANNEL_AUTH has duplicates!') from asyncpg.IntegrityConstraintViolationError

    async def whitelist_remove(self, server_id: int, channel_id: int):
        await self.__init_check__()
        query = 'DELETE FROM "CHANNEL_AUTH" WHERE "SERVER_ID" = $1 AND "CHANNEL_ID" = $2'
        await self.db_pool.execute(query, server_id, channel_id)

    async def add_nucleus_user(self, user_id: str, first_name: str, last_name: str, email: str, mobile: str,
                               class_id: str, year: int, cookies: str, last_login: datetime, discord_id: int):
        await self.__init_check__()
        nucleus_query = 'INSERT INTO "NUCLEUS_USERS" ("USER_ID", "FIRST_NAME", "LAST_NAME", "EMAIL", "MOBILE_NO", ' \
                        '"CLASS_ID", "YEAR", "COOKIES", "LAST_LOGIN", "DISCORD_ID") VALUES ($1, $2, $3, $4, $5, $6, ' \
                        '$7, $8, $9, $10) '
        try:
            await self.db_pool.execute(nucleus_query, user_id, first_name, last_name, email, mobile, class_id, year,
                                       cookies, last_login, discord_id)
        except asyncpg.IntegrityConstraintViolationError:
            raise DatabaseDuplicateEntry(
                'NUCLEUS_USERS has duplicates!') from asyncpg.IntegrityConstraintViolationError

    async def update_nucleus_user(self, user_id: str, first_name: str, last_name: str, email: str, mobile: str,
                                  class_id: str, year: int, cookies: str, last_login: datetime, discord_id: int):
        await self.__init_check__()
        query = 'UPDATE "NUCLEUS_USERS" SET "USER_ID"= $1, "FIRST_NAME" = $2, "LAST_NAME" = $3, "EMAIL" = $4, ' \
                '"MOBILE_NO" = $5, ' \
                '"CLASS_ID" = $6, "YEAR" = $7, "COOKIES" = $8, "LAST_LOGIN" = $9 WHERE "DISCORD_ID" = $10'
        await self.db_pool.execute(query, user_id, first_name, last_name, email, mobile, class_id, year, cookies,
                                   last_login, discord_id)

    async def delete_nucleus_user(self, user_id: str):
        await self.__init_check__()
        query = 'DELETE FROM "NUCLEUS_USERS" WHERE "USER_ID"=$1'
        await self.db_pool.execute(query, user_id)

    async def get_last_checked(self, class_id: str):
        await self.__init_check__()
        query = 'SELECT "COURSE_ID", "LAST_CHECKED" FROM "NUCLEUS_COURSES" WHERE "CLASS_ID" = $1'
        result = await self.db_pool.fetch(query, class_id)
        return result

    async def update_last_checked(self, class_id: str, course_id: str, new_date: datetime):
        await self.__init_check__()
        query = 'UPDATE "NUCLEUS_COURSES" SET "LAST_CHECKED" = $3 WHERE "CLASS_ID" = $1 AND "COURSE_ID" = $2'
        await self.db_pool.execute(query, class_id, course_id, new_date)

    async def add_nucleus_class(self, class_id: str):
        await self.__init_check__()
        query = 'INSERT INTO "NUCLEUS_CLASS" ("CLASS_ID") VALUES ($1)'
        try:
            await self.db_pool.execute(query, class_id)
        except asyncpg.IntegrityConstraintViolationError:
            raise DatabaseDuplicateEntry(
                'NUCLEUS_CLASS has duplicates!') from asyncpg.IntegrityConstraintViolationError

    async def get_nucleus_class(self):
        await self.__init_check__()
        query = 'SELECT "CLASS_ID" FROM "NUCLEUS_CLASS"'
        records = await self.db_pool.fetch(query)
        return [record[0] for record in records]

    async def add_class_alert(self, class_id: str, role_id: int, channel_id: int, guild_id: int):
        await self.__init_check__()
        query = 'INSERT INTO "CLASS_ALERTS" ("CLASS_ID","ROLE_ID", "ALERT_CHANNEL_ID", "ALERT_GUILD_ID") VALUES ($1, ' \
                '$2, $3, $4) '
        try:
            await self.db_pool.execute(query, class_id, role_id, channel_id, guild_id)
        except asyncpg.IntegrityConstraintViolationError:
            raise DatabaseDuplicateEntry(
                'CLASS_ALERTS has duplicates!') from asyncpg.IntegrityConstraintViolationError

    async def add_nucleus_course(self, class_id: str, course_id: str, course_name: str, is_elective: bool,
                                 last_checked: Optional[datetime] = datetime.now()):
        await self.__init_check__()
        query = 'INSERT INTO "NUCLEUS_COURSES" ("CLASS_ID", "COURSE_ID", "COURSE_NAME", "IS_ELECTIVE", ' \
                '"LAST_CHECKED") VALUES ($1, ' \
                '$2, $3, $4, $5) '
        try:
            await self.db_pool.execute(query, class_id, course_id, course_name, is_elective, last_checked)
        except asyncpg.IntegrityConstraintViolationError:
            raise DatabaseDuplicateEntry(
                'CLASS_ALERTS has duplicates!') from asyncpg.IntegrityConstraintViolationError

    async def get_nucleus_course(self, class_id: str):
        await self.__init_check__()
        query = 'SELECT "COURSE_ID" FROM "NUCLEUS_COURSES" WHERE "CLASS_ID"=$1'
        records = await self.db_pool.fetch(query, class_id)
        return [record[0] for record in records]

    async def get_nucleus_user_ids(self):
        await self.__init_check__()
        query = 'SELECT DISTINCT "USER_ID" FROM "NUCLEUS_USERS"'
        records = await self.db_pool.fetch(query)
        return [record[0] for record in records]

    async def add_alert_account(self, user_id: str, password: str, cookies: str, class_id: str):
        await self.__init_check__()
        query = 'INSERT INTO "ALERT_ACCOUNTS" ("USER_ID", "PASSWORD", "COOKIES", "CLASS_ID") VALUES ($1, $2, $3, $4)'
        await self.db_pool.execute(query, user_id, password, cookies, class_id)

    async def get_user(self, user_id: str):
        await self.__init_check__()
        query = 'SELECT * FROM "NUCLEUS_USERS" WHERE "USER_ID"=$1'
        record = await self.db_pool.fetchrow(query, user_id)
        return record

    async def get_user_by_discord_id(self, discord_id: int):
        await self.__init_check__()
        query = 'SELECT * FROM "NUCLEUS_USERS" WHERE "DISCORD_ID"=$1'
        return await self.db_pool.fetchrow(query, discord_id)

    async def get_alert_accounts(self):
        await self.__init_check__()
        query = 'SELECT "USER_ID", "COOKIES", "CLASS_ID" FROM "ALERT_ACCOUNTS"'
        records = await self.db_pool.fetch(query)
        return records

    async def get_alert_account_by_id(self, user_id: str):
        await self.__init_check__()
        query = 'SELECT * FROM "ALERT_ACCOUNTS" WHERE "USER_ID"=$1'
        return await self.db_pool.fetchrow(query, user_id)

    async def update_alert_account(self, user_id: str, cookies: str):
        await self.__init_check__()
        query = 'UPDATE "ALERT_ACCOUNTS" SET ("COOKIES","UPDATED_AT") = ($2, $3) WHERE "USER_ID"=$1'
        try:
            await self.db_pool.execute(query, user_id, cookies, datetime.now())
        except Exception as err:
            print(err)

    async def get_alert_details(self, class_id: str):
        await self.__init_check__()
        query = 'SELECT "ALERT_CHANNEL_ID", "ALERT_GUILD_ID", "ROLE_ID" FROM "CLASS_ALERTS" WHERE "CLASS_ID"=$1'
        records = await self.db_pool.fetch(query, class_id)
        return records

    async def add_discord_user(self, discord_id: int, discord_username: str):
        await self.__init_check__()
        query = 'INSERT INTO "NUCLEUS_DISCORD_USERS" ("DISCORD_ID", "DISCORD_USERNAME") VALUES ($1, $2)'
        await self.db_pool.execute(query, discord_id, discord_username)

    async def get_discord_user(self, discord_id: int):
        await self.__init_check__()
        query = 'SELECT * FROM "NUCLEUS_DISCORD_USERS" WHERE "DISCORD_ID"=$1'
        record = await self.db_pool.fetchrow(query, discord_id)
        return record

    async def delete_discord_user(self, discord_id: int):
        await self.__init_check__()
        query = 'DELETE FROM "NUCLEUS_DISCORD_USERS" WHERE "DISCORD_ID"=$1'
        await self.db_pool.execute(query, discord_id)

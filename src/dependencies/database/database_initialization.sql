/*
  DATABASE INITIALIZATION FILE FOR RAIDER

  Used to verify all constraints and reinforce them
  at the start up of the bot.

*/


/*  TABLE:  PERMISSIONS_NAMES    */
CREATE TABLE IF NOT EXISTS "USER_AUTH"
(
    "ENTRY_ID"  SERIAL
        constraint channel_auth_pk
            primary key,
    "ITEM_ID"   bigint             not null,
    "LEVEL"     int      default 0 not null,
    "ROLE"      smallint default 0 not null,
    "SERVER_ID" bigint   default 0 not null,

    constraint "ENTRY_ID_UNIQUE"
        unique ("ENTRY_ID"),
    constraint "ITEM_ID_UNIQUE"
        unique ("ITEM_ID")
);

/*  TABLE:  PERMISSIONS_NAMES    */
CREATE TABLE IF NOT EXISTS "PERMISSIONS_NAMES"
(
    "ID"    SERIAL
        constraint channel_auth_pk
            primary key,
    "NAME"  varchar(45) not null,
    "LEVEL" int         not null,

    constraint "LEVEL_UNIQUE"
        unique ("LEVEL")
);

/*  TABLE:  CHANNEL_AUTH    */
CREATE TABLE IF NOT EXISTS "CHANNEL_AUTH"
(
    "ENTRY_ID"        SERIAL
        constraint channel_auth_pk
            primary key,
    "SERVER_ID"       bigint   not null,
    "CHANNEL_ID"      bigint   not null,
    "WHITELIST_LEVEL" smallint not null,

    constraint "CHANNEL_ID_UNIQUE"
        unique ("CHANNEL_ID")
);

/*  TABLE:  NUCLEUS_CLASS     */
CREATE TABLE IF NOT EXISTS "NUCLEUS_CLASS"
(
    "CLASS_ID"  varchar(4)
        constraint nucleus_class_pk
            primary key,

    constraint "CLASS_ID_UNIQUE"
        unique ("CLASS_ID")
);

/*  TABLE:  NUCLEUS_DISCORD_USERS     */
CREATE TABLE IF NOT EXISTS "NUCLEUS_DISCORD_USERS"
(
    "DISCORD_ID"          bigint not null
        constraint discord_users_pk
            primary key,
    "DISCORD_USERNAME"    varchar not null,

    constraint "DISCORD_ID_UNIQUE"
        unique ("DISCORD_ID")
);

/*  TABLE:  NUCLEUS_USERS     */
CREATE TABLE IF NOT EXISTS "NUCLEUS_USERS"
(
    "USER_ID"    varchar(7)                not null,
    "FIRST_NAME" text                      not null,
    "LAST_NAME"  text,
    "EMAIL"      varchar(50)               not null,
    "MOBILE_NO"  varchar(12),
    "CLASS_ID"   varchar(7),
    "YEAR"       smallint,
    "PASSWORD"   varchar(50) default NULL::character varying,
    "COOKIES"    text,
    "LAST_LOGIN" timestamp,
    "DATE_ADDED" timestamp   default now() not null,
    "EXPIRED"    boolean     default false not null,
    "DISCORD_ID" bigint     not null
        constraint nucleus_users_pk
            primary key,

    constraint "DISCORD_ID_FKEY"
        foreign key ("DISCORD_ID") references "NUCLEUS_DISCORD_USERS" ("DISCORD_ID"),

    constraint "CLASS_ID_FKEY_USERS"
        foreign key ("CLASS_ID") references "NUCLEUS_CLASS" ("CLASS_ID")

);

/*  TABLE:  CLASS_ALERTS     */
CREATE TABLE IF NOT EXISTS "CLASS_ALERTS"
(
    "CLASS_ID"         varchar(4),
    "ALERT_CHANNEL_ID" bigint not null,
    "ALERT_GUILD_ID"   bigint not null,
    "ROLE_ID"          bigint not null,

    constraint "UNIQUE_ENTRY_ALERTS"
        unique ("CLASS_ID", "ALERT_GUILD_ID", "ALERT_CHANNEL_ID"),

    constraint "CLASS_ID_FKEY_ALERTS"
        foreign key ("CLASS_ID") references "NUCLEUS_CLASS" ("CLASS_ID")
);

/*  TABLE:  NUCLEUS_COURSES    */
CREATE TABLE IF NOT EXISTS "NUCLEUS_COURSES"
(
    "CLASS_ID"      varchar(4),
    "COURSE_ID"     varchar(7) not null,
    "COURSE_NAME"   text not null,
    "IS_ELECTIVE"   boolean default false not null,
    "ASSIGNMENTS_LAST_CHECKED"  timestamp default now() not null,
    "RESOURCES_LAST_CHECKED"  timestamp default now() not null,

    constraint "UNIQUE_ENTRY_COURSES"
        unique ("CLASS_ID", "COURSE_ID", "COURSE_NAME"),

    constraint "CLASS_ID_FKEY_COURSES"
        foreign key ("CLASS_ID") references "NUCLEUS_CLASS" ("CLASS_ID")
);

/*  TABLE:  ALERT_ACCOUNTS     */
CREATE TABLE IF NOT EXISTS "ALERT_ACCOUNTS"
(
    "USER_ID"       varchar(7)
        constraint alert_accounts_pk
            primary key,
    "PASSWORD"      varchar,
    "COOKIES"       text not null,
    "CLASS_ID"      varchar(4),
    "CREATED_AT"    timestamp default now(),
    "UPDATED_AT"    timestamp default now(),
    constraint "CLASS_ID_FKEY_ALERT_ACCOUNTS"
        foreign key ("CLASS_ID") references "NUCLEUS_CLASS" ("CLASS_ID")
);

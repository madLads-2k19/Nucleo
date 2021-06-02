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

/*  TABLE:  NUCLEUS_USERS     */
CREATE TABLE IF NOT EXISTS  "NUCLEUS_USERS"
(
    "USER_ID"    varchar(7)                not null
        constraint nucleus_users_pk
            primary key,
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

    constraint "USER_ID_UNIQUE"
        unique ("USER_ID"),

    constraint "CLASS_ID_FKEY"
        foreign key ("CLASS_ID") references "NUCLEUS_CLASS" ("CLASS_ID")

);


CREATE TABLE IF NOT EXISTS "NUCLEUS_CLASS"
(
    "CLASS_ID"     varchar(4)
        constraint nucleus_class_pk
            primary key,
    "LAST_CHECKED" date not null default CURRENT_DATE,

    constraint "CLASS_ID_UNIQUE"
        unique ("CLASS_ID")
);



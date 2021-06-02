/*
  DATABASE INITIALIZATION FILE FOR RAIDER

  Used to verify all constraints and reinforce them
  at the start up of the bot.

*/


/*  TABLE:  PERMISSIONS_NAMES    */
CREATE TABLE IF NOT EXISTS "USER_AUTH"
(
    "ENTRY_ID"  SERIAL primary key,
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
    "ID"    SERIAL primary key,
    "NAME"  varchar(45) not null,
    "LEVEL" int         not null,

    constraint "LEVEL_UNIQUE"
        unique ("LEVEL")
);

/*  TABLE:  CHANNEL_AUTH    */
CREATE TABLE IF NOT EXISTS "CHANNEL_AUTH"
(
    "ENTRY_ID"        SERIAL primary key,
    "SERVER_ID"       bigint   not null,
    "CHANNEL_ID"      bigint   not null,
    "WHITELIST_LEVEL" smallint not null,

    constraint "CHANNEL_ID_UNIQUE"
        unique ("CHANNEL_ID")
);

/*  TABLE:  ASSIGNMENTS     */
CREATE TABLE IF NOT EXISTS "ASSIGNMENTS"
(
    "CLASS_ID"     varchar(4),
    "LAST_CHECKED" date not null default CURRENT_DATE,

    constraint "CLASS_ID_FKEY"
        foreign key("CLASS_ID") references "NUCLEUS_USERS"("classId"),
    constraint "CLASS_ID_CHECK" check ("CLASS_ID" ~ [12][0-9][A-Za-z]{2}[0-9]{2})
);



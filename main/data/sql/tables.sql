CREATE TABLE guilds (
    guild_id BIGINT PRIMARY KEY
)

CREATE TABLE usage (
    command TEXT PRIMARY KEY,
    counter INTEGER
)

CREATE TABLE frozen_names(
    guild_id BIGINT REFERENCES guilds ON DELETE CASCADE,
    user_id BIGINT,
    frozen_name VARCHAR(32),
    PRIMARY KEY (guild_id, user_id)
)

CREATE TABLE "guild_config" (
    guild_id BIGINT REFERENCES guilds ON DELETE CASCADE,
    prefix VARCHAR DEFAULT 'g.',
    grole BIGINT,
    premium BOOL DEFAULT 'FALSE', blacklisted BOOL DEFAULT "FALSE", 
    PRIMARY KEY (guild_id)
)


CREATE TABLE tags (
    tag_guild_id BIGINT REFERENCES guilds ON DELETE CASCADE, 
    tag_name VARCHAR(32),
    tag_content TEXT NOT NULL,
    tag_author BIGINT NOT NULL,
    tag_uses INT DEFAULT 0 NOT NULL,
    tag_creation_date INT NOT NULL,
    tag_aliases TEXT [],
    UNIQUE(tag_guild_id, tag_name),
    PRIMARY KEY(tag_guild_id, tag_name, tag_aliases)
)

CREATE TABLE users_data (
    user_id BIGINT,
    commands_ran BIGINT,
    blacklisted BOOL DEFAULT "FALSE",
    tips BOOL DEFAULT "FALSE",
    premium BOOL DEFAULT "FALSE",
    PRIMARY KEY (user_id)
)

CREATE TABLE disabled_commands (
    snowflake_id BIGINT,
    command_name TEXT,
    PRIMARY KEY(snowflake_id, command_name)
)

CREATE TABLE "item_info" (
    item_id INTEGER PRIMARY KEY NOT NULL,
    item_price INTEGER NOT NULL,
    item_name TEXT NOT NULL,
    item_description TEXT NOT NULL,
    item_brief TEXT
)

CREATE TABLE user_Inventory(
    user_id BIGINT NOT NULL,
    item_id INT NOT NULL,
    amount INT, 
    PRIMARY KEY (user_id, item_id)
) 

CREATE TABLE playlists (
    user_id BIGINT NOT NULL,
    playlist_name VARTEXT(32) NOT NULL,
    playlist_id INT NOT NULL
)

CREATE TABLE playlist_songs (
    playlist_id INT NOT NULL,
    playlist_song TEXT NOT NULL,
    playlist_url TEXT NOT NULL,
    song_id INT NOT NULL DEFAULT -1
)

CREATE TABLE timers (
    id INTEGER PRIMARY KEY,
    expires TIMESTAMP NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event TEXT NOT NULL,
    extra TEXT
)
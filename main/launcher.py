import logging
import sys

sys.dont_write_bytecode = True

from os import environ
from os.path import dirname, join

import discord
from bot import GrootBot
from dotenv import load_dotenv

environ["JISHAKU_NO_UNDERSCORE"] = "True"
environ["JISHAKU_NO_DM_TRACEBACK"] = "True"

dotenv_path = join(dirname(__file__), "config/secrets.env")
load_dotenv(dotenv_path)

intent_data = {
    x: True for x in ("guilds", "members", "emojis", "messages", "reactions", "presences", "voice_states")
}
intents = discord.Intents(**intent_data)
mentions = discord.AllowedMentions(
    roles=False, users=True, everyone=False, replied_user=True
)
bot_data = {
    "token": environ.get("main"),
    "intents": intents,
    "case_insensitive": True,
    "help_command": None,
    "allowed_mentions": mentions,
    "owner_id": 396805720353275924,
}

bot = GrootBot(**bot_data)

logging.basicConfig(
    filename=f"{bot.cwd}/config/logs/error.log",
    filemode="w",
    datefmt="%d-%b-%y %H:%M:%S",
    format="[{asctime}] {levelname:<10} | {name:<10}: {message}",
    style="{",
    level=logging.WARNING,
)

bot.starter()

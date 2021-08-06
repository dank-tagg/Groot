import sys
import discord
sys.dont_write_bytecode = True

from os import environ
from utils._type import *

environ["JISHAKU_NO_UNDERSCORE"] = "True"
environ["JISHAKU_NO_DM_TRACEBACK"] = "True"

intents = discord.Intents.all()
mentions = discord.AllowedMentions(roles=False, everyone=False)

bot_data = {
    "intents": intents,
    "case_insensitive": True,
    "help_command": None,
    "allowed_mentions": mentions,
    "owner_id": 396805720353275924,
}

bot = GrootBot(**bot_data)

bot.starter()

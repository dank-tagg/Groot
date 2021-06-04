import logging
import re
import sys

sys.dont_write_bytecode = True

from os import environ
from os.path import dirname, join

import discord
from bot import GrootBot
from dotenv import load_dotenv
from utils.useful import wait_ready

environ["JISHAKU_NO_UNDERSCORE"] = "True"
environ["JISHAKU_NO_DM_TRACEBACK"] = "True"

dotenv_path = join(dirname(__file__), "bot_config/secrets.env")
load_dotenv(dotenv_path)

intent_data = {
    x: True for x in ("guilds", "members", "emojis", "messages", "reactions", "presences")
}
intents = discord.Intents(**intent_data)
mentions = discord.AllowedMentions(
    roles=False, users=True, everyone=False, replied_user=True
)
bot_data = {
    "token": environ.get("dev"),
    "intents": intents,
    "case_insensitive": True,
    "help_command": None,
    "allowed_mentions": mentions,
    "owner_id": 396805720353275924,
}

bot = GrootBot(**bot_data)

logging.basicConfig(
    filename=f"{bot.cwd}/bot_config/logs/error.log",
    filemode="w",
    datefmt="%d-%b-%y %H:%M:%S",
    format="[{asctime}] {levelname:<10} | {name:<10}: {message}",
    style="{",
    level=logging.INFO,
)


@bot.event
@wait_ready(bot=bot)
async def on_message(message):
    if re.fullmatch("<@(!)?812395879146717214>", message.content):
        await message.channel.send(f"My prefix is `{await bot.get_prefix(message)}`")
        return

    ctx = await bot.get_context(message)
    if message.author.id == bot.owner.id:
        return await bot.process_commands(message)
    if (
        message.author.id in bot.cache["blacklisted_users"]
        or getattr(message.guild, "id", None) in bot.cache["blacklisted_users"]
    ):
        return
    if ctx.valid and ctx.command.name in bot.cache["disabled_commands"].keys():
        if (
            ctx.valid
            and message.channel.id in bot.cache["disabled_commands"][ctx.command.name]
            or ctx.valid
            and message.guild.id in bot.cache["disabled_commands"][ctx.command.name]
        ):
            return
    await bot.process_commands(message)


bot.starter()

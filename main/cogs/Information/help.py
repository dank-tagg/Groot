from utils._type import *

import discord
import difflib

from datetime import datetime
from discord.ext import commands
from utils.json import read_json
from utils.useful import Cooldown, Embed


class GrootHelp(commands.HelpCommand):


    @staticmethod
    def get_doc(command):
        _help = command.help or "This command has no description"
        return _help

    def get_command_help(self, command) -> Embed:
        # Base
        em = Embed(
            title=f"{command.qualified_name} {command.signature}",
            description=self.get_doc(command)
        )

        # Cooldowns
        cooldown = discord.utils.find(lambda x: isinstance(x, Cooldown), command.checks) or Cooldown(1, 3, 1, 1, commands.BucketType.user)

        default_cooldown = cooldown.default_mapping._cooldown.per
        altered_cooldown = cooldown.altered_mapping._cooldown.per

        em.add_field(
            name="Cooldowns",
            value=f"Default: `{default_cooldown}s`\nPremium: `{altered_cooldown}s`",
        )

        #Aliases
        em.add_field(
            name="Aliases",
            value=f"```{', '.join(command.aliases) or 'No aliases'}```",
            inline=False
        )

        if not isinstance(command, commands.Group) or not command.commands:
            return em

        # Subcommands
        all_subs = [
            f"{sub.name}{f' {sub.signature}' or ''}" for sub in command.walk_commands()
        ]

        em.add_field(
            name="Subcommands",
            value='```\n' + '\n'.join(all_subs) + '```'
        )

        return em

    async def handle_help(self, command: commands):
        return await self.context.send(embed=self.get_command_help(command))

    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot


        em = Embed(description=
            f"My prefixes for **{ctx.guild.name}** are `{await bot.get_prefix(ctx.message)}`\n"
            f"Total commands: {len(list(bot.walk_commands()))} | Usable by you: {len(await self.filter_commands(list(bot.walk_commands()), sort=True))} \n"
            "```diff\n- [] = optional argument\n"
            "- <> = required argument\n"
            f"+ Type {await bot.get_prefix(ctx.message)}help [command | category] for "
            "more help on a specific category or command!```"
            "[Support](<https://discord.gg/nUUJPgemFE>) | "
            "[Vote](https://top.gg/bot/812395879146717214/vote) | "
            f"[Invite](https://grootdiscordbot.xyz/invite) | "
            "[Website](https://grootdiscordbot.xyz)"
        )

        em.set_author(
            name=ctx.author,
            icon_url=ctx.author.avatar.url
        )
        # Cogs
        cogs = bot.cogs.copy()
        if ctx.author != bot.owner:
            cogs.pop("Unlisted")
            cogs.pop("Krypton")
            cogs.pop("Jishaku")

        newline = '\n'
        em.add_field(
            name="Categories",
            value=f'```\n{newline.join(cogs.keys())}```'
        )

        # News
        config = read_json("config")
        news = config['updates']
        date = datetime.strptime(news['date'], "%Y-%m-%d %H:%M:%S.%f")
        date, link, message = date.strftime("%d %B, %Y"), news['link'], news['message']

        def shorten(message):
            if len(message) > 275:
                message = message[:275] + f'... [read more]({link})'
            return message

        em.add_field(
            name=f"📰 Latest News - {date}",
            value=f"{shorten(message)}"
        )
        channel = self.get_destination()
        await channel.send(embed=em)

    async def send_command_help(self, command):
        await self.handle_help(command)

    async def send_group_help(self, group):
        await self.handle_help(group)

    async def send_cog_help(self, cog):
        commands = [f"`{c.name}`" for c in await self.filter_commands(cog.walk_commands(), sort=True)]
        em = Embed(
            description=" ".join(commands)
        )
        em.set_author(name=cog.__cog_name__)
        channel = self.get_destination()
        await channel.send(embed=em)


    # Error handlers
    async def command_not_found(self, command):
        if command.lower() == "all":
            commands = [f"`{command.name}`" for command in await self.filter_commands(self.context.bot.commands)]
            em = Embed(description=" ".join(commands))
            em.set_author(name=f"All commands [{len(commands)}]")
            channel = self.get_destination()
            await channel.send(embed=em)
            return None

        close_matches = difflib.get_close_matches(
            command,
            list(self.context.bot.cogs) + list(self.context.bot.all_commands)
        )
        if close_matches:
            await self.context.send_help(close_matches[0])
            return

        return f"No command/category called `{command}` found."


    async def send_error_message(self, error):
        if error is None:
            return
        channel = self.get_destination()
        await channel.send(error)


class Help(commands.Shard):
    def __init__(self, cog: commands.Cog):
        super().__init__(cog)
        self.bot = cog.bot
        help_command = GrootHelp()
        help_command.cog = cog
        cog.bot.help_command = help_command

def setup(cog):
    cog.add_shard(Help(cog))

import discord
from discord.ext import commands
from utils.useful import Embed, Cooldown
import contextlib



class GrootHelp(commands.HelpCommand):

    def __init__(self, bot, **options):
        super().__init__(bot, **options)
        self.categories = bot.categories
    
    @staticmethod
    def get_doc(command):
        _help = command.help or "This command has no description"
        return _help
    
    def get_command_help(self, command) -> Embed:
        # Base
        em = Embed(
            title=f"{command.name} {command.signature}",
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
            value=f"```{','.join(command.aliases) or 'No aliases'}```", 
            inline=False
        )

        if not isinstance(command, commands.Group):
            return em
        # Subcommands
        all_subs = [
            f"`{sub.name}` {f'`{sub.signature}`' if sub.signature else ''}" for sub in command.walk_commands()
        ]
        
        em.add_field(
            name="Subcommands", 
            value="\n".join(all_subs)
        )

        return em
        
    async def handle_help(self, command):
        with contextlib.suppress(commands.CommandNotFound):
            await command.can_run(self.context)
            return await self.context.send(embed=self.get_command_help(command))
        raise commands.BadArgument("You do not have the permissions to view this command's help.")

    async def send_bot_help(self, mapping):
        
        em = Embed(description=
            f"Prefix `{self.context.prefix or 'g.'}`\n"
            f"Total commands: {len(self.context.bot.commands)} | Usable by you: {len(await self.filter_commands(self.context.bot.walk_commands(), sort=True))} \n"
            "```diff\n- [] = optional argument\n"
            "- <> = required argument\n"
            f"+ Type {self.context.prefix}help [command | category] for "
            "more help on a specific category or command!```"
            "[Support](<https://discord.gg/nUUJPgemFE>) | "
            "[Vote](https://top.gg/bot/812395879146717214/vote) | "
            f"[Invite]({discord.utils.oauth_url(812395879146717214)})\n"
        )

        em.set_author(
            name=self.context.author, 
            icon_url=self.context.author.avatar_url
        )
        # Categories
        categories = self.categories.keys()
        em.add_field(
            name="Categories",
            value=", \n".join(self.context.bot.categories.keys())
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
        em.set_author(name=cog.name)
        channel = self.get_destination()
        await channel.send(embed=em)

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        help_command, help_command.cog = GrootHelp(bot), self
        bot.help_command = help_command
    
def setup(bot):
    bot.add_cog(Help, category="Information")
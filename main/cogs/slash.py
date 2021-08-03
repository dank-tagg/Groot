from utils._type import *
import discord

from discord.ext import commands

class SlashCommand(commands.Command):
    """The class for SlashCommand registration."""

    def __init__(self, func, **kwargs):
        super().__init__(func, **kwargs)

async def get_interaction_context(self, interaction, *, cls=None):
    pass


API_URL = 'https://discord.com/api/v8/applications/{app}/guilds/{guild}/commands'

class Slash(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.loop.create_task(self.ready_commands())

    async def ready_commands(self):
        await self.bot.wait_until_ready()

        send_to = API_URL.format(app=self.bot.user.id, guild=int(self.bot.config['SUPPORT_SERVER']))
        headers = {"Authorization": f"Bot {self.bot.http.token}"}

        slash_commands = [
            {
                'name': command.name,
                'description': command.help or 'This command is not documented yet',
                'options': [
                    {
                        'type': 3,
                        'name': name,
                        'description': f'Parameter {name}',
                        'required': param.default is param.empty
                    }
                    for name, param in iter(command.clean_params.items())
                ]
            }
            for command in self.get_commands()
            if not isinstance(command, commands.Group)
        ]


        async with self.bot.session.put(send_to, json=slash_commands, headers=headers) as resp:
            resp.raise_for_status()

    @SlashCommand
    async def w(self, ctx, text: str):
        await ctx.send('yo')

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.application_command:
            return
        




def setup(bot):
    bot.add_cog(Slash(bot))
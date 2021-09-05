from utils._type import *

import discord
import functools
import time
import inspect
import os
import contextlib
import io
import textwrap

from discord.ext import commands
from utils.useful import Embed
from discord.types.interactions import (
    ApplicationCommandInteractionDataOption as CommandOption
)

class SlashMeta(commands.Command):
    """The class for SlashCommand registration."""

    def __init__(self, func, **kwargs):
        self.slash = True
        self.beta = kwargs.get('beta')
        super().__init__(func, **kwargs)

SlashCommand = functools.partial(commands.command, cls=SlashMeta)

def unpack_group(group: commands.Group, subcommands: List[str]):
    for subcommand in subcommands:
        group = group.all_commands[subcommand]

    return group

def construct_unslotted(cls, *args, **kwargs):
    return type(cls.__name__, (cls,), {})(*args, **kwargs)

async def convert_params(ctx: customContext, options: List[CommandOption]):
    if ctx.guild is None:
        get_channel = ctx.bot.get_channel
        fetch_user = ctx.bot.fetch_user
        get_role = lambda _: None
    else:
        get_channel = ctx.guild.get_channel
        fetch_user = ctx.guild.fetch_member
        get_role = ctx.guild.get_role

    kwargs = {}
    for option in options:
        if option["type"] in {1, 2}:
            continue

        cleaned_value = option.get("value")
        if option["type"] == 6:
            cleaned_value = await fetch_user(int(option["value"]))
        elif option["type"] == 7:
            cleaned_value = get_channel(int(option["value"]))
        elif option["type"] == 8:
            cleaned_value = get_role(int(option["value"]))

        elif option["type"] == 9:
            cleaned_value = discord.Object(int(option["value"]))
        kwargs[option["name"]] = cleaned_value

    return [ctx.cog, ctx], kwargs

async def _parse_arguments(ctx: customContext, callback=None):
    if ctx.interaction is None or callback is None:
        await callback(ctx)

API_URL = 'https://discord.com/api/v8/applications/{app}/commands'
PRIVATE_URL = 'https://discord.com/api/v8/applications/{app}/guilds/{guild}/commands'

class Slash(commands.Shard):

    def __init__(self, cog: commands.Cog):
        super().__init__(cog)
        self.bot = cog.bot
        self.bot.loop.create_task(self.ready_commands())

    async def ready_commands(self):
        await self.bot.wait_until_ready()

        send_to = API_URL.format(app=self.bot.user.id)
        headers = {"Authorization": f"Bot {self.bot.http.token}"}

        slash_commands = [
            {
                'name': command.name.rstrip('_slashCommand'),
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
            for command in self.bot.commands if getattr(command, 'slash', False)
            if not isinstance(command, commands.Group) and not command.beta
        ]

        async with self.bot.session.put(send_to, json=slash_commands, headers=headers) as resp:
            resp.raise_for_status()

        beta_commands = [
            {
                'name': command.name.rstrip('_slashCommand'),
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
            for command in self.bot.commands if getattr(command, 'slash', False)
            if not isinstance(command, commands.Group) and command.beta
        ]

        beta_url = PRIVATE_URL.format(app=self.bot.user.id, guild=self.bot.config.getint('Other', 'SUPPORT_SERVER'))
        async with self.bot.session.put(beta_url, json=beta_commands, headers=headers) as resp:
            resp.raise_for_status()

    @SlashCommand()
    async def ping(self, ctx: customContext):
        """
        Shows the bot's latency in miliseconds.
        Useful if you want to know if the bot is lagging or not
        """
        start = time.perf_counter()
        await ctx.interaction.response.send_message(f'{self.bot.icons["loading"]} pinging...')
        end = time.perf_counter()
        typing_ping = (end - start) * 1000

        start = time.perf_counter()
        await self.bot.db.execute('SELECT 1')
        end = time.perf_counter()

        sql_ping = (end - start) * 1000
        await ctx.interaction.followup.send(
            f"{self.bot.icons['typing']} ** | Typing**: {round(typing_ping, 1)} ms\n{self.bot.icons['groot']} ** | Websocket**: {round(self.bot.latency*1000)} ms\n{self.bot.icons['database']} ** | Database**: {round(sql_ping, 1)} ms"
        )

    @SlashCommand(beta=True)
    async def source(self, ctx: customContext, command: str):
        """Displays my full source code or for a specific command.
        To display the source code of a subcommand you can separate it by
        periods, e.g. tag.create for the create subcommand of the tag command
        or by spaces.
        """
        source_url = 'https://github.com/dank-tagg/Groot'
        branch = 'main'
        if command is None:
            return await ctx.send(source_url)

        obj = self.bot.get_command(command.replace('.', ' '))
        if obj is None:
            return await ctx.send('Could not find command.')

        src = obj.callback.__code__
        filename = src.co_filename

        lines, firstlineno = inspect.getsourcelines(src)
        location = os.path.relpath(filename).replace('\\', '/')

        final_url = f'{source_url}/tree/{branch}/main/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}'

        class SourceView(discord.ui.View):
            def __init__(self, ctx: customContext):
                super().__init__()
                self.ctx = ctx
                self.add_item(discord.ui.Button(label='Source URL', url=final_url))

            @discord.ui.button(emoji='<:trashcan:822050746333003776>')
            async def delete(self, button: discord.ui.Button, interaction: discord.Interaction):
                with contextlib.suppress(discord.HTTPException):
                    await self.ctx.message.delete()
                await interaction.message.delete()

            @discord.ui.button(label='Source File')
            async def send_file(self, button: discord.ui.Button, interaction: discord.Interaction):
                if interaction.user != self.ctx.author:
                    await interaction.response.send_message('Oops. This is not your interaction.', ephemeral=True)
                    return

                await interaction.channel.send(file=discord.File(io.BytesIO(textwrap.dedent(''.join(lines)).encode('ascii')), 'source.py'))
                button.disabled = True
                await interaction.response.edit_message(view=self)

        em = Embed(title=f'Here is the source for {obj.qualified_name}')

        if len("".join(lines)) < 2000:
            zwsp = '\u200b'
            em.description = f'```py\n{textwrap.dedent("".join(lines).replace("``", f"`{zwsp}`"))}\n```'
        else:
            em.description = '```\nSource was too long to be shown here. Click Source File/Source URL below to see it.```'
        await ctx.interaction.response.send_message(embed=em, view=SourceView(ctx))

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.application_command:
            return

        command = interaction.data['name'] + '_slashCommand'
        options = interaction.data.get('options') or []

        message = construct_unslotted(
            cls=discord.PartialMessage,
            channel=interaction.channel,
            id=interaction.id
        )

        message.edited_at = None
        message.author = interaction.user
        prefix = await self.bot.get_prefix(message)
        if isinstance(prefix, list):
            prefix = prefix[0]

        subcommands = []
        for option in options:
            if option['type'] in {1, 2}:
                subcommand = option['name']
                options = option.get('options') or []

                subcommands.append(subcommand)
                command += " " + subcommand

        message.content = f'{prefix}{command}'
        message.clean_content = message.content

        ctx = await self.bot.get_context(message)
        if not ctx.command:
            await interaction.response.send_message("I cannot find this command! Please wait 1 hour if the bot has just updated")
            return

        ctx.prefix = '/'
        ctx.interaction = interaction
        if isinstance(ctx.command, commands.Group):
            ctx.command = unpack_group(ctx.command, subcommands)

        ctx.args, ctx.kwargs = await convert_params(ctx, options)
        if not hasattr(ctx.command._parse_arguments, "func"):
            ctx.command._parse_arguments = functools.partial(
                _parse_arguments,
                callback=ctx.command._parse_arguments
            )
        try:
            await ctx.command.invoke(ctx)
        except commands.CommandError as e:
            await ctx.command.dispatch_error(ctx, e)
        else:
            if ctx.interaction.response.is_done():
                return

def setup(cog):
    cog.add_shard(Slash(cog))
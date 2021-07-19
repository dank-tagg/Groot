"""
The root file for the Krypton extension
"""

import discord
import sys
import math

from discord.ext import commands
from ..utils.embed import Krybed
from .base import KryFeature

try:
    import psutil
except ImportError:
    psutil = None

__all__ = ('Root', )


def natural_size(size_in_bytes: int):
    """
    Converts a number of bytes to an appropriately-scaled unit
    E.g.:
        1024 -> 1.00 KiB
        12345678 -> 11.77 MiB
    """
    units = ('B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB')

    power = int(math.log(size_in_bytes, 1024))

    return f"{size_in_bytes / (1024 ** power):.2f} {units[power]}"

class Root(KryFeature):

    @KryFeature.Command(name='krypton', aliases=['kry'], invoke_without_command=True)
    async def krypton(self, ctx: commands.Context):
        """
        The Krypton debug and diagnostic commands.

        This command on its own gives a status brief.
        All other functionality is within its subcommands.
        """
        summary = [
            f'Krypton v1.0.0, discord.py `v{discord.__version__}`, ',
            f'Python `{sys.version}` on `{sys.platform}`'.replace('\n', '')
        ]

        if psutil:
            try:
                proc = psutil.Process()
                with proc.oneshot():
                    try:
                        mem = proc.memory_full_info()
                        summary.append(f'Using {natural_size(mem.rss)} physical memory and '
                                       f'{natural_size(mem.vms)} virtual memory, '
                                       f'{natural_size(mem.uss)} of which unique to this process.')
                    except psutil.AccessDenied:
                        pass
                    
                    try:
                        name = proc.name()
                        pid = proc.pid
                        threads = proc.num_threads()
                        summary.append(f'Running on PID {pid} (`{name}`) with `{threads}` thread(s)')
                    except psutil.AccessDenied:
                        pass

                    summary.append('')
            except psutil.AccessDenied:
                summary.append(
                    'psutil is installed, but this process does not have high enough access rights '
                    'to query process information.'
                )
                summary.append('')

        cache_summary = f'`{len(self.bot.guilds):,}` guild(s) and `{len(self.bot.users):,}` user(s)'
        if isinstance(self.bot, discord.AutoShardedClient):
            if len(self.bot.shards) > 20:
                summary.append(
                    f"This bot is automatically sharded ({len(self.bot.shards)} shards of {self.bot.shard_count})"
                    f" and can see {cache_summary}."
                )
            else:
                shard_ids = ', '.join(str(i) for i in self.bot.shards.keys())
                summary.append(
                    f"This bot is automatically sharded (Shards {shard_ids} of {self.bot.shard_count})"
                    f" and can see {cache_summary}."
                )
        elif self.bot.shard_count:
            summary.append(
                f"This bot is manually sharded (Shard {self.bot.shard_id} of {self.bot.shard_count})"
                f" and can see {cache_summary}."
            )
        else:
            summary.append(f"This bot is not sharded and can see {cache_summary}.")

        if self.bot._connection.max_messages:
            message_cache = f"Message cache capped at {self.bot._connection.max_messages}"
        else:
            message_cache = "Message cache is disabled"

        if discord.version_info >= (1, 5, 0):
            presence_intent = f"presence intent is {'enabled' if self.bot.intents.presences else 'disabled'}"
            members_intent = f"members intent is {'enabled' if self.bot.intents.members else 'disabled'}"

            summary.append(f"{message_cache}, {presence_intent} and {members_intent}.")
        else:
            guild_subscriptions = f"guild subscriptions are {'enabled' if self.bot._connection.guild_subscriptions else 'disabled'}"

            summary.append(f"{message_cache} and {guild_subscriptions}.")

        summary.append(f"Average websocket latency: {round(self.bot.latency * 1000, 2)}ms")

        await ctx.send(embed=Krybed(description='\n'.join(summary)))

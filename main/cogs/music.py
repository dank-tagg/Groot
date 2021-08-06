from utils._type import *

import asyncio
import async_timeout
import discord
import re
import wavelink
import math
import random

from discord.ext import commands, menus
from utils.useful import Cooldown, Embed, get_title
from utils import paginations


URL_REG = re.compile(r'https?://(?:www\.)?.+')

def convert(ms):
    seconds, milliseconds = divmod(ms, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    result = [hours, minutes, seconds]
    format_result = [f"0{i}" if len(str(i)) == 1 else str(i) for i in result]
    return ":".join(format_result).removeprefix("00:").removesuffix(":")

class Track(wavelink.Track):
    """Wavelink Track object with a requester attribute."""

    __slots__ = ('requester', )

    def __init__(self, *args, **kwargs):
        super().__init__(*args)

        self.requester = kwargs.get('requester')

class Player(wavelink.Player):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ctx = kwargs.get('context', None)
        if self.ctx:
            self.dj = self.ctx.author

        self.waiting = False
        self.updating = False
        self.looping = False
        self.loading = False

        self.previous = None
        self.queue = asyncio.Queue()

        self.skip_votes = set()
        self.stop_votes = set()
        self.shuffle_votes = set()

    async def play_next(self):
        if self.is_playing or self.waiting or self.loading:
            return

        self.skip_votes.clear()
        self.stop_votes.clear()
        self.shuffle_votes.clear()

        if self.looping and (track := self.previous):
            self.waiting = True
            await self.play(track)
            self.waiting = False
            return

        try:
            self.waiting = True
            with async_timeout.timeout(300):
                track = await self.queue.get()
        except asyncio.TimeoutError:
            self.waiting = False
            return await self.teardown()

        await self.play(track)
        await self.send_embed()

        self.previous = track
        self.waiting = False
        self.looping = False

    async def stop(self):
        """Custom stop method"""
        self.looping = False
        await super().stop()

    async def send_embed(self):
        if self.updating: return

        self.updating = True
        track = self.current
        if not track: return

        em = Embed(
            title = get_title(track),
            url = track.uri
        )

        fields = {
            "Author": (track.author, True),
            "Duration": (convert(int(track.length)), True),
            "Looping": (f"{self.ctx.bot.icons['greenTick'] if self.looping else self.ctx.bot.icons['redTick']}", True),
            "Requested by": (track.requester.mention, True),
            "DJ": (self.dj.mention, True),
            "Volume": (f"{self.volume}%", True)
        }
        for k, v in fields.items():
            em.add_field(name=k, value=v[0], inline=True)

        em.set_thumbnail(url=track.thumb)
        em.set_footer(text=f"Queue index: 1/{self.queue.qsize()+1}", icon_url=track.requester.avatar.url)
        await self.ctx.reply(content=f"Now playing: **{track.title}**", embed=em)
        self.updating = False

    async def teardown(self):
        try:
            await self.destroy()
        except KeyError:
            pass

    def update_context(self, ctx: customContext):
        self.ctx = ctx

class Music(commands.Cog, wavelink.WavelinkMixin):
    def __init__(self, bot: GrootBot):
        self.bot = bot

        if not hasattr(bot, 'wavelink'):
            self.bot.wavelink = wavelink.Client(bot=bot)

        self.bot.loop.create_task(self.start_nodes())

    async def start_nodes(self):
        await self.bot.wait_until_ready()

        if self.bot.wavelink.nodes:
            previous = self.bot.wavelink.nodes.copy()

            for node in previous.values():
                await node.destroy()

        created = False
        node_num = 1

        while not created:
            try:
                await self.bot.wavelink.initiate_node(
                    host='127.0.0.1',
                    port=2333,
                    rest_uri='http://127.0.0.1:2333',
                    password=self.bot.config.get('password'),
                    identifier=f"Node {node_num}",
                    region=f"us_central"
                )
            except wavelink.errors.NodeOccupied:
                node_num += 1
                created = True

    def required(self, ctx: customContext):
        """Method which returns required votes based on amount of members in a channel."""
        player = self.get_player(ctx)
        channel = self.bot.get_channel(int(player.channel_id))
        required = math.ceil((len(channel.members) - 1) / 2.5)

        if ctx.command.name == 'stop':
            if len(channel.members) == 3:
                required = 2

        return required

    def get_player(self, ctx: customContext):
        player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)
        player.update_context(ctx)
        return player

    def is_privileged(self, ctx: customContext):
        player = self.get_player(ctx)
        return ctx.author in [player.dj, getattr(player.current, "requester", None)] or ctx.author.guild_permissions.kick_members

    @wavelink.WavelinkMixin.listener('on_track_stuck')
    @wavelink.WavelinkMixin.listener('on_track_end')
    @wavelink.WavelinkMixin.listener('on_track_exception')
    async def on_player_stop(self, node: wavelink.Node, payload):
        await payload.player.play_next()

    @wavelink.WavelinkMixin.listener("on_track_exception") #ty to cryptex for helping because jadon is stupid omegalul
    async def on_node_event_(self, node, event):
        if "YouTube (429)" in event.error:
            player = event.player
            if URL_REG.fullmatch(player.query):
                new_track = await self.bot.wavelink.get_tracks(f"scsearch:{player.track.title}")
            else:
                new_track = await self.bot.wavelink.get_tracks(f"scsearch:{player.query}")
            if new_track:
                track = Track(
                    new_track[0].id,
                    new_track[0].info,
                    requester=player.ctx.author,
                )
                await player.play(track)
                await player.send_embed()
            else:
                raise commands.BadArgument(f"{self.bot.icons['redTick']} | No song was found with the given query. Try again.")
        else:
            await event.player.ctx.send(event.error)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return

        player = self.bot.wavelink.get_player(member.guild.id, cls=Player)

        if not player.channel_id or not player.ctx:
            player.node.players.pop(member.guild.id)
            return

        channel = self.bot.get_channel(int(player.channel_id))

        if member == player.dj and after.channel is None:
            for m in channel.members:
                if m.bot:
                    continue
                else:
                    player.dj = m
                    return

        elif after.channel == channel and player.dj not in channel.members:
            player.dj = member

    @commands.command(name='connect', usage="[channel]")
    async def _connect(self, ctx: customContext, channel: discord.VoiceChannel = None, invoked_from=None):
        """Connects to the given voice channel. If none is given, it defaults to the voice channel the user is in"""
        player = self.get_player(ctx)

        channel = getattr(ctx.author.voice, "channel", channel)
        if not channel:
            raise commands.BadArgument(f"{self.bot.icons['redTick']} | No channel to join. Either join one, or specify a valid channel to join.")

        if channel == getattr(ctx.guild.me.voice, "channel", False):
            raise commands.BadArgument(f"{self.bot.icons['redTick']} | Already connected to {channel.mention} !")

        if not invoked_from:
            await ctx.reply(f"{self.bot.icons['greenTick']} | Connected to {channel.mention}")
        await player.connect(channel.id)

    @commands.command(name='disconnect')
    async def _disconnect(self, ctx: customContext):
        """Disconnects from a voice channel if the bot was in one."""
        player = self.get_player(ctx)

        if self.is_privileged(ctx):
            await ctx.reply(f"{self.bot.icons['greenTick']} | The song requester/DJ ({ctx.author.mention}) has disconnected the bot.")
            player.stop_votes.clear()
            await player.teardown()
        else:
            await ctx.reply("You aren't allowed to do that. Please ask the DJ or an admin to run this command.")

    @commands.command(name='play')
    @commands.check(Cooldown(1, 10, 1, 3, commands.BucketType.user))
    async def _play(self, ctx: customContext, *, query: str):
        """Searches YouTube for the query, plays the song found."""
        player = self.get_player(ctx)

        if not player.is_connected:
            await ctx.invoke(self._connect, invoked_from=ctx.command)

        query = query.strip('<>')
        if not URL_REG.match(query):
            query = f'ytsearch:{query}'

        tracks = await self.bot.wavelink.get_tracks(query)
        if not tracks:
            raise commands.BadArgument(f"{self.bot.icons['redTick']} | No song was found with the given query. Try again.")

        if isinstance(tracks, wavelink.TrackPlaylist):
            for track in tracks.tracks:
                track = Track(track.id, track.info, requester=ctx.author)
                await player.queue.put(track)

            await ctx.reply(f"{self.bot.icons['plus']} | Added the playlist {tracks.data['playlistInfo']['name']} to the queue.")
        else:
            track = Track(tracks[0].id, tracks[0].info, requester=ctx.author)
            await ctx.reply(f"{self.bot.icons['plus']} | Added the song **{track.title}** to the queue.")
            await player.queue.put(track)

        if not player.is_playing:
            await player.play_next()

    @commands.command(name="loop")
    @commands.check(Cooldown(1, 10, 1, 3, commands.BucketType.user))
    async def _loop(self, ctx: customContext):
        """Loops the current song or turns the loop off"""
        player = self.get_player(ctx)

        if player.looping:
            player.looping = False
            message = f"Stopped looping **{player.current.title}**"
        else:
            player.looping = True
            message = f"Looping **{player.current.title}**..."

        return await ctx.reply(f"{self.bot.icons['greenTick']} | {message}")

    @commands.command(name="skip", aliases=["next"])
    async def _skip(self, ctx: customContext):
        """Skips the current song"""
        player = self.get_player(ctx)


        if not player.is_connected:
            raise commands.BadArgument(f"{self.bot.icons['redTick']} | No song is playing.")

        if self.is_privileged(ctx):
            await ctx.reply(f"{self.bot.icons['greenTick']} | The song requester/DJ ({ctx.author.mention}) has skipped the song.")
            player.skip_votes.clear()
            return await player.stop()

        required = self.required(ctx)
        player.skip_votes.add(ctx.author)
        if (votes := len(player.skip_votes)) >= required:
            await ctx.reply(f"{self.bot.icons['greenTick']} | {votes} people voted to skip this song. Skipping...")
            player.skip_votes.clear()
            await player.stop()
        else:
            await ctx.reply(f"{ctx.author.mention} has voted to skip this song (`{votes}/{required}`)")

    @commands.command(name="stop")
    async def _stop(self, ctx: customContext):
        """Stops the current player"""
        player = self.get_player(ctx)

        if not player.is_connected:
            return

        if self.is_privileged(ctx):
            await ctx.reply(f"{self.bot.icons['greenTick']} | The song requester/DJ ({ctx.author.mention}) has stopped the player.")
            player.stop_votes.clear()
            return await player.teardown()

        required = self.required(ctx)
        player.stop_votes.add(ctx.author)

        if (votes := len(player.stop_votes)) >= required:
            await ctx.reply(f"{self.bot.icons['greenTick']} | {votes} people voted to stop the player. Stopping...")
            await player.teardown()
        else:
            await ctx.reply(f'{ctx.author.mention} has voted to stop the player. (`{votes}/{required}`)')

    @commands.group(case_insensitive=True,invoke_without_command=True, aliases=['q'])
    @commands.check(Cooldown(1, 10, 1, 3, commands.BucketType.user))
    async def queue(self, ctx: customContext):
        """Display the players queued songs."""
        player = self.get_player(ctx)

        if not player.is_connected or player.loading:
            return

        if player.queue.qsize() == 0:
            await ctx.reply(f"{self.bot.icons['redTick']} | No more songs in the queue. Add some songs to the queue and try again.")
            return


        entries = [f"**{i+1}**. [{track.title}]({track.uri}) | `{convert(int(track.length))}`" for i, track in enumerate(player.queue._queue, start=1)]
        menu = menus.MenuPages(paginations.QueueSource(entries, player))
        await menu.start(ctx)

    @queue.command(name="remove")
    async def _remove(self, ctx: customContext, position: int):
        """Removes a song from the queue by it's position."""
        player = self.get_player(ctx)

        if not player.is_connected:
            return

        size = player.queue.qsize() + 1

        if position > size or position == 1:
            raise commands.BadArgument(f"{self.bot.icons['redTick']} | The given song number to remove must be inside the queue (and not the current playing one).")

        track = player.queue._queue[position-2]
        del player.queue._queue[position-2]
        await ctx.reply(f"{self.bot.icons['minus']} | Removed **{position}. {track.title}** from the queue.")


    @commands.command(name="volume")
    async def _volume(self, ctx: customContext, volume: int):
        """Changes the volume"""
        player = self.get_player(ctx)

        if not player.is_connected:
            raise commands.BadArgument(f"{self.bot.icons['redTick']} | No song is playing.")

        if not self.is_privileged(ctx):
            return await ctx.reply(f"{self.bot.icons['redTick']} | Only the requester or the DJ can change volume value.")

        if not 0 < volume < 101:
            return await ctx.reply(f"{self.bot.icons['redTick']} | The volume value must be in between 0 and 100")

        await player.set_volume(volume)
        await ctx.reply(f"{self.bot.icons['greenTick']} | Changed volume to {volume}%")

    @commands.command(name="shuffle")
    async def _shuffle(self, ctx: customContext):
        """Shuffles the queue"""
        player = self.get_player(ctx)

        if not player.is_connected:
            raise commands.BadArgument(f"{self.bot.icons['redTick']} | No song is playing.")

        if player.queue.qsize() < 3:
            return await ctx.reply(f"{self.bot.icons['redTick']} | Add more songs to the queue first before shuffling.")

        if self.is_privileged(ctx):
            random.shuffle(player.queue._queue)
            return await ctx.reply(f"{self.bot.icons['greenTick']} | {ctx.author.mention} shuffled the playlist.")

        required = self.required(ctx)
        player.skip_votes.add(ctx.author)

        if (votes := len(player.skip_votes)) >= required:
            player.skip_votes.clear()
            random.shuffle(player.queue._queue)
            await ctx.reply(f"{self.bot.icons['greenTick']} | Shuffled playlist.")
        else:
            await ctx.reply(f'{ctx.author.mention} has voted to shuffle the playlist. (`{votes}/{required}`)')

    @commands.command(name="nowplaying", aliases=["np", "current"])
    async def _nowplaying(self, ctx: customContext):
        """Shows the current playing song"""
        player = self.get_player(ctx)

        if not player.is_connected:
            raise commands.BadArgument(f"{self.bot.icons['redTick']} | No song is playing.")

        await player.send_embed()

    @commands.command(aliases=['eq'], usage="<flat|boost|metal|piano>")
    async def equalizer(self, ctx: customContext, *, equalizer: str):
        """Change the players equalizer."""
        player = self.get_player(ctx)

        if not player.is_connected:
            raise commands.BadArgument(f"{self.bot.icons['redTick']} | No song is playing.")

        if not self.is_privileged(ctx):
            return await ctx.reply(f"{self.bot.icons['redTick']} | Only privileged members (DJ/requester) can change the equalizer.")

        eqs = {
            'flat': wavelink.Equalizer.flat(),
            'boost': wavelink.Equalizer.boost(),
            'metal': wavelink.Equalizer.metal(),
            'piano': wavelink.Equalizer.piano()
        }

        eq = eqs.get(equalizer.lower(), None)

        if not eq:
            joined = "\n".join(eqs.keys())
            return await ctx.reply(f"{self.bot.icons['redTick']} | Invalid EQ provided. Choose from `flat` `boost` `metal` `piano`.")

        await ctx.reply(f"{self.bot.icons['greenTick']} | Successfully changed equalizer to {equalizer}")
        await player.set_eq(eq)

    @commands.command(aliases=['dj', 'swap'])
    async def swap_dj(self, ctx: customContext, member: discord.Member = None):
        """Swap the current DJ to another member in the voice channel."""
        player = self.get_player(ctx)

        if not player.is_connected:
            return

        if not self.is_privileged(ctx):
            return await ctx.reply(f"{self.bot.icons['redTick']} | Only admins and the DJ may use this command.")

        channel = self.bot.get_channel(int(player.channel_id))
        members = channel.members

        if member and member not in members:
            return await ctx.reply(f"{self.bot.icons['redTick']} | **{member.name}** is not currently in {channel.mention}, so can not be a DJ.")

        if member and member == player.dj:
            return await ctx.reply(f"{self.bot.icons['redTick']} | Cannot swap DJ to the current DJ...")

        if len(members) <= 2:
            return await ctx.reply(f"{self.bot.icons['redTick']} | No more members to swap to.")

        if member:
            player.dj = member
            return await ctx.send(f"{member.mention} is now the DJ.")

        for m in members:
            if m == player.dj or m.bot:
                continue
            else:
                player.dj = m
                return await ctx.send(f"{self.bot.icons['greenTick']} | {member.mention} is now the DJ.")

def setup(bot):
    bot.add_cog(Music(bot), cat_name="Music")

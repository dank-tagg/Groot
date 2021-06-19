import asyncio
import async_timeout
import discord
import re
import wavelink
import math
import datetime
from discord.ext import commands
from utils.useful import Embed, get_title


URL_REG = re.compile(r'https?://(?:www\.)?.+')

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

        self.queue = asyncio.Queue()

        self.skip_votes = set()
        self.stop_votes = set()
        self.shuffle_votes = set()
    
    async def play_next(self):
        if self.is_playing or self.waiting:
            return
        
        self.skip_votes.clear()
        self.stop_votes.clear()
        self.shuffle_votes.clear()

        try:
            self.waiting = True
            with async_timeout.timeout(300):
                track = await self.queue.get()
        except asyncio.TimeoutError:
            return await self.teardown()
        
        await self.play(track)
        self.waiting = False
        await self.send_embed()
    
    async def send_embed(self):
        if self.updating: return

        self.updating = True
        track = self.current
        if not track: return

        channel = self.bot.get_channel(int(self.channel_id))
        queue_size = self.queue.qsize()

        em = Embed(
            title = get_title(track),
            url = track.uri
        )

        fields = {
            "Author": (track.author, True), 
            "Duration": (str(datetime.timedelta(milliseconds=int(track.length))), True),
            "\u200b": ("\u200b", True),
            "Requested by": (track.requester.mention, True),
            "DJ": (self.dj.mention, True),
            "Volume": (f"{self.volume}%", True)
        }
        for k, v in fields.items():
            em.add_field(name=k, value=v[0], inline=True)
        
        em.set_thumbnail(url=track.thumb)
        em.set_footer(text=f"Queue index: 1/{self.queue.qsize()+1}", icon_url=track.requester.avatar_url)
        await self.ctx.reply(content=f"Now playing: **{track.title}**", embed=em)
        self.updating = False

    async def teardown(self):
        try:
            await self.destroy()
        except KeyError:
            pass
    
    def update_context(self, ctx):
        self.ctx = ctx

class Music(commands.Cog, wavelink.WavelinkMixin):
    def __init__(self, bot):
        self.bot = bot

        if not hasattr(bot, 'wavelink'):
            self.bot.wavelink = wavelink.Client(bot=bot)
        
        self.bot.loop.create_task(self.start_nodes())
    
    async def start_nodes(self):
        await self.bot.wait_until_ready()

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
            else:
                created = True
    
    def required(self, ctx: commands.Context):
        """Method which returns required votes based on amount of members in a channel."""
        player = self.get_player(ctx)
        channel = self.bot.get_channel(int(player.channel_id))
        required = math.ceil((len(channel.members) - 1) / 2.5)

        if ctx.command.name == 'stop':
            if len(channel.members) == 3:
                required = 2

        return required
    
    def get_player(self, ctx):
        player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)
        player.update_context(ctx)
        return player
    
    def is_privileged(self, ctx):
        player = self.get_player(ctx)
        return ctx.author in [player.dj, player.current.requester] or ctx.author.guild_permissions.kick_members

    @wavelink.WavelinkMixin.listener('on_track_stuck')
    @wavelink.WavelinkMixin.listener('on_track_end')
    @wavelink.WavelinkMixin.listener('on_track_exception')
    async def on_player_stop(self, node: wavelink.Node, payload):
        await payload.player.play_next()

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
    async def _connect(self, ctx, channel: discord.VoiceChannel = None, invoked_from=None):
        """Connects to the given voice channel. If none is given, it defaults to the voice channel the user is in"""
        player = self.get_player(ctx)

        channel = getattr(ctx.author.voice, "channel", channel)
        if not channel:
            raise commands.BadArgument(f"{self.bot.redTick} | No channel to join. Either join one, or specify a valid channel to join.")
        
        if channel == getattr(ctx.guild.me.voice, "channel", False):
            raise commands.BadArgument(f"{self.bot.redTick} | Already connected to {channel.mention} !")

        if not invoked_from:
            await ctx.reply(f"{self.bot.greenTick} | Connected to {channel.mention}")
        await player.connect(channel.id)
    
    @commands.command(name='play')
    async def _play(self, ctx, *, query: str):
        """Searches YouTube for the query, plays the song found."""
        player = self.get_player(ctx)

        if not player.is_connected:
            await ctx.invoke(self._connect, invoked_from=ctx.command)
        
        query = query.strip('<>')
        if not URL_REG.match(query):
            query = f'ytsearch:{query}'
        
        tracks = await self.bot.wavelink.get_tracks(query)
        if not tracks:
            raise commands.BadArgument(f"{self.bot.redTick} | No song was found with the given query. Try again.")
        
        if isinstance(tracks, wavelink.TrackPlaylist):
            for track in tracks.tracks:
                track = Track(track.id, track.info, requester=ctx.author)
                await player.queue.put(track)
            
            await ctx.reply(f"{self.bot.plus} | Added the playlist {tracks.data['playlistInfo']['name']} to the queue.")
        else:
            track = Track(tracks[0].id, tracks[0].info, requester=ctx.author)
            await ctx.reply(f"{self.bot.plus} | Added the song **{track.title}** to the queue.")
            await player.queue.put(track)
        
        if not player.is_playing:
            await player.play_next()
    
    @commands.command(name="skip", aliases=["next"])
    async def _skip(self, ctx):
        """Skips the current song"""
        player = self.get_player(ctx)
        

        if not player.is_connected:
            raise commands.BadArgument(f"{self.bot.redTick} | No song is playing.")
        
        if self.is_privileged(ctx):
            await ctx.reply(f"{self.bot.greenTick} | The song requester/DJ ({ctx.author.mention}) has skipped the song.")
            player.skip_votes.clear()
            return await player.stop()
        
        required = self.required(ctx)
        player.skip_votes.add(ctx.author)
        if (votes := len(player.skip_votes)) >= required:
            await ctx.reply(f"{self.bot.greenTick} | {votes} people voted to skip this song. Skipping...")
            player.skip_votes.clear()
            await player.stop()
        else:
            await ctx.reply(f"{ctx.author.mention} has voted to skip this song (`{votes}/{required}`)")

    @commands.command(name="stop")
    async def _stop(self, ctx):
        """Stops the current player"""
        player = self.get_player(ctx)
        
        if not player.is_connected:
            return
        
        if self.is_privileged(ctx):
            await ctx.reply(f"{self.bot.greenTick} | The song requester/DJ ({ctx.author.mention}) has stopped the player.")
            player.stop_votes.clear()
            return await player.teardown()
        
        required = self.required(ctx)
        player.stop_votes.add(ctx.author)

        if (votes := len(player.stop_votes)) >= required:
            await ctx.reply(f"{self.bot.greenTick} | {votes} people voted to stop the player. Stopping...")
            await player.teardown()
        else:
            await ctx.reply(f'{ctx.author.mention} has voted to stop the player. (`{votes}/{required}`)')

    @commands.command(aliases=['q', 'que'])
    async def queue(self, ctx: commands.Context):
        """Display the players queued songs."""
        player = self.get_player(ctx)

        if not player.is_connected:
            return

        entries = [f"{i+1}. {get_title(track)} - {player.current.requester.mention}" for i, track in enumerate(player.queue._queue)][:8]
        entries.insert(0, f"NOW: **{get_title(player.current, 20)}** - {player.current.requester.mention}\n")
        em = Embed(
            description="\n".join(entries)
        )
        em.set_author(name=f"🎶 Current queue [{len(entries)}]")
        await ctx.reply(embed=em)
    
    @commands.command(name="volume")
    async def _volume(self, ctx, volume: int):
        """Changes the volume"""
        player = self.get_player(ctx)

        if not player.is_connected:
            return

        if not self.is_privileged(ctx):
            return await ctx.reply(f"{self.bot.redTick} | Only the requester or the DJ can change volume value.")
        
        if not 0 < volume < 101:
            return await ctx.reply(f"{self.bot.redTick} | The volume value must be in between 0 and 100")
        
        await player.set_volume(volume)
        await ctx.reply(f"{self.bot.greenTick} | Changed volume to {volume}%")

    @commands.command(name="shuffle")
    async def _shuffle(self, ctx):
        """Shuffles the playlist"""
        player = self.get_player(ctx)

        if not player.is_connected:
            return
        
        if player.queue.qsize() < 3:
            return await ctx.reply(f"{self.bot.redTick} | Add more songs to the queue first before shuffling.")

        if self.is_privileged(ctx):
            random.shuffle(player.queue._queue)
            return await ctx.reply(f"{self.bot.greenTick} | {ctx.author.mention} shuffled the playlist.")

        required = self.required(ctx)
        player.skip_votes.add(ctx.author)

        if (votes := len(player.skip_votes)) >= required:
            player.skip_votes.clear()
            random.shuffle(player.queue._queue)
            await ctx.reply(f"{self.bot.greenTick} | Shuffled playlist.")
        else:
            await ctx.reply(f'{ctx.author.mention} has voted to shuffle the playlist. (`{votes}/{required}`)')
    
    @commands.command(name="nowplaying", aliases=["np", "current"])
    async def _nowplaying(self, ctx):
        """Shows the current playing song"""
        player = self.get_player(ctx)

        if not player.is_connected:
            return
        
        await player.send_embed()

    @commands.command(aliases=['eq'], usage="<flat|boost|metal|piano>")
    async def equalizer(self, ctx, *, equalizer: str):
        """Change the players equalizer."""
        player = self.get_player(ctx)

        if not player.is_connected:
            return
        
        if not self.is_privileged(ctx):
            return await ctx.reply(f"{self.bot.redTick} | Only privileged members (DJ/requester) can change the equalizer.")

        eqs = {
            'flat': wavelink.Equalizer.flat(),
            'boost': wavelink.Equalizer.boost(),
            'metal': wavelink.Equalizer.metal(),
            'piano': wavelink.Equalizer.piano()
        }

        eq = eqs.get(equalizer.lower(), None)

        if not eq:
            joined = "\n".join(eqs.keys())
            return await ctx.reply(f'{self.bot.redTick} | Invalid EQ provided. Choose from `flat` `boost` `metal` `piano`.')

        await ctx.reply(f'{self.bot.greenTick} | Successfully changed equalizer to {equalizer}')
        await player.set_eq(eq)

    @commands.command(aliases=['dj', 'swap'])
    async def swap_dj(self, ctx, member: discord.Member = None):
        """Swap the current DJ to another member in the voice channel."""
        player = self.get_player(ctx)

        if not player.is_connected:
            return

        if not self.is_privileged(ctx):
            return await ctx.reply(f'{self.bot.redtick} | Only admins and the DJ may use this command.')
        
        channel = self.bot.get_channel(int(player.channel_id))
        members = channel.members

        if member and member not in members:
            return await ctx.reply(f'{self.bot.redTick} | **{member.name}** is not currently in {channel.mention}, so can not be a DJ.')

        if member and member == player.dj:
            return await ctx.reply(f'{self.bot.redTick} | Cannot swap DJ to the current DJ...')

        if len(members) <= 2:
            return await ctx.reply(f'{self.bot.redTick} | No more members to swap to.', delete_after=15)

        if member:
            player.dj = member
            return await ctx.send(f'{member.mention} is now the DJ.')

        for m in members:
            if m == player.dj or m.bot:
                continue
            else:
                player.dj = m
                return await ctx.send(f'{self.bot.greenTick} | {member.mention} is now the DJ.')

def setup(bot):
    bot.add_cog(Music(bot))
import asyncio
import discord
import re
import wavelink
import math
import datetime
import typing
import random
from discord.ext import commands, menus
from utils.useful import Embed, get_title, is_beta
from utils import paginations
from cogs.music import Track


URL_REG = re.compile(r'https?://(?:www\.)?.+')

class Playlist:
    """Custom class for playlist"""
    def __init__(self, **kwargs):
        self.name = kwargs['name']
        self.id = kwargs['id']
        self.length = kwargs['length']
        self.songs = kwargs['songs'] # In tuples (song_name, url, song_id)
    
    async def play(self, ctx, wavelink, player, requester, **kwargs):
        amt_of_songs = kwargs['songs']
        msg = await ctx.reply(f"<a:loading:856978168476205066> | `(0/{amt_of_songs})` Queueing songs... please be patient.\n_This might take a while_")
        loaded_songs = 0
        for song in self.songs:
            if random.randint(0, 20) > 16:
                await msg.edit(content=f"<a:loading:856978168476205066> | `({loaded_songs}/{amt_of_songs})` Queueing songs... please be patient.\n_This might take a while_")
            tracks = await wavelink.get_tracks(song[1])
            try:
                track = Track(tracks[0].id, tracks[0].info, requester=requester)
            except Exception as e:
                await ctx.send(f"{song[0]} couldn't be loaded...")
            else:
                await player.queue.put(track)
            loaded_songs += 1
        
        await msg.edit(content=f"<:greenTick:814504388139155477> | `({loaded_songs}/{amt_of_songs})` Queued songs! Now playing...")
        await asyncio.sleep(0.5)
        await player.play_next()
        
    
    async def remove_song(self, db, song_id):
        songs = [tup[2] for tup in self.songs]
        if song_id not in songs:
            return None
        query = "DELETE FROM playlist_songs WHERE song_id = ?"
        cur = await db.execute(query, (song_id, ))
        return cur.rowcount




async def get_playlist(db, playlist_id: int):
    query = """
            SELECT playlist_song, playlist_url, song_id,
                (
                    SELECT playlist_name
                    FROM playlists
                    WHERE playlists.playlist_id = ?
                )
            FROM playlist_songs 
            WHERE playlist_id = (
                SELECT playlist_id FROM playlists 
                WHERE playlist_id = ?
            )
            """
    cur = await db.execute(query, (playlist_id, playlist_id))
    data = await cur.fetchall()

    if not data:
        return None

    playlist_info = {
        "name": data[0][3],
        "id": playlist_id,
        "length": len(data),
        "songs": [(name, url, song_id) for name, url, song_id, _ in data]
    }
    return Playlist(**playlist_info)
    

class Playlists(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
        # Playlists -
    async def is_playlistOwner(self, user_id, playlist):
        query = "SELECT user_id FROM playlists WHERE playlist_id = ?"
        cur = await self.bot.db.execute(query, (playlist, ))
        owner = await cur.fetchone()
        if not owner:
            return None
        return user_id == owner[0]
    
    async def new_id(self):
        query = "SELECT playlist_id FROM playlists ORDER BY playlist_id DESC"
        cur = await self.bot.db.execute(query)
        _id = await cur.fetchone()
        return (0 if not _id else _id[0]) + 1

    async def new_song_id(self):
        query = "SELECT song_id FROM playlist_songs ORDER BY song_id DESC"
        cur = await self.bot.db.execute(query)
        _id = await cur.fetchone()
        return (0 if not _id else _id[0]) + 1
    
 
    @commands.group(invoke_without_command=True, case_insensitive=True)
    async def playlist(self, ctx):
        query = """
                SELECT playlist_name, playlist_id, 
                (
                    SELECT Count(*) 
                    FROM playlist_songs
                    WHERE playlist_songs.playlist_id = playlists.playlist_id
                )
                FROM playlists
                WHERE user_id = ?
                """
        cur = await self.bot.db.execute(query, (ctx.author.id, ))
        playlists = await cur.fetchall()
        
        formatted = [f"{i+1}. Playlist **{playlist[0]}** with `ID {playlist[1]}` and `{playlist[2]}` songs" for i, playlist in enumerate(playlists)]
        em = Embed(
            description="\n".join(formatted)
        )
        em.set_author(name=f"{ctx.author.name}'s playlists [{len(formatted)}/5]", icon_url=ctx.author.avatar_url)

        await ctx.reply(embed=em)
    
    @playlist.command(name="info", usage="<id> [page]")
    async def _playlist_info(self, ctx, playlist_id: int):
        playlist = await get_playlist(self.bot.db, playlist_id)

        if not playlist:
            return await ctx.reply(f"{self.bot.emojis_dict('redTick')} | No playlist data was found with `ID {playlist_id}` (Empty or does not exist)")

        entries = [f"`ID {tup[2]}`. [{get_title(tup[0])}]({tup[1]})" for tup in playlist.songs]
        menu = menus.MenuPages(paginations.PlaylistSource(entries, playlist))
        await menu.start(ctx)
    
    @playlist.command(name="create", usage="<name>")
    async def _playlist_create(self, ctx, *, name):
        query = "SELECT Count(*) FROM playlists WHERE user_id = ?"
        cur = await self.bot.db.execute(query, (ctx.author.id, ))
        number_of_playlists = await cur.fetchone()

        if number_of_playlists[0] == 5:
            return await ctx.reply(f"{self.bot.emojis_dict('redTick')} | You only can have up to 5 playlists")
        
        query = "INSERT INTO playlists VALUES (?, ?, ?)"
        _id = await self.new_id()
        cur = await self.bot.db.execute(query, (ctx.author.id, name, _id))
        
        await ctx.reply(f"{self.bot.emojis_dict('greenTick')} | Created playlist **{name}** with `ID {_id}`")

    @playlist.command(name="delete", aliases=["del"], usage="<id>")
    async def _playlist_delete(self, ctx, playlist_id: int):
        if check := await self.is_playlistOwner(ctx.author.id, playlist_id) is False:
            return await ctx.reply(f"{self.bot.emojis_dict('redTick')} | You do not own this playlist.")
        elif check is None:
            return await ctx.reply(f"{self.bot.emojis_dict('redTick')} | This playlist doesn't seem to exist.")

        queries = ["DELETE FROM playlist_songs WHERE playlist_id = ?", "DELETE FROM playlists WHERE playlist_id = ?"]
        for query in queries:
            await self.bot.db.execute(query, (playlist_id, ))
        await ctx.reply(f"{self.bot.emojis_dict('greenTick')} | Deleted playlist with `ID {playlist_id}`")

    @playlist.command(name="addsong", usage="<playlist ID> <song>")
    async def _playlist_addsong(self, ctx, playlist_id:int, *, query):
        if (check := await self.is_playlistOwner(ctx.author.id, playlist_id)) is False:
            return await ctx.reply(f"{self.bot.emojis_dict('redTick')} | You do not own this playlist.")
        elif check is None:
            return await ctx.reply(f"{self.bot.emojis_dict('redTick')} | This playlist doesn't seem to exist.")

        query.strip('<>')
        if not URL_REG.match(query):
            query = f'ytsearch:{query}'
        
        tracks = await self.bot.wavelink.get_tracks(query)
        
        if not tracks:
            return await ctx.reply(f"{self.bot.emojis_dict('redTick')} | The provided song was invalid. Try again with a different URL.")
        
        if isinstance(tracks, wavelink.TrackPlaylist):
            return await ctx.reply(f"{self.bot.emojis_dict('redTick')} | You can not add a playlist to a playlist...")
        else:
            track = Track(tracks[0].id, tracks[0].info, requester=ctx.author)
            query = """
                    INSERT INTO playlist_songs
                    VALUES (?, ?, ?, ?)
                    """
            await self.bot.db.execute(query, (playlist_id, track.title, track.uri, await self.new_song_id()))
            await ctx.reply(f"{self.bot.plus} | Added the song **{track.title}** to playlist with `ID {playlist_id}`.\nSong url: <{track.uri}>")
        
    
    @playlist.command(name="removesong", aliases=["rmsong", "rmsongs"], usage="<playlist ID> <song ID/song IDs>")
    async def _playlist_removesong(self, ctx, playlist_id:int, *songs):
        if not songs:
            raise commands.BadArgument(f"{self.bot.emojis_dict('redTick')} | Please supply a song id or a list of song ID's seperated by spaces.")
        if check := await self.is_playlistOwner(ctx.author.id, playlist_id) is False:
            return await ctx.reply(f"{self.bot.emojis_dict('redTick')} | You do not own this playlist.")
        elif check is None:
            return await ctx.reply(f"{self.bot.emojis_dict('redTick')} | This playlist doesn't seem to exist.")
        
        playlist = await get_playlist(self.bot.db, playlist_id)

        if not playlist:
            return await ctx.reply(f"{self.bot.emojis_dict('redTick')} | No playlist data was found with `ID {playlist_id}` (Empty or does not exist)")
        
        affected_rows = 0
        fails = []
        for song_id in songs:
            try:
                res = await playlist.remove_song(self.bot.db, int(song_id))
            except ValueError:
                raise commands.BadArgument(f"{self.bot.emojis_dict('redTick')} | `{song_id}` is not a valid ID.")
            if res is None:
                fails.append(song_id)
            else:
                affected_rows += res

        if fails:
            await ctx.reply(f"{self.bot.emojis_dict('redTick')} | The song(s) with `ID {', '.join(fails)}` does not belong to the playlist you supplied. Deleted **{affected_rows}** songs.")
        else:
            await ctx.reply(f"{self.bot.minus} | Deleted **{affected_rows}** songs in total.")
    
    @playlist.command(name="play", usage="<playlist ID>")
    async def _playlist_play(self, ctx, playlist_id: int):
        if (check := await self.is_playlistOwner(ctx.author.id, playlist_id)) is False:
            return await ctx.reply(f"{self.bot.emojis_dict('redTick')} | You do not own this playlist.")
        elif check is None:
            return await ctx.reply(f"{self.bot.emojis_dict('redTick')} | This playlist doesn't seem to exist.")
        
        player = self.bot.get_cog("Music").get_player(ctx)

        if not player.is_connected:
            await ctx.invoke(self.bot.get_cog("Music")._connect, invoked_from=ctx.command)
        
        playlist = await get_playlist(self.bot.db, playlist_id)
        await playlist.play(ctx, self.bot.wavelink, self.bot.get_cog("Music").get_player(ctx), requester=ctx.author, songs=playlist.length)


def setup(bot):
    bot.add_cog(Playlists(bot), category="Music")
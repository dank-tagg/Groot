import re
import discord

from discord.ext import menus
from utils.useful import Embed

class PlaylistSource(menus.ListPageSource):
    def __init__(self, data, playlist):
        super().__init__(data, per_page=10)
        self.playlist = playlist

    async def format_page(self, menu, entries):
        em = Embed(
            description=f"\🎶 Playlist `{self.playlist.name}` with `{self.playlist.length}` songs\n"+"\n".join(entries)
        )
        em.set_footer(text=f"Viewing page {menu.current_page + 1}/{self.get_max_pages()}")
        return em

class QueueSource(menus.ListPageSource):
    def __init__(self, data, player):
        super().__init__(data, per_page=10)
        self.player = player

    async def format_page(self, menu, entries):
        em = Embed(
            description=f"**Currently playing:**\n **1.** [{self.player.current.title}]({self.player.current.uri})\nRequested by {self.player.current.requester.mention}\n\n"+
                        f"**Next up [{self.player.queue.qsize()}]: **\n" +
                         "\n".join(entries)
        )
        em.set_footer(text=f"Page {menu.current_page + 1} of {self.get_max_pages()} | Looping track: {'❌' if not self.player.looping else '✅' }")
        return em

class UrbanSource(menus.ListPageSource):
    BRACKETED = re.compile(r'(\[(.+?)\])')

    def __init__(self, data):
        super().__init__(data, per_page=1)

    def cleanup_definition(self, definition, *, regex=BRACKETED):
        def repl(m):
            word = m.group(2)
            return f'[{word}](http://{word.replace(" ", "-")}.urbanup.com)'

        ret = regex.sub(repl, definition)
        if len(ret) >= 2048:
            return ret[0:2000] + ' [...]'
        return ret

    async def format_page(self, menu, entries):
        definition = self.cleanup_definition(entries['definition'])

        permalink = entries['permalink']
        thumbs_up = entries['thumbs_up']
        author = entries['author']
        example = self.cleanup_definition(entries['example'])

        em = Embed(
            title=f"📚 Definition of {entries['word']}",
            url=permalink,
            description=f'**Definition:**\n{definition}\n\n**Examples:**\n{example}'
        )

        em.set_footer(text=f"👍 {thumbs_up} • 👤 {author} • Page {menu.current_page + 1}/{self.get_max_pages()}")

        try:
            date = discord.utils.parse_time(entries['written_on'][0:-1])
        except (ValueError, KeyError):
            pass
        else:
            em.timestamp = date

        return em
import re

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
    def __init__(self, data):
        super().__init__(data, per_page=1)
    
    async def format_page(self, menu, entries):
        definition = entries['definition']
        permalink = entries['permalink']
        thumbs_up = entries['thumbs_up']
        author = entries['author']
        example = entries['example']

        em = Embed(
            title=f"📚 Definition of {entries['word']}",
            url=permalink,
            description=f'**Definition:**\n{definition}\n\n**Examples:**\n{example}'
        )
        
        hyperlinks = re.findall(r'((?<=\[)[^\]]+(?=\]))', em.description)

        for link in hyperlinks:
            em.description = em.description.replace(link, f'[{link}](http://{link.lower().replace(" ", "-")}.urbanup.com)')
        
        em.set_footer(text=f"👍 {thumbs_up} • 👤 {author} • Page {menu.current_page + 1}/{self.get_max_pages()}")
        return em
from discord.ext import menus
from utils.useful import Embed, get_title

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
            description=f"**Currently playing:**\n **1.** [{get_title(self.player.current, 35)}]({self.player.current.uri})\nRequested by {self.player.current.requester.mention}\n\n"+
                        f"**Next up [{self.player.queue.qsize()}]: **\n" + 
                         "\n".join(entries)
        )
        em.set_footer(text=f"Page {menu.current_page + 1} of {self.get_max_pages()} | Looping track: {'❌' if not self.player.looping else '✅' }")
        return em


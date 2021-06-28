import typing
if typing.TYPE_CHECKING:
    from utils._type import *

import aiohttp

class Client:
    def __init__(self, bot: GrootBot, token):
        self.auth = {"Authorization": token}
        self.bot = bot
        self.api = "https://discordbotlist.com/api/v1"

    async def post_stats(self):
        url = f"{self.api}/bots/{self.bot.user.id}/stats"
        to_post = {"guilds": len(self.bot.guilds), "users": len(self.bot.users)}
        res = await self.bot.session.post(url, json=to_post, headers=self.auth)

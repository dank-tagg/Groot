<<<<<<< HEAD
from discord.ext import commands
from typing import Union

class CacheManager:

    def __init__(self, bot: Union[commands.Bot, commands.AutoShardedBot]) -> None:
        self.bot = bot
        self._cache = {}

    def key_exists(self, key, value) -> None:
        self._cache[key] = value

    def __setitem__(self, key, value) -> None:
        if self._cache.get(key):
            return self.key_exists(key, value)

        self._cache[key] = value

    def __getitem__(self, key):
        return self._cache[key]

    def __delitem__(self, key) -> None:
        del self._cache[key]

    def get(self, key):
        return self._cache.get(key)
=======
from discord.ext import commands
from typing import Union

class CacheManager:

    def __init__(self, bot: Union[commands.Bot, commands.AutoShardedBot]) -> None:
        self.bot = bot
        self._cache = {}

    def key_exists(self, key, value) -> None:
        self._cache[key] = value

    def __setitem__(self, key, value) -> None:
        if self._cache.get(key):
            return self.key_exists(key, value)

        self._cache[key] = value

    def __getitem__(self, key):
        return self._cache[key]

    def __delitem__(self, key) -> None:
        del self._cache[key]

    def get(self, key):
        return self._cache.get(key)
>>>>>>> 49d80156d5629766d96cea370b74cb9323e1fdcc

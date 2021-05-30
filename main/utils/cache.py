from discord.ext import commands
from typing import Union, Optional
from utils.useful import fuzzy
import numpy as np

class CacheManager(dict):
    def __init__(self, bot: Union[commands.Bot, commands.AutoShardedBot]) -> None:
        self.bot = bot
        self.log = []


    @property
    def length(self):
        return len(self)
    
    @staticmethod
    def iterate_all(iterable, returned="key"):
        
        """Returns an iterator that returns all keys or values
        of a (nested) iterable.
        
        Arguments:
            - iterable: <list> or <dictionary>
            - returned: <string> "key" or "value"
            
        Returns:
            - <iterator>
        """
    
        if isinstance(iterable, dict):
            for key, value in iterable.items():
                if returned == "key":
                    yield key
                elif returned == "value":
                    if not (isinstance(value, dict) or isinstance(value, list)):
                        yield value
                else:
                    raise ValueError("'returned' keyword only accepts 'key' or 'value'.")
                for ret in iterate_all(value, returned=returned):
                    yield ret
        elif isinstance(iterable, list):
            for el in iterable:
                for ret in iterate_all(el, returned=returned):
                    yield ret

    def search(self):
        whole = self.iterate_all(self)
        return self

cache = CacheManager(bot)
cache['hello'] = 1
cache.search()
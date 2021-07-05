import discord

from itertools import chain
from discord.ext.commands import Cog

__all__ = ('Category')


class Category:
    __slots__ = ('name', '__cogs')
    def __init__(self, name):
        self.name = name
        self.__cogs = {}

    def add_cog(self, cog: Cog, override: bool = False) -> None:
        
        if not isinstance(cog, Cog):
            raise TypeError('cog must derive from Cog not ' + cog.__class__.__name__)

        cog_name = cog.__cog_name__
        existing = self.__cogs.get(cog_name)

        if existing is not None:
            if not override:
                raise discord.ClientException(f'Cog named {cog_name!r} is already loaded in this category')
            self.remove_cog(cog_name)

        self.__cogs[cog_name] = cog

    def remove_cog(self, name):
        cog = self.__cogs.pop(name, None)
        if not cog:
            raise discord.ClientException(f'Cog {name} is not in this category.')
        return cog
    
    def get_commands(self):
        commands = []
        for cog in self.__cogs.values():
            commands.append([c for c in cog.__cog_commands__ if c.parent is None])
        return list(chain(*commands))
    

    @property
    def qualified_name(self):
        return self.name
    
    def walk_commands(self):
        from discord.ext.commands.core import GroupMixin
        for cog in self.__cogs.values():
            for command in cog.__cog_commands__:
                if command.parent is None:
                    yield command
                    if isinstance(command, GroupMixin):
                        yield from command.walk_commands()
    


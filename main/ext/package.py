from discord.ext import commands
from inspect import getmembers

class Package:
    def __init__(self, cog: commands.Cog, *, name=None, description=None):
        self.name = name or self.__class__.__name__
        self.description = description or self.__doc__
        self.cog = cog
        self.bot = cog.bot

        self.__shard_commands__ = (
            command for _, command in getmembers(self)
            if isinstance(command, commands.Command)
        )

        self.__shard_listeners__ = ()


    def _inject(self):
        for index, command in enumerate(self.__shard_commands__):
            command.cog = self
            if command.parent is None:
                try:
                    self.bot.add_command(command)
                except Exception as e:
                    for to_undo in self.__shard_commands__[:index]:
                        if to_undo.parent is None:
                            self.bot.remove_command(to_undo.name)
                    raise e

        for name, method_name in self.__shard_listeners__:
            self.bot.add_listener(getattr(self, method_name), name)

        return self

    def _eject(self):

        try:
            for command in self.__cog_commands__:
                if command.parent is None:
                    self.bot.remove_command(command.name)

            for _, method_name in self.__cog_listeners__:
                self.bot.remove_listener(getattr(self, method_name))

        finally:
            try:
                self.shard_unload()
            except Exception:
                pass


from discord.ext import commands
import inspect

class Shard:
    def __init__(self, cog: commands.Cog, *, name=None, description=None):
        self.name = name or self.__class__.__name__
        self.description = description or self.__doc__
        self.cog = cog
        self.bot = cog.bot

        self.__shard_commands__ = (
            command for _, command in inspect.getmembers(self)
            if isinstance(command, commands.Command)
        )

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

        for listener in inspect.getmembers(self):
            if hasattr(listener, "__cog_listener__") and listener.__cog_listener__ is True:
                setattr(self.cog, listener.__name__, listener)
                self.cog.__cog_listeners__.append((listener.__cog_listener_names__[0], listener.__name__))
                self.bot.add_listener(listener, listener.__cog_listener_names__[0])

        return self

    def _eject(self):

        try:
            for command in self.__shard_commands__:
                if command.parent is None:
                    self.bot.remove_command(command.name)

            for listener in self.__shard_listeners__:
                for _, method_name in self.__cog_listeners__:
                    self.bot.remove_listener(getattr(self, method_name))

        finally:
            try:
                self.shard_unload()
            except Exception:
                pass


import importlib
import inspect
import sys

from discord.ext import commands


class Shard:
    """
    A class to sort commands in but listeners aren't supported here.
    """
    def __init__(self, cog: commands.Cog, *, name=None, description=None):
        self.name = name or self.__class__.__name__
        self.description = description or self.__doc__
        self.cog = cog

        self.__shard_commands__ = [
            command for _, command in inspect.getmembers(self)
            if isinstance(command, commands.Command)
        ]

        self.__shard_listeners__ = []

    def _inject(self):
        for index, command in enumerate(self.__shard_commands__):
            if command.parent is None:
                command.cog = self.cog
                try:
                    self.bot.add_command(command)
                except Exception as e:
                    for to_undo in self.__shard_commands__[:index]:
                        if to_undo.parent is None:
                            self.bot.remove_command(command.name)
                    raise e

        for _, func in inspect.getmembers(self):
            if hasattr(func, '__cog_listener__') and func.__cog_listener__ is True:

                setattr(self.cog, func.__name__, func)
                self.cog.__cog_listeners__.append((func.__cog_listener_names__[0], func.__name__))
                self.__shard_listeners__.append((func.__cog_listener_names__[0], func.__name__))

        return self

    def _eject(self):
        try:
            for command in self.__shard_commands__:
                if command.parent is None:
                    self.bot.remove_command(command.name)

            for _, method_name in self.__shard_listeners__:
                self.bot.remove_listener(getattr(self, method_name))


        finally:
            try:
                self.shard_unload()
            except AttributeError:
                pass

def override_discord():

    def add_command(self: commands.Cog, command: commands.Command):
        self.__cog_commands__ += (command, )

    def remove_command(self: commands.Cog, command: commands.Command):
        self.__cog_commands__ = tuple([cmd for cmd in self.__cog_commands__ if cmd != command])
        command.cog = None
        self.bot.remove_command(command)

    def load_shard(self: commands.Cog, shard_path: str):
        spec = importlib.util.find_spec(shard_path)
        if spec is None:
            raise commands.ExtensionNotLoaded(shard_path)
        lib = importlib.util.module_from_spec(spec)


        key = shard_path
        sys.modules[key] = lib

        try:
            spec.loader.exec_module(lib)
        except Exception as e:
            del sys.modules[key]
            raise commands.ExtensionFailed(key, e) from e

        try:
            setup = getattr(lib, 'setup')
        except AttributeError:
            del sys.modules[key]
            raise commands.NoEntryPointError(key)

        try:
            setup(self)
        except Exception as e:
            del sys.modules[key]
            raise commands.ExtensionFailed(key, e) from e


    def add_shard(self: commands.Cog, shard: Shard):
        shard._inject()
        print(list(map(lambda c: c.name, shard.__shard_commands__)))
        cog_shards = getattr(self, '__shards', {})
        cog_shards[shard.name] = shard
        self.__shards = cog_shards

    def remove_shard(self: commands.Cog, shard: Shard):
        shard._eject()
        del self.__shards[shard.name]


    commands.Cog.add_command = add_command
    commands.Cog.remove_command = remove_command
    commands.Cog.load_shard = load_shard
    commands.Cog.remove_shard = remove_shard
    commands.Shard = Shard
    commands.Cog.add_shard = add_shard

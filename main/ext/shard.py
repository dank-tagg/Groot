import inspect
import sys
import importlib
import discord

from discord.ext import commands
from discord.ext.commands.converter import get_converter, run_converters

class Shard:
    """
    A class to sort commands in
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
            command.cog = self.cog
            command.shard = self
            if command.parent is None:
                try:
                    self.cog.__cog_commands__ += (command, )
                except Exception as e:
                    for to_undo in self.__shard_commands__[:index]:
                        if to_undo.parent is None:
                            self.bot.remove_command(to_undo.name)
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


# Command classes

class ShardCommand(commands.Command):
    def __init__(self, func, **kwargs):
        self.shard = None
        super().__init__(func, **kwargs)

    async def _parse_arguments(self, ctx):
        ctx.args = [ctx] if self.shard is None and self.cog is None else [self.shard or self.cog, ctx]
        ctx.kwargs = {}
        args = ctx.args
        kwargs = ctx.kwargs

        view = ctx.view
        iterator = iter(self.params.items())

        if self.cog is not None:
            # we have 'self' as the first parameter so just advance
            # the iterator and resume parsing
            try:
                next(iterator)
            except StopIteration:
                raise discord.ClientException(f'Callback for {self.name} command is missing "self" parameter.')

        # next we have the 'ctx' as the next parameter
        try:
            next(iterator)
        except StopIteration:
            raise discord.ClientException(f'Callback for {self.name} command is missing "ctx" parameter.')

        for name, param in iterator:
            ctx.current_parameter = param
            if param.kind in (param.POSITIONAL_OR_KEYWORD, param.POSITIONAL_ONLY):
                transformed = await self.transform(ctx, param)
                args.append(transformed)
            elif param.kind == param.KEYWORD_ONLY:
                # kwarg only param denotes "consume rest" semantics
                if self.rest_is_raw:
                    converter = get_converter(param)
                    argument = view.read_rest()
                    kwargs[name] = await run_converters(ctx, converter, argument, param)
                else:
                    kwargs[name] = await self.transform(ctx, param)
                break
            elif param.kind == param.VAR_POSITIONAL:
                if view.eof and self.require_var_positional:
                    raise commands.MissingRequiredArgument(param)
                while not view.eof:
                    try:
                        transformed = await self.transform(ctx, param)
                        args.append(transformed)
                    except RuntimeError:
                        break

        if not self.ignore_extra and not view.eof:
            raise commands.TooManyArguments('Too many arguments passed to ' + self.qualified_name)

class ShardGroupMixin:
    def __init__(self, *args, **kwargs):
        case_insensitive = kwargs.get('case_insensitive', False)
        self.all_commands = commands.core._CaseInsensitiveDict() if case_insensitive else {}
        self.case_insensitive = case_insensitive
        super().__init__(*args, **kwargs)

    @property
    def commands(self):
        """Set[:class:`.Command`]: A unique set of commands without aliases that are registered."""
        return set(self.all_commands.values())

    def recursively_remove_all_commands(self):
        for command in self.all_commands.copy().values():
            if isinstance(command, ShardGroupMixin):
                command.recursively_remove_all_commands()
            self.remove_command(command.name)

    def add_command(self, command):

        if not isinstance(command, ShardCommand):
            raise TypeError('The command passed must be a subclass of Command')

        if isinstance(self, ShardCommand):
            command.parent = self

        if command.name in self.all_commands:
            raise commands.CommandRegistrationError(command.name)

        self.all_commands[command.name] = command
        for alias in command.aliases:
            if alias in self.all_commands:
                self.remove_command(command.name)
                raise commands.CommandRegistrationError(alias, alias_conflict=True)
            self.all_commands[alias] = command

    def remove_command(self, name):
        command = self.all_commands.pop(name, None)

        # does not exist
        if command is None:
            return None

        if name in command.aliases:
            # we're removing an alias so we don't want to remove the rest
            return command

        # we're not removing the alias so let's delete the rest of them.
        for alias in command.aliases:
            cmd = self.all_commands.pop(alias, None)
            # in the case of a CommandRegistrationError, an alias might conflict
            # with an already existing command. If this is the case, we want to
            # make sure the pre-existing command is not removed.
            if cmd not in (None, command):
                self.all_commands[alias] = cmd
        return command

    def walk_commands(self):
        for command in self.commands:
            yield command
            if isinstance(command, ShardGroupMixin):
                yield from command.walk_commands()

    def get_command(self, name):
        # fast path, no space in name.
        if ' ' not in name:
            return self.all_commands.get(name)

        names = name.split()
        if not names:
            return None
        obj = self.all_commands.get(names[0])
        print(obj)
        if not isinstance(obj, ShardGroupMixin):
            return obj

        for name in names[1:]:
            try:
                obj = obj.all_commands[name]
            except (AttributeError, KeyError):
                return None

        return obj

    def command(self, *args, **kwargs):
        """A shortcut decorator that invokes :func:`.command` and adds it to
        the internal command list via :meth:`~.GroupMixin.add_command`.

        Returns
        --------
        Callable[..., :class:`Command`]
            A decorator that converts the provided method into a Command, adds it to the bot, then returns it.
        """
        def decorator(func):
            kwargs.setdefault('parent', self)
            result = commands.command(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator

    def group(self, *args, **kwargs):
        """A shortcut decorator that invokes :func:`.group` and adds it to
        the internal command list via :meth:`~.GroupMixin.add_command`.

        Returns
        --------
        Callable[..., :class:`Group`]
            A decorator that converts the provided method into a Group, adds it to the bot, then returns it.
        """
        def decorator(func):
            kwargs.setdefault('parent', self)
            result = commands.group(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator

class ShardGroup(ShardGroupMixin, ShardCommand):
    def __init__(self, *args, **attrs):
        self.invoke_without_command = attrs.pop('invoke_without_command', False)
        super().__init__(*args, **attrs)

    def copy(self):
        """Creates a copy of this :class:`Group`.

        Returns
        --------
        :class:`Group`
            A new instance of this group.
        """
        ret = super().copy()
        for cmd in self.commands:
            ret.add_command(cmd.copy())
        return ret

    async def invoke(self, ctx):
        ctx.invoked_subcommand = None
        ctx.subcommand_passed = None
        early_invoke = not self.invoke_without_command
        if early_invoke:
            await self.prepare(ctx)

        view = ctx.view
        previous = view.index
        view.skip_ws()
        trigger = view.get_word()

        if trigger:
            ctx.subcommand_passed = trigger
            ctx.invoked_subcommand = self.all_commands.get(trigger, None)

        if early_invoke:
            injected = commands.core.hooked_wrapped_callback(self, ctx, self.callback)
            await injected(*ctx.args, **ctx.kwargs)

        ctx.invoked_parents.append(ctx.invoked_with)
        if trigger and ctx.invoked_subcommand:
            ctx.invoked_with = trigger
            print(type(ctx.invoked_subcommand))
            await ctx.invoked_subcommand.invoke(ctx)
        elif not early_invoke:
            # undo the trigger parsing
            view.index = previous
            view.previous = previous
            await super().invoke(ctx)

    async def reinvoke(self, ctx, *, call_hooks=False):
        ctx.invoked_subcommand = None
        early_invoke = not self.invoke_without_command
        if early_invoke:
            ctx.command = self
            await self._parse_arguments(ctx)

            if call_hooks:
                await self.call_before_hooks(ctx)

        view = ctx.view
        previous = view.index
        view.skip_ws()
        trigger = view.get_word()

        if trigger:
            ctx.subcommand_passed = trigger
            ctx.invoked_subcommand = self.all_commands.get(trigger, None)

        if early_invoke:
            try:
                await self.callback(*ctx.args, **ctx.kwargs)
            except:
                ctx.command_failed = True
                raise
            finally:
                if call_hooks:
                    await self.call_after_hooks(ctx)

        ctx.invoked_parents.append(ctx.invoked_with)

        if trigger and ctx.invoked_subcommand:
            ctx.invoked_with = trigger
            await ctx.invoked_subcommand.reinvoke(ctx, call_hooks=call_hooks)
        elif not early_invoke:
            # undo the trigger parsing
            view.index = previous
            view.previous = previous
            await super().reinvoke(ctx, call_hooks=call_hooks)



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
    cog_shards = getattr(self, '__shards', {})
    cog_shards[shard.name] = shard
    self.__shards = cog_shards

def remove_shard(self: commands.Cog, shard: Shard):
    shard._eject()
    del self.__shards[shard.name]

def shard_command(name=None, cls=ShardCommand, **attrs):
    def decorator(func):
        if isinstance(func, commands.Command):
            raise TypeError('Callback is already a command.')
        return cls(func, name=name, **attrs)

    return decorator

def shard_group(name=None, **attrs):
    attrs.setdefault('cls', ShardGroup)
    return commands.command(name=name, **attrs)

def override_discord():

    commands.command = shard_command
    commands.group = shard_group
    commands.Cog.load_shard = load_shard
    commands.Cog.remove_shard = remove_shard
    commands.Shard = Shard
    commands.Cog.add_shard = add_shard
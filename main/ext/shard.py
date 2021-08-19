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

def override_discord():

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

    class ShardCommand(commands.Command):
        def __init__(self, func, **kwargs):
            self.shard = None
            super().__init__(func, **kwargs)

        async def _parse_arguments(self, ctx):
            ctx.args = [ctx] if self.shard is None and self.cog is None else [self.shard or self.cog, ctx]
            print(ctx.args)
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

    class ShardGroup(commands.GroupMixin, ShardCommand):
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

    def shard_command(name=None, cls=ShardCommand, **attrs):
        def decorator(func):
            if isinstance(func, commands.Command):
                raise TypeError('Callback is already a command.')
            return cls(func, name=name, **attrs)

        return decorator

    def shard_group(name=None, **attrs):
        attrs.setdefault('cls', ShardGroup)
        return commands.command(name=name, **attrs)

    commands.command = shard_command
    commands.group = shard_group
    commands.Cog.load_shard = load_shard
    commands.Cog.remove_shard = remove_shard
    commands.Shard = Shard
    commands.Cog.add_shard = add_shard
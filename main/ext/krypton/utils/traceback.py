import discord
import traceback
from discord.ext import commands

async def send_traceback(destination: discord.abc.Messageable, verbosity: int, *exc_info):
    """
    Sends a traceback of an exception to a destination.
    Used when REPL fails for any reason.
    :param destination: Where to send this information to
    :param verbosity: How far back this traceback should go. 0 shows just the last stack.
    :param exc_info: Information about this exception, from sys.exc_info or similar.
    :return: The last message sent
    """

    etype, value, trace = exc_info

    traceback_content = "".join(traceback.format_exception(etype, value, trace, verbosity)).replace("``", "`\u200b`")

    paginator = commands.Paginator(prefix='```py')
    for line in traceback_content.split('\n'):
        paginator.add_line(line)

    message = None

    for page in paginator.pages:
        message = await destination.send(page)

    return message

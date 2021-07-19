

from discord.ext import commands
from .utils.codeblocks import CodeConvert


from .KryFeatures.root import Root
from .KryFeatures.management import ManagementFeature
from .KryFeatures.python import PythonFeature
from .KryFeatures.invocation import InvocationFeature
__all__ = (
    'Krypton',
    'setup'
)

AllKryFeatures = (Root, ManagementFeature, PythonFeature, InvocationFeature)

class Krypton(*AllKryFeatures):
    """
    Frontend class that mixes in to form the Krypton cog
    """



def setup(bot: commands.Bot):
    bot.add_cog(Krypton(bot=bot))
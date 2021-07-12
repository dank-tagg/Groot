[![Discord Bots](https://top.gg/api/widget/status/812395879146717214.svg?)](https://top.gg/bot/812395879146717214)
[![Discord Bots](https://top.gg/api/widget/servers/812395879146717214.svg?)](https://top.gg/bot/812395879146717214)
[![Discord Bots](https://top.gg/api/widget/owner/812395879146717214.svg)](https://top.gg/bot/812395879146717214)

# Groot
Groot is a simple yet feature-rich discord bot.<br>
Featuring over 150 commands, the best discord bot you could ask for!<br>
Made by [`dank tagg#6017`](https://discord.com/users/396805720353275924) with 💖

## List of contents
- [Usage](#usage)
- [Features](#features)
- [How do I contribute?](#how-do-i-contribute)
  - [Requirements](#requirements-to-contribute)
- [Contact me](#contact-me)
- [Links](#links)
- [Licensing Information](#licensing-information)


## Usage
If you anyhow want to _copy_ my code, feel free to. Be sure to read the [license](#licensing-information) though.<br>
You can find me at the [support server](https://discord.gg/nUUJPgemFE) for Groot, or just shoot me a [DM](https://discord.com/users/396805720353275924).<br>

## Features
```css
Fun               -> Want to have some fun? 😉
Utilities         -> Handy utilities that make your life easier
Information       -> Information about the bot
Moderation        -> Powerful moderation commands
Music             -> Play music! Has playlist functionalities
Configuration     -> Configure your own settings
Image             -> Image manipulation commands
Support           -> Support commands to report bugs/suggest features
```

## How do I contribute?
If you somehow have interest in contributing, please start an issue.\
State in it the code and a short description.\
It should look like the following:

```py
# The code you want to add:
import discord
from discord.ext import commands

class aNewCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="Thank", aliases=["You"])
    async def hello(self, ctx):
        await ctx.send(f"Hello {ctx.author.mention}")
    
def setup(bot):
    bot.add_cog(aNewCog(bot))

# A short description
'''
This code adds a new command that sends 'Hello {ctx.author.mention}' when invoked.
My discord is anUser#6969, you can ask me about it there.
'''
```
**Note that this is not required. It can also be pseudocode, and a small explaination.**


For more information, contact me on discord.<br>
If you want to contribute anything big, please DM me.<br>
I would be more than happy to talk to you.



### Requirements to contribute
- [ ] It must be written in Python
- [ ] It must be able to run on `python 3.9.5` and `discord.py 1.7.3`



## Contact me
**DISCORD:**<br>
[dank tagg#6017](https://discord.com/users/396805720353275924) or [support server](https://discord.gg/nUUJPgemFE)\
**EMAIL:**<br>
grootdiscordbot@gmail.com

## Links
- [Vote](https://top.gg/bot/812395879146717214/vote)
- [Source](https://github.com/dank-tagg/Groot)
- [Website](https://grootdiscordbot.xyz/)


## Licensing Information
Groot is licensed under the [Mozilla Public License 2.0](https://github.com/dank-tagg/Groot/blob/main/LICENSE)

Permissions of this weak copyleft license are conditioned on making available source code of licensed files and modifications of those files under the same license (or in certain cases, one of the GNU licenses). Copyright and license notices must be preserved. Contributors provide an express grant of patent rights. However, a larger work using the licensed work may be distributed under different terms and without source code for files added in the larger work.

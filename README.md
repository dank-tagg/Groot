[![Discord Bots](https://top.gg/api/widget/status/812395879146717214.svg?)](https://top.gg/bot/812395879146717214)
[![Discord Bots](https://top.gg/api/widget/servers/812395879146717214.svg?)](https://top.gg/bot/812395879146717214)
[![Discord Bots](https://top.gg/api/widget/owner/812395879146717214.svg)](https://top.gg/bot/812395879146717214)

# Groot
A multipurpose discord bot, for educational and experimental purposes.<br>
Made by `dank tagg#6017`

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
You can find me at the [support server](https://discord.gg/ANbxZmqyK5) for Groot, or just shoot me a DM.<br>

## Features
```css
Fun               -> Funny commands
Utilities         -> Handy utilities
Information       -> Information about the bot
Moderation        -> Powerful moderation commands
Admin             -> Admin commands and not available for the public
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
- [ ] It must be able to run on `python 3.9.4` and `discord.py 1.7.1`



## Contact me
**DISCORD:**<br>
dank tagg#6017 _or_ [support server](https://discord.gg/ANbxZmqyK5)\
**EMAIL:**<br>
grootdiscordbot@gmail.com

## Links
- [Vote](https://top.gg/bot/812395879146717214/vote)
- [Source](https://github.com/dank-tagg/Groot)
- [Website](https://dank-tagg.github.io/website/)


## Licensing Information
```
MIT License

Copyright (c) 2021 dank tagg

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

import discord

class Krybed(discord.Embed):
    def __init__(self, color=0x5EAEEB, fields=(), field_inline=False, **kwargs):
        super().__init__(color=color, **kwargs)
        for n, v in fields:
            self.add_field(name=n, value=v, inline=field_inline)

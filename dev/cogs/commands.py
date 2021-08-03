from discord.ext import commands
import discord
import random
from typing import List
import time
import asyncio

class PosixLikeFlags(commands.FlagConverter, prefix='--', delimiter=' '):
    member: discord.Member


class Timer:
    __slots__ = ("start_time", "end_time")

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop()

    def start(self):
        self.start_time = time.perf_counter()

    def stop(self):
        self.end_time = time.perf_counter()

    @property
    def total_time(self):
        return self.end_time - self.start_time

class Viewer(discord.ui.View):
    def __init__(self, embed):
        super().__init__(timeout=None)
        self.em = embed

    @discord.ui.button(label='⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ACCEPT⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀', style=discord.ButtonStyle.green)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message('https://i.giphy.com/media/Ju7l5y9osyymQ/giphy.webp', ephemeral=True)
        self.em.description = "Hmm, it seems someone \nalready claimed this gift."
        button.style = discord.ButtonStyle.grey
        button.disabled = True
        button.label = "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀Claimed⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"

        await interaction.message.edit(embed=self.em, view=self)

class buttonforrickroll(discord.ui.Button):
    def __init__(self):
        super().__init__(label="\u200b", style=discord.ButtonStyle.grey)

    async def callback(self, interaction):
        assert self.view is not None
        view = self.view
        self.style = discord.ButtonStyle.green
        self.disabled = True
        await interaction.response.edit_message(view=view)

class TicTacToeButton(discord.ui.Button['TicTacToe']):
    def __init__(self, x: int, y: int):
        # A label is required, but we don't need one so a zero-width space is used
        # The row parameter tells the View which row to place the button under.
        # A View can only contain up to 5 rows -- each row can only have 5 buttons.
        # Since a Tic Tac Toe grid is 3x3 that means we have 3 rows and 3 columns.
        super().__init__(style=discord.ButtonStyle.secondary, label='\u200b', row=y)
        self.x = x
        self.y = y

    # This function is called whenever this particular button is pressed
    # This is part of the "meat" of the game logic
    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: TicTacToe = self.view
        state = view.board[self.y][self.x]
        if state in (view.X, view.O):
            return

        if view.current_player == view.X:
            self.style = discord.ButtonStyle.danger
            self.label = 'X'
            self.disabled = True
            view.board[self.y][self.x] = view.X
            view.current_player = view.O
            content = "It is now O's turn"
        else:
            self.style = discord.ButtonStyle.success
            self.label = 'O'
            self.disabled = True
            view.board[self.y][self.x] = view.O
            view.current_player = view.X
            content = "It is now X's turn"

        winner = view.check_board_winner()
        if winner is not None:
            if winner == view.X:
                content = 'X won!'
            elif winner == view.O:
                content = 'O won!'
            else:
                content = "It's a tie!"

            for child in view.children:
                child.disabled = True

            view.stop()

        await interaction.response.edit_message(content=content, view=view)


# This is our actual board View
class TicTacToe(discord.ui.View):
    # This tells the IDE or linter that all our children will be TicTacToeButtons
    # This is not required
    children: List[TicTacToeButton]
    X = -1
    O = 1
    Tie = 2

    def __init__(self):
        super().__init__()
        self.current_player = self.X
        self.board = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]

        # Our board is made up of 3 by 3 TicTacToeButtons
        # The TicTacToeButton maintains the callbacks and helps steer
        # the actual game.
        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y))

    # This method checks for the board winner -- it is used by the TicTacToeButton
    def check_board_winner(self):
        for across in self.board:
            value = sum(across)
            if value == 3:
                return self.O
            elif value == -3:
                return self.X

        # Check vertical
        for line in range(3):
            value = self.board[0][line] + self.board[1][line] + self.board[2][line]
            if value == 3:
                return self.O
            elif value == -3:
                return self.X

        # Check diagonals
        diag = self.board[0][2] + self.board[1][1] + self.board[2][0]
        if diag == 3:
            return self.O
        elif diag == -3:
            return self.X

        diag = self.board[0][0] + self.board[1][1] + self.board[2][2]
        if diag == 3:
            return self.O
        elif diag == -3:
            return self.X

        # If we're here, we need to check if a tie was made
        if all(i != 0 for row in self.board for i in row):
            return self.Tie

        return None

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def reload(self, ctx):
        self.bot.reload_extension("commands")
        await ctx.send("yo done. im cool.")

    @commands.command()
    async def nitro(self, ctx):

        em = discord.Embed(title="A WILD GIFT APPEARS!", color=0x2F3136).set_thumbnail(url="https://i.imgur.com/w9aiD6F.png")
        em.description = "**Nitro**\nExpires in 48 hours."
        view = Viewer(em)
        await ctx.send(embed=em, view=view)

    @commands.command()
    async def test(self, ctx):
        await ctx.send("Only you can see it nab", ephemeral=True)

    @commands.command()
    async def ttt(self, ctx):
        await ctx.send('Tic Tac Toe: X goes first', view=TicTacToe())

    @commands.command()
    async def choose(self, ctx):
        options = [
            discord.SelectOption(label='Pineapple', value='Pineapple', description='The sweet tasting pineapple', emoji='🍍', default=False),
            discord.SelectOption(label='Eggplant', value='Eggplant', description='Suspicious', emoji='🍆', default=False),
            discord.SelectOption(label='Grapes', value='Grapes', description='Mhm, perfect for the summer', emoji='🍇', default=False),
            discord.SelectOption(label='Apples', value='Apples', description='An apple a day keeps Jotte away', emoji='🍎', default=False),
            discord.SelectOption(label='Banana', value='Banana', description='MMMM BAANAAAANAAA', emoji='🍌', default=False)
        ]
        class View(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)
                self.votes = {}

            @discord.ui.select(placeholder="Choose your favorite fruit", options=options)
            async def select(self, select, interaction):
                if interaction.user.name in (keys := list(self.votes.keys())):
                    return await interaction.response.send_message("You've already chosen.", ephemeral=True)
                self.votes[interaction.user.name] = interaction.data['values'][0]
                em = discord.Embed(title=f"What is your favorite fruit?")
                for k, v in self.votes.items():
                    em.add_field(name=str(k), value=v)
                await interaction.message.edit(embed=em)
        await ctx.send("What is your favorite fruit?", view = View())
    @commands.command(
        brief=(
            "Get the cookie! (If you mention a user, I will listen to you and the member that you mentioned.)"),
        aliases=["\U0001F36A", "vookir", "kookie"]
        )
    @commands.cooldown(5, 10, commands.BucketType.member)
    @commands.max_concurrency(2, commands.BucketType.channel)
    async def cookie(self, ctx):
        cookie_embed = discord.Embed(
            title="Get the cookie!",
            description="Get ready to grab the cookie!")
        cd_cookie = await ctx.send(embed=cookie_embed)
        await asyncio.sleep(5)
        await cd_cookie.edit(embed=cookie_embed)
        await asyncio.sleep(random.randint(1, 8))
        cookie_embed.title = "GO!"
        cookie_embed.description = "GET THE COOKIE NOW!"
        await cd_cookie.edit(embed=cookie_embed)
        await cd_cookie.add_reaction("\U0001F36A")

        def check(reaction, user):
            return (
                reaction.message.id == cd_cookie.id and
                str(reaction.emoji) in "\U0001F36A" and
                user != self.bot.user
            )

        try:
            with Timer() as reaction_time:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", check=check, timeout=10
                )
        except asyncio.TimeoutError:
            cookie_embed.title = "Game over!"
            cookie_embed.description = "Nobody got the cookie :("
            await cd_cookie.edit(embed=cookie_embed)
            await cd_cookie.remove_reaction("\U0001F36A", ctx.guild.me)
        else:
            if str(reaction.emoji) == "\U0001F36A":
                thing = reaction_time.total_time * 1000
                total_second = f"**{thing:.2f}ms**"
                if thing > 1000:
                    gettime = thing / 1000
                    total_second = f"**{gettime:.2f}s**"
                cookie_embed.title = "Nice!"
                cookie_embed.description = f"{user.mention} got the cookie in **{total_second}**"
                await cd_cookie.remove_reaction("\U0001F36A", ctx.guild.me)
                return await cd_cookie.edit(embed=cookie_embed)


    @commands.command(name='rps')
    async def _eee_(self, ctx, *, flags: PosixLikeFlags):
        await ctx.send(flags.member.name)

def setup(bot):
    bot.add_cog(Commands(bot))


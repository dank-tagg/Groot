from utils._type import *

import asyncio
import discord
import random

from discord.ext import commands
from utils.useful import Embed
from utils.chat_formatting import hyperlink as link
from itertools import chain

class SimonGame:
    def __init__(self, ctx: customContext):
        self.ctx = ctx
        self.bot = ctx.bot

        self.player = ctx.author
        self.answer = None
        self.tiles = ['🟥', '🟨', '🟩', '🟦']
        self.sequence = []
        self.answer = []

        self.message = None
    
    async def start(self):
        # Prepare
        self.sequence.append(random.choice(self.tiles))
        em = self.build_embed(1)
        msg = self.message = await self.ctx.send(embed=em)
        for tile in self.tiles:
            await msg.add_reaction(tile)
        
        # Start the game
        def check(reaction, user):
            return user == self.player and str(reaction) in self.tiles

        finished = False
        while not finished:
            await self.message.edit(embed=self.build_embed(2))
            self.answer = []
            for tile in self.sequence:
                try:
                    done, _ = await asyncio.wait(
                        [
                            self.bot.wait_for('reaction_remove', check=check, timeout=len(self.sequence) * 5),
                            self.bot.wait_for('reaction_add', check=check, timeout=len(self.sequence) * 5)
                        ],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    for future in _:
                        future.cancel()
                    reaction = done.pop().result()[0].emoji
                except asyncio.TimeoutError:
                    await self.message.edit(embed=self.build_embed(-1))
                    return
                self.answer.append(reaction)
            if self.answer != self.sequence:
                await self.message.edit(embed=self.build_embed(-2))
                finished = True
            else:
                await self.message.edit(embed=self.next(1))
                await asyncio.sleep(len(self.sequence) * 1)
    
    def next(self, res: int):
        self.sequence.append(random.choice(self.tiles))
        return self.build_embed(res)
    
    def build_embed(self, res: int) -> Embed:
        color = {
            1: 'invisible',
            2: 'invisible',
            -1: 'red',
            -2: 'red'
        }

        em = Embed(title=f"{self.ctx.author}'s Simon Game", color=self.bot.colors[color[res]])
        
        val = {
            1: 'Memorize this sequence: ' + ' '.join(self.sequence) + "\n\n **⚠️ Do not click now, it won't register**",
            2: "Now react with the correct emojis \n\n **⚠️ Click slowly otherwise it may not register**",
            -1: f'**Timeout!** Your score: {str(len(self.sequence) - 1)}',
            -2: f'Wrong sequence! Your score: {str(len(self.sequence) - 1)}\n\nCorrect sequence was {" ".join(self.sequence)}\nYour answer was {" ".join(self.answer)}'
        }

        em.description = val[res]
        em.set_footer(text=f'Current score: {len(self.sequence) - 1}')
        em.set_author(name=self.ctx.author, icon_url=self.ctx.author.avatar_url)
        return em

class TicTacToe:
    X = -1
    O = 1
    Tie = 2
    def __init__(self, ctx: customContext, x: discord.Member, o: discord.Member):
        self.ctx = ctx
        self.x = x
        self.o = o
        self.board = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0]
        ]

        self.rows = {'a': 0, 'b': 1, 'c': 2}
        self.icons = {0: '⬜', 1: '🅾️', -1: '❌'}

        self.players = {-1: self.x, 1: self.o}
        self.current_player = (self.x, self.X)

    async def start(self):
        fails = 0
        while fails < 3:
            await self.send_board()
            try:
                move = (await self.ctx.bot.wait_for('message', check=lambda m: m.author == self.current_player[0], timeout=15)).content
            except asyncio.TimeoutError:
                await self.ctx.send('❕ Woops. The game ended due to inactivity. Next time please be quicker to answer.')
                return
            
            if not move in [f'{x}{y}' for x in ['a', 'b', 'c'] for y in [1, 2, 3]]:
                await self.ctx.send(f'⚠️ That is not a valid move {self.current_player[0].mention}! Please enter a valid move again.')
                fails += 1
                continue
            
            if self.board[self.rows[move[0]]][int(move[1])-1]== 0:
                self.board[self.rows[move[0]]][int(move[1])-1] = self.current_player[1]
            else:
                await self.ctx.send('⚠️ There already is a marker on that spot. Choose another please.')
                fails += 1
                continue
            
            winner = self.check_winner()
            if winner is not None:
                await self.send_board(end=True)
                winner = self.players.get(winner)
                if winner is not None:
                    await self.ctx.send(f'🎉🎉{winner.mention} has won the game! ')
                else:
                    await self.ctx.send('It was a tie! Well played 😄')
                return
            else:
                self.current_player = (self.o, self.O) if self.current_player[1] == self.X else (self.x, self.X)
                
        await self.ctx.send('😫 Game ended due to too many failures to answer.')

    async def send_board(self, end=False):
        message = [
            "⬛1️⃣2️⃣3️⃣",
           f"🇦{''.join(self.icons[c] for c in self.board[0])}  ❌ {self.x.mention}{'⬅️' if self.x == self.current_player[0] else ''}",
           f"🇧{''.join(self.icons[c] for c in self.board[1])}  🅾️ {self.o.mention}{'⬅️' if self.o == self.current_player[0] else ''}",
           f"🇨{''.join(self.icons[c] for c in self.board[2])}"
           "\n\nReply in the format `a1`, `b2`, `c3`"
        ]
        end_message = [
           f"End result of the game {self.x.mention} vs {self.o.mention}",
            "⬛1️⃣2️⃣3️⃣",
           f"🇦{''.join(self.icons[c] for c in self.board[0])}",
           f"🇧{''.join(self.icons[c] for c in self.board[1])}",
           f"🇨{''.join(self.icons[c] for c in self.board[2])}"
        ]
        await self.ctx.send('\n'.join(message if not end else end_message))
    
    def check_winner(self):
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

class Battleship:
    class Board:
        def __init__(self, bot, owner: discord.Member, hidden=False, board=None):
            self.bot = bot

            self.owner = owner
            self.hidden = hidden
            if self.hidden:
                self.board: self = board
            self.ships = {'Carrier': 5, 'Battleship': 4, 'Cruiser': 3, 'Submarine': 3, 'Destroyer': 2}

            if not self.hidden:
                self.rows = [[random.randint(0, 1) for _ in range(10)] for _ in range(10)]
            else:
                self.rows = self.board.rows

            self.icons = {0: '🟦', 1: '🟥', 2: '💥', -2: '⬛'}

            self.letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
        
        def mark(self, coordinate: str):
            coordinate = coordinate.lower()
            possible_coords = [f'{letter}{number}' for letter in self.letters for number in [i for i in range(1, 11)]]
            if not coordinate in possible_coords:
                return None
            
            placement = self.rows[self.letters.index(coordinate[0])][int(coordinate[1:])-1]
            if placement == 2 or placement == -2:
                return None
            elif placement == 1:
                self.rows[self.letters.index(coordinate[0])][int(coordinate[1:])-1] = 2
                return True
            else:
                self.rows[self.letters.index(coordinate[0])][int(coordinate[1:])-1] = -2
                return False

        
        def setup(self):
            pass
            
        def get(self):
            if not self.hidden:
                struc = [[self.icons[row] for row in self.rows[i]] for i in range(10)]
            else:
                struc = [[self.icons[row] if row in [0, 2, -2] else self.icons[0] for row in self.rows[i]] for i in range(10)]

            for i, row in enumerate(struc):
                alphabet = ['🇦', '🇧', '🇨', '🇩', '🇪', '🇫', '🇬', '🇭', '🇮', '🇯']
                row.insert(0, alphabet[i])

            board = [''.join(row) for row in struc]
            board.insert(0, '\u200b'.join(['⬛', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']))
            return '\n'.join(board)

    def __init__(self, ctx: customContext, x: discord.Member, y: discord.Member):
        self.ctx = ctx
        self.bot = ctx.bot
        self.x = x
        self.y = y

        self.current_player = self.x
        self.messages = dict()
        self.boards = dict()
        
        self.setup()
        self.bot.loop.create_task(self.send_initial_messages())

    def setup(self):
        self.boards = {
            self.x: {
                'hidden': None, 
                'own': self.Board(self.bot, self.x)
            },
            self.y: {
                'hidden': None, 
                'own': self.Board(self.bot, self.y)
            }
        }

        self.boards[self.x]['hidden'] = self.Board(self.bot, self.x, hidden=True, board=self.boards[self.x]['own'])
        self.boards[self.y]['hidden'] = self.Board(self.bot, self.y, hidden=True, board=self.boards[self.y]['own'])
    
    async def send_initial_messages(self):
        for player in [self.x, self.y]:
            msg = await player.send(content=f'Link to go back to {self.ctx.channel.mention}', embed=self.build_embed(player))
            self.messages[player.id] = msg

    async def start(self):
        fails = 0
        while fails < 3:
            move = (await self.bot.wait_for('message', check=lambda m: m.author == self.current_player and not m.guild)).content
            mark = self.boards[self.opponent(self.current_player)]['own'].mark(move)
            if mark is None:
                fails += 1
                await self.current_player.send(f'⚠️ That is not a valid coordinate (hit already or not on board). Try again. (Fails threshold `{fails}/3`)')
                continue
            self.current_player = self.opponent(self.current_player)
            for player in [self.x, self.y]:
                await self.messages[player.id].edit(embed=self.build_embed(player))

            winner = self.check_winner()
            if winner is not None:
                for player in [self.x, self.y]:
                    await player.send(f'{winner.mention} has won the game. GG!')
                return
        for player in [self.x, self.y]:
            await player.send('😢 Game ended due to reaching the fail threshold.')
            
        
    def check_winner(self):
        for board in [self.boards[self.x]['own'], self.boards[self.y]['own']]:
            if 1 not in chain(*board.rows):
                return self.opponent(board.owner)
        return None
    
    def build_embed(self, player: discord.Member):
        em = Embed(title=f'Battleship | {self.x.name} VS {self.y.name}')
        em.add_field(name='Your board', value=self.boards[player]['own'].get())
        em.add_field(name='Opponent\'s board', value=self.boards[self.opponent(player)]['hidden'].get())
        em.add_field(name='Icons and what they mean', value='🟦 = Water\n🟥 = Boat\n💥 = Target Hit\n⬛ = Missed shot', inline=False)
        em.add_field(
            name='Instructions', 
            value='Send a coordinate to mark (`a1`, `a2`, `b3`) etc. \nThe goal is to destroy all enemy ships before the enemy destroys yours. Good luck!'
        )
        em.set_footer(text=f'({self.current_player.name}\'s turn)')
        return em

    def opponent(self, player: discord.Member):
        if player == self.x:
            return self.y
        return self.x


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def simon(self, ctx: customContext):
        """
        A single player memory game. Memorize the sequence and answer accordingly.
        Try to get the highest score possible!
        """
        game = SimonGame(ctx)
        await game.start()

    @commands.command(aliases=['ttt'])
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def tictactoe(self, ctx: customContext, opponent: discord.Member):
        """
        Play a classical game of Tic Tac Toe with a friend!
        """
        if opponent.bot or opponent == ctx.author:
            raise commands.BadArgument(f'Opponent can not be yourself or another bot.')

        confirmation = await ctx.confirm(opponent, message=f'**{opponent.name}**, do you want to play TicTacToe with {ctx.author.name}?')
        if confirmation is False:
            await ctx.send(f'{ctx.author.mention} The opponent declined... try again later.')
            return

        game = TicTacToe(ctx, ctx.author, opponent)
        await game.start()
    
    @commands.command(aliases=['ship'])
    @commands.max_concurrency(1, commands.BucketType.user)
    async def battleship(self, ctx: customContext, opponent: discord.Member):
        """
        Play a game of battleship with a friend.
        """
        if opponent.bot or opponent == ctx.author:
            raise commands.BadArgument(f'Opponent can not be yourself or another bot.')
        
        confirmation = await ctx.confirm(opponent, message=f'**{opponent.name}**, do you want to play Battleship with {ctx.author.name}?')
        if confirmation is False:
            await ctx.send(f'{ctx.author.mention} The opponent declined... try again later.')
            return
        
        game = Battleship(ctx, ctx.author, opponent)
        async with ctx.processing(ctx, message='Setting up the game...', delete_after=True):
            await asyncio.sleep(2) # let it set up the game first
            urls = [game.messages[ctx.author.id].jump_url, game.messages[opponent.id].jump_url]
            em = Embed()
            em.add_field(name='Game links for battleship game', value=f'**{ctx.author.name}**: {link("Click here", urls[0])} \n\n**{opponent.name}**: {link("Click here", urls[1])}')

        await ctx.send('Game started in DMs. Good luck both players, may the odds be ever in your favour.\n',embed=em)
        await game.start()

def setup(bot):
    bot.add_cog(Games(bot), cat_name='Fun')
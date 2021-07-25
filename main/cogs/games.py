from utils._type import *

import asyncio
import discord
import random
import io
import textwrap
import time
import difflib

from discord.ext import commands
from utils.useful import Cooldown, Embed, run_in_executor
from utils.chat_formatting import hyperlink as link
from itertools import chain
from cogs.image import get_bytes


class GameExit(Exception):
    def __init__(self, game, force=False, message='Game exited.'):
        super().__init__(message)
        self.game = game
        self.force = force

class Game:
    def __init__(self, ctx: customContext, *args, **kwargs):
        self.owner = ctx.author
    
    def end(self, force=False) -> GameExit:
        raise GameExit(self, force)

class SimonGame(Game):
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
                            self.bot.wait_for('reaction_add', check=check, timeout=len(self.sequence) * 5),
                            self.bot.wait_for('message', check=lambda m: m.author == self.player, timeout=len(self.sequence) * 5)
                        ],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    for future in _:
                        future.cancel()
                    reaction = done.pop().result()[0].emoji if not isinstance(done.copy().pop().result(), discord.Message) else done.pop().result().content
                    if reaction == 'end':
                        self.end()
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
        em.set_author(name=self.ctx.author, icon_url=self.ctx.author.avatar.url)
        return em

class TicTacToe(Game):
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

        self.grid = {'a': 0, 'b': 1, 'c': 2}
        self.icons = {0: '⬜', 1: '🅾️', -1: '❌'}

        self.players = {-1: self.x, 1: self.o}
        self.current_player = (self.x, self.X)

    async def start(self):
        self.fails = 0
        while self.fails < 3:
            await self.send_board()
            try:
                move = (await self.ctx.bot.wait_for('message', check=lambda m: m.author == self.current_player[0], timeout=15)).content.lower()
            except asyncio.TimeoutError:
                await self.ctx.send('❕ Woops. The game ended due to inactivity. Next time please be quicker to answer.')
                return
            if move == 'end':
                self.end()
            if not move in [f'{x}{y}' for x in ['a', 'b', 'c'] for y in [1, 2, 3]]:
                await self.ctx.send(f'⚠️ That is not a valid move {self.current_player[0].mention}! Please enter a valid move again.')
                self.fails += 1
                continue
            
            if self.board[self.grid[move[0]]][int(move[1])-1]== 0:
                self.board[self.grid[move[0]]][int(move[1])-1] = self.current_player[1]
            else:
                await self.ctx.send('⚠️ There already is a marker on that spot. Choose another please.')
                self.fails += 1
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

class Battleship(Game):
    class Board:
        def __init__(self, bot, owner: discord.Member, hidden=False, board=None):
            # If it is a hidden board it inherits the grid from the given board
            self.bot = bot

            self.owner = owner
            self.hidden = hidden
            if self.hidden:
                self.board: self = board
            self.ships: List[Battleship.Ship] = []
            self.ship_blueprint = {'Battleship': 4, 'Cruiser': 3, 'Submarine': 2, 'Destroyer': 1}

            if not self.hidden:
                self.grid = [[0 for _ in range(8)] for _ in range(8)]
            else:
                self.grid = self.board.grid

            self.icons = {0: '🟦', 1: '🔴', 2: '💥', -2: '⚫'}

            self.letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
            self.setup()
        
        def mark(self, coordinate: str):
            coordinate = coordinate.lower()
            if coordinate == 'end':
                raise GameExit(self)
            possible_coords = [f'{letter}{number}' for letter in self.letters for number in [i for i in range(1, 9)]]
            if not coordinate in possible_coords:
                return None
            
            placement = self.grid[self.letters.index(coordinate[0])][int(coordinate[1:])-1]
            if placement == 2 or placement == -2:
                return None
            elif placement == 1:
                self.grid[self.letters.index(coordinate[0])][int(coordinate[1:])-1] = 2
                for ship in self.ships:
                    if ship.destroyed():
                        self.ships.remove(ship)
                        return ship
                return True
            else:
                self.grid[self.letters.index(coordinate[0])][int(coordinate[1:])-1] = -2
                return False

        
        def setup(self):
            if self.hidden:
                return
            for name, size in self.ship_blueprint.items():
                self.place_ship(name, size)
        
        def place_ship(self, name: str, size: int):
            ship = self.generate_ship(name, size)
            self.ships.append(ship)
            ship.place()

        def generate_ship(self, name: str, size: int):
            orientation = random.choice(['horizontal', 'vertical'])

            locations = self.get_available_location(size, orientation)
            if locations is None:
                return None
            return Battleship.Ship(self, name, orientation, size, locations)

        def get_available_location(self, size, orientation):
            locations = []
            if orientation == 'horizontal':
                for row in range(8):
                    for col in range(8 - size + 1):
                        if 1 not in self.grid[row][col:col+size]:
                            locations.append((row, col))
    
            elif orientation == 'vertical':
                for col in range(8):
                    for row in range(8 - size + 1):
                        if 1 not in [self.grid[i][col] for i in range(row, row+size)]:
                            locations.append((row, col))
            return locations[random.randint(0, len(locations) - 1)] or None

        def get(self):
            if not self.hidden:
                struc = [[self.icons[row] for row in self.grid[i]] for i in range(8)]
            else:
                struc = [[self.icons[row] if row in [0, 2, -2] else self.icons[0] for row in self.grid[i]] for i in range(8)]

            for i, row in enumerate(struc):
                alphabet = ['🇦', '🇧', '🇨', '🇩', '🇪', '🇫', '🇬', '🇭']
                row.insert(0, alphabet[i])

            board = [''.join(row) for row in struc]
            board.insert(0, '\u200b'.join(['⬛', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣']))
            return '\n'.join(board)

    class Ship:
        def __init__(self, board, name, orientation: str, size: int, locations: list):
            self.board = board
            self.size = size
            self.name = name
            self.locations = locations

            if orientation in ['vertical', 'horizontal']:
                self.orientation = orientation
            else:
                raise ValueError('Value for orientation must be either vertical or horizontal')
            
        def place(self):
            if self.orientation == 'horizontal':
                self.coordinates = []
                for i in range(self.size):
                    self.coordinates.append((self.locations[0], self.locations[1] + i))
            elif self.orientation == 'vertical':
                self.coordinates = []
                for i in range(self.size):
                    self.coordinates.append((self.locations[0] + i, self.locations[1]))
            self.fill()

        def contains(self, location: tuple):
            for coords in self.coordinates:
                if coords == location:
                    return True
            return False
        
        def destroyed(self):
            for coords in self.coordinates:
                if self.board.grid[coords[0]][coords[1]] == 1:
                    return False
            return True
        
        def fill(self):
            for coords in self.coordinates:
                self.board.grid[coords[0]][coords[1]] = 1

    def __init__(self, ctx: customContext, x: discord.Member, y: discord.Member):
        self.ctx = ctx
        self.bot = ctx.bot
        self.x = x
        self.y = y

        self.players = [self.x, self.y]

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
        await self.send_embeds()

    async def send_embeds(self):
        for message in self.messages.values():
            await message.delete()
        for player in self.players:
            msg = await player.send(embed=self.build_embed(player))
            self.messages[player.id] = msg

    async def start(self):
        self.fails = {self.x.id: 0, self.y.id: 0}
        while self.fails[self.x.id] < 5 and self.fails[self.y.id] < 5:
            msg = await self.current_player.send(f'It is your turn now {self.current_player.mention}')
            move = (await self.bot.wait_for('message', check=lambda m: m.author == self.current_player and not m.guild)).content
            board = self.boards[self.opponent(self.current_player)]['own']
            try:
                mark = board.mark(move)
            except GameExit:
                self.end()
            await msg.delete()
            if mark is None:
                self.fails[self.current_player.id] += 1
                await self.current_player.send(f'⚠️ That is not a valid coordinate (hit already or not on board). Try again. (Fails threshold `{self.fails[self.current_player.id]}/5`)')
                continue
            elif isinstance(mark, Battleship.Ship):
                winner = self.check_winner()
                if winner is not None:
                    for player in self.players:
                        await player.send(f'{winner.mention} has won the game. GG!')
                    return
                
                await self.current_player.send(f'💣 You destroyed their {mark.name}! They have {len(board.ships)} other boats left.', delete_after=10)
                self.current_player = self.opponent(self.current_player)
                await self.send_embeds()
                continue
            elif mark is True:
                await self.current_player.send('💥 You hit a boat! You get another shot.', delete_after=10)
                await self.send_embeds()
                continue


            self.current_player = self.opponent(self.current_player)
            await self.send_embeds()

            winner = self.check_winner()
            if winner is not None:
                for player in self.players:
                    await player.send(f'{winner.mention} has won the game. GG!')
                return
        
        for player in self.players:
            await player.send(f'Oops. {self.current_player.mention} has reached the fail threshold. {self.opponent(self.current_player).mention} won the game!')
            
        
    def check_winner(self):
        for board in [self.boards[self.x]['own'], self.boards[self.y]['own']]:
            if 1 not in chain(*board.grid):
                return self.opponent(board.owner)
        return None
    
    def build_embed(self, player: discord.Member):
        em = Embed(title=f'Battleship | {self.x.name} VS {self.y.name}')
        em.add_field(
            name='Instructions', 
            value='Send a coordinate to mark (`a1`, `a2`, `b3` e.g.)  \nThe goal is to destroy all enemy ships before the enemy destroys yours. Good luck!'
        )
        em.add_field(name='Icons and what they mean', value='🟦 = Water\n🟥 = Boat\n💥 = Target Hit\n⬛ = Missed shot', inline=False)
        em.add_field(name='Your board', value=self.boards[player]['own'].get())
        em.add_field(name='Opponent\'s board', value=self.boards[self.opponent(player)]['hidden'].get())
        em.set_footer(text=f'({self.current_player.name}\'s turn)')
        return em

    def opponent(self, player: discord.Member):
        if player == self.x:
            return self.y
        return self.x

class TypeRace(Game):
    def __init__(self, ctx):
        self.ctx = ctx

        self.to_type: str = None

    @run_in_executor
    def draw(self, image, text):
        from PIL import Image, ImageDraw, ImageFont
        im = Image.open(io.BytesIO(image))
        draw = ImageDraw.Draw(im)
        font = ImageFont.truetype(f'{self.ctx.bot.cwd}/data/assets/Milliard.otf', 50)

        text = textwrap.fill(text, width=30)
        draw.multiline_text((im.width/2-400,im.height/2-70), text, (255,255,255), align='left', font=font)
        

        buffer = io.BytesIO()
        im.save(buffer, format='png')
        return buffer.getvalue()

    async def start(self):
        bot = self.ctx.bot
        image_url = random.choice(['https://i.imgur.com/Fwed3c2.png', 'https://imgur.com/PX8cjhG.png', 'https://i.imgur.com/rpSyUdI.png', 'https://i.imgur.com/Xx8rvbE.png'])
        byt = await get_bytes(self.ctx, image_url, bot.session)
        res = await bot.session.get('https://api.quotable.io/random', params={'minLength': 30, 'maxLength': 90})
        data = await res.json()

        
        self.to_type = data['content']
        buffer = await self.draw(byt, self.to_type)
        em = Embed(title='Typerace!', description='Type the following sentence as fast as possible:')
        em.set_image(url='attachment://TypeRace.png')
        em.set_footer(text=f"Quote by {data['author']}")
        self._message = await self.ctx.send(embed=em, file=discord.File(io.BytesIO(buffer), 'TypeRace.png'))

        await self.wait_for_response(self.ctx, self.to_type, timeout=30)

    
    async def wait_for_response(self, ctx: commands.Context, text: str, *, timeout: int):
        emoji_map = {1: '🥇', 2: '🥈', 3: '🥉'}

        format_line = lambda i, x: f" {emoji_map[i]} {x['user'].mention} in {x['time']:.2f}s | **WPM:** {x['wpm']:.2f} | **ACC:** {x['acc']:.2f}%"

        text = text.replace('\n', ' ')
        participants = []

        start = time.perf_counter()

        while True:
            def check(m):
                content = m.content.replace('\n', ' ')
                if m.channel == ctx.channel and not m.author.bot and m.author not in map(lambda m: m["user"], participants):
                    sim = difflib.SequenceMatcher(None, content, text).ratio()
                    return sim >= 0.75
            
            try:
                message = await ctx.bot.wait_for(
                    'message',
                    timeout=timeout,
                    check=check
                )
            except asyncio.TimeoutError:
                if participants:
                    break
                else:
                    return await ctx.reply('Oops. Seems like no one responded... sad.')
            end = time.perf_counter()
            content = message.content.replace('\n', ' ')
            timeout -= round(end-start)

            participants.append({
                'user': message.author,
                'time': end - start,
                'wpm': len(text.split(' ')) / ((end-start) / 60),
                'acc': difflib.SequenceMatcher(None, content, text).ratio() * 100
            })

            await message.add_reaction(emoji_map[len(participants)])
            
            if len(participants) >= 3:
                break

        desc = [format_line(i, x) for i, x in enumerate(participants, 1)]
        em = Embed(
            title='Typerace finished!',
            description=f'This typerace has finished. You can start another game by running `{ctx.prefix}typerace`'
        )
        em.add_field(name='Participants', value='\n'.join(desc))
        em.add_field(name='Prompt', value=text, inline=False)

        await self._message.reply(embed=em)


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games: List[Game] = []
    
    async def start_game(self, game: Union[SimonGame, TicTacToe, Battleship, TypeRace]):
        self.active_games.append(game)
        await game.start()
        self.active_games.remove(game)

    @commands.command()
    @commands.check(Cooldown(1, 20, 1, 10, commands.BucketType.user))
    async def simon(self, ctx: customContext):
        """
        A single player memory game. Memorize the sequence and answer accordingly.
        Try to get the highest score possible!
        """
        game = SimonGame(ctx)
        await self.start_game(game)

    @commands.command(aliases=['ttt'])
    @commands.check(Cooldown(1, 10, 1, 3, commands.BucketType.user))
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def tictactoe(self, ctx: customContext, opponent: discord.Member):
        """
        Play a classical game of Tic Tac Toe with a friend!
        """
        if opponent.bot or opponent == ctx.author:
            raise commands.BadArgument(f'Opponent can not be yourself or another bot.')

        view = ctx.Confirm(opponent)
        await ctx.send(f'**{opponent.name}**, do you want to play TicTacToe with {ctx.author.name}?', view=view)
        await view.wait()

        if view.value is False:
            await ctx.send(f'{ctx.author.mention} The opponent declined... try again later.')
            return
        elif view.value is None:
            await ctx.send(f'{ctx.author.mention} The opponent did not react... try again later.')
            return

        game = TicTacToe(ctx, ctx.author, opponent)
        await self.start_game(game)
    
    @commands.command(aliases=['ship'])
    @commands.check(Cooldown(1, 60, 1, 30, commands.BucketType.user))
    @commands.max_concurrency(1, commands.BucketType.user)
    async def battleship(self, ctx: customContext, opponent: discord.Member):
        """
        Play a game of battleship with a friend. 
        Rules are listed here: https://www.cs.nmsu.edu/~bdu/TA/487/brules.htm
        """
        if opponent.bot or opponent == ctx.author:
            raise commands.BadArgument(f'Opponent can not be yourself or another bot.')
        
        view = ctx.Confirm(opponent)
        await ctx.send(f'**{opponent.name}**, do you want to play Battleship with {ctx.author.name}?', view=view)
        await view.wait()

        if view.value is False:
            await ctx.send(f'{ctx.author.mention} The opponent declined... try again later.')
            return

        elif view.value is None:
            await ctx.send(f'{ctx.author.mention} The opponent did not react... try again later.')
            return
        
        game = Battleship(ctx, ctx.author, opponent)
        async with ctx.processing(ctx, message='Setting up the game...', delete_after=True):
            await asyncio.sleep(1) # let it set up the game first
            urls = [game.messages[ctx.author.id].jump_url, game.messages[opponent.id].jump_url]
            em = Embed()
            em.add_field(name='Game links for battleship game', value=f'**{ctx.author.name}**: {link("Click here", urls[0])} \n\n**{opponent.name}**: {link("Click here", urls[1])}')

        await ctx.send('Game started in DMs. Good luck both players, may the odds be ever in your favour.\n',embed=em)
        await self.start_game(game)

    @commands.command(aliases=['tr'])
    @commands.check(Cooldown(1, 10, 1, 5, commands.BucketType.user))
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def typerace(self, ctx: customContext):
        """
        Prepare for the best typerace ever! Compete with your friends and foes, who is the fastest?
        """
        async with ctx.processing(ctx, message='Starting... get ready!', delete_after=True):
            await asyncio.sleep(2)
            game = TypeRace(ctx)
        await self.start_game(game)

def setup(bot):
    bot.add_cog(Games(bot), cat_name='Fun')
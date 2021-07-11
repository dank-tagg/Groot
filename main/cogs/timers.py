from utils._type import *

import asyncio
import aiosqlite
import discord

from discord.ext import commands
from datetime import datetime
from dateparser.search import search_dates
from discord.ext import commands

class ParsedTime:
    def __init__(self, dt, arg):
        self.dt = dt
        self.arg = arg

class TimeConverter(commands.Converter):
    async def convert(self, ctx, argument) -> ParsedTime:
        parsed = search_dates(
            argument, settings={
                'TIMEZONE': 'UTC', 
                'PREFER_DATES_FROM': 'future', 
                'FUZZY': True
            }
        )

        if not parsed:
            raise commands.BadArgument('Invalid time provided. Try again with a different time.') # Time can't be parsed from the argument

        string_date = parsed[0][0]
        date_obj = parsed[0][1]
        if date_obj <= datetime.utcnow(): # Check if the argument parsed time is in the past.
            raise commands.BadArgument('Time can not be in the past.') # Raise an error.

        reason = argument.replace(string_date, "")
        if reason[0:2] == 'me' and reason[0:6] in ('me to ', 'me in ', 'me at '): # Checking if reason startswith me to/in/at
            reason = reason[6:] # Strip it.

        if reason[0:2] == 'me' and reason[0:9] == 'me after ': # Checking if the reason starts with me after
            reason = reason[9:] # Strip it.

        if reason[0:3] == 'me ': # Checking if the reason starts with "me "
            reason = reason[3:] # Strip it.

        if reason[0:2] == 'me': # Checking if the reason starts with me
            reason = reason[2:] # Strip it.

        if reason[0:6] == 'after ': # Checking if the argument starts with "after "
            reason = reason[6:] # Strip it.

        if reason[0:5] == 'after': # Checking if the argument starts with after
            reason = reason[5:] # Strip it.

        return ParsedTime(date_obj, reason)

class Timer:
    def __init__(self, record):
        self.id = record['id']

        extra = record['extra']
        self.args = extra.get('args', [])
        self.kwargs = extra.get('kwargs', {})
        self.event = record['event']

        self.created_at = record['created']
        self.expires = record['expires']
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, obj):
        try:
            return self.id == obj.id
        except AttributeError:
            return False
    
    def __repr__(self):
        return f'<Timer created={self.created_at} expires={self.expires} event={self.event}'

    @classmethod
    def temporary(cls, *, expires, created, event, args, kwargs):
        pseudo = {
            'id': None,
            'extra': { 'args': args, 'kwargs': kwargs },
            'event': event,
            'created': created,
            'expires': expires
        }
        return cls(record=pseudo)

class Reminders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._have_data = asyncio.Event(loop=bot.loop)
        self._current_timer = None
    
    def cog_unload(self):
        self._task.cancel()
    
    async def get_current_timer(self, days=7):
        query = query = "SELECT * FROM timers WHERE expires < (date(CURRENT_TIMESTAMP, ?)) ORDER BY expires LIMIT 1"
        self.bot.db.row_factory = aiosqlite.Row
        cur = await self.bot.db.execute(query, (f'+{days} days',))
        record = await cur.fetchrow()
        self.bot.db.row_factory = None
        return Timer(record=record) if record else None
    
    async def wait_for_timers(self, days=7):
        timer = await self.get_current_timer(days=days)
        if timer is not None:
            self._have_data.set()
            return timer

        self._have_data.clear()
        self._current_timer = None
        await self._have_data.wait()
        return await self.get_current_timer(days=days)
    
    async def call_timer(self, timer: Timer):
        query = "DELETE FROM timers WHERE id = ?"
        await self.bot.db.execute(query, timer.id)

        event = f'{timer.event}_timer_complete'
        self.bot.dispatch(event, timer)

    async def dispatch_timers(self):
        try:
            while not self.bot.is_closed():
                timer = self._current_timer = await self.wait_for_timers(days=40)
                now = datetime.utcnow()

                if timer.expires >= now:
                    to_sleep = (timer.expires - now).total_seconds()
                    await asyncio.sleep(to_sleep)
                
                await self.call_timer(timer)
        except asyncio.CancelledError:
            raise
        except (OSError, discord.ConnectionClosed):
            self._task.cancel()
            self._task = self.bot.loop.create_task(self.dispatch_timers())
    
    async def short_timer(self, seconds, timer):
        await asyncio.sleep(seconds)
        event = f'{timer.event}_timer_complete'
        self.bot.dispatch(event, timer)
    
    async def create_timer(self, expires, event, *args, **kwargs):
        try:
            now = kwargs.pop('created')
        except KeyError:
            now = datetime.utcnow()
        
        timer = Timer.temporary(event=event, args=args, kwargs=kwargs, expires=expires, created=now)
        delta = (expires - now).total_seconds()
        if delta <= 60:
            self.bot.loop.create_task(self.short_timer(delta, timer))
            return timer
        
        query = """
                INSERT INTO timers (event, extra, expires, created)
                VALUES (?, ?, ?, ?)
                RETURNING id
                """
        
        cur = await self.bot.db.execute(query, (event, { 'args': args, 'kwargs': kwargs }, expires, now))
        row = await cur.fetchone()
        timer.id = row[0]

        if delta <= (86400*40): # 40 days
            self._have_data.set()
        
        if self._current_timer and expires < self._current_timer.expires:
            self._task.cancel()
            self._task = self.bot.loop.create_task(self.dispatch_timers())
        
        return timer

    @commands.group(name='reminder', usage='<when>', invoke_without_command=True)
    async def reminder(self, ctx: customContext, *, when: TimeConverter):
        timer = await self.create_timer(
            when.dt,
            'reminder',
            ctx.author.id,
            ctx.channel.id,
            when.arg,
            created=ctx.message.created_at,
            message_id = ctx.message.id
        )
        timestamp = f'<t:{int(when.dt.timestamp())}:R>'
        await ctx.send(f'Alright {ctx.author.mention}, {timestamp}: {when.arg}, {timer}')

def setup(bot):
    bot.add_cog(Reminders(bot))
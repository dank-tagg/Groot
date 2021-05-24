import asyncio
import datetime
import math
import time

import discord
import humanize
import utils.json_loader
from discord.ext import commands
from utils.chat_formatting import hyperlink
from utils.useful import Embed, grootCooldown


class Information(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping", brief="Shows the bots latency")
    async def ping(self, ctx):
        """
        Shows the bot's latency in miliseconds.\n
        Useful if you want to know if the bot is lagging or not
        """
        start = time.perf_counter()
        msg = await ctx.send("<a:typing:826939777290076230> pinging...")
        end = time.perf_counter()
        typing_ping = (end - start) * 1000
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"

        async with self.bot.db.execute(query) as cur:
            row = await cur.fetchall()
        a = [i[0] for i in row]
        start = time.perf_counter()
        for name in a:
            query = f"SELECT * FROM {name}"
            async with self.bot.db.execute(query):
                end = time.perf_counter()

        sql_ping = (end - start) * 1000
        await msg.edit(
            content=f"**Typing**: {round(typing_ping, 1)} ms\n**Websocket**: {round(self.bot.latency*1000)} ms\n**Database**: {round(sql_ping, 1)} ms"
        )

    @commands.command(name="vote", brief="The links where you can vote for the bot.")
    async def _vote(self, ctx):
        """
        Sends an embed containing two hyperlinks,\n
        one for Top.gg and one for discordbotlist.com
        """
        em = Embed(
            title="Vote for Groot!",
            description=f'{hyperlink("**top.gg**", "https://top.gg/bot/812395879146717214/vote")}\n\n'
            f'{hyperlink("**discordbotlist.com**", "https://discordbotlist.com/bots/groot/upvote")}',
        )
        em.set_thumbnail(url=self.bot.user.avatar_url)
        await ctx.send(embed=em)

    @commands.command(name="invite", brief="Sends an invite for the bot.")
    async def invite(self, ctx):
        """
        Sends an invite for the bot with no permissions.\n
        Note that a few permissions are required to let the bot run smoothly,\n
        as shown in `perms`
        """
        em = Embed(title=f"Invite {self.bot.user.name} to your server!", color=0x2F3136)
        em.add_field(
            name=f"Invite the bot",
            value=f"{hyperlink('**Click Here**', f'{discord.utils.oauth_url(812395879146717214)}')}",
            inline=False,
        )

        em.add_field(
            name="Support server",
            value=f"{hyperlink('**Click Here**','https://discord.gg/nUUJPgemFE')}",
            inline=False,
        )
        em.set_thumbnail(url=self.bot.user.avatar_url)
        await ctx.send(embed=em)

    async def create_menu(self, ctx: commands.Context, cog: str):

        if self.bot.get_cog(cog) == None:
            return await ctx.reply(
                f"No command/category found. Try using `{ctx.prefix}help` to see all available commands.",
                mention_author=False,
            )
        all_commands = self.bot.get_cog(cog).get_commands()
        allcommands = [f"{command.name}" for command in all_commands]

        for commands in allcommands:
            if self.bot.get_command(commands).hidden:
                allcommands.remove(commands)

        page = 1
        if len(allcommands) == 0:
            return await ctx.send("Empty.")

        items_per_page = 4
        pages = math.ceil(len(allcommands) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ""
        embed = (
            Embed(
                description="**Commands [{}]**\n\n{}".format(len(allcommands), queue),
                color=0x2F3136,
            )
            .set_footer(
                text="Viewing page {}/{}".format(page, pages),
                icon_url=self.bot.user.avatar_url,
            )
            .set_author(name=f"Category {str.capitalize(cog)}")
        )

        for command in enumerate(allcommands[start:end], start=start):
            command = self.bot.get_command(command[1])
            embed.add_field(
                name="{} {}".format(command, command.signature),
                value="{}".format(command.brief),
                inline=False,
            )
        msg = await ctx.send(embed=embed)
        ALLEMOJIS = [
            "\U000023ea",
            "\U000025c0",
            "<:trashcan:822050746333003776>",
            "\U000025b6",
            "\U000023e9",
        ]
        for e in ALLEMOJIS:
            await msg.add_reaction(e)
        n = 1
        while True:
            page = n
            if len(allcommands) == 0:
                return await ctx.send("Empty.")

            items_per_page = 4
            pages = math.ceil(len(allcommands) / items_per_page)

            start = (page - 1) * items_per_page
            end = start + items_per_page

            queue = ""
            embed = (
                Embed(
                    description="**Commands [{}]**\n\n{}".format(
                        len(allcommands), queue
                    ),
                    color=0x2F3136,
                )
                .set_footer(
                    text="Viewing page {}/{}".format(page, pages),
                    icon_url=self.bot.user.avatar_url,
                )
                .set_author(name=f"Category {str.capitalize(cog)}")
            )
            for command in enumerate(allcommands[start:end], start=start):
                command = self.bot.get_command(command[1])
                embed.add_field(
                    name="{} {}".format(command, command.signature),
                    value="{}".format(command.brief),
                    inline=False,
                )

            await msg.edit(embed=embed)

            def check(reaction, m):
                return (
                    m == ctx.author
                    and str(reaction.emoji) in ALLEMOJIS
                    and reaction.message == msg
                )

            try:
                ret = await self.bot.wait_for("reaction_add", timeout=30, check=check)
                if str(ret[0]) == "\U000023ea":
                    try:
                        await msg.remove_reaction("\U000023ea", ctx.author)
                    except:
                        pass
                    n = 1
                elif str(ret[0]) == "\U000025c0":
                    try:
                        await msg.remove_reaction("\U000025c0", ctx.author)
                    except:
                        pass
                    if n <= 1:
                        pass
                    else:
                        n -= 1
                elif str(ret[0]) == "\U000025b6":
                    try:
                        await msg.remove_reaction("\U000025b6", ctx.author)
                    except:
                        pass
                    if n >= pages:
                        pass
                    else:
                        n += 1
                elif str(ret[0]) == "\U000023e9":
                    try:
                        await msg.remove_reaction("\U000023e9", ctx.author)
                    except:
                        pass
                    n = pages
                elif str(ret[0]) == "<:trashcan:822050746333003776>":
                    await msg.delete()
                    return
            except asyncio.TimeoutError:
                return

    @commands.command(
        name="help", brief="Shows help for the bot", usage="[command|cog]"
    )
    async def _help(self, ctx, *, command: str = None):
        """Sends an embed containing all information you need for the bot."""
        if command:
            if self.bot.get_command(command) == None:
                f = str(self.bot.get_cog(command))
                if f != None:
                    await self.create_menu(ctx, f"{str.capitalize(command.lower())}")
                    return
                else:
                    await ctx.reply(
                        f"No command/category found. Try using `{ctx.prefix}help` to see all available commands.",
                        mention_author=False,
                    )

            command = self.bot.get_command(command)
            em = Embed(
                title=f"{command} {command.signature}",
                color=0x2F3136,
                description=f"{command.help}",
            )

            if command.aliases:
                aliases = ", ".join(command.aliases)
            else:
                aliases = "No aliases"

            try:
                default = discord.utils.find(
                    lambda c: isinstance(c, grootCooldown), command.checks
                ).default_mapping._cooldown.per
                altered = discord.utils.find(
                    lambda c: isinstance(c, grootCooldown), command.checks
                ).altered_mapping._cooldown.per
            except:
                default = 3
                altered = 1

            if default is not None and altered is not None:
                em.add_field(
                    name="Cooldowns",
                    value=f"Default: `{default}s`\nPremium: `{altered}s`",
                )

            em.add_field(name="Aliases", value=f"```{aliases}```", inline=False)
            subs = ""
            try:
                for sub in command.walk_commands():

                    subs += (
                        f"`{str(sub).replace(' ', '` `')}` `{str(sub.signature).replace(' ', '` `')}` — {sub.brief}\n"
                        if sub.signature
                        else f"`{str(sub).replace(' ', '` `')}` — {sub.brief}\n"
                    )
            except:
                pass
            if subs != "":
                em.add_field(name="Subcommands", value=f"{subs}")

            await ctx.send(embed=em)

            return
        allcogs = [
            "• <:infosymbol:813730829989576714> **Information**",
            "🔧 **Configuration**",
            ":gear: **Moderation**",
            ":hammer_pick: **Utilities**",
            ":partying_face: **Fun**",
            "💰 **Currency**",
        ]

        allemojis = [
            "<:infosymbol:813730829989576714>",
            "🔧",
            "⚙️",
            "⚒️",
            "🥳",
            "💰",
            "<:trashcan:822050746333003776>",
        ]
        query = "SELECT sum(counter) FROM usage"
        cur = await self.bot.db.execute(query)
        row = await cur.fetchone()
        total_usage = row[0]

        updates = utils.json_loader.read_json("updates")
        date_time_obj = datetime.datetime.strptime(
            updates["upDATE"], "%Y-%m-%d %H:%M:%S.%f"
        )
        upDATE = date_time_obj.strftime("%d %B, %Y")
        f = Embed(
            title="",
            description=f"Prefix `{ctx.prefix}`\n"
            f"Total commands: {len(self.bot.commands)} | Commands used: {total_usage}\n"
            "```diff\n- [] = optional argument\n"
            "- <> = required argument\n"
            f"+ Type {ctx.prefix}help [command | category] for "
            "more help on a specific category or command!```"
            "[Support](<https://discord.gg/nUUJPgemFE>) | "
            "[Vote](https://top.gg/bot/812395879146717214/vote) | "
            f"[Invite]({discord.utils.oauth_url(812395879146717214)})\n",
            color=0x2F3136,
            timestamp=datetime.datetime.utcnow(),
        )

        f.add_field(name="Categories", value="\n• ".join(cogs for cogs in allcogs))
        f.add_field(
            name=f"📰 Latest News - {upDATE}",
            value="[Jump to the full message\n"
            "Can't open? Click the support button to join the support server]"
            f"({updates['link']})\n\n"
            f"{updates['update']}",
        )
        f.set_author(name=f"{ctx.author}", icon_url=ctx.author.avatar_url)
        f.set_footer(
            text="You can also click on one of the reactions "
            "to view the commands of their matching category!"
        )
        msg = await ctx.send(embed=f)
        for e in allemojis:
            await msg.add_reaction(e)

        def check(reaction, m):
            return (
                m == ctx.message.author
                and str(reaction.emoji) in allemojis
                and reaction.message == msg
            )

        try:
            ret = await self.bot.wait_for("reaction_add", timeout=45, check=check)
            if str(ret[0]) == "🔧":
                await msg.delete()
                cmd = self.bot.get_command("help")
                await ctx.invoke(cmd, command="configuration")
                return
            elif str(ret[0]) == "⚙️":
                await msg.delete()
                cmd = self.bot.get_command("help")
                await ctx.invoke(cmd, command="moderation")
                return
            elif str(ret[0]) == "⚒️":
                await msg.delete()
                cmd = self.bot.get_command("help")
                await ctx.invoke(cmd, command="utilities")
                return
            elif str(ret[0]) == "🥳":
                await msg.delete()
                cmd = self.bot.get_command("help")
                await ctx.invoke(cmd, command="fun")
                return
            elif str(ret[0]) == "💰":
                await msg.delete()
                cmd = self.bot.get_command("help")
                await ctx.invoke(cmd, command="currency")
                return
            elif str(ret[0]) == "<:infosymbol:813730829989576714>":
                await msg.delete()
                cmd = self.bot.get_command("help")
                await ctx.invoke(cmd, command="information")
                return
            elif str(ret[0]) == "<:trashcan:822050746333003776>":
                await ctx.message.delete()
                await msg.delete()
                return

        except asyncio.TimeoutError:
            try:
                await ctx.message.delete()
            except:
                pass
            await msg.delete()
            return

    @commands.command(name="uptime", brief="Shows the bot's uptime")
    async def _uptime(self, ctx):
        """
        Shows the bot's uptime in days | hours | minutes | seconds
        """
        em = Embed(
            description=f"{humanize.precisedelta(datetime.datetime.utcnow() - self.bot.launch_time, format='%.0f')}",
            colour=0x2F3136,
        )
        em.set_author(name="Uptime")
        em.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=em)

    @commands.command(name="source")
    async def _source(self, ctx):
        em = Embed(title="Be sure to read the licenses.")
        em.set_thumbnail(url="https://i.imgur.com/AyoXstG.png")
        em.add_field(
            name="Source of Groot:", value="https://github.com/dank-tagg/Groot"
        )
        em.add_field(
            name="Source of Groot-Website:",
            value="https://github.com/dank-tagg/Groot-Website/",
            inline=False,
        )
        em.add_field(
            name="More links",
            value="[Website](https://dank-tagg.github.io/Groot-Website) | "
            "[Advanced website](https://github.com/dank-tagg/GrootWebsiteFlask)",
        )
        return await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Information(bot))

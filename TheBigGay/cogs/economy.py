import discord
from discord.ext import commands
from datetime import datetime, timedelta
import calendar

from .utils import mysql
from .utils import checks


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        guilds = self.bot.guilds

        for guild in guilds:
            # Check for database tables
            mysql.initialize_guild(guild.id)

            await self.check_lottery(guild)

    async def check_lottery(self, guild: discord.Guild):
        # Check for lottery events
        events = await guild.fetch_scheduled_events()
        drawing_event = [event for event in events if event.name == "Lottery Drawing"]
        if not drawing_event:
            await self.create_lottery_event(guild)

        # Lottery is held on the last day of every month. Heroku reloads daily, so this will be checked daily.
        now = datetime.now(mysql.timezone)
        tomorrows_month = (now + timedelta(days=1)).month
        if now.month != tomorrows_month:
            channels = [item[1] for item in guild.by_category() if item[0].name == "Gambling"][0]
            main_hall = [channel for channel in channels if channel.name == "main-hall"][0]

            winner, balance = mysql.choose_lottery_winner(self.bot, guild)

            description = f"CONGRATS, {winner.mention}, you're rich!! Your balance is now **{balance} gaybucks**"
            embed = discord.Embed(title="Lottery Results", description=description, color=discord.Color.gold())
            message = await main_hall.send(embed=embed)
            await message.pin()

            await self.create_lottery_event(guild, next_month=True)

    async def create_lottery_event(self, guild: discord.Guild, next_month: bool = False):
        if next_month:
            now = datetime.now(mysql.timezone) + timedelta(days=1)
        else:
            now = datetime.now(mysql.timezone)
        first_weekday, total_days = calendar.monthrange(now.year, now.month)
        start_time = now + timedelta(days=total_days-now.day)
        end_time = start_time + timedelta(minutes=15)

        description = (
            "A random lottery ticket will be pulled to choose the winner of the entire jackpot! "
            "Use .ticket to purchase lottery tickets, and .lottery to see the current jackpot total."
        )
        await guild.create_scheduled_event(name="Lottery Drawing", description=description, start_time=start_time, end_time=end_time, entity_type=discord.EntityType.external, location="main-hall")

    @commands.command(brief="Get your current balance.", description="Retrieve your current balance in gaybucks.")
    async def wallet(self, ctx: commands.Context):
        result = mysql.get_wallet(ctx.author)
        await ctx.send(f"{ctx.author.mention}, your balance is **{result[0]}** gaybucks and you have **{result[1]}** lottery tickets.")

    @commands.command(brief="Poor? Use this once per day!",
                      description="You must have less than 50 gaybucks in your account to be eligible. "
                                  "You can also only receive a subsidy once per day.")
    @checks.check_subsidy()
    @checks.is_gambling_category()
    async def subsidy(self, ctx: commands.Context):
        balance = mysql.subsidize(ctx.author)

        await ctx.send(f"{ctx.author.mention}, 50 gaybucks have been added to your account, "
                       f"courtesy of your sugar daddy 😉 (You now have **{balance} GB**)")

    @commands.command(brief="Check the current economy standings.",
                      description="Shows each member's current balance in gaybucks.")
    async def economy(self, ctx: commands.Context):
        economy = mysql.get_economy(self.bot, ctx.guild)
        sorted_economy = sorted(economy, key=lambda tup: tup[1], reverse=True)

        embed = discord.Embed(title="Economy Top 5", color=discord.Color.purple())
        for row in sorted_economy[:5]:
            member = ctx.guild.get_member(int(row[0]))
            balance = row[1]
            embed.add_field(name=f"{member.name}", value=f"{balance} GB", inline=False)

        await ctx.send(embed=embed)

    @commands.command(brief="Donate gaybucks to another member.",
                      description="Donate gaybucks to another member of the server.")
    @checks.is_gambling_category()
    async def donate(self, ctx: commands.Context, member: discord.Member, amt: int):
        if member.id == ctx.author.id:
            return await ctx.send(f"{ctx.author.mention} Wow, how generous...")

        checks.is_valid_bet(ctx, ctx.author, amt)

        mysql.update_balance(ctx.author, -amt)
        balance = mysql.update_balance(member, amt)
        await ctx.send(f"{ctx.author.mention} has just donated {amt} GB to {member.mention}! They now have {balance} GB.")

    @commands.command(brief="Buy lottery tickets for 50 GB each.", description="Lottery tickets get you a chance to win the monthly lottery. 50 GB each.")
    @checks.is_gambling_category()
    async def ticket(self, ctx:commands.Context, amt: int = 1):
        ticket_price = 50
        checks.is_valid_bet(ctx, ctx.author, amt * ticket_price)

        tickets = mysql.buy_ticket(self.bot, ctx.author, amt)

        await ctx.send(f"{ctx.author.mention}, you now have **{tickets}** lottery tickets.")

    @commands.command(brief="Check the current jackpot.", description="Shows the current lottery jackpot.")
    @checks.is_gambling_category()
    async def lottery(self, ctx: commands.Context):
        result = mysql.get_lottery(self.bot, ctx.guild)

        description = f"The current lottery jackpot is **{result} gaybucks**. Buy your tickets with **.ticket** before the drawing at the end of the month!"
        
        embed = discord.Embed(title="Lottery", description=description, color=discord.Color.gold())
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Economy(bot))

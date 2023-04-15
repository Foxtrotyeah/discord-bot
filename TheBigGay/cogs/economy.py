import discord
from discord import app_commands
from discord.ext import commands, tasks
import datetime
from dateutil.relativedelta import relativedelta

from .utils import mysql, checks


time = datetime.time(hour=21, tzinfo=mysql.timezone)


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            # Check for database tables
            mysql.initialize_guild(guild.id)

        self.check_lottery.start()

    @tasks.loop(time=time)
    async def check_lottery(self):
        for guild in self.bot.guilds:
            # Check for lottery events
            events = await guild.fetch_scheduled_events()
            drawing_event = [event for event in events if event.name == "Lottery Drawing"]
            if not drawing_event:
                drawing_event = [await self.create_lottery_event(guild)]

            # Lottery is held on the last day of every month. Heroku reloads daily, so this will be checked daily.
            if drawing_event[0].start_time.date() == datetime.datetime.now().date():
                channels = [item[1] for item in guild.by_category() if item[0].name == "Gambling"][0]
                main_hall = [channel for channel in channels if channel.name == "main-hall"][0]

                winner, balance = mysql.choose_lottery_winner(self.bot.application_id, guild)

                description = f"CONGRATS, {winner.mention}, you're rich!! Your balance is now **{balance} gaybucks**"
                embed = discord.Embed(title="Lottery Results", description=description, color=discord.Color.gold())
                message = await main_hall.send(embed=embed)
                await message.pin()

                await drawing_event[0].delete()
                await self.create_lottery_event(guild)

    async def create_lottery_event(self, guild: discord.Guild) -> discord.ScheduledEvent:
        # Create the date for the first of next month at 8:00p Pacific. discord.py incorrectly inputs 8pm MST as 9pm MST.
        now = datetime.datetime.now(mysql.timezone)
        start_time = datetime.datetime(now.year, now.month, 1, 20, tzinfo=mysql.timezone) + relativedelta(months=1)
        end_time = start_time + datetime.timedelta(minutes=15)

        description = (
            "A random lottery ticket will be pulled to choose the winner of the entire jackpot! "
            "Use .ticket to purchase lottery tickets, and .lottery to see the current jackpot total."
        )
        return await guild.create_scheduled_event(name="Lottery Drawing", description=description, start_time=start_time, end_time=end_time, entity_type=discord.EntityType.external, location="main-hall")

    @app_commands.command(description="Get your current balance and lottery tickets")
    async def wallet(self, interaction: discord.Interaction):
        result = mysql.get_wallet(interaction.user)
        await interaction.response.send_message(f"Your balance is **{result[0]}** gaybucks and you have **{result[1]}** lottery ticket(s).", ephemeral=True)

    @app_commands.command(description="Receive your daily 50GB subsidy (if you're poor)")
    @checks.check_subsidy()
    async def subsidy(self, interaction: discord.Interaction):
        balance = mysql.subsidize(interaction.user)

        await interaction.response.send_message(f"50 gaybucks have been added to your account, "
                       f"courtesy of your sugar daddy 😉 (You now have **{balance}GB**)", ephemeral=True)

    @app_commands.command(description="Shows each member's current GB balance")
    async def economy(self, interaction: discord.Interaction):
        economy = mysql.get_economy(self.bot.application_id, interaction.guild)
        sorted_economy = sorted(economy, key=lambda tup: tup[1], reverse=True)

        embed = discord.Embed(title="Economy Top 5", color=discord.Color.purple())
        for row in sorted_economy[:5]:
            member = interaction.guild.get_member(int(row[0]))
            balance = row[1]
            embed.add_field(name=f"{member.name}", value=f"{balance}GB", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(description="Donate gaybucks to another member of the server")
    @app_commands.describe(member="the member to donate to", amount="amount of GB to donate")
    async def donate(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if member.id == interaction.user.id:
            return await interaction.response.send_message("Wow, how generous...?")

        checks.is_valid_bet(interaction.channel, interaction.user, amount)

        mysql.update_balance(interaction.user, -amount)
        balance = mysql.update_balance(interaction.user, amount)
        await interaction.response.send_message(f"Successfully donated {amount}GB to {member.mention}! They now have {balance}GB.")

    @app_commands.command(description="Buy lottery tickets for 50GB each")
    @app_commands.describe(amount="amount of lottery tickets to buy")
    async def ticket(self, interaction: discord.Interaction, amount: int = 1):
        ticket_price = 50
        checks.is_valid_bet(interaction.channel, interaction.user, amount * ticket_price)

        tickets = mysql.buy_ticket(self.bot.application_id, interaction.user, amount)

        await interaction.response.send_message(f"You now have **{tickets}** lottery tickets.", ephemeral=True)

    @app_commands.command(description="Shows the current lottery jackpot.")
    async def lottery(self, interaction: discord.Interaction):
        result = mysql.get_lottery(self.bot.application_id, interaction.guild)

        description = f"The current lottery jackpot is **{result} gaybucks**. Buy your tickets with **/ticket** before the drawing at the end of the month!"
        
        embed = discord.Embed(title="Lottery", description=description, color=discord.Color.gold())
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Economy(bot))

import discord
from discord.ext import commands
import mysql.connector

from .utils import mysql
from .utils import checks


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Hidden commands from shop cog
        self.shop_items = [
            (".mute [user]", 50, "Mute a user for 60 seconds."),
            (".boot [user]", 100, "Force a user to disconnect until they message The Big Gay."),
            (".admin", 200, "Receive admin privileges for 30 minutes."),
            (".daddy", 1000, "Receive the permanent title of 'Daddy'.")
        ]

    @commands.Cog.listener()
    async def on_ready(self):
        guilds = self.bot.guilds

        for guild in guilds:
            mysql.initialize_guild(guild)

    @commands.command(brief="Get your current balance.", description="Retrieve your current balance in gaybucks.")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def balance(self, ctx):
        result = mysql.get_balance(ctx.author)
        await ctx.send(f"{ctx.author.mention}, your balance is {result} gaybucks.")

    @commands.command(brief="Running low on funds? Use this once per day!",
                      description="You must have less than 50 gaybucks in your account to be eligible. "
                                  "You can also only receive a subsidy once per day.")
    @checks.is_gambling_category()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def subsidy(self, ctx):
        if not mysql.check_subsidy(ctx.author):
            return await ctx.send(
                f"{ctx.author.mention}, you are not eligible for a subsidy. "
                f"Either you have more than 100 gaybucks in your account, "
                f"or your sugar daddy has already bailed you out once today."
            )

        await mysql.subsidize(ctx.author)
        await ctx.send(f"{ctx.author.mention}, 50 gaybucks have been added to your account, "
                       f"courtesy of your sugar daddy 😉. (You now have {mysql.get_balance(ctx, bal_check=True)} GB)")

    @commands.command(brief="Check the current economy standings.",
                      description="Shows each member's current balance in gaybucks.")
    @checks.is_gambling_category()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def economy(self, ctx):
        economy = mysql.get_economy(ctx.guild)
        sorted_economy = sorted(economy, key=lambda tup: tup[1], reverse=True)

        embed = discord.Embed(title="Economy Standings", color=discord.Color.purple())
        for row in sorted_economy:
            member = ctx.guild.get_member(int(row[0]))
            balance = row[1]
            embed.add_field(name=f"{member.name}", value=f"{balance} GB", inline=False)

        await ctx.send(embed=embed)

    @commands.command(brief="Show the available options to spend gaybucks on.",
                      description="View and purchase options with your available gaybuck funds.")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def shop(self, ctx):
        message = "__You can purchase any of the following commands:__"
        for item, cost, description in self.shop_items:
            message += f"\n\n-**{item}** - *{cost} gb*: {description}"

        embed = discord.Embed(title="Shop", description=message, color=discord.Color.dark_gold())
        await ctx.send(embed=embed)

    @commands.command(brief="Donate gaybucks to another member of the server.",
                      description="Donate gaybucks to another member of the server.")
    @checks.is_gambling_category()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def donate(self, ctx, member: discord.Member, amt: int = None):
        # if not member or not amt:
        #     return  ctx.send(f"{ctx.author.mention} Try `.help` + `[the function name]` "
        #                                 f"to get more info on how to use this command.")
        # try:
        #     amt = int(amt)
        # except ValueError:
        #     return ctx.send(f"{ctx.author.mention} Your donation must be an integer (whole) number.")

        checks.is_valid_bet(ctx.author, amt)

        await mysql.update_balance(ctx, ctx.author, -amt)
        await mysql.update_balance(ctx, member, amt)
        await ctx.send(f"{ctx.author.mention} has donated {amt} GB to {member.mention}!")


async def setup(bot):
    await bot.add_cog(Economy(bot))

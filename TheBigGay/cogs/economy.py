import discord
from discord.ext import commands

from .utils import mysql
from .utils import checks


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        guilds = self.bot.guilds

        for guild in guilds:
            mysql.initialize_guild(guild)

    @commands.command(brief="Get your current balance.", description="Retrieve your current balance in gaybucks.")
    async def balance(self, ctx: commands.Context):
        result = mysql.get_balance(ctx.author)
        await ctx.send(f"{ctx.author.mention}, your balance is {result} gaybucks.")

    @commands.command(brief="Poor? Use this once per day!",
                      description="You must have less than 50 gaybucks in your account to be eligible. "
                                  "You can also only receive a subsidy once per day.")
    @checks.is_gambling_category()
    @checks.check_subsidy()
    async def subsidy(self, ctx: commands.Context):
        balance = mysql.subsidize(ctx.author)

        await ctx.send(f"{ctx.author.mention}, 50 gaybucks have been added to your account, "
                       f"courtesy of your sugar daddy 😉 (You now have {balance} GB)")

    @commands.command(brief="Check the current economy standings.",
                      description="Shows each member's current balance in gaybucks.")
    async def economy(self, ctx: commands.Context):
        economy = mysql.get_economy(ctx.guild)
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

        checks.is_valid_bet(ctx.author, amt)

        await mysql.update_balance(ctx, ctx.author, -amt)
        balance = await mysql.update_balance(ctx, member, amt)
        await ctx.send(f"{ctx.author.mention} has just donated {amt} GB to {member.mention}! They now have {balance} GB.")


async def setup(bot):
    await bot.add_cog(Economy(bot))

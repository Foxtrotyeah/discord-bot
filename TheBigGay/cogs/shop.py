import discord
from discord.ext import commands
import asyncio

from .utils import mysql
from .utils import checks


class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief="Deafens a user.", description="Deafens a user for 60 seconds.", hidden=True)
    @checks.has_funds(50)
    async def mute(self, ctx, user: discord.Member = None):
        if not user:
            raise commands.CommandError(f"{ctx.author.mention} Try `.help` + `[the function name]` "
                                        f"to get more info on how to use this command.")

        await mysql.update_balance(ctx, ctx.author, -50)

        role = discord.utils.get(ctx.guild.roles, name="Bitch")
        await user.add_roles(role)
        try:
            await user.edit(mute=True)
        except Exception as e:
            print(e)

        await ctx.send(f"{user.mention} Shush.")

        await asyncio.sleep(60)

        await user.remove_roles(role)
        try:
            await user.edit(mute=False)
        except Exception as e:
            print(e)

    # TODO Add description?
    @commands.command(hidden=True)
    @checks.has_funds(100)
    async def boot(self, ctx, user: discord.Member = None):
        if not user:
            raise commands.CommandError(f"{ctx.author.mention} Try `.help` + `[the function name]` "
                                        f"to get more info on how to use this command.")

        await mysql.update_balance(ctx, ctx.author, -100)

        role = discord.utils.get(ctx.guild.roles, name="Banished")
        await user.add_roles(role)
        try:
            await user.move_to(None)
        except Exception as e:
            print(e)

        await ctx.send(f"{user.mention} Begone, THOT! Check your DM's to get your privileges back 😉")

        await user.send("Looks like you got put in time out. If you want back in, you'd better beg for daddy.")

    @commands.command(brief="Gives admin-like control to a user.",
                      description="The user receives basically every permission that an admin has. "
                                  "Lasts for 5 minutes.",
                      hidden=True)
    @checks.has_funds(200)
    async def admin(self, ctx):
        if "Admin Lite" in [x.name for x in ctx.author.roles]:
            raise commands.CommandError(f"{ctx.author.mention} "
                                        f"You still have more time on your current admin privileges!")

        role = discord.utils.get(ctx.guild.roles, name="Admin Lite")

        await ctx.author.add_roles(role)

        await mysql.update_balance(ctx, ctx.author, -200)

        await asyncio.sleep(60*30)
        await ctx.author.remove_roles(role)

    @commands.command(hidden=True)
    async def give_me_money(self, ctx):
        await mysql.update_balance(ctx, ctx.author, 1000000)
        await ctx.send(f"moneys: {mysql.get_balance(ctx.author)}")

    @commands.command(brief="The Big Gay will now recognize you as a higher being.",
                      description="This privilege is permanent.", hidden=True)
    @checks.has_funds(1000)
    async def daddy(self, ctx):
        if "Daddy" in [x.name for x in ctx.author.roles]:
            raise commands.CommandError(f"{ctx.author.mention} You're already a daddy! What more do you want?")

        await mysql.update_balance(ctx, ctx.author, -1000)

        role = discord.utils.get(ctx.guild.roles, name="Daddy")
        await ctx.author.add_roles(role)
        await ctx.send(f"{ctx.author.mention} Congratulations daddy! ;)")


async def setup(bot):
    await bot.add_cog(Shop(bot))

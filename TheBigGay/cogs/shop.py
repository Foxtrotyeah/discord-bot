import discord
from discord.ext import commands
import asyncio

from .utils import mysql
from .utils import checks


class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.content.startswith('.'):
            return

        if str(message.channel.type) == "private":
            guilds = message.author.mutual_guilds
            for guild in guilds:
                member = discord.utils.get(guild.members, name=message.author.name)
                roles = [x.name for x in member.roles]
                if "Banished" not in roles:
                    continue

                if "please" not in message.content.lower():
                    return await message.channel.send("What's the magic word?")
                elif "daddy" not in message.content.lower():
                    return await message.channel.send("That's 'daddy' to you.")
                else:
                    role = discord.utils.get(guild.roles, name="Banished")
                    await member.remove_roles(role)
                    return await message.channel.send("Good boy. You can reconnect to voice channels now!")

    @commands.command(brief="Deafens a user.", description="Deafens a user for 60 seconds.", hidden=True)
    async def mute(self, ctx: commands.Context, user: discord.Member = None):
        checks.is_valid_bet(ctx.author, 50)
        
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
    async def boot(self, ctx: commands.Context, member: discord.Member = None):    
        checks.is_valid_bet(ctx.author, 100)

        await mysql.update_balance(ctx, ctx.author, -100)

        role = discord.utils.get(ctx.guild.roles, name="Banished")
        await member.add_roles(role)
        try:
            await member.move_to(None)
        except Exception as e:
            print(e)

        await ctx.send(f"{member.mention} Begone, THOT! Check your DM's to get your privileges back 😉")

        await member.send("Looks like you got put in time out. If you want back in, you'd better beg for daddy.")

    @commands.command(brief="Gives admin-like control to a user.",
                      description="The user receives basically every permission that an admin has. "
                                  "Lasts for 5 minutes.",
                      hidden=True)
    async def admin(self, ctx: commands.Context):
        if "Admin Lite" in [x.name for x in ctx.author.roles]:
            return await ctx.send(
                f"{ctx.author.mention} You still have more time on your current admin privileges!"
            )

        checks.is_valid_bet(ctx.author, 200)
        
        role = discord.utils.get(ctx.guild.roles, name="Admin Lite")

        await ctx.author.add_roles(role)

        await mysql.update_balance(ctx, ctx.author, -200)

        await asyncio.sleep(60*30)
        await ctx.author.remove_roles(role)

    @commands.command(brief="The Big Gay will now recognize you as a higher being.",
                      description="This privilege is permanent.", hidden=True)
    async def daddy(self, ctx: commands.Context):
        if "Daddy" in [x.name for x in ctx.author.roles]:
            return await ctx.send(f"{ctx.author.mention} You're already a daddy! What more do you want?")

        checks.is_valid_bet(ctx.author, 1000)
        
        await mysql.update_balance(ctx, ctx.author, -1000)

        role = discord.utils.get(ctx.guild.roles, name="Daddy")
        await ctx.author.add_roles(role)
        await ctx.send(f"{ctx.author.mention} Congratulations daddy! ;)")


async def setup(bot):
    await bot.add_cog(Shop(bot))

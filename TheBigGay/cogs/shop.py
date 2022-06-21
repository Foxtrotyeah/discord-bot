import discord
from discord.ext import commands
import asyncio

from .utils import mysql
from .utils import checks


class Shop(commands.Cog, command_attrs=dict(hidden=True)):
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

    @commands.command(brief="The gaybuck shop.",
                      description="View and purchase options with your available gaybuck funds.", hidden=False)
    async def shop(self, ctx: commands.Context):
        message = "__You can purchase any of the following commands:__"

        embed = discord.Embed(title="Shop", description=message, color=discord.Color.dark_gold())

        description = str()

        for command in self.get_commands():
            if command.name == "shop":
                continue

            if command.name in ('admin', 'daddy'):
                description += f"**{command.name}** - {command.description}\n\n"
            
            else:
                description += f"**{command.name} <user>** - {command.description}\n\n"


        embed.add_field(name="\u200b", value=description, inline=False)

        await ctx.send(embed=embed)

    @commands.command(description="*75 gb*: Mutes a user for 60 seconds.")
    async def mute(self, ctx: commands.Context, member: discord.Member):
        checks.is_valid_bet(ctx, ctx.author, 50)
        
        mysql.update_balance(ctx.author, -50)

        role = discord.utils.get(ctx.guild.roles, name="Bitch")
        await member.add_roles(role)
        try:
            await member.edit(mute=True)
        except Exception as e:
            print(e)

        await ctx.send(f"{member.mention} Shush.")

        await asyncio.sleep(60)

        await member.remove_roles(role)
        try:
            await member.edit(mute=False)
        except Exception as e:
            print(e)

    @commands.command(description="*100 gb*: Force a user to disconnect until they message The Big Gay.")
    async def boot(self, ctx: commands.Context, member: discord.Member):    
        checks.is_valid_bet(ctx, ctx.author, 100)

        mysql.update_balance(ctx.author, -100)

        role = discord.utils.get(ctx.guild.roles, name="Banished")
        await member.add_roles(role)
        try:
            await member.move_to(None)
        except Exception as e:
            print(e)

        await ctx.send(f"{member.mention} Begone, THOT! Check your DM's to get your privileges back 😉")

        await member.send("Looks like you got put in time out. If you want back in, you'd better beg for daddy.")

    @commands.command(description="*300 gb*: Receive admin privileges for 30 minutes.")
    async def admin(self, ctx: commands.Context):
        if "Admin Lite" in [x.name for x in ctx.author.roles]:
            return await ctx.send(
                f"{ctx.author.mention} You still have more time on your current admin privileges!"
            )

        checks.is_valid_bet(ctx, ctx.author, 200)
        
        role = discord.utils.get(ctx.guild.roles, name="Admin Lite")

        await ctx.author.add_roles(role)

        mysql.update_balance(ctx.author, -200)

        await asyncio.sleep(60*30)
        await ctx.author.remove_roles(role)

    @commands.command(description="*1000 gb*: Lay a trap for someone upon joining voice chat.")
    async def trap(self, ctx: commands.Context, *, username: str):    
        checks.is_valid_bet(ctx, ctx.author, 1000)

        member = discord.utils.find(lambda m: m.name.lower() == username.lower(), ctx.guild.members)
        if not member:
            await ctx.send(f"{ctx.author.mention} I couldn't find user \"{username}\". Try copy-pasting the exact name from their profile (don't @). Deleting...", delete_after=5)
            await asyncio.sleep(5)
            await ctx.message.delete()
            return

        mysql.update_balance(ctx.author, -1000)

        role = discord.utils.get(ctx.guild.roles, name="Windows")
        await member.add_roles(role)

        await ctx.send(f"{ctx.author.mention} Trap is set! Deleting the evidence now...", delete_after=5)
        await asyncio.sleep(5)
        await ctx.message.delete()

    # 'Daddy' title is no longer able to be bought. Role is still available to those that bought it previously.
    # @commands.command(description="*2000 gb*: Receive the permanent title of 'Daddy'.")
    # async def daddy(self, ctx: commands.Context):
    #     if "Daddy" in [x.name for x in ctx.author.roles]:
    #         return await ctx.send(f"{ctx.author.mention} You're already a daddy! What more do you want?")

    #     checks.is_valid_bet(ctx.author, 1000)
        
    #     mysql.update_balance(ctx.author, -1000)

    #     role = discord.utils.get(ctx.guild.roles, name="Daddy")
    #     await ctx.author.add_roles(role)
    #     await ctx.send(f"{ctx.author.mention} Congratulations daddy! ;)")

    @commands.command(description="*10,000 gb*: Receive the permanent title of 'Mommy'.")
    async def mommy(self, ctx: commands.Context):
        if "Mommy" in [x.name for x in ctx.author.roles]:
            return await ctx.send(f"{ctx.author.mention} You're already a mommy! What more do you want?")

        checks.is_valid_bet(ctx, ctx.author, 10000)
        
        mysql.update_balance(ctx.author, -10000)

        role = discord.utils.get(ctx.guild.roles, name="Mommy")
        await ctx.author.add_roles(role)
        await ctx.send(f"{ctx.author.mention} Congratulations... uh, mommy! ;)")


async def setup(bot):
    await bot.add_cog(Shop(bot))

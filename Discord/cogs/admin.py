import discord
from discord.ext import commands
import asyncio
from Discord.cogs.economy import *


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(breif="Adds a role to a user.", description="Adds a role to a user. Admin permission required.",
                      hidden=True)
    @commands.has_permissions(administrator=True)
    async def addrole(self, ctx, role, user: discord.Member = None):
        if not user or user.bot:
            return

        roles = [x.name.lower() for x in await ctx.guild.fetch_roles()]
        if role.lower() not in roles:
            return await ctx.send(f"{role} is not a role on this server.")

        await user.add_roles(role)
        await ctx.send(f"Successfully added the '{role}' role to {user.mention}")

    @commands.command(brief="Removes a role from a user",
                      description="Removes a role from a user. Admin permission required.", hidden=True)
    @commands.has_permissions(administrator=True)
    async def removerole(self, ctx, role, user: discord.Member = None):
        if not user or not role:
            return
        roles = [x.name.lower() for x in user.roles]
        if role.lower() not in roles:
            return await ctx.send(f"{user.mention} does not have the '{role}' role.")

        remove = user.roles[roles.index(role)]
        await user.remove_roles(remove)
        await ctx.send(f"Successfully removed the '{role}' role from {user.mention}")

    @commands.command(brief="Clears messages.", description="Clears the number of messages specified.", hidden=True)
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount=5):
        deleted = await ctx.channel.purge(limit=amount)
        await ctx.channel.send("Deleted {} message(s)".format(len(deleted)))

    @commands.command(brief="Deafens a user.", description="Deafens a user for 60 seconds.", hidden=True)
    async def mute(self, ctx, user: discord.Member = None):
        if not user:
            raise commands.CommandError(f"{ctx.author.mention} Try `.help` + `[the function name]` "
                                        f"to get more info on how to use this command.")
        check_funds(ctx, 50)
        await update_bal(ctx, ctx.author, ctx.author.guild, amt=-50)

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

    @commands.command(hidden=True)
    async def boot(self, ctx, user: discord.Member = None):
        if not user:
            raise commands.CommandError(f"{ctx.author.mention} Try `.help` + `[the function name]` "
                                        f"to get more info on how to use this command.")
        check_funds(ctx, 100)
        await update_bal(ctx, ctx.author, ctx.author.guild, amt=-100)

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
    async def admin(self, ctx):
        if "Admin Lite" in [x.name for x in ctx.author.roles]:
            raise commands.CommandError(f"{ctx.author.mention} "
                                        f"You still have more time on your current admin privileges!")
        check_funds(ctx, 200)
        await update_bal(ctx, ctx.author, ctx.author.guild, amt=-200)

        role = discord.utils.get(ctx.guild.roles, name="Admin Lite")
        await ctx.author.add_roles(role)
        await asyncio.sleep(60*30)
        await ctx.author.remove_roles(role)

    @commands.command(brief="The Big Gay will now recognize you as a higher being.",
                      description="This privilege is permanent.", hidden=True)
    async def daddy(self, ctx):
        if "Daddy" in [x.name for x in ctx.author.roles]:
            raise commands.CommandError(f"{ctx.author.mention} You're already a daddy! What more do you want?")
        check_funds(ctx, 1000)
        await update_bal(ctx, ctx.author, ctx.author.guild, amt=-1000)

        role = discord.utils.get(ctx.guild.roles, name="Daddy")
        await ctx.author.add_roles(role)
        await ctx.send(f"{ctx.author.mention} Congratulations daddy! ;)")


def setup(bot):
    bot.add_cog(Admin(bot))

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select, UserSelect
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

    @app_commands.command(description="The gaybucks shop")
    async def shop(self, interaction: discord.Interaction):
        options = {
            "mute": (discord.SelectOption(
                label="Mute",
                emoji="🔇",
                description="*75 gb*: Mutes a user for 60 seconds",
                value="mute"
            ), 75, self.mute),
            "boot": (discord.SelectOption(
                label="Boot",
                emoji="🥾",
                description="*100 gb*: Kick a user",
                value="boot"
            ), 100, self.boot),
            "admin": (discord.SelectOption(
                label="Admin",
                emoji="🛡️",
                description="*300 gb*: Receive admin privileges for 30 minutes",
                value="admin"
            ), 300, self.admin),
            "trap": (discord.SelectOption(
                label="Trap",
                emoji="❗",
                description="*1000 gb*: Lay a trap for someone upon joining voice chat",
                value="trap"
            ), 1000, self.trap),
            "step_bro": (discord.SelectOption(
                label="Step Bro",
                emoji="👨‍👦",
                description="*10,000 gb*: Receive the permanent title of 'Step Bro'",
                value="step_bro"
            ), 10000, self.step_bro)
        }

        view = View()
        select = Select(
            min_values=0,
            max_values=1,
            placeholder="View shop items",
            options=[x[0] for x in options.values()]
        )

        async def callback(interaction: discord.Interaction):
            value = select.values[0]
            option = options[value]

            # Lock select value to the item they chose
            option[0].default = True
            view.children[0].disabled = True

            # Check if they can affor this option
            if mysql.get_wallet(interaction.user)[0] < option[1]:
                await interaction.response.edit_message(view=view)
                return await interaction.followup.send("Yeah? With what money?", ephemeral=True)

            if value in ("mute", "boot", "trap"):
                user_select = UserSelect(
                    min_values=0,
                    max_values=1,
                    placeholder=f"Select a user to {value}"
                )
                
                async def user_callback(interaction: discord.Interaction):
                    member = user_select.values[0]

                    if member.bot:
                        return await interaction.response.send_message("...wanna try that again?", ephemeral=True)

                    # Disable user_select
                    view.children[1].disabled = True
                    await interaction.response.edit_message(view=view)

                    await option[2](interaction, member)

                user_select.callback = user_callback

                view.add_item(user_select)

                await interaction.response.edit_message(view=view)

            elif value in ("admin", "step_bro"):
                await interaction.response.edit_message(view=view)
                await option[2](interaction)

        select.callback = callback

        view.add_item(select)

        await interaction.response.send_message(view=view, ephemeral=True)

    async def mute(self, interaction: discord.Interaction, member: discord.Member):        
        mysql.update_balance(interaction.user, -75)

        role = discord.utils.get(interaction.guild.roles, name="Bitch")
        await member.add_roles(role)
        try:
            await member.edit(mute=True)
        except discord.errors.HTTPException:
            pass
        except Exception as e:
            print(e)

        await interaction.followup.send(f"{member.mention} Shush.")

        await asyncio.sleep(60)

        await member.remove_roles(role)
        try:
            await member.edit(mute=False)
        except discord.errors.HTTPException:
            pass
        except Exception as e:
            print(e)

    async def boot(self, interaction: discord.Interaction, member: discord.Member):    
        mysql.update_balance(interaction.user, -100)

        role = discord.utils.get(interaction.guild.roles, name="Banished")
        await member.add_roles(role)
        try:
            await member.move_to(None)
        except Exception as e:
            print(e)

        await interaction.followup.send(f"{member.mention} Begone, THOT! Check your DMs to get your privileges back 😉")

        await member.send("Looks like you got put in time out. If you want back in, you'd better beg for daddy.")

    async def admin(self, interaction: discord.Interaction):
        member = interaction.user

        if "Admin Lite" in [x.name for x in member.roles]:
            return await interaction.followup.send(
                "You still have more time on your current admin privileges!",
                ephemeral=True
            )
        
        mysql.update_balance(member, -300)
        
        role = discord.utils.get(interaction.guild.roles, name="Admin Lite")
        await member.add_roles(role)

        await interaction.followup.send("Enjoy being admin. Watch out, everybody!")

        await asyncio.sleep(60*30)
        await member.remove_roles(role)

    async def trap(self, interaction: discord.Interaction, member: discord.Member):    
        mysql.update_balance(interaction.user, -1000)

        role = discord.utils.get(interaction.guild.roles, name="Windows")
        await member.add_roles(role)

        await interaction.followup.send(f"Trap for {member.mention} is set!", ephemeral=True)

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

    # async def mommy(self, ctx: commands.Context):
    #     if "Mommy" in [x.name for x in ctx.author.roles]:
    #         return await ctx.send(f"{ctx.author.mention} You're already a mommy! What more do you want?")

    #     checks.is_valid_bet(ctx, ctx.author, 10000)
        
    #     mysql.update_balance(ctx.author, -10000)

    #     role = discord.utils.get(ctx.guild.roles, name="Mommy")
    #     await ctx.author.add_roles(role)
    #     await ctx.send(f"{ctx.author.mention} Congratulations... uh, mommy! ;)")

    async def step_bro(self, interaction: discord.Interaction):
        member = interaction.user
        if "Step Bro" in [x.name for x in member.roles]:
            return await interaction.followup.send("You're already a Step Bro! What more do you want?", ephemeral=True)
        
        mysql.update_balance(member, -10000)

        role = discord.utils.get(interaction.guild.roles, name="Step Bro")
        await member.add_roles(role)
        await interaction.followup.send("Welcome to the family, Step Bro! ;)")


async def setup(bot):
    await bot.add_cog(Shop(bot))

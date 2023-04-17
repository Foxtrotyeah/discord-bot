import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select, UserSelect, Button
import asyncio
from numpy.random import choice
from pyfiglet import Figlet

from .utils import mysql, checks


figlet = Figlet(font='slant')


class Shop(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
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
            ), 10000, self.step_bro),
            "private_room": (discord.SelectOption(
                label="Private Room",
                emoji="🔒",
                description="*(Step Bro only) 500 gb*: Get your own private betting thread",
                value="private_room"
            ), 50000, self.private_room)
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

            # Check if they can afford this option
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

            elif value in ("admin", "step_bro", "private_room"):
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

        await interaction.followup.send(f"{member.mention} Shush. {interaction.user.mention} says you were talking too much.")

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

        await interaction.followup.send(f"{member.mention} Begone, THOT! {interaction.user.mention} has booted you. Check your DMs to get your privileges back 😉")

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

        await interaction.followup.send(f"Enjoy being admin, {member.mention}. Watch out, everybody!")

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
        await interaction.followup.send(f"{interaction.user.mention} Welcome to the family, Step Bro! ;)")

    async def private_room(self, interaction: discord.Interaction):
        member = interaction.user
        channel = discord.utils.get(interaction.guild.channels, name="main-hall")

        if "Step Bro" not in [role.name for role in member.roles]:
            return await interaction.followup.send("Private rooms are only for my Step Bros.", ephemeral=True)
        elif f"{member.name}'s Room" in [thread.name for thread in interaction.guild.threads]:
            thread = discord.utils.get(interaction.guild.threads, name=f"{member.name}'s Room")
            return await interaction.followup.send(f"You already have a private room open: {thread.mention}", ephemeral=True)
        
        mysql.update_balance(member, -500)
        
        thread = await channel.create_thread(name=f"{member.name}'s Room", auto_archive_duration=10080)
        await thread.leave()
        await thread.add_user(member)
        await interaction.followup.send(f"Enjoy your private gambling experience! Here is your room: {thread.mention}", ephemeral=True)

    @app_commands.command(description="Buy a crate to open")
    @app_commands.describe(crate_type="the type of crate to purchase")
    @app_commands.rename(crate_type='type')
    @app_commands.choices(crate_type=[
        app_commands.Choice(name='Standard - 500GB', value=0),
        app_commands.Choice(name='Epic - 1000GB', value=1),
        app_commands.Choice(name='Elite - 2500GB', value=2)
    ])
    async def crate(self, interaction: discord.Interaction, crate_type: app_commands.Choice[int]):
        crate = [
            (500, [100, 300, 500, 750, 1000, 2000], [0.1, 0.55, 0.1, 0.1, 0.1, 0.05], 'standard.png'),
            (1000, [200, 400, 1000, 1500, 2000, 5000], [0.1, 0.5, 0.1, 0.15, 0.1, 0.05], 'epic.png'),
            (2500, [250, 500, 1000, 2500, 3750, 5000, 7500, 10000], [0.05, 0.1, 0.45, 0.1, 0.1, 0.1, 0.05, 0.05], 'elite.png'),
        ][crate_type.value]

        member = interaction.user

        mysql.update_balance(member, -crate[0])

        crate_name = crate_type.name.split(' - ')[0]

        embed = discord.Embed(title=f'{crate_name} Crate', color=discord.Color.gold())
        embed.set_footer(text=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)

        attachment = discord.File(f'./assets/chests/{crate[3]}', filename=f'{crate[3]}')
        embed.set_thumbnail(url=f'attachment://{crate[3]}')

        view = checks.ExclusiveView(member)
        button = Button(style=discord.ButtonStyle.green, label='Open')

        async def callback(interaction: discord.Interaction):
            value = choice(crate[1], p=crate[2])

            balance = mysql.update_balance(interaction.user, int(value))

            embed.description = f"`{figlet.renderText('{:,}'.format(value))}`"
            embed.add_field(name="Balance", value=f"You now have {balance} gaybucks", inline=False)
            await interaction.response.edit_message(embed=embed, view=None)

        button.callback = callback
        view.add_item(button)

        await interaction.response.send_message(file=attachment, embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Shop(bot))

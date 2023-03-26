import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Modal, Button, View, TextInput
import random
from datetime import datetime
import pytz
import json

from .utils import papago


class Miscellaneous(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Clears messages")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(amount="the number of messages to delete")
    async def purge(self, interaction: discord.Interaction, amount: int = 5):
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.response.send_message("Deleted {} message(s)".format(len(deleted)))

    @app_commands.command(description="Gives the latency between the bot and server in ms")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Pong! My latency right now is {round(self.bot.latency * 1000)}ms")

    @app_commands.command(description="Says hi, but gayer")
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"{interaction.user.mention} Heyyy ;)")

    @app_commands.command(description="Roast a user with a preset insult from The Big Gay")
    @app_commands.describe(member="the member to roast")
    async def roast(self, interaction: discord.Interaction, member: discord.Member):
        if member.bot:
            return await interaction.response.send_message(f"{interaction.user.mention} No one roasts me, twat.")

        with open("./assets/text.json", encoding="utf8", errors="ignore") as file:
            selected = random.choice(json.load(file)["roasts"]).format(member.mention)
        await interaction.response.send_message(selected)

    @app_commands.command(description="Pastes a hot emojipasta.")
    async def emojipasta(self, interaction: discord.Interaction):
        with open("./assets/text.json", encoding="utf8", errors="ignore") as file:
            selected = random.choice(json.load(file)["emojipastas"])
        await interaction.response.send_message(selected)

    @app_commands.command(description="Vibecheck a user or the whole server.")
    @app_commands.describe(member="the member to vibecheck")
    async def vibecheck(self, interaction: discord.Interaction, member: discord.Member = None):
        if member:
            if member.bot:
                return await interaction.response.send_message("Bitch, I'm always fabulous.")
            if member.status == discord.Status.offline:
                return await interaction.response.send_message(f"I can't read minds if they aren't on online. "
                                      f"I'm sure {member.mention} is doing fine!")
            vibe = random.randint(0, 100)
            message = "{} Vibe levels at {}%.".format(member.mention, vibe)
            if vibe < 15:
                message += "..You good?? 🥴"
            elif 15 <= vibe < 40:
                message += " Get your shit together 😬"
            elif 40 <= vibe < 60:
                message += " Doing alright 😳"
            elif 60 <= vibe < 85:
                if vibe == 69:
                    message += " Nice."
                else:
                    message += " Eyy not bad 😏"
            elif 85 <= vibe:
                message += " BIG CHILLING right now 😎"

            await interaction.response.send_message(message)
        else:
            user_list = [x for x in interaction.guild.members if x.status != discord.Status.offline]
            user_list = [x for x in user_list if not x.bot]
            
            if len(user_list) < 1:
                return await interaction.response.send_message("Apparently nobody's online. Awkward.")
            
            rand_user = random.choice(user_list)
            vibes = [
                "{} is salty as hell, watch out 👀".format(rand_user.mention),
                "{} is on one right now 🔥".format(rand_user.mention)
            ]
            vibe = random.choice(vibes)
            await interaction.response.send_message(vibe)

    @app_commands.command(description="A 50/50 virtual coin toss.")
    async def coinflip(self, interaction: discord.Interaction):
        coin = ["Heads!", "Tails!"]
        await interaction.response.send_message(random.choice(coin))

    @app_commands.command(description="I will make a decision for you")
    @app_commands.describe(inputs="separate each choice by a **comma**")
    async def choose(self, interaction: discord.Interaction, *, inputs: str):
        choices = str(inputs).split(", ")
        return await interaction.response.send_message(f"{interaction.user.mention} I choose **{random.choice(choices)}**!")

    @app_commands.command(description="The bot's local time")
    async def time(self, interaction: discord.Interaction):
        timezone = pytz.timezone("US/Mountain")
        await interaction.response.send_message("MST time: {}".format(datetime.now(timezone)))

    @app_commands.command(description="Send the owner an anonymous request or bug report.")
    async def request(self, interaction: discord.Interaction):
        user = interaction.user
        me = discord.utils.get(interaction.guild.members, id=403969156510121987)

        modal = Modal(title="Request")
        textinput = TextInput(label="Type your message here", style=discord.TextStyle.long)
        modal.add_item(textinput)

        async def on_submit(interaction: discord.Interaction):
            await me.send(f'New request from {user.mention}: "{textinput.value}"')
            await interaction.response.send_message("Thank you for your contribution to The Big Gay agenda.")

        modal.on_submit = on_submit
    
        await interaction.response.send_modal(modal)

    # TODO move this to a context menu, maybe keep as a command...
    @commands.command(description="Translate using Papago")
    async def translate(self, ctx: commands.Context, *, text: str):
        translation, language = papago.translate(text)

        await ctx.send(f'Translated from **{language}**: "{translation}"')

    @app_commands.command(description="Test function")
    @app_commands.describe(text="test text")
    @app_commands.default_permissions(administrator=True)
    async def test(self, interaction: discord.Interaction, text: str):
        button = Button(label="Click me!", style=discord.ButtonStyle.green, emoji="❗")
        textinput = TextInput(label="Type here", style=discord.TextStyle.short)
        modal = Modal(title="Choose")
        modal.add_item(textinput)
        await interaction.response.send_modal(modal)

    @app_commands.command(description="Sync command tree")
    @app_commands.default_permissions(administrator=True)
    async def sync(self, interaction: discord.Interaction):
        await self.bot.tree.sync()
        await interaction.response.send_message("Synced", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Miscellaneous(bot))

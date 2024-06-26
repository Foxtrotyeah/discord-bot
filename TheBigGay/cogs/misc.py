import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Modal, TextInput
import random
from datetime import datetime
import pytz
import json

from .utils import papago


class Miscellaneous(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Bans a member")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.describe(member="the member to ban", reason="the reason for being banned")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        if member.bot:
            return await interaction.response.send_message("Well this is awkward... can we talk about it?", ephemeral=True)
        
        await member.ban(reason=reason)

        embed = discord.Embed(title="Bitch, Bye", description=f"{member.mention} *has been banned*", color=discord.Color.red())
        if reason:
            embed.add_field(name="Reason", value=reason, inline=False)

        attachment = discord.File('./assets/werk.gif', filename='werk.gif')
        embed.set_thumbnail(url=f'attachment://werk.gif')

        await interaction.response.send_message(embed=embed, file=attachment)
    
    @app_commands.command(description="Clears messages")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(amount="the number of messages to delete")
    async def purge(self, interaction: discord.Interaction, amount: int = 5):
        await interaction.response.defer(thinking=True)

        deleted = await interaction.channel.purge(limit=amount, before=interaction.created_at)
        await interaction.followup.send("Deleted {} message(s)".format(len(deleted)))

    @app_commands.command(description="Gives the latency between the bot and server in ms")
    @app_commands.default_permissions(administrator=True)
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Pong! My latency right now is {round(self.bot.latency * 1000)}ms")

    @app_commands.command(description="Gives the latency between the bot and server in ms")
    @app_commands.default_permissions(administrator=True)
    async def version(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Current agenda: {self.bot.version}")

    @app_commands.command(description="Says hi, but gayer")
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message("Heyyy ;)")

    @app_commands.command(description="Roast a user with a preset insult from The Big Gay")
    @app_commands.describe(member="the member to roast")
    async def roast(self, interaction: discord.Interaction, member: discord.Member):
        if member.bot:
            return await interaction.response.send_message("No one roasts me, twat.", ephemeral=True)

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
            # App commands don't get the same member objects as normal commands...
            member = interaction.guild.get_member(member.id)
            if member.bot:
                return await interaction.response.send_message("Bitch, I'm always fabulous.", ephemeral=True)
            if member.status == discord.Status.offline:
                return await interaction.response.send_message(f"I can't read minds if they aren't on online. "
                                      f"I'm sure {member.mention} is doing fine!", ephemeral=True)
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
    @app_commands.describe(inputs="your choices *separated by a comma*")
    async def choose(self, interaction: discord.Interaction, *, inputs: str):
        choices = str(inputs).split(",")
        return await interaction.response.send_message(f"I choose **{random.choice(choices).strip()}**!")

    @app_commands.command(description="The bot's local time")
    @app_commands.default_permissions(administrator=True)
    async def time(self, interaction: discord.Interaction):
        timezone = pytz.timezone("US/Mountain")
        await interaction.response.send_message("Current time: {} MST".format(datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")))

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

    @app_commands.command(description="Translate using Papago")
    async def translate(self, interaction: discord.Interaction, *, text: str):
        translation, language = papago.translate(text)

        description = f"Original text: *{text}*"
        embed = discord.Embed(title="Translation", description=description, color=discord.Color.blue())
        embed.add_field(name="Detected language", value=language, inline=False)
        embed.add_field(name="Translated to English", value=translation, inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(description="Pick a random Overwatch 2 hero")
    @app_commands.describe(role="Specify what role(s) to randomize")
    @app_commands.choices(role=[
        app_commands.Choice(name='Tank', value=0),
        app_commands.Choice(name='Damage', value=1),
        app_commands.Choice(name='Support', value=2),
        app_commands.Choice(name='Team', value=3)
    ])
    async def randomhero(self, interaction:discord.Interaction, role:app_commands.Choice[int] = None):
        with open("./assets/text.json", encoding="utf8", errors="ignore") as file:
            all_heroes = json.load(file)["overwatch_heroes"]
            if role:
                if role.value == 3:
                    tank = random.choice(all_heroes["tank"])
                    damage = random.sample(all_heroes["damage"], 2)
                    support = random.sample(all_heroes["support"], 2)

                    message = f"Your random Overwatch team:\n" \
                        f"**{tank}** | **{damage[0]}** | **{damage[1]}** | " \
                        f"**{support[0]}** | **{support[1]}**"
                else:
                    hero = random.choice(all_heroes[role.name.lower()])
                    message = f"Your random Overwatch hero: **{hero}**"
            else:
                hero = random.choice(random.choice(list(all_heroes.values())))
                message = f"Your random Overwatch hero: **{hero}**"
                
        await interaction.response.send_message(message)

    @app_commands.command(description="Sync command tree")
    @app_commands.default_permissions(administrator=True)
    async def sync(self, interaction: discord.Interaction):
        await self.bot.tree.sync()
        await interaction.response.send_message("Synced", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Miscellaneous(bot))

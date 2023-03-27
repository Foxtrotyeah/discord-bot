import discord
from discord import app_commands
from discord.ext import commands
import asyncio

from .utils.audio import play

from typing import List


class Poll:
    reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    voting = ["👍", "👎"]
    active_polls = []

    def __init__(self, interaction: discord.Interaction, title: str, description: str, inputs: List[str] = None):
        self.interaction = interaction
        self.title = title
        self.description = description

        self.inputs = inputs

        self.response = None
        self.embed = None
        self.closed = False

    async def send(self) -> str:
        Poll.active_polls.append(self)

        embed = discord.Embed(title=self.title, description=self.description, color=discord.Color.blue())
        await self.interaction.response.send_message(embed=embed)
        self.response = await self.interaction.original_response()

        if self.inputs:
            for i in range(len(self.inputs)):
                await self.response.add_reaction(Poll.reactions[i])
        else:
            for i in Poll.voting:
                await self.response.add_reaction(i)

        for i in range(60):
            if self.closed:
                return await self.close()
            if i == 44:
                embed.description += f"\n\n Poll closing in 15 seconds..."
                await self.interaction.edit_original_response(embed=embed)
            await asyncio.sleep(1)

        return await self.close()

    async def close(self) -> str:
        Poll.active_polls.remove(self)
        self.closed = True

        cached_msg = await self.interaction.channel.fetch_message(self.response.id)

        results = {react.emoji: react.count - 1 for react in cached_msg.reactions}
        final = sorted(results.items(), key=lambda x: x[1], reverse=True)
        total = sum(final[x][1] for x in range(len(final)))

        await self.response.clear_reactions()

        if total == 0:
            return await self.interaction.edit_original_response(content="Poll closed. No one voted!")
        elif self.inputs:
            description = ""
            for key, value in final:
                description += "**{}**: {} vote(s) [{:.4}%]\n".format(self.inputs[Poll.reactions.index(key)], value,
                                                                  value / total * 100)
                
            self.embed = discord.Embed(title="Poll Results", description=description[:-1], color=discord.Color.blue())

        if final[0][1] > final[1][1]:
            result = final[0][0]
        else:
            result = "Tie"
        return result
        

class Polls(commands.Cog):
    current_poll = []

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Vote on a list of entries")
    @app_commands.describe(inputs="your poll entries *separated by a comma*")
    async def poll(self, interaction: discord.Interaction, *, inputs: str):
        description = str()
        choices = str(inputs).split(", ")

        i = 0
        for choice in choices:
            if i > 0:
                description += "\n\n"
            description += "{}: **{}**".format(Poll.reactions[i], choice)
            i += 1

        reg_poll = Poll(interaction, "Poll", description, inputs=choices)
        await reg_poll.send()
        await interaction.edit_original_response(embed=reg_poll.embed)


    @app_commands.command(description="Vote on if a user is bitching too much")
    @app_commands.describe(member="the member to accuse")
    async def bitchalert(self, interaction: discord.Interaction, member: discord.Member):
        # App commands don't get the same member objects as normal commands...
        member = interaction.guild.get_member(member.id)

        if member.bot:
            return await interaction.response.send_message("Nice try, bitch.", ephemeral=True)
        if member.status == discord.Status.offline:
            return await interaction.response.send_message(f"Chill out! {member.mention} isn't even online.", ephemeral=True)

        description = f"Is {member.mention} being a little bitch?"
        bitch_poll = Poll(interaction, "Bitch Alert", description)
        result = await bitch_poll.send()

        if result == "👍":
            role = discord.utils.get(interaction.guild.roles, name="Bitch")
            await member.add_roles(role)
            try:
                await member.edit(mute=True)
            except discord.errors.HTTPException:
                pass
            except Exception as e:
                print("Error muting member for bitchalert: ", e)

            await interaction.edit_original_response(content=f"The people have spoken.\n{member.mention} Begone, THOT!", embed=None)

            await asyncio.sleep(60)

            await member.remove_roles(role)
            try:
                await member.edit(mute=False)
            except discord.errors.HTTPException:
                pass
            except Exception as e:
                print("Error unmuting member for bitchalert: ", e)

        else:
            await interaction.edit_original_response(content=f"{member.mention}, you just keep on bitching. All good here.", embed=None)

    # TODO Make a banish command for the shop that does this without the poll?
    # creates a poll for sending a user to a secondary channel, adding the 'banished' role
    @app_commands.command(description="Vote to send a user to The Shadow Realm")
    @app_commands.describe(member="the member to banish")
    async def banish(self, interaction: discord.Interaction, member: discord.Member = None):
        # App commands don't get the same member objects as normal commands...
        member = interaction.guild.get_member(member.id)
        if not hasattr(member.voice, "channel"):
            return await interaction.response.send_message(f"{member.mention} is not in a voice channel!", ephemeral=True)
        channel = member.voice.channel

        if member.bot:
            return await interaction.response.send_message("Nice try, bitch.")
        if member.status == discord.Status.offline:
            return await interaction.response.send_message(f"Chill out! {member.mention} isn't even online.", ephemeral=True)

        description = f"Send {member.mention} to the shadow realm?"
        banish_poll = Poll(interaction, "Banishment", description)
        result = await banish_poll.send()

        if result == "👍":
            role = discord.utils.get(interaction.guild.roles, name="Banished")
            await member.add_roles(role)

            category = await interaction.guild.create_category("The Shadow Realm")
            s_channel = await interaction.guild.create_voice_channel("Hell", category=category)

            embed = discord.Embed(title="Banishment", description=f"The people have spoken.\nLater, {member.mention}!", color=discord.Color.blue())

            await interaction.edit_original_response(embed=embed)

            # TODO use a soundboard clip for this?
            await play(interaction.client, name="shadow.mp3", channel=channel, wait=3)

            try:
                await member.move_to(s_channel)

                await play(interaction.client, name="hell.mp3", channel=s_channel, wait=60)

            except discord.errors.HTTPException:
                await asyncio.sleep(60)

            await member.remove_roles(role)
            await s_channel.delete()
            await category.delete()

        else:
            await interaction.edit_original_response(content="Not enough votes. Lucky you!", embed=None)

    @app_commands.command(description="Closes the most recent poll.")
    @app_commands.default_permissions(manage_messages=True)
    async def closepoll(self, interaction: discord.Interaction):
        if Poll.active_polls:
            Poll.active_polls[-1].closed = True
            return await interaction.response.send_message("Current poll closed.")
        else:
            return await interaction.response.send_message("There is no poll currently running!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Polls(bot))

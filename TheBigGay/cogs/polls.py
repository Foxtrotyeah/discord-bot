import discord
from discord.ext import commands
import asyncio

from typing import List


class Poll:
    reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    voting = ["👍", "👎"]
    current_poll = []

    def __init__(self, ctx: commands.Context, title: str, description: str, inputs: List[str] = None, yes_no: bool = False, bot=None):
        self.bot = bot
        self.ctx = ctx
        self.title = title
        self.description = description
        if inputs:
            self.inputs = inputs
        elif yes_no:
            self.yes_no = True
            self.result = None

        self.message = None
        self.closed = False

    async def send(self):
        Poll.current_poll.append(self)

        embed = discord.Embed(title=self.title, description=self.description, color=discord.Color.blue())
        message = await self.ctx.send(embed=embed)
        self.message = message

        if hasattr(self, "inputs"):
            for i in range(len(self.inputs)):
                await self.message.add_reaction(Poll.reactions[i])
        elif self.yes_no:
            for i in Poll.voting:
                await self.message.add_reaction(i)

        for i in range(60):
            if self.closed:
                return
            await asyncio.sleep(1)
            if i == 45:
                await self.ctx.send(f"{self.title} closing in 15 seconds...")
        await self.close()

    async def close(self):
        Poll.current_poll.remove(self)

        self.closed = True

        cache_msg = discord.utils.get(self.bot.cached_messages, id=self.message.id)
        results = {react.emoji: react.count - 1 for react in cache_msg.reactions}
        final = sorted(results.items(), key=lambda x: x[1], reverse=True)
        total = sum(final[x][1] for x in range(len(final)))

        if total == 0:
            await self.ctx.send("Poll closed. No one voted!")
        elif hasattr(self, "yes_no"):
            if final[0][1] > final[1][1]:
                self.result = final[0][0]
            else:
                self.result = "Tie"
        else:
            message = "Results are in!"
            for key, value in final:
                message += "\n**{}**: {} vote(s) [{:.3}%]".format(self.inputs[Poll.reactions.index(key)], value,
                                                                  value / total * 100)
            await self.ctx.send(message)


class Polls(commands.Cog):
    current_poll = []

    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief="Vote on a list of entries.",
                      description="Give The Big Gay a list of entries separated by a comma, and then vote.")
    async def poll(self, ctx: commands.Context, *, inputs: str):
        description = str()
        choices = str(inputs).split(", ")

        i = 0
        for choice in choices:
            if i > 0:
                description += "\n\n"
            description += "{}: **{}**".format(Poll.reactions[i], choice)
            i += 1

        reg_poll = Poll(ctx, "Poll", description, inputs=choices, bot=self.bot)
        await reg_poll.send()

    @commands.command(brief="Vote on if a user is bitching too much",
                      description="If found guilty, the user caught bitching will be muted for 60 seconds.")
    async def bitchalert(self, ctx: commands.Context, member: discord.Member = None):
        if member.bot:
            return await ctx.send(f"{ctx.author.mention} Nice try bitch.")
        if member.status == discord.Status.offline:
            return await ctx.send(f"Chill out! {member.mention} isn't even online.")

        description = f"Is {member.mention} being a little bitch?"
        bitch_poll = Poll(ctx, "Bitch Alert", description, yes_no=True, bot=self.bot)
        await bitch_poll.send()

        if bitch_poll.result == "👍":
            role = discord.utils.get(ctx.guild.roles, name="Bitch")
            await member.add_roles(role)
            try:
                await member.edit(mute=True)
            except Exception as e:
                print(e)

            await ctx.send(f"{member.mention} Begone, THOT!")

            await asyncio.sleep(60)

            await member.remove_roles(role)
            try:
                await member.edit(mute=False)
            except Exception as e:
                print(e)

        elif bitch_poll.result is None:
            return

        else:
            await ctx.send(f"{member.mention}, you just keep on bitching. All good here.")

    # creates a poll for sending a user to a secondary channel, adding the 'banished' role
    @commands.command(brief="Vote to send a user to The Shadow Realm",
                      description="If the vote passes, the user is banished and cannot come back to the main channels, "
                                  "and must remain in purgatory for 60 seconds.")
    async def banish(self, ctx: commands.Context, member: discord.Member = None):
        if not hasattr(member.voice, "channel"):
            return await ctx.send(f"{member.mention} is not in a voice channel!")
        if member.bot:
            return await ctx.send(f"{ctx.author.mention} Nice try, bitch.")
        if member.status == discord.Status.offline:
            return await ctx.send(f"Chill out! {member.mention} isn't even online.")

        description = f"Send {member.mention} to the shadow realm?"
        banish_poll = Poll(ctx, "Banishment", description, yes_no=True, bot=self.bot)
        await banish_poll.send()

        if banish_poll.result == "👍":
            role = discord.utils.get(ctx.guild.roles, name="Banished")
            await member.add_roles(role)

            category = await ctx.guild.create_category("The Shadow Realm")
            s_channel = await ctx.guild.create_voice_channel("Hell", category=category)

            # The voice cog needs to be imported to get the 'play' command
            audio = self.bot.get_cog("Audio")

            await audio.play(ctx, url="https://youtu.be/ts7rkLrAios", name="shadow.mp3",
                             channel=member.guild.voice_channels[0], wait=3)

            try:
                await member.move_to(s_channel)

                await audio.play(ctx, url="https://youtu.be/AVz_lLnp6wI", name="hell.mp3",
                                 channel=s_channel, wait=60)

            except discord.errors.HTTPException:
                await asyncio.sleep(60)

            await member.remove_roles(role)
            await s_channel.delete()
            await category.delete()

        elif banish_poll.result is None:
            return

        else:
            await ctx.send("Not enough votes. Lucky you!")

    @commands.command(brief="Closes the most recent poll.",
                      description="The latest poll to be created will be closed with this command.", hidden=True)
    @commands.has_permissions(manage_messages=True)
    async def closepoll(self, ctx: commands.Context):
        if Poll.current_poll:
            await Poll.current_poll[-1].close()
        else:
            return await ctx.send("There is no poll currently running!")


async def setup(bot):
    await bot.add_cog(Polls(bot))

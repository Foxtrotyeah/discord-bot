import discord
from discord.ext import commands
import asyncio


class Poll:
    reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    voting = ["👍", "👎"]
    current_poll = []

    def __init__(self, ctx, title, description, inputs=None, yes_no=False, bot=None):
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
    def __init__(self, bot):
        self.bot = bot

    current_poll = []

    @commands.command(brief="Vote on a list of entries.",
                      description="Give The Big Gay a list of entries separated by a comma, and then vote.")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def poll(self, ctx, *, inputs=None):
        if not inputs:
            raise commands.CommandError(f"{ctx.author.mention} Try `.help` + `[the function name]` "
                                        f"to get more info on how to use this command.")

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
    @commands.cooldown(1, 60 * 5, commands.BucketType.guild)
    async def bitchalert(self, ctx, user: discord.Member = None):
        if not user:
            raise commands.CommandError(f"{ctx.author.mention} Try `.help` + `[the function name]` "
                                        f"to get more info on how to use this command.")
        if user.bot:
            raise commands.CommandError(f"{ctx.author.mention} Bitch, I'm flawless.")
        if user.status == discord.Status.offline:
            raise commands.CommandError(f"Chill out! {user.mention} isn't even online.")

        description = f"Is {user.mention} being a little bitch?"
        bitch_poll = Poll(ctx, "Bitch Alert", description=description, yes_no=True, bot=self.bot)
        await bitch_poll.send()

        if bitch_poll.result == "👍":
            role = discord.utils.get(ctx.guild.roles, name="Bitch")
            await user.add_roles(role)
            try:
                await user.edit(mute=True)
            except Exception as e:
                print(e)

            await ctx.send(f"{user.mention} Begone, THOT!")

            await asyncio.sleep(60)

            await user.remove_roles(role)
            try:
                await user.edit(mute=False)
            except Exception as e:
                print(e)

        elif bitch_poll.result is None:
            return

        else:
            await ctx.send(f"{user.mention}, you just keep on bitching. All good here.")

    # creates a poll for sending a user to a secondary channel, adding the 'banished' role
    @commands.command(brief="Vote to send a user to The Shadow Realm",
                      description="If the vote passes, the user is banished and cannot come back to the main channels, "
                                  "and must remain in purgatory for 60 seconds.")
    @commands.cooldown(1, 60 * 5, commands.BucketType.guild)
    async def banish(self, ctx, user: discord.Member = None):
        if not user:
            raise commands.CommandError(f"{ctx.author.mention} Try `.help` + `[the function name]` "
                                        f"to get more info on how to use this command.")
        if not hasattr(user.voice, "channel"):
            raise commands.CommandError(f"{user.mention} is not in a voice channel!")
        if user.bot:
            raise commands.CommandError(f"{ctx.author.mention} ...I'll remember that.")
        if user.status == discord.Status.offline:
            raise commands.CommandError(f"Chill out! {user.mention} isn't even online.")

        description = f"Send {user.mention} to the shadow realm?"
        banish_poll = Poll(ctx, "Banishment", description=description, yes_no=True, bot=self.bot)
        await banish_poll.send()

        if banish_poll.result == "👍":
            role = discord.utils.get(ctx.guild.roles, name="Banished")
            await user.add_roles(role)

            category = await ctx.guild.create_category("The Shadow Realm")
            s_channel = await ctx.guild.create_voice_channel("Hell", category=category)

            # The voice cog needs to be imported to get the 'play' command
            audio = self.bot.get_cog("Audio")

            await audio.play(ctx, url="https://youtu.be/ts7rkLrAios", name="shadow.mp3",
                             channel=user.guild.voice_channels[0], wait=3)

            try:
                await user.move_to(s_channel)

                await audio.play(ctx, url="https://youtu.be/AVz_lLnp6wI", name="hell.mp3",
                                 channel=s_channel, wait=60)

            except discord.errors.HTTPException:
                await asyncio.sleep(60)

            await user.remove_roles(role)
            await s_channel.delete()
            await category.delete()

        elif banish_poll.result is None:
            return

        else:
            await ctx.send("Not enough votes. Lucky you!")

    @commands.command(brief="Closes the most recent poll. (admin)",
                      description="The latest poll to be created will be closed with this command.")
    @commands.has_permissions(administrator=True)
    async def closepoll(self, ctx):
        if Poll.current_poll:
            await Poll.current_poll[-1].close()
        else:
            raise commands.CommandError("There is no poll currently running!")


async def setup(bot):
    await bot.add_cog(Polls(bot))

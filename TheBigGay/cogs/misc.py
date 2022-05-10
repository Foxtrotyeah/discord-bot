import discord
from discord.ext import commands
import random
from datetime import datetime
import pytz
import json


class Miscellaneous(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief="The bot's current latency.",
                      description="Gives the latency between the bot and server in ms.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ping(self, ctx):
        await ctx.send(f"Pong! My latency right now is {round(self.bot.latency * 1000)}ms")

    @commands.command(brief="Says hi, but gayer", description="Says hi, but gayer.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def hello(self, ctx):
        await ctx.send(f"{ctx.author.mention} Heyyy ;)")

    @commands.command(brief="Roasts a user.", description="Roast a user with a preset insult from The Big Gay")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def roast(self, ctx, user: discord.Member = None):
        if not user:
            raise commands.CommandError(f"{ctx.author.mention} Try `.help` + `[the function name]` "
                                        f"to get more info on how to use this command.")
        if user.bot:
            await ctx.send(f"{ctx.author.mention} No one roasts me, twat.")
            return
        if user.status == discord.Status.offline:
            await ctx.send(f"Damn, you're trying to roast someone behind their back! {user.mention} isn't even online.")

        with open("discord/assets/text.json", encoding="utf8", errors="ignore") as file:
            selected = random.choice(json.load(file)["roasts"]).format(user.mention)
        await ctx.send(selected)

    @commands.command(brief="Pastes a hot emojipasta.", description="Pastes only the greatest from r/emojipastas")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def emojipasta(self, ctx):
        with open("discord/assets/text.json", encoding="utf8", errors="ignore") as file:
            selected = random.choice(json.load(file)["emojipastas"])
        await ctx.send(selected)

    @commands.command(brief="Vibecheck a user or the whole server.",
                      description="If no user is specified, the whole server will be vibechecked.")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def vibecheck(self, ctx, user: discord.Member = None):
        if user:
            if user.bot:
                return await ctx.send("Bitch, I'm always fabulous.")
            if user.status == discord.Status.offline:
                return await ctx.send(f"I can't read minds if they aren't on online. "
                                      f"I'm sure {user.mention} is doing fine!")
            vibe = random.randint(0, 100)
            message = "{} Vibe levels at {}%.".format(user.mention, vibe)
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

            await ctx.send(message)
        else:
            user_list = [x for x in ctx.guild.members if x.status == discord.Status.online]
            user_list = [x for x in user_list if not x.bot]
            rand_user = random.choice(user_list)
            vibes = [
                "{} is salty as hell, watch out 👀".format(rand_user.mention),
                "{} is on one right now 🔥".format(rand_user.mention)
            ]
            vibe = random.choice(vibes)
            await ctx.send(vibe)

    @commands.command(brief="A 50/50 virtual coin toss.", description="Completely random 50/50 decision")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def coinflip(self, ctx):
        coin = ["Heads!", "Tails!"]
        await ctx.send(random.choice(coin))

    @commands.command(brief="I will select from a list of options at random.",
                      description="Can't decide for yourself? Let computers think for you. "
                                  "Give me a list of options separated by commas.")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def choose(self, ctx, *, inputs=None):
        if not inputs:
            raise commands.CommandError(f"{ctx.author.mention} Try `.help` + `[the function name]` "
                                        f"to get more info on how to use this command.")

        choices = str(inputs).split(", ")
        return await ctx.send(f"{ctx.author.mention} I choose **{random.choice(choices)}**!")

    @commands.command(hidden=True)
    async def time(self, ctx):
        timezone = pytz.timezone("US/Pacific")
        await ctx.send("PST time: {}".format(datetime.now(timezone)))

    @commands.command(brief="Submit an anonymous request for a new idea or bug.",
                      description="Send the owner of The Big Gay a request for a feature idea "
                                  "or a bug that you may have come across.")
    async def request(self, ctx, *, content):
        user = ctx.author
        me = discord.utils.get(ctx.guild.members, id=403969156510121987)
        await ctx.message.delete()
        await ctx.send(f"{ctx.author.mention} Thank you for your contribution to The Big Gay agenda.")

        await me.send(f'New request from {user.mention}: "{content}"')


async def setup(bot):
    await bot.add_cog(Miscellaneous(bot))

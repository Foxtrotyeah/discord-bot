import discord
from discord.ext import commands
import asyncio
from googletrans import Translator
import requests
import os
# import enchant


class Events(commands.Cog):
    # Give all errors back except for these
    exceptions = [commands.errors.CommandInvokeError, commands.errors.CommandNotFound]
    translator = Translator()

    def __init__(self, bot):
        self.bot = bot

        @bot.before_invoke
        async def daddy_checker(ctx):
            roles = [x.name for x in ctx.author.roles]
            if "Daddy" in roles:
                await ctx.send("*yes, daddy~*")

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot:
            return
        if msg.content.startswith('.'):
            return
        if str(msg.channel.type) == "private":
            guilds = msg.author.mutual_guilds
            for guild in guilds:
                member = discord.utils.get(guild.members, name=msg.author.name)
                roles = [x.name for x in member.roles]
                if "Banished" not in roles:
                    continue

                if "please" not in msg.content.lower():
                    return await msg.channel.send("What's the magic word?")
                elif "daddy" not in msg.content.lower():
                    return await msg.channel.send("That's 'daddy' to you.")
                else:
                    role = discord.utils.get(guild.roles, name="Banished")
                    await member.remove_roles(role)
                    return await msg.channel.send("Good boy. You can reconnect to voice channels now!")
            return

        if "gay" in msg.content.lower():
            await msg.channel.send("8====D")
        if "ligma" in msg.content.lower():
            await msg.channel.send("LIGMA BALLS")
        if "sugma" in msg.content.lower():
            await msg.channel.send("SUGMA DICK")
        if "sugondese" in msg.content.lower():
            await msg.channel.send("SUGONDESE NUTS")
        if "imagine dragons" in msg.content.lower():
            await msg.channel.send("IMAGINE DRAGON DEEZ NUTS ACROSS UR FACE")
        if "pudding" in msg.content.lower():
            await msg.channel.send("WE SHOULD BE PUDDING DEEZ NUTS IN UR MOUTH")
        if "sea of thieves" in msg.content.lower():
            await msg.channel.send("SEA OF THIEVES NUTS FIT IN UR MOUTH")

        # todo pyenchant doesn't work with heroku.
        # message = self.translator.detect(msg.content)
        # if message.lang != 'en' and message.confidence == 1:
        #     translation = self.translator.translate(msg.content)
        #
        #     # hopefully this cuts down on some false 'translations'
        #     english = enchant.Dict("en_US")
        #     if not english.check(translation.text.split(" ")[0]):
        #         return
        #
        #     wait = await msg.channel.send("(type 'yes' to translate)")
        #
        #     def check(msg2):
        #         if "yes" == msg2.content.lower():
        #             return True
        #         return False
        #
        #     try:
        #         await self.bot.wait_for("message", timeout=60, check=check)
        #     except asyncio.TimeoutError or commands.MessageNotFound:
        #         return await wait.delete()
        #
        #     await msg.channel.send(f"Translated from {message.lang}: '{translation.text}'")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before, after):
        if after.channel is None:
            return

        if "Banished" in [x.name for x in member.roles]:
            if after.channel.name != "Hell":
                try:
                    return await member.move_to(None)
                except Exception as e:
                    print(e)

        if "Bitch" not in [x.name for x in member.roles]:
            if member.voice.mute:
                await member.edit(mute=False)
        # If the member has the bitch role but isn't muted yet
        elif not member.voice.mute:
            await member.edit(mute=True)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, exc):
        if type(exc) in Events.exceptions:
            return
        # todo is there a way to check this for spam?
        # elif type(exc) is commands.errors.CommandOnCooldown:
        #     pass
        elif type(exc) is discord.errors.HTTPException:
            r = requests.head(url=os.environ['URL'])
            try:
                print(f"Rate limit {int(r.headers['Retry-After']) / 60} minutes left")
            finally:
                print("No rate limit")
        else:
            await ctx.send(exc)


def setup(bot):
    bot.add_cog(Events(bot))

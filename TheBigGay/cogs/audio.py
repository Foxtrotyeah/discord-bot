import discord
from discord.ext import commands
import os
import youtube_dl
import asyncio


class Audio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @commands.command()
    # async def youtube(ctx, *, search):
    #     query_string = parse.urlencode({'search_query': search})
    #     html_content = request.urlopen('http://www.youtube.com/results?' + query_string)
    #     # print(html_content.read().decode())
    #     search_results = re.findall(r"watch\?v=(\S{11})", html_content.read().decode())
    #     print(search_results)
    #     # I will put just the first result, you can loop the response to show more results
    #     await ctx.send('https://www.youtube.com/watch?v=' + search_results[0])

    # todo Make this functional as a bot command. How to disconnect?? Don't know how to realize when audio is finished
    # todo Add a check to see if bot is already connected to a voice channel
    async def play(self, ctx, url: str = None, name=None, channel=None, wait=60 * 5):
        is_there = os.path.isfile(f"./tracks/{name}")
        if not is_there:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'./tracks/{name}',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192'
                }],
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        await channel.connect()
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        voice.play(discord.FFmpegPCMAudio(source=f"./tracks/{name}"))

        await asyncio.sleep(wait)
        await voice.disconnect()

    @commands.command(brief="Soudbyte", description="What are you aiming at?")
    @commands.cooldown(1, 30, commands.BucketType.category)
    async def aim(self, ctx):
        channel = ctx.guild.voice_channels[0]
        await self.play(ctx, url="https://youtu.be/VoOxzT1ngeM", name="aim.mp3", channel=channel, wait=5)

    @commands.command(brief="Soudbyte", description="It smells like bitch in here.")
    @commands.cooldown(1, 30, commands.BucketType.category)
    async def bitch(self, ctx):
        channel = ctx.guild.voice_channels[0]
        await self.play(ctx, url="https://youtu.be/ppxmxVhkr7c", name="bitch.mp3", channel=channel, wait=5)

    @commands.command(brief="Soudbyte", description="Lord have mercy.")
    @commands.cooldown(1, 30, commands.BucketType.category)
    async def bust(self, ctx):
        channel = ctx.guild.voice_channels[0]
        await self.play(ctx, url="https://youtu.be/jzge_j-_PME", name="bust.mp3", channel=channel, wait=5)

    @commands.command(brief="Soudbyte", description="You just have to say that you're fine.")
    @commands.cooldown(1, 30, commands.BucketType.category)
    async def fine(self, ctx):
        channel = ctx.guild.voice_channels[0]
        await self.play(ctx, url="https://youtu.be/77sS5IuR0Gs", name="fine.mp3", channel=channel, wait=7)

    @commands.command(brief="Soudbyte", description="Plays the 'get your shit together' scene from Rick and Morty.")
    @commands.cooldown(1, 30, commands.BucketType.category)
    async def morty(self, ctx):
        channel = ctx.guild.voice_channels[0]
        await self.play(ctx, url="https://youtu.be/UYKKQn3WXh0", name="morty.mp3", channel=channel, wait=21)

    @commands.command(brief="Soudbyte", description="Plays audio from the 'It's Wednesday my dudes' scream.")
    @commands.cooldown(1, 30, commands.BucketType.category)
    async def nut(self, ctx):
        channel = ctx.guild.voice_channels[0]
        await self.play(ctx, url="https://youtu.be/dlRKA1nirrg", name="nut.mp3", channel=channel, wait=4)

    @commands.command(brief="Soudbyte", description="Plays audio from the death sound in Roblox.")
    @commands.cooldown(1, 30, commands.BucketType.category)
    async def oof(self, ctx):
        channel = ctx.guild.voice_channels[0]
        await self.play(ctx, url="https://youtu.be/3w-2gUSus34", name="oof.mp3", channel=channel, wait=3)

    @commands.command(brief="Soudbyte", description="Plays TikTok sheesh sound.")
    @commands.cooldown(1, 30, commands.BucketType.category)
    async def sheesh(self, ctx):
        channel = ctx.guild.voice_channels[0]
        await self.play(ctx, url="https://youtu.be/hRj1VyUsVjw", name="sheesh.mp3", channel=channel, wait=13)

    @commands.command(brief="Soudbyte", description="Plays audio from this dude having a real good time while cooking.")
    @commands.cooldown(1, 30, commands.BucketType.category)
    async def sogood(self, ctx):
        channel = ctx.guild.voice_channels[0]
        await self.play(ctx, url="https://youtu.be/-FrpuPLYnvY", name="sogood.mp3", channel=channel, wait=17)

    @commands.command(brief="Soudbyte", description="Plays audio from the 'Damn, this n**** spitting' meme")
    @commands.cooldown(1, 30, commands.BucketType.category)
    async def spitting(self, ctx):
        channel = ctx.guild.voice_channels[0]
        await self.play(ctx, url="https://youtu.be/xuLfu0z5_m0", name="spitting.mp3", channel=channel, wait=5)

    @commands.command(brief="Soudbyte", description="Plays audio from the spongebob heckler.")
    @commands.cooldown(1, 30, commands.BucketType.category)
    async def stinks(self, ctx):
        channel = ctx.guild.voice_channels[0]
        await self.play(ctx, url="https://youtu.be/ppb8A5QqPj8", name="stinks.mp3", channel=channel, wait=4)

    @commands.command(brief="Soudbyte", description="Begone...")
    @commands.cooldown(1, 30, commands.BucketType.category)
    async def thot(self, ctx):
        channel = ctx.guild.voice_channels[0]
        await self.play(ctx, url="https://youtu.be/tyrKeThaEJM", name="thot.mp3", channel=channel, wait=5)

    @commands.command(brief="Soudbyte", description="Uh oh stinky")
    @commands.cooldown(1, 30, commands.BucketType.category)
    async def uhoh(self, ctx):
        channel = ctx.guild.voice_channels[0]
        await self.play(ctx, url="https://youtu.be/PJNBJAYFyKE", name="uhoh.mp3", channel=channel, wait=5)

    @commands.command(brief="Soudbyte", description="Plays audio from a guy hitting a real nice yeet.")
    @commands.cooldown(1, 30, commands.BucketType.category)
    async def yeet(self, ctx):
        channel = ctx.guild.voice_channels[0]
        await self.play(ctx, url="https://youtu.be/won6qew1da4", name="yeet.mp3", channel=channel, wait=7)


async def setup(bot):
    await bot.add_cog(Audio(bot))

import discord
from discord.ext import commands
import os
import youtube_dl
import asyncio


async def _before_play(ctx: commands.Context) -> discord.VoiceChannel:
    if ctx.author.voice:
        channel = ctx.author.voice.channel
    else:
        channel = ctx.guild.voice_channels[0]

    return channel

    
def _after_play(error: Exception):
    if error:
        raise commands.CommandError(error)


async def play(bot: commands.Bot, url: str, name: str, ctx: commands.Context = None, channel: discord.VoiceChannel = None, wait: int = 60 * 5): 
    if ctx and not channel:
        channel = await _before_play(ctx)

    if not os.path.isfile(f"./tracks/{name}"):
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

    voice = discord.utils.get(bot.voice_clients, guild=channel.guild)
    if voice and voice.is_playing():
        raise commands.CommandError("I'm already playing something. Wait a sec")

    voice_client = await channel.connect()

    voice_client.play(discord.FFmpegPCMAudio(source=f"./tracks/{name}"), after=_after_play)

    await asyncio.sleep(wait)
    await voice_client.disconnect()

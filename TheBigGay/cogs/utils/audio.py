import discord
from discord.ext import commands
import os
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


async def play(client: discord.Client, name: str, ctx: commands.Context = None, channel: discord.VoiceChannel = None, wait: int = 60 * 5): 
    if ctx and not channel:
        channel = await _before_play(ctx)

    if not os.path.isfile(f"./tracks/{name}"):
        raise commands.CommandError(f"No track found for {name}")

    voice = discord.utils.get(client.voice_clients, guild=channel.guild)
    if voice and voice.is_playing():
        raise commands.CommandError("I'm already playing something. Wait a sec")

    voice_client = await channel.connect()

    voice_client.play(discord.FFmpegPCMAudio(source=f"./tracks/{name}"), after=_after_play)

    await asyncio.sleep(wait)
    await voice_client.disconnect()

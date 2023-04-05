import discord
from discord import app_commands
import asyncio


async def play(client: discord.Client, name: str, channel: discord.VoiceChannel = None, wait = False):
    voice = discord.utils.get(client.voice_clients, guild=channel.guild)
    if voice and voice.is_playing():
        raise app_commands.AppCommandError("I'm already playing something. Wait a sec.")

    voice_client = await channel.connect()

    def after_play(error: Exception):
        asyncio.run_coroutine_threadsafe(voice_client.disconnect(), voice_client.loop).result()

        nonlocal wait 
        wait = False

        if error:
            raise app_commands.CommandInvokeError(error)

    voice_client.play(discord.FFmpegPCMAudio(source=f"./tracks/{name}"), after=after_play)

    while wait:
        await asyncio.sleep(1)

import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta

from .utils import papago


class Context(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.translate_menu = app_commands.ContextMenu(
            name="Translate",
            callback=self.translate
        )
        self.bot.tree.add_command(self.translate_menu)
        
        self.purge_menu = app_commands.ContextMenu(
            name="Purge",
            callback=self.purge
        )
        self.bot.tree.add_command(self.purge_menu)

    async def translate(self, interaction: discord.Interaction, message: discord.Message):
        translation, language = papago.translate(message.content)

        await interaction.response.send_message(f'Translated from **{language}**: "{translation}"')

    async def purge(self, interaction: discord.Interaction, message: discord.Message):
        await interaction.response.defer(thinking=True)

        deleted = await interaction.channel.purge(before=interaction.created_at, after=message.created_at-timedelta(milliseconds=1))
        await interaction.followup.send("Deleted {} message(s)".format(len(deleted)))
        

async def setup(bot):
    await bot.add_cog(Context(bot))
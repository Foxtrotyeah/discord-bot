import discord
from discord.ui import View
from discord import app_commands
from datetime import datetime
import typing

from . import mysql


high_roller_minimum = 1000


class ExclusiveView(View):
    def __init__(self, authorized: typing.Union[discord.Member, discord.User, list[typing.Union[discord.Member, discord.User]]]):
        if type(authorized) is not list: authorized = [authorized]
        self.authorized = authorized
        super().__init__()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in self.authorized:
            await interaction.response.send_message("That's not yours.", delete_after=5, ephemeral=True)
            return False
        return True


class MinimumBet(app_commands.CheckFailure):
    def __str__(self):
        return f"Bets in the high roller hall must meet the minimum bet: **{high_roller_minimum} gaybucks**."


class IneligibleForSubsidy(app_commands.CheckFailure):
    def __str__(self):
        return (
            "You are not eligible for a subsidy. "
            "Either you have more than 100 gaybucks in your account, "
            "or your sugar daddy has already bailed you out once today."
        )


def is_valid_bet(channel: discord.TextChannel, amt: int) -> bool:
    if amt <= 0:
        raise app_commands.CheckFailure("You have to place a nonzero bet.")

    if channel.name == 'high-roller-hall' and amt < high_roller_minimum:
        raise MinimumBet()

    return True


# Check eligibility status for a subsidy
def check_subsidy():
    def predicate(interaction: discord.Interaction) -> bool:
        result = mysql._get_user_data(interaction.user.id, interaction.guild.id)

        if result[1] < 100 and result[2].date() < datetime.now(mysql.timezone).date():
            return True
        else:
            raise IneligibleForSubsidy()

    return app_commands.check(predicate)

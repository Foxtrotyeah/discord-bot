import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

from . import mysql


high_roller_minimum = 1000


class WrongChannel(commands.CheckFailure):
    def __str__(self):
        return "This command is only allowed in the gambling hall channels."


class MinimumBet(commands.CheckFailure):
    def __str__(self):
        return f"Bets in the high roller hall must meet the minimum bet: **{high_roller_minimum} gaybucks**."


class IneligibleForSubsidy(app_commands.CheckFailure):
    def __str__(self):
        return (
            "You are not eligible for a subsidy. "
            "Either you have more than 100 gaybucks in your account, "
            "or your sugar daddy has already bailed you out once today."
        )


def is_valid_bet(channel: discord.TextChannel, member: discord.Member, amt: int):
    if amt <= 0:
        raise commands.CommandError("You have to place a nonzero bet.")

    if channel.name == 'high-roller-hall' and amt < high_roller_minimum:
        raise MinimumBet()

    if mysql.get_wallet(member)[0] < amt:
        raise commands.CommandError(f"Insufficient funds.")

    return True


def is_gambling_category_pred(ctx: commands.Context) -> bool:
        if ctx.channel.category.name != "Gambling":
            raise WrongChannel()
        else:
            return True


def is_gambling_category():
    return commands.check(is_gambling_category_pred)


# Check eligibility status for a subsidy
def check_subsidy():
    def predicate(interaction: discord.Interaction) -> bool:
        result = mysql._get_user_data(interaction.user.id, interaction.guild.id)

        if result[1] < 100 and result[2].date() < datetime.now(mysql.timezone).date():
            return True
        else:
            raise IneligibleForSubsidy()

    return app_commands.check(predicate)

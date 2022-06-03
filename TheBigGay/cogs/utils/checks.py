import discord
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


class IneligibleForSubsidy(commands.CheckFailure):
    def __str__(self):
        return (
            "You are not eligible for a subsidy. "
            "Either you have more than 100 gaybucks in your account, "
            "or your sugar daddy has already bailed you out once today."
        )


def is_valid_bet(ctx: commands.Context, member: discord.Member, amt: int):
    if amt <= 0:
        raise commands.CommandError("You have to place a nonzero bet.")

    if mysql.get_wallet(member)[0] < amt:
        raise commands.CommandError(f"Insufficient funds.")

    if ctx.channel.name == 'high-roller-hall' and amt < high_roller_minimum:
        raise MinimumBet()

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
    def pred(ctx: commands.Context) -> bool:
        result = mysql._get_user_data(ctx.author.id, ctx.guild.id)

        if result[1] < 100 and result[2].date() < datetime.now(mysql.timezone).date():
            return True
        else:
            raise IneligibleForSubsidy()

    return commands.check(pred)

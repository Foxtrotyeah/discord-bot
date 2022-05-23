import discord
from discord.ext import commands
from datetime import datetime

from . import mysql


class WrongChannel(commands.CheckFailure):
    def __str__(self):
        return "Gambling is only allowed in the gambling hall channels."


class IneligibleForSubsidy(commands.CheckFailure):
    def __str__(self):
        return (
            "You are not eligible for a subsidy. "
            "Either you have more than 100 gaybucks in your account, "
            "or your sugar daddy has already bailed you out once today."
        )


def is_valid_bet(member: discord.Member, amt: int):
    if amt <= 0:
        raise commands.CommandError("You have to place a nonzero bet.")

    if mysql.get_balance(member) >= amt:
        return True
    else:
        raise commands.CommandError(f"Insufficient funds.")


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
        result = mysql._get_user_data(ctx.author)

        if result[1] < 100 and result[2].date() < datetime.now(mysql.timezone).date():
            return True
        else:
            raise IneligibleForSubsidy()

    return commands.check(pred)

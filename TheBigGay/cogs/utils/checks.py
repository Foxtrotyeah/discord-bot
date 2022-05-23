import discord
from discord.ext import commands

from . import mysql


def is_valid_bet(member: discord.Member, amt: int):
    if amt <= 0:
        raise commands.CommandError(f"{member.mention} You have to place a nonzero bet.")

    if mysql.get_balance(member) >= amt:
        return True
    else:
        raise commands.CommandError(f"Insufficient funds: {member.mention}")


def is_gambling_category():
    def pred(ctx: commands.Context) -> bool:
        if ctx.channel.category.name != "Gambling":
            return False
        else:
            return True

    return commands.check(pred)

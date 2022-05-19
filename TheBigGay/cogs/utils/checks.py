import discord
from discord.ext import commands

from . import mysql


def has_funds(member: discord.Member, amt: int):
    if mysql.get_balance(member) >= amt:
        return True
    else:
        raise commands.CommandError(f"Insufficient funds: {member.mention}")


def is_gambling_category():
    def pred(ctx) -> bool:
        if ctx.channel.category.name != "Gambling":
            return False
        else:
            return True

    return commands.check(pred)

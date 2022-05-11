import discord
from discord.ext import commands

from . import mysql


def has_funds(amt: int):
    def pred(ctx) -> bool:
        if mysql.get_balance(ctx.author) >= amt:
            return True
        else:
            return False

    return commands.check(pred)

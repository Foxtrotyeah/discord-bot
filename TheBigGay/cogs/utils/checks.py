import discord
from discord.ext import commands

from . import mysql


def has_funds(amt: int, member: discord.Member = None):
    def pred(ctx) -> bool:            
        if mysql.get_balance(member if member else ctx.author) >= amt:
            return True
        else:
            return False

    return commands.check(pred)


def is_gambling_category():
    def pred(ctx) -> bool:
        if ctx.channel.category.name != "Gambling":
            return False
        else:
            return True

    return commands.check(pred)

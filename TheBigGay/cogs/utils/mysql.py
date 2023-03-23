import discord
from discord.ext import commands
import pymysql
import os
from datetime import datetime
import pytz
import random

from typing import List, Tuple


config = {
    "host": os.environ['MYSQL_HOST'],
    "user": os.environ['MYSQL_USER'],
    "password": os.environ['MYSQL_PASSWORD'],
    "database": os.environ['MYSQL_DATABASE'],
    "connect_timeout": 86400
}

# Using any other timzeone messes with the guild.create_scheduled_event fucntion.
timezone = pytz.timezone("US/Mountain")

db = pymysql.connect(**config)


def _test_connection(function: callable):
    while True:
        try:
            function()
            break
        except pymysql.OperationalError:
            db.ping(reconnect=True)

def _execute(sql: str, commit: bool = False) -> Tuple[Tuple, ...]:
    cursor = db.cursor()
    _test_connection(lambda: cursor.execute(sql))

    result = cursor.fetchall()

    if commit:
        db.commit()

    cursor.close()
    return result


def create_economy_table(guild_id: int):
    sql = f"CREATE TABLE {str(guild_id) + '_economy'} "\
        "(user_id VARCHAR(20) NOT NULL, "\
        "balance INT(9) NOT NULL, "\
        "subsidy_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, "\
        "tickets INT(9) NOT NULL, " \
        "PRIMARY KEY (user_id))" 
    _execute(sql, commit=True)
    

def create_leaderboard_table(guild_id: int):
    sql = f"CREATE TABLE {str(guild_id) + '_leaderboard'} "\
        "(game VARCHAR(20) NOT NULL, "\
        "user_id VARCHAR(20) NOT NULL, "\
        "score INT(9) NOT NULL, "\
        "date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, "\
        "PRIMARY KEY (game))"
    _execute(sql, commit=True)


# Check guild for having economy and leaderboard tables in the database
def initialize_guild(guild_id: int):
    sql = "SHOW TABLES LIKE '{}_economy'".format(str(guild_id))
    result = _execute(sql)
    
    if not result:
        print(f"Creating economy table for guild with ID: {guild_id}")
        create_economy_table(guild_id)

    sql = "SHOW TABLES LIKE '{}_leaderboard'".format(guild_id)
    result = _execute(sql)

    if not result:
        print(f"Creating leaderboard table for guild with ID: {guild_id}")
        create_leaderboard_table(guild_id)


def _check_status(table: str, member_id: int):
    cursor = db.cursor()
    _test_connection(lambda: cursor.execute(f"SELECT EXISTS(SELECT * from {table} WHERE user_id={member_id})"))
    
    # If user isn't in DB, add a row for them.
    if cursor.fetchone()[0] != 1:
        cursor.execute(
            f"INSERT into {table}(user_id, balance, subsidy_date) "
			f"VALUES ({member_id}, 50, %s)", (datetime.now(timezone).date(),)
        )
        db.commit()

    cursor.close()


def _get_user_data(member_id: int, guild_id: int) -> Tuple:
    cursor = db.cursor()
    table = str(guild_id) + "_economy"

    _check_status(table, member_id)

    cursor.execute(f"SELECT * from {table} WHERE user_id={member_id}")
    result = cursor.fetchone()
    cursor.close()

    return result


def get_wallet(member: discord.Member) -> Tuple[int, int]:
    result = _get_user_data(member.id, member.guild.id)

    return (result[1], result[3])


# Get all economy data
def get_economy(bot: commands.Bot, guild: discord.Guild) -> List[tuple]:
    cursor = db.cursor()
    table = str(guild.id) + "_economy"

    _test_connection(lambda: cursor.execute(f"SELECT user_id, balance from {table}"))

    result = cursor.fetchall()
    cursor.close()

    result = [x for x in result if x[0] != str(bot.application_id)]

    return result


# Updates a user's balance
def update_balance(member: discord.Member, amt: int) -> int:  
    cursor = db.cursor()      
    table = str(member.guild.id) + "_economy"

    result = _get_user_data(member.id, member.guild.id)

    if amt != 0:
        new_bal = max(result[1] + amt, 0)

        cursor.execute(f"UPDATE {table} SET balance={new_bal} WHERE user_id={member.id}")
        db.commit()
    else:
        new_bal = result[1]

    cursor = db.cursor()
    return new_bal


def subsidize(member: discord.Member) -> int:
    cursor = db.cursor()
    table = str(member.guild.id) + "_economy"

    result = _get_user_data(member.id, member.guild.id)

    new_bal = max(result[1] + 50, 0)
    
    cursor.execute(
        f"UPDATE {table} " \
        f"SET balance={new_bal}, subsidy_date=%s " \
        f"WHERE user_id={member.id}", (datetime.now(timezone).date(),)
    )
    db.commit()
    cursor.close()

    return new_bal


def add_to_lottery(bot: commands.Bot, guild: discord.Guild, amt: int):
    cursor = db.cursor()
    table = str(guild.id) + "_economy"

    result = _get_user_data(bot.application_id, guild.id)

    new_bal = result[1] + int(round(amt * 0.05))    # Add 5% of all losings to the lottery.

    cursor.execute(f"UPDATE {table} SET balance={new_bal} WHERE user_id={bot.application_id}")
    db.commit()
    cursor.close()


def buy_ticket(bot: commands.Bot, member: discord.Member, amt: int) -> int:
    cursor = db.cursor()
    table = str(member.guild.id) + "_economy"

    ticket_price = 50

    user_result = _get_user_data(member.id, member.guild.id)
    bot_result = _get_user_data(bot.application_id, member.guild.id)

    user_bal = max(user_result[1] - (ticket_price * amt), 0)
    bot_bal = bot_result[1] + (ticket_price * amt)

    total = user_result[3] + amt

    cursor.execute(f"UPDATE {table} SET balance={user_bal}, tickets={total} WHERE user_id={member.id}")
    cursor.execute(f"UPDATE {table} SET balance={bot_bal} WHERE user_id={bot.application_id}")
    db.commit()
    cursor.close()

    return total


def choose_lottery_winner(bot: commands.Bot, guild: discord.Guild) -> Tuple[discord.Member, int]:
    cursor = db.cursor()
    table = str(guild.id) + "_economy"

    _test_connection(lambda: cursor.execute(f"SELECT user_id, tickets from {table}"))

    result = cursor.fetchall()

    ticket_holders = [member for member in result if member[1] > 0]
    if ticket_holders:
        tickets = []
        for holder in ticket_holders:
            for ticket in range(holder[1]):
                tickets.append(holder[0])
    # If no ticket holders, a random person gets the pot.
    else:
        tickets = [member[0] for member in result if member[0] != str(bot.application_id)]

    winner_id = int(random.choice(tickets))

    winner_balance = _get_user_data(winner_id, guild.id)[1]
    lottery_total = get_lottery(bot, guild)
    new_bal = winner_balance + lottery_total

    cursor.execute(f"UPDATE {table} SET balance={new_bal} WHERE user_id={winner_id}")
    db.commit()
    cursor.close()

    _reset_lottery(bot, guild)

    return guild.get_member(winner_id), new_bal


def get_lottery(bot: commands.Bot, guild: discord.Guild) -> int:
    result = _get_user_data(bot.application_id, guild.id)

    return result[1]


def _reset_lottery(bot: commands.Bot, guild: discord.Guild):
    cursor = db.cursor()
    table = str(guild.id) + "_economy"

    cursor.execute(f"UPDATE {table} SET tickets=0")
    cursor.execute(f"UPDATE {table} SET balance=0 WHERE user_id={bot.application_id}")
    db.commit()
    cursor.close()


def get_leaderboard(guild: discord.Guild) -> Tuple[Tuple, ...]:
    cursor = db.cursor()
    table = str(guild.id) + "_leaderboard"

    _test_connection(lambda: cursor.execute(f"SELECT game, user_id, score, date from {table}"))

    result = cursor.fetchall()
    cursor.close()

    return result


def check_leaderboard(game: str, member: discord.Member, score: int) -> bool:
    cursor = db.cursor()
    table = str(member.guild.id) + "_leaderboard"

    _test_connection(lambda: cursor.execute(f"SELECT EXISTS(SELECT * from {table} WHERE game='{game}')"))

    if cursor.fetchone()[0] == 1:
        cursor.execute(f"SELECT * from {table} WHERE game='{game}'")
        result = cursor.fetchone()

        if score > int(result[2]):
            # new high score
            cursor.execute(
                f"UPDATE {table} SET user_id={member.id}, score={score}, date=%s WHERE game='{game}'",
                (datetime.now(timezone).date(),)
            )
            db.commit()
            cursor = db.cursor()
            return True
    else:
        # new game high score
        cursor.execute(
            f"INSERT into {table}(game, user_id, score, date) " \
            f"VALUES ('{game}', {member.id}, {score}, %s)", 
            (datetime.now(timezone).date(),)
        )
        db.commit()
        cursor = db.cursor()
        return True

    cursor.close()
    return False

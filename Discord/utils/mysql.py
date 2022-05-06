import discord
import pymysql
import os
from datetime import datetime
import pytz


config = {
    "host": os.environ['MYSQL_HOST'],
    "user": os.environ['MYSQL_USER'],
    "password": os.environ['MYSQL_PASSWORD'],
    "database": os.environ['MYSQL_DATABASE']
}

timezone = pytz.timezone("US/Pacific")


# def connect(callback=None):
#   db = pymysql.connect(**config)
#   cursor = db.cursor()

#   if callback:
#     callback(db, cursor)

#   db.close()


def _check_exists(table: str, user_id: str):
	db = pymysql.connect(**config)
	cursor = db.cursor()

	cursor.execute(f"SELECT EXISTS(SELECT * from {table} WHERE user_id={user_id})")

	if cursor.fetchone()[0] != 1:
		cursor.execute(f"INSERT into {table}(user_id, balance, subsidy_date) "
						f"VALUES ({user_id}, 50, %s)", (datetime.now(timezone).date(),))
		db.commit()

	db.close()


def _get_user_data(ctx):
    table = str(ctx.guild.id) + "_economy"
    user_id = str(ctx.author.id)

    _check_exists(table, user_id)

    db = pymysql.connect(**config)
    cursor = db.cursor()

    cursor.execute(f"SELECT * from {table} WHERE user_id={user_id}")
    result = cursor.fetchone()

    db.close()

    return result


def get_balance(ctx):
    result = _get_user_data(ctx)

    return result[1]


def check_subsidy(ctx):
    result = _get_user_data(ctx)

    if result[1] < 100 and result[2].date() < datetime.now(timezone).date():
        return True
    else:
        return False


# Get all economy data
def get_economy(ctx):
    table = str(ctx.guild.id) + "_economy"

    db = pymysql.connect(**config)
    cursor = db.cursor()

    cursor.execute(f"SELECT user_id, balance from {table}")
    result = cursor.fetchall()

    db.close()

    return result


# Updates a user's balance
async def update_bal(ctx, user: discord.Member, amt: int):
    _check_exists(ctx)

    guild = user.guild

    table = str(guild.id) + "_economy"
    user_id = str(user.id)

    db = pymysql.connect(**config)
    cursor = db.cursor()

    cursor.execute(f"SELECT * from {table} WHERE user_id={user_id}")
    result = cursor.fetchone()

    new_bal = max(result[1] + amt, 0)

    cursor.execute(f"UPDATE {table} SET balance={new_bal} WHERE user_id={user_id}")
    db.commit()

    db.close()

    if new_bal == 0:
        await ctx.send(f"{user.mention} is broke! LOL")

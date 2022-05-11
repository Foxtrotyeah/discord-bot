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


def execute(sql: str):
    db = pymysql.connect(**config)
    cursor = db.cursor()

    cursor.execute(sql)

    db.close()


def _check_exists(table: str, user_id: str):
	db = pymysql.connect(**config)
	cursor = db.cursor()

	cursor.execute(f"SELECT EXISTS(SELECT * from {table} WHERE user_id={user_id})")

	if cursor.fetchone()[0] != 1:
		cursor.execute(f"INSERT into {table}(user_id, balance, subsidy_date) "
						f"VALUES ({user_id}, 50, %s)", (datetime.now(timezone).date(),))
		db.commit()

	db.close()


def _get_user_data(member: discord.Member):
    table = str(member.guild.id) + "_economy"
    user_id = str(member.id)

    _check_exists(table, user_id)

    db = pymysql.connect(**config)
    cursor = db.cursor()

    cursor.execute(f"SELECT * from {table} WHERE user_id={user_id}")
    result = cursor.fetchone()

    db.close()

    return result


def get_balance(member: discord.Member):
    result = _get_user_data(member)

    return result[1]


def check_subsidy(member: discord.Member):
    result = _get_user_data(member)

    if result[1] < 100 and result[2].date() < datetime.now(timezone).date():
        return True
    else:
        return False


# Get all economy data
def get_economy(guild: discord.Guild):
    table = str(guild.id) + "_economy"

    db = pymysql.connect(**config)
    cursor = db.cursor()

    cursor.execute(f"SELECT user_id, balance from {table}")
    result = cursor.fetchall()

    db.close()

    return result


# Updates a user's balance
async def update_bal(ctx, member: discord.Member, amt: int):
    table = str(member.guild.id) + "_economy"
    user_id = str(member.id)

    _check_exists(table, user_id)

    db = pymysql.connect(**config)
    cursor = db.cursor()

    cursor.execute(f"SELECT * from {table} WHERE user_id={user_id}")
    result = cursor.fetchone()

    new_bal = max(result[1] + amt, 0)

    cursor.execute(f"UPDATE {table} SET balance={new_bal} WHERE user_id={user_id}")
    db.commit()

    db.close()

    if new_bal == 0:
        await ctx.send(f"{member.mention} is broke! LOL")

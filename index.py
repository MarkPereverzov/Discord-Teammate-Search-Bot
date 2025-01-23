import discord
from discord.ext import commands
import sqlite3
from addrole import addrole
from search import search

# Подключение к базе данных
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Создание таблиц, если они еще не существуют
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        role_id INTEGER,
        show_in_search INTEGER DEFAULT 0,
        message_id INTEGER
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS roles (
        role_id INTEGER PRIMARY KEY,
        role_name TEXT
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS branches (
        role_id INTEGER PRIMARY KEY,
        branch_id INTEGER
    )
''')

conn.commit()

# Инициализация бота
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.guild_messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Регистрация команды addrole
bot.add_command(addrole())

# Регистрация команды search
bot.add_command(search(conn))

bot.run("MTMzMTYwNzkwNTY0MzkyNTUzNQ.GWmwGc.h5lvyqkDnZgN1352pBQveWMiR_Ya3EDj9LGeJU")
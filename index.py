import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import sqlite3

# Настройка бота с корректными интентами
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  # Необходимо для чтения команд
bot = commands.Bot(command_prefix="!", intents=intents)

# Функция для сохранения роли пользователя в базу данных
def save_user_role(user_id, role, show_in_search=True):
    conn = sqlite3.connect('teammate_search.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR REPLACE INTO users (user_id, role, show_in_search)
    VALUES (?, ?, ?)
    ''', (user_id, role, show_in_search))
    conn.commit()
    conn.close()

# Команда start
@bot.command()
async def start(ctx):
    try:
        # Создаем кнопки
        button_open_search = Button(label="Відкрити пошук", style=discord.ButtonStyle.primary)
        button_show_in_search = Button(label="Показати мене в пошуку", style=discord.ButtonStyle.success)
        button_hide_in_search = Button(label="Не показувати мене в пошуку", style=discord.ButtonStyle.danger)

        # Обработчик кнопки "Відкрити пошук"
        async def button_open_search_callback(interaction):
            roles = ["valorant", "dota", "apex"]
            select = Select(placeholder="Виберіть роль", options=[discord.SelectOption(label=role) for role in roles])

            async def select_callback(interaction):
                selected_role = select.values[0]
                save_user_role(interaction.user.id, selected_role)
                await interaction.response.send_message(f"Ви вибрали роль: {selected_role}", ephemeral=True)

            select.callback = select_callback

            view = View()
            view.add_item(select)
            await interaction.response.send_message("Оберіть вашу роль:", view=view)

        # Обработчик кнопки "Показати мене в пошуку"
        async def button_show_in_search_callback(interaction):
            save_user_role(interaction.user.id, "none", True)
            await interaction.response.send_message("Ви тепер у пошуку!", ephemeral=True)

        # Обработчик кнопки "Не показувати мене в пошуку"
        async def button_hide_in_search_callback(interaction):
            save_user_role(interaction.user.id, "none", False)
            await interaction.response.send_message("Ви більше не показуєтеся в пошуку.", ephemeral=True)

        # Привязываем обработчики к кнопкам
        button_open_search.callback = button_open_search_callback
        button_show_in_search.callback = button_show_in_search_callback
        button_hide_in_search.callback = button_hide_in_search_callback

        # Создаем View с кнопками
        view = View()
        view.add_item(button_open_search)
        view.add_item(button_show_in_search)
        view.add_item(button_hide_in_search)

        # Отправляем сообщение
        await ctx.send("Виберіть опцію:", view=view)
    except Exception as e:
        await ctx.send(f"Ошибка: {e}")

# Запуск бота
bot.run('MTMzMTYwNzkwNTY0MzkyNTUzNQ.G9wUHU.h1chlKqUgBCX-tSZoUJldWO1STbQ3qFmgCx_BQ')

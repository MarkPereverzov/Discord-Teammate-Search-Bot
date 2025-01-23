import discord
from discord.ext import commands
from discord.ui import View, Button, Select
import sqlite3
from addrole import addrole

# Подключение к базе данных
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Создание таблиц, если они еще не созданы
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    role_id INTEGER,
                    show_in_search BOOLEAN)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS roles (
                    role_id INTEGER PRIMARY KEY,
                    role_name TEXT)''')
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

# Команда !search
@bot.command()
async def search(ctx):
    async def update_user_status(interaction, status):
        cursor.execute("INSERT OR REPLACE INTO users (user_id, username, role_id, show_in_search) VALUES (?, ?, ?, ?)", 
                       (interaction.user.id, interaction.user.name, None, status))
        conn.commit()
        await interaction.response.edit_message(view=create_search_view(not status))

    async def create_search_view_after_role(interaction, role_name, selected_role_id):
        # Создаем ветку (тред) для выбранной роли
        thread = await ctx.channel.create_thread(
            name=f"Роль: {role_name}",
            type=discord.ChannelType.public_thread
        )

        # Получаем список пользователей с выбранной ролью
        teammates = cursor.execute(
            "SELECT username FROM users WHERE role_id = ? AND show_in_search = 1", 
            (selected_role_id,)
        ).fetchall()

        if teammates:
            description = "\n".join([f"**@{teammate[0]}** ищет команду" for teammate in teammates])
        else:
            description = "Пока никто не ищет команду для этой роли."

        embed = discord.Embed(
            title=f"Роль: {role_name}",
            description=description,
            color=discord.Color.green()
        )

        # Добавляем кнопку "Написать в ЛС"
        write_dm_button = Button(label="Написать в ЛС", style=discord.ButtonStyle.blurple)

        async def write_dm_callback(i):
            await i.user.send(f"Привет! Вы можете связаться с @{ctx.author.name} для поиска команды.")
            await i.response.send_message("Сообщение отправлено!", ephemeral=True)

        write_dm_button.callback = write_dm_callback

        view = View()
        view.add_item(write_dm_button)

        # Отправляем embed-сообщение в ветку
        await thread.send(embed=embed, view=view)

        # Обновляем сообщение с выбором роли
        embed = discord.Embed(
            title="Вы выбрали роль",
            description=f"Вы выбрали роль: **{role_name}**. Перейдите в ветку для общения.",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=create_search_view(True))

    async def select_role_callback(interaction):
        selected_role_id = int(interaction.data["values"][0])
        role_name = cursor.execute("SELECT role_name FROM roles WHERE role_id = ?", (selected_role_id,)).fetchone()[0]

        # Обновляем таблицу пользователя
        cursor.execute("UPDATE users SET role_id = ? WHERE user_id = ?", (selected_role_id, interaction.user.id))
        conn.commit()

        # Создаем интерфейс после выбора роли
        await create_search_view_after_role(interaction, role_name, selected_role_id)

    def create_search_view(show_in_search):
        view = View()
        
        search_button = Button(label="Поиск", style=discord.ButtonStyle.blurple)
        search_button.callback = lambda i: display_role_select(i)
        view.add_item(search_button)

        toggle_button = Button(
            label="Отображать меня при поиске" if not show_in_search else "Не отображать меня при поиске",
            style=discord.ButtonStyle.green if not show_in_search else discord.ButtonStyle.red
        )
        toggle_button.callback = lambda i: update_user_status(i, not show_in_search)
        view.add_item(toggle_button)

        return view

    async def display_role_select(interaction):
        roles = cursor.execute("SELECT * FROM roles").fetchall()
        if not roles:
            embed = discord.Embed(
                title="Роли не найдены",
                description="В базе данных нет доступных ролей для выбора.",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed)
            return

        select_menu = Select(placeholder="Выберите роль", options=[
            discord.SelectOption(label=role[1], value=str(role[0])) for role in roles
        ])
        select_menu.callback = select_role_callback

        embed = discord.Embed(
            title="Выберите роль для поиска",
            description="Пожалуйста, выберите роль из списка ниже.",
            color=discord.Color.light_grey()
        )
        await interaction.response.edit_message(embed=embed, view=View().add_item(select_menu))

    embed = discord.Embed(
        title="Выберите действие",
        description="Используйте кнопки или меню ниже.",
        color=discord.Color.light_grey()
    )
    await ctx.send(embed=embed, view=create_search_view(False))

bot.run("MTMzMTYwNzkwNTY0MzkyNTUzNQ.GWmwGc.h5lvyqkDnZgN1352pBQveWMiR_Ya3EDj9LGeJU")
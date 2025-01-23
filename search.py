import discord
from discord.ext import commands
from discord.ui import View, Button, Select
import sqlite3

# Подключение к базе данных
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Функция команды search
def search(conn):
    cursor = conn.cursor()

    @commands.command()
    async def search(ctx):
        await ctx.message.delete()

        async def update_user_status(interaction, status):
            user_id = interaction.user.id
            username = interaction.user.name

            # Получаем информацию о текущей роли и сообщении пользователя
            user_data = cursor.execute("SELECT role_id, message_id, show_in_search FROM users WHERE user_id = ?", (user_id,)).fetchone()
            role_id = user_data[0] if user_data else None
            message_id = user_data[1] if user_data else None
            current_status = user_data[2] if user_data else None

            # Обновляем статус пользователя в базе данных
            cursor.execute(
                "INSERT OR REPLACE INTO users (user_id, username, role_id, show_in_search, message_id) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, role_id, status, None if not status else message_id)
            )
            conn.commit()

            # Если статус "Не відображати мене під час пошуку", удаляем сообщение
            if not status and message_id:
                role_data = cursor.execute("SELECT branch_id FROM branches WHERE role_id = ?", (role_id,)).fetchone()
                if role_data:
                    thread = await ctx.guild.fetch_channel(role_data[0])
                    try:
                        msg = await thread.fetch_message(message_id)
                        await msg.delete()
                    except discord.NotFound:
                        pass

            # Если статус "Відображати мене під час пошуку", создаем сообщение
            elif status and role_id:
                role_data = cursor.execute("SELECT branch_id FROM branches WHERE role_id = ?", (role_id,)).fetchone()
                if role_data:
                    thread = await ctx.guild.fetch_channel(role_data[0])
                    embed = discord.Embed(
                        title="Користувач шукає команду",
                        description=f"**<@{user_id}>** шукає команду для ролі **<@&{role_id}>**.",
                        color=discord.Color.green()
                    )
                    msg = await thread.send(embed=embed)
                    # Сохраняем ID сообщения
                    cursor.execute("UPDATE users SET message_id = ? WHERE user_id = ?", (msg.id, user_id))
                    conn.commit()

            # Обновляем интерфейс
            new_view = create_search_view(status)
            await interaction.response.edit_message(view=new_view)

        async def create_search_view_after_role(interaction, role_name, role_id):
            # Проверяем, существует ли ветка для роли
            branch_data = cursor.execute("SELECT branch_id FROM branches WHERE role_id = ?", (role_id,)).fetchone()
            if branch_data:
                branch_id = branch_data[0]
                thread = await ctx.guild.fetch_channel(branch_id)
            else:
                # Создаём новую ветку, если её ещё нет
                thread = await interaction.channel.create_thread(
                    name=f"{role_name} - поиск",
                    type=discord.ChannelType.public_thread
                )
                # Сохраняем информацию о ветке в таблицу branches
                cursor.execute("INSERT INTO branches (role_id, branch_id) VALUES (?, ?)", (role_id, thread.id))
                conn.commit()

            # Проверяем наличие старого сообщения
            user_data = cursor.execute("SELECT message_id FROM users WHERE user_id = ?", (interaction.user.id,)).fetchone()
            if user_data and user_data[0]:  # Если сообщение уже существует
                old_message_id = user_data[0]
                try:
                    old_message = await thread.fetch_message(old_message_id)
                    await old_message.delete()  # Удаляем старое сообщение
                except discord.NotFound:
                    pass  # Сообщение уже удалено, пропускаем

            # Отправляем новое сообщение о поиске
            embed = discord.Embed(
                title="Користувач шукає команду",
                description=f"**<@{interaction.user.id}>** шукає команду для ролі **<@&{role_id}>**.",
                color=discord.Color.green()
            )
            msg = await thread.send(embed=embed)

            # Сохраняем ID нового сообщения в базу данных
            cursor.execute(
                "INSERT OR REPLACE INTO users (user_id, username, role_id, show_in_search, message_id) VALUES (?, ?, ?, ?, ?)",
                (interaction.user.id, interaction.user.name, role_id, 1, msg.id)
            )
            conn.commit()

            # Отправляем ответ с результатами поиска
            embed = discord.Embed(
                title=f"Результат пошуку **{role_name}**",
                description=f"{interaction.user.mention} **результати** вашого пошуку знаходяться у гілці ниже.",
                color=discord.Color.green()
            )
            await interaction.response.edit_message(embed=embed, view=create_search_view(True))

        async def select_role_callback(interaction):
            selected_role_id = int(interaction.data["values"][0])
            role_name = cursor.execute("SELECT role_name FROM roles WHERE role_id = ?", (selected_role_id,)).fetchone()[0]
            await create_search_view_after_role(interaction, role_name, selected_role_id)

        def create_search_view(show_in_search):
            view = View()
            search_button = Button(label="Пошук", style=discord.ButtonStyle.blurple)
            search_button.callback = lambda i: display_role_select(i)
            view.add_item(search_button)

            # Используем статус show_in_search для правильного отображения кнопки
            toggle_button = Button(
                label="Не відображати мене під час пошуку" if show_in_search else "Відображати мене під час пошуку",
                style=discord.ButtonStyle.red if show_in_search else discord.ButtonStyle.green
            )
            toggle_button.callback = lambda i: update_user_status(i, not show_in_search)
            view.add_item(toggle_button)
            return view

        async def display_role_select(interaction):
            roles = cursor.execute("SELECT * FROM roles").fetchall()
            if not roles:
                embed = discord.Embed(
                    title="Ролі не знайдено",
                    description="У базі даних немає доступних ролей для вибору.",
                    color=discord.Color.red()
                )
                await interaction.response.edit_message(embed=embed)
                return

            select_menu = Select(placeholder="Виберіть роль", options=[
                discord.SelectOption(label=role[1], value=str(role[0])) for role in roles
            ])
            select_menu.callback = select_role_callback

            embed = discord.Embed(
                title="Вибір параметрів пошуку",
                description="Будь ласка, виберіть потрібну роль зі списку.",
                color=discord.Color.light_grey()
            )
            await interaction.response.edit_message(embed=embed, view=View().add_item(select_menu))

        # Получаем статус пользователя для отображения правильной кнопки
        user_data = cursor.execute("SELECT show_in_search FROM users WHERE user_id = ?", (ctx.author.id,)).fetchone()
        show_in_search = user_data[0] if user_data else False

        embed = discord.Embed(
            title="Пошук команди",
            description="Будь ласка, натисніть кнопку пошук і виберіть параметри.",
            color=discord.Color.light_grey()
        )
        await ctx.send(embed=embed, view=create_search_view(show_in_search))

    return search

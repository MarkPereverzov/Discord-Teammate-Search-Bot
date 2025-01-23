import discord
from discord.ext import commands
from discord.ui import View, Button, Select
import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

def search(conn):
    cursor = conn.cursor()

    @commands.command()
    async def search(ctx):
        await ctx.message.delete()
        
        async def update_user_status(interaction, status):
            # Обновляем значение show_in_search в базе данных
            cursor.execute(
                "INSERT OR REPLACE INTO users (user_id, username, role_id, show_in_search) VALUES (?, ?, ?, ?)", 
                (interaction.user.id, interaction.user.name, None, status)
            )
            conn.commit()

            # Меняем текст кнопки в зависимости от статуса
            new_view = create_search_view(status)
            await interaction.response.edit_message(view=new_view)


        async def create_search_view_after_role(interaction, role_name, selected_role_id):
            # Создаем ветку (тред) для выбранной роли
            thread = await interaction.channel.create_thread(
                name=f"{role_name}",
                type=discord.ChannelType.public_thread
            )

            # Получаем список пользователей с выбранной ролью
            teammates = cursor.execute(
                "SELECT username FROM users WHERE role_id = ? AND show_in_search = 1", 
                (selected_role_id,)
            ).fetchall()

            if teammates:
                for teammate in teammates:
                    # Создаем embed для каждого пользователя
                    embed = discord.Embed(
                        title=f"Користувач шукає команду",
                        description=f"**<@{interaction.user.id}>** шукає команду для ролі **<@&{selected_role_id}>**.",
                        color=discord.Color.green()
                    )

                    # Добавляем кнопку "Написать в ЛС" для каждого embed
                    view = View()
                    write_dm_button = Button(label="Написати в ЛП", style=discord.ButtonStyle.blurple)

                    async def write_dm_callback(i, username=teammate[0]):
                        await i.user.send(f"Привіт! Ви можете зв'язатися з @{username} для пошуку команди.")
                        await i.response.send_message("Повідомлення надіслано!", ephemeral=True)

                    write_dm_button.callback = write_dm_callback
                    view.add_item(write_dm_button)

                    # Отправляем сообщение в ветку
                    await thread.send(embed=embed, view=view)
            else:
                # Если пользователей нет, отправляем сообщение об этом
                embed = discord.Embed(
                    title=f"{role_name}",
                    description="Поки що ніхто не шукає команду для цієї ролі.",
                    color=discord.Color.red()
                )
                await thread.send(embed=embed)

            # Обновляем сообщение с выбором роли
            embed = discord.Embed(
                title=f"Результат пошуку **{role_name}**",
                description=f"{ctx.author.mention} **результати** вашого пошуку знаходяться у гілці нижче.\n Якщо результату немає, спробуйте **змінити** запит.\n **Люди нижче** раніше включили показ себе в пошуку, значить шукали партнера, і можливо ще шукають.",
                color=discord.Color.green()
            )
            await interaction.response.edit_message(embed=embed, view=create_search_view(True))


        async def select_role_callback(interaction):
            selected_role_id = int(interaction.data["values"][0])
            role_name = cursor.execute("SELECT role_name FROM roles WHERE role_id = ?", (selected_role_id,)).fetchone()[0]

            # Добавляем или обновляем запись пользователя в базе данных
            cursor.execute(
                "INSERT OR REPLACE INTO users (user_id, username, role_id, show_in_search) VALUES (?, ?, ?, ?)", 
                (interaction.user.id, interaction.user.name, selected_role_id, 1)  # show_in_search = 1
            )
            conn.commit()

            # Создаем интерфейс после выбора роли
            await create_search_view_after_role(interaction, role_name, selected_role_id)


        def create_search_view(show_in_search):
            view = View()
            
            # Кнопка для поиска
            search_button = Button(label="Пошук", style=discord.ButtonStyle.blurple)
            search_button.callback = lambda i: display_role_select(i)
            view.add_item(search_button)

            # Кнопка переключения видимости
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

        embed = discord.Embed(
            title="Пошук команди",
            description="Будь ласка, натисніть кнопку пошук і виберіть параметри.",
            color=discord.Color.light_grey()
        )
        await ctx.send(embed=embed, view=create_search_view(False))

    return search

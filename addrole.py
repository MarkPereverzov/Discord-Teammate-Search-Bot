import discord
from discord.ext import commands
import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

def addrole():
    @commands.command()
    async def addrole(ctx, role: discord.Role):
        await ctx.message.delete()

        # Перевіряємо права адміністратора
        if ctx.author.guild_permissions.administrator:
            role_in_db = cursor.execute("SELECT * FROM roles WHERE role_id = ?", (role.id,)).fetchone()
            if role_in_db:
                embed = discord.Embed(
                    title="Додавання ролі",
                    description=f"Роль {role.mention} вже існує.",
                    color=discord.Color.light_grey()
                )
            else:
                # Додаємо роль базу даних
                cursor.execute("INSERT INTO roles (role_id, role_name) VALUES (?, ?)", (role.id, role.name))
                conn.commit()
                embed = discord.Embed(
                    title="Додавання ролі",
                    description=f"Роль {role.mention} успішно додана.",
                    color=discord.Color.light_grey()
                )
        else:
            embed = discord.Embed(
                title="Немає прав доступу",
                description="У вас немає прав для додавання ролей.",
                color=discord.Color.red()
            )

        await ctx.send(embed=embed)

    return addrole
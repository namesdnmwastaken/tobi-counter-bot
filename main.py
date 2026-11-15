import os
import sqlite3
import discord
from discord.ext import commands
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

db = sqlite3.connect("tobi_counter.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS counters (
    guild_id INTEGER,
    user_id INTEGER,
    count INTEGER DEFAULT 0,
    PRIMARY KEY (guild_id, user_id)
)
""")
db.commit()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()
    print("Slash commands synced!")


@bot.event
async def on_message(message):
    if message.author.bot or message.guild is None:
        return

    if "tobi" in message.content.lower():
        cursor.execute("""
        INSERT INTO counters (guild_id, user_id, count)
        VALUES (?, ?, 1)
        ON CONFLICT(guild_id, user_id)
        DO UPDATE SET count = count + 1
        """, (message.guild.id, message.author.id))

        db.commit()

        cursor.execute(
            "SELECT SUM(count) FROM counters WHERE guild_id = ?",
            (message.guild.id,)
        )
        total = cursor.fetchone()[0] or 0

        user = message.author.mention

        await message.channel.send(
            f"{user}\n"
            f"**Tobi Counter**\n"
            f"{user} has said Tobi! This has been said "
            f"**{total}** times. Want to see the leaderboard? "
            f"Do /leaderboard!"
        )

    await bot.process_commands(message)


@bot.tree.command(
    name="leaderboard",
    description="See who has said Tobi the most!"
)
async def leaderboard(interaction: discord.Interaction):

    cursor.execute("""
    SELECT user_id, count
    FROM counters
    WHERE guild_id = ?
    ORDER BY count DESC
    LIMIT 10
    """, (interaction.guild_id,))

    results = cursor.fetchall()

    if not results:
        await interaction.response.send_message(
            "Nobody has said Tobi yet!"
        )
        return

    embed = discord.Embed(
        title="🏆 Tobi Leaderboard",
        description="The people who have said Tobi the most!",
        color=discord.Color.gold()
    )

    medals = ["🥇", "🥈", "🥉"]

    for index, (user_id, count) in enumerate(results):
        medal = medals[index] if index < 3 else f"`#{index + 1}`"

        embed.add_field(
            name=f"{medal} <@{user_id}>",
            value=f"**{count}** times",
            inline=False
        )

    await interaction.response.send_message(embed=embed)


bot.run(TOKEN)

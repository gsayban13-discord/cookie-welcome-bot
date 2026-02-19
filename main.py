import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os
import aiosqlite
import random
from welcome_card import create_welcome_card

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

DB = "database.db"
GUILD_ID = 1459935661116100730

AI_MESSAGES = [
    "🌸 A new cutie has arrived! Welcome {user}!",
    "✨ Everyone say hiiii to {user}!",
    "💖 {user} just joined the cookie family!",
    "🎀 Welcome {user}! Hope you love it here!",
    "🐾 A wild {user} appeared!",
    "🍪 Fresh cookie delivered! Welcome {user}!",
    "🌷 {user} joined the cookie paradise!",
]

# ---------------- DATABASE SETUP ----------------

async def setup_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                guild_id INTEGER PRIMARY KEY,
                welcome_channel INTEGER,
                auto_role INTEGER,
                background TEXT,
                log_channel INTEGER,
                logger_enabled INTEGER DEFAULT 0
            )
            """
        )
        await db.commit()

# ---------------- BOT READY ----------------

@bot.event
async def on_ready():
    await setup_db()
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Logged in as {bot.user}")

# ---------------- MEMBER JOIN EVENT ----------------

@bot.event
async def on_member_join(member):
    async with aiosqlite.connect(DB) as db:
        cursor = await db.execute(
            "SELECT welcome_channel, auto_role, background FROM settings WHERE guild_id=?",
            (member.guild.id,),
        )
        row = await cursor.fetchone()

    if not row:
        return

    channel_id, role_id, bg_path = row

    channel = member.guild.get_channel(channel_id)
    role = member.guild.get_role(role_id)

    if role:
        await member.add_roles(role)

    card = await create_welcome_card(member, bg_path)

    if channel:
        message = random.choice(AI_MESSAGES).format(user=member.mention)
        await channel.send(
            message,
            file=discord.File(card, "welcome.png"),
        )

# ---------------- MESSAGE DELETE EVENT ----------------

@bot.event
async def on_message_delete(message):

    if message.author.bot:
        return

    async with aiosqlite.connect(DB) as db:
        cursor = await db.execute(
            "SELECT log_channel, logger_enabled FROM settings WHERE guild_id=?",
            (message.guild.id,)
        )
        row = await cursor.fetchone()

    if not row or not row[1]:
        return

    log_channel = message.guild.get_channel(row[0])
    if not log_channel:
        return

    embed = discord.Embed(
        title="🗑️ Message Deleted",
        color=discord.Color.red()
    )

    embed.add_field(name="Author", value=message.author.mention, inline=True)
    embed.add_field(name="Channel", value=message.channel.mention, inline=True)

    if message.content:
        embed.add_field(name="Content", value=message.content[:1000], inline=False)

    embed.set_footer(text=f"User ID: {message.author.id}")

    await log_channel.send(embed=embed)

# ---------------- MESSAGE EDIT EVENT ----------------

@bot.event
async def on_message_edit(before, after):

    if before.author.bot:
        return

    if before.content == after.content:
        return

    async with aiosqlite.connect(DB) as db:
        cursor = await db.execute(
            "SELECT log_channel, logger_enabled FROM settings WHERE guild_id=?",
            (before.guild.id,)
        )
        row = await cursor.fetchone()

    if not row or not row[1]:
        return

    log_channel = before.guild.get_channel(row[0])
    if not log_channel:
        return

    embed = discord.Embed(
        title="✏️ Message Edited",
        color=discord.Color.orange()
    )

    embed.add_field(name="Author", value=before.author.mention, inline=True)
    embed.add_field(name="Channel", value=before.channel.mention, inline=True)

    embed.add_field(name="Before", value=before.content[:1000] or "*empty*", inline=False)
    embed.add_field(name="After", value=after.content[:1000] or "*empty*", inline=False)

    embed.set_footer(text=f"User ID: {before.author.id}")

    await log_channel.send(embed=embed)

# ---------------- TOGGLE LOGGER ----------------
@tree.command(name="togglelogger", description="Enable or disable message logger",
              guild=discord.Object(id=1459935661116100730))
@app_commands.checks.has_permissions(administrator=True)
async def togglelogger(interaction: discord.Interaction):

    async with aiosqlite.connect(DB) as db:
        cursor = await db.execute(
            "SELECT logger_enabled FROM settings WHERE guild_id=?",
            (interaction.guild.id,)
        )
        row = await cursor.fetchone()

        new_value = 0 if row and row[0] else 1

        await db.execute("""
            INSERT INTO settings (guild_id, logger_enabled)
            VALUES (?, ?)
            ON CONFLICT(guild_id)
            DO UPDATE SET logger_enabled=excluded.logger_enabled
        """, (interaction.guild.id, new_value))
        await db.commit()

    status = "enabled" if new_value else "disabled"
    await interaction.response.send_message(f"✅ Logger {status}!", ephemeral=True)


# ---------------- SET log channel ----------------
@tree.command(name="setlogchannel", description="Set private message log channel",
              guild=discord.Object(id=1459935661116100730))
@app_commands.checks.has_permissions(administrator=True)
async def setlogchannel(interaction: discord.Interaction, channel: discord.TextChannel):

    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            INSERT INTO settings (guild_id, log_channel, logger_enabled)
            VALUES (?, ?, 1)
            ON CONFLICT(guild_id)
            DO UPDATE SET log_channel=excluded.log_channel, logger_enabled=1
        """, (interaction.guild.id, channel.id))
        await db.commit()

    await interaction.response.send_message("✅ Log channel set!", ephemeral=True)

# ---------------- SET BACKGROUND ----------------

@tree.command(
    name="setbackground",
    description="Upload custom background",
    guild=discord.Object(id=1459935661116100730),
)
@app_commands.checks.has_permissions(administrator=True)
async def setbackground(interaction: discord.Interaction, image: discord.Attachment):
    if not image.content_type or not image.content_type.startswith("image"):
        await interaction.response.send_message(
            "❌ Upload an image.", ephemeral=True
        )
        return

    os.makedirs("backgrounds", exist_ok=True)
    path = f"backgrounds/{interaction.guild.id}.png"
    await image.save(path)

    async with aiosqlite.connect(DB) as db:
        await db.execute(
            """
            INSERT INTO settings (guild_id, background)
            VALUES (?, ?)
            ON CONFLICT(guild_id)
            DO UPDATE SET background=excluded.background
            """,
            (interaction.guild.id, path),
        )
        await db.commit()

    await interaction.response.send_message("✅ Background saved!", ephemeral=True)

# ---------------- SET CHANNEL ----------------

@tree.command(
    name="setchannel",
    description="Set welcome channel",
    guild=discord.Object(id=1459935661116100730),
)
@app_commands.checks.has_permissions(administrator=True)
async def setchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            """
            INSERT INTO settings (guild_id, welcome_channel)
            VALUES (?, ?)
            ON CONFLICT(guild_id)
            DO UPDATE SET welcome_channel=excluded.welcome_channel
            """,
            (interaction.guild.id, channel.id),
        )
        await db.commit()

    await interaction.response.send_message("✅ Channel set!", ephemeral=True)

# ---------------- SET ROLE ----------------

@tree.command(
    name="setrole",
    description="Set auto role",
    guild=discord.Object(id=1459935661116100730),
)
@app_commands.checks.has_permissions(administrator=True)
async def setrole(interaction: discord.Interaction, role: discord.Role):
    async with aiosqlite.connect(DB) as db: 
        await db.execute(
            """
            INSERT INTO settings (guild_id, auto_role)
            VALUES (?, ?)
            ON CONFLICT(guild_id)
            DO UPDATE SET auto_role=excluded.auto_role
            """,
            (interaction.guild.id, role.id),
        )
        await db.commit()

    await interaction.response.send_message("✅ Role set!", ephemeral=True)

bot.run(TOKEN)

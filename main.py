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
                background TEXT
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

# ---------------- SET BACKGROUND ----------------

@tree.command(
    name="setbackground",
    description="Upload custom background",
    guild=discord.Object(id=GUILD_ID),
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
    guild=discord.Object(id=GUILD_ID),
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
    guild=discord.Object(id=GUILD_ID),
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

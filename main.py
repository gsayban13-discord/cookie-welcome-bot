import discord
import discord.opus
from discord.ext import commands
from dotenv import load_dotenv
import os
from motor.motor_asyncio import AsyncIOMotorClient

if not discord.opus.is_loaded():
    try:
        discord.opus.load_opus("libopus.so.0")
    except OSError:
        print("⚠️ Opus not found, voice receive may not work")

load_dotenv()

TOKEN = os.getenv("TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ---------- DATABASE ----------
mongo_client = AsyncIOMotorClient(MONGO_URI)
bot.db = mongo_client["cookie_bot"]
bot.settings_col = bot.db["settings"]


# ---------- LOAD COGS ----------
@bot.event
async def on_ready():

    guild = discord.Object(id=1459935661116100730)

    # 2️⃣ Sync commands ONLY to your guild
    synced = await bot.tree.sync(guild=guild)

    print(f"✅ Synced {len(synced)} guild commands")

    print("====================================")
    print(f"🤖 Logged in as: {bot.user}")
    print(f"🧠 Connected to MongoDB: {bot.db.name}")
    print("🚀 Bot is fully ready!")
    print("====================================")

async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Loaded cog: {filename}")
            except Exception as e:
                print(f"❌ Failed to load {filename}: {e}")


async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


import asyncio

asyncio.run(main())







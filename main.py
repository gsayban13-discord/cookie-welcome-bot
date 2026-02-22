import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os
import random
import asyncio
import requests
from motor.motor_asyncio import AsyncIOMotorClient
from welcome_card import create_welcome_card

load_dotenv()

TOKEN = os.getenv("TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

# ---------------- DISCORD ----------------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree
GUILD_ID = 1459935661116100730

# ---------------- MONGODB ----------------
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["cookie_bot"]
settings_col = db["settings"]

async def get_settings(guild_id):
    data = await settings_col.find_one({"guild_id": guild_id})
    return data or {}

async def update_settings(guild_id, updates: dict):
    await settings_col.update_one(
        {"guild_id": guild_id},
        {"$set": updates},
        upsert=True
    )

# ---------------- AI MESSAGES ----------------
AI_MESSAGES = [
    "🌸 A new cutie has arrived! Welcome {user}!",
    "✨ Everyone say hiiii to {user}!",
    "💖 {user} just joined the cookie family!",
    "🎀 Welcome {user}! Hope you love it here!",
    "🐾 A wild {user} appeared!",
    "🍪 Fresh cookie delivered! Welcome {user}!",
    "🌷 {user} joined the cookie paradise!",
]

# ---------------- READY ----------------
@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    bot.loop.create_task(check_tiktok_live())
    print(f"Logged in as {bot.user}")

# ---------------- MEMBER JOIN ----------------
@bot.event
async def on_member_join(member):
    settings = await get_settings(member.guild.id)

    channel_id = settings.get("welcome_channel")
    role_id = settings.get("auto_role")

    if role_id:
        role = member.guild.get_role(role_id)
        if role:
            await member.add_roles(role)

    if channel_id:
        channel = member.guild.get_channel(channel_id)
        if channel:
            card = await create_welcome_card(member)
            message = random.choice(AI_MESSAGES).format(user=member.mention)

            await channel.send(
                message,
                file=discord.File(card, "welcome.png")
            )

# ---------------- LOGGER ----------------
@bot.event
async def on_raw_message_delete(payload):

    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return

    settings = await get_settings(guild.id)

    if not settings.get("logger_enabled"):
        return

    log_channel = guild.get_channel(settings.get("log_channel"))
    if not log_channel:
        return

    channel = guild.get_channel(payload.channel_id)

    embed = discord.Embed(
        title="🗑️ Message Deleted",
        color=discord.Color.red()
    )

    embed.add_field(name="Channel", value=channel.mention if channel else "Unknown")

    # Try to get cached message (may or may not exist)
    if payload.cached_message:
        msg = payload.cached_message

    # Ignore bots
        if msg.author.bot:
            return

    embed.add_field(name="Author", value=msg.author.mention)

    # TEXT CONTENT
    if msg.content:
        embed.add_field(
            name="Content",
            value=msg.content[:1000],
            inline=False
        )

    # 📎 ATTACHMENTS
    if msg.attachments:
        files = []
        image_url = None

        for att in msg.attachments:
            files.append(att.filename)

            # If it's an image, show preview
            if att.content_type and "image" in att.content_type:
                image_url = att.url

        embed.add_field(
            name="Attachments",
            value="\n".join(files),
            inline=False
        )

        # Show first image preview
        if image_url:
            embed.set_image(url=image_url)

    await log_channel.send(embed=embed)

@bot.event
async def on_raw_message_edit(payload):

    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return

    settings = await get_settings(guild.id)
    if not settings.get("logger_enabled"):
        return

    log_channel = guild.get_channel(settings.get("log_channel"))
    if not log_channel:
        return

    if payload.cached_message:
        before = payload.cached_message

        if before.author.bot:
            return

        after = payload.data.get("content")

        if not after or before.content == after:
            return

        embed = discord.Embed(
            title="✏️ Message Edited",
            color=discord.Color.orange()
        )

        embed.add_field(name="Author", value=before.author.mention)
        embed.add_field(name="Channel", value=f"<#{payload.channel_id}>")
        embed.add_field(name="Before", value=before.content[:1000], inline=False)
        embed.add_field(name="After", value=after[:1000], inline=False)

        if before.attachments:
            files = []
            image_url = None

            for att in before.attachments:
                files.append(f"[{att.filename}]({att.url})")

                if att.content_type and "image" in att.content_type:
                    image_url = att.url

        embed.add_field(
            name="Attachments",
            value="\n".join(files),
            inline=False
        )

        if image_url:
            embed.set_image(url=image_url)
            
        await log_channel.send(embed=embed)

# ---------------- VOICE VIP ----------------
@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is None and after.channel is not None:

        settings = await get_settings(member.guild.id)

        if not settings.get("voice_vip_enabled"):
            return

        if member.id != settings.get("voice_vip_user"):
            return

        msg = settings.get("voice_vip_message", "🎤 {user} joined voice!")

        msg = msg.replace("{user}", member.mention)
        msg = msg.replace("{channel}", after.channel.name)

        try:
            await after.channel.send(msg, delete_after=20)
        except:
            fallback = member.guild.get_channel(settings.get("log_channel"))
            if fallback:
                await fallback.send(msg, delete_after=20)

def get_tiktok_thumbnail(html):
    import re
    
    patterns = [
        r'property="og:image" content="([^"]+)"',
        r'property=\'og:image\' content=\'([^\']+)\'',
        r'name="og:image" content="([^"]+)"',
        r'name=\'og:image\' content=\'([^\']+)\''
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            return match.group(1)
    
    return None

# ---------------- TIKTOK CHECK ----------------
async def check_tiktok_live():
    await bot.wait_until_ready()

    while not bot.is_closed():
        async for settings in settings_col.find({"tiktok_username": {"$exists": True}}):

            guild = bot.get_guild(settings["guild_id"])
            if not guild:
                continue

            username = settings["tiktok_username"]
            channel_id = settings.get("tiktok_channel")
            was_live = settings.get("tiktok_live", 0)

            try:
                url = f"https://www.tiktok.com/@{username}/live"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9"
}
                response = requests.get(url, headers=headers)
                html = response.text

                is_live = "LIVE" in html

                thumbnail = get_tiktok_thumbnail(html)

                if is_live and not was_live:
                    channel = guild.get_channel(channel_id)

                    if channel:
                        embed = discord.Embed(
                            title="🔴 LIVE ON TIKTOK!",
                            description=f"**{username}** is streaming right now!",
                            color=discord.Color.red()
                        )

                        embed.add_field(
                            name="🎥 Watch the Stream",
                            value=f"[Click here to join](https://www.tiktok.com/@{username}/live)",
                            inline=False
                        )

                        embed.set_footer(text="TikTok Live Notification")
                        if thumbnail:
                            embed.set_image(url=thumbnail)
                            
                        await channel.send(
                            content=f"@everyone\n\nhttps://www.tiktok.com/@{username}/live",
                            embed=embed,
                            allowed_mentions=discord.AllowedMentions(everyone=True)
                        )

                    await update_settings(guild.id, {"tiktok_live": 1})

                elif not is_live and was_live:
                    await update_settings(guild.id, {"tiktok_live": 0})

            except Exception as e:
                print("TikTok error:", e)

        await asyncio.sleep(180)

# ---------------- COMMANDS ----------------
@tree.command(name="setchannel", description="Set welcome channel", guild=discord.Object(id=GUILD_ID))
async def setchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    await update_settings(interaction.guild.id, {"welcome_channel": channel.id})
    await interaction.response.send_message("✅ Welcome channel set!", ephemeral=True)

@tree.command(name="setrole", description="Set the role automatically given to new members", guild=discord.Object(id=GUILD_ID))
async def setrole(interaction: discord.Interaction, role: discord.Role):
    await update_settings(interaction.guild.id, {"auto_role": role.id})
    await interaction.response.send_message("✅ Role set!", ephemeral=True)

@tree.command(name="setlogchannel", description="Set the channel where deleted/edited messages will be logged", guild=discord.Object(id=GUILD_ID))
async def setlogchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    await update_settings(interaction.guild.id, {"log_channel": channel.id, "logger_enabled": 1})
    await interaction.response.send_message("✅ Log channel set!", ephemeral=True)

@tree.command(name="togglelogger", description="Enable or disable the message logging system", guild=discord.Object(id=GUILD_ID))
async def togglelogger(interaction: discord.Interaction):
    settings = await get_settings(interaction.guild.id)
    new_val = 0 if settings.get("logger_enabled") else 1
    await update_settings(interaction.guild.id, {"logger_enabled": new_val})
    await interaction.response.send_message("✅ Logger toggled!", ephemeral=True)

@tree.command(name="settiktok", description="Set the TikTok username to monitor for live streams", guild=discord.Object(id=GUILD_ID))
async def settiktok(interaction: discord.Interaction, username: str):
    await update_settings(interaction.guild.id, {"tiktok_username": username})
    await interaction.response.send_message("✅ TikTok username saved!", ephemeral=True)

@tree.command(name="settiktokchannel", description="Set the channel where TikTok live alerts will be posted", guild=discord.Object(id=GUILD_ID))
async def settiktokchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    await update_settings(interaction.guild.id, {"tiktok_channel": channel.id})
    await interaction.response.send_message("✅ TikTok channel set!", ephemeral=True)

# ---------------- DEBUG: WELCOME PREVIEW ----------------
@tree.command(name="showwelcomepreview", description="Preview welcome message",
              guild=discord.Object(id=GUILD_ID))
async def showwelcomepreview(interaction: discord.Interaction, user: discord.Member):

    await interaction.response.defer()

    settings = await get_settings(interaction.guild.id)
    bg_path = settings.get("background")

    card = await create_welcome_card(user, bg_path)
    message = random.choice(AI_MESSAGES).format(user=user.mention)

    await interaction.followup.send(
        message,
        file=discord.File(card, "welcome.png")
    )


# ---------------- DEBUG: TIKTOK PREVIEW ----------------
@tree.command(name="showliveannouncement", description="Preview TikTok live announcement",
              guild=discord.Object(id=GUILD_ID))
async def showliveannouncement(interaction: discord.Interaction):

    settings = await get_settings(interaction.guild.id)
    username = settings.get("tiktok_username")

    if not username:
        await interaction.response.send_message(
            "❌ TikTok username not set.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    url = f"https://www.tiktok.com/@{username}/live"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    response = requests.get(url, headers=headers)
    html = response.text

    # Check if live
    is_live = "LIVE" in html

    # Extract thumbnail
    thumbnail = get_tiktok_thumbnail(html)

    # Build embed based on status
    if is_live:
        embed = discord.Embed(
            title="🔴 LIVE ON TIKTOK!",
            description=f"**{username}** is streaming right now!",
            color=discord.Color.red()
        )
    else:
        embed = discord.Embed(
            title="⚫ NOT LIVE",
            description=f"**{username}** is currently offline.",
            color=discord.Color.dark_grey()
        )

    embed.add_field(
        name="🎥 Watch Page",
        value=f"[Click here]({url})",
        inline=False
    )

    embed.set_footer(text="TikTok Live Debug Preview")

    if thumbnail:
        embed.set_image(url=thumbnail)

    await interaction.followup.send(embed=embed)

    # ---------------- DEBUG: SHOW SETTINGS ----------------
@tree.command(name="showsettings", description="View current bot settings",
              guild=discord.Object(id=GUILD_ID))
async def showsettings(interaction: discord.Interaction):

    settings = await get_settings(interaction.guild.id)

    embed = discord.Embed(
        title="⚙️ Bot Settings",
        color=discord.Color.purple()
    )

    # Welcome
    welcome_channel = settings.get("welcome_channel")
    auto_role = settings.get("auto_role")

    embed.add_field(
        name="👋 Welcome System",
        value=f"Channel: {f'<#{welcome_channel}>' if welcome_channel else 'Not set'}\n"
              f"Auto Role: {f'<@&{auto_role}>' if auto_role else 'Not set'}",
        inline=False
    )

    # Logger
    logger_channel = settings.get("log_channel")
    logger_enabled = settings.get("logger_enabled")

    embed.add_field(
        name="📝 Logger",
        value=f"Enabled: {'✅ Yes' if logger_enabled else '❌ No'}\n"
              f"Channel: {f'<#{logger_channel}>' if logger_channel else 'Not set'}",
        inline=False
    )

    # TikTok
    tiktok_user = settings.get("tiktok_username")
    tiktok_channel = settings.get("tiktok_channel")

    embed.add_field(
        name="🎵 TikTok Notifier",
        value=f"Username: {tiktok_user if tiktok_user else 'Not set'}\n"
              f"Channel: {f'<#{tiktok_channel}>' if tiktok_channel else 'Not set'}",
        inline=False
    )

    # Voice VIP
    vip_user = settings.get("voice_vip_user")
    vip_enabled = settings.get("voice_vip_enabled")

    embed.add_field(
        name="🎤 VIP Voice Welcome",
        value=f"Enabled: {'✅ Yes' if vip_enabled else '❌ No'}\n"
              f"VIP User: {f'<@{vip_user}>' if vip_user else 'Not set'}",
        inline=False
    )

    # Background
    bg = settings.get("background")

    embed.add_field(
        name="🎨 Welcome Background",
        value="Custom Background Set" if bg else "Default",
        inline=False
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(
    name="setvoicevip",
    description="Set which user receives a special voice join welcome",
    guild=discord.Object(id=GUILD_ID)
)
async def setvoicevip(interaction: discord.Interaction, user: discord.Member):

    await update_settings(interaction.guild.id, {
        "voice_vip_user": user.id
    })

    await interaction.response.send_message(
        f"✅ VIP voice user set to {user.mention}",
        ephemeral=True
    )

@tree.command(
    name="setvoicemsg",
    description="Set the custom message when the VIP joins voice",
    guild=discord.Object(id=GUILD_ID)
)
async def setvoicemsg(interaction: discord.Interaction, message: str):

    await update_settings(interaction.guild.id, {
        "voice_vip_message": message
    })

    await interaction.response.send_message(
        "✅ VIP voice message saved!",
        ephemeral=True
    )

@tree.command(
    name="togglevoicevip",
    description="Enable or disable VIP voice welcome feature",
    guild=discord.Object(id=GUILD_ID)
)
async def togglevoicevip(interaction: discord.Interaction):

    settings = await get_settings(interaction.guild.id)
    new_val = 0 if settings.get("voice_vip_enabled") else 1

    await update_settings(interaction.guild.id, {
        "voice_vip_enabled": new_val
    })

    status = "enabled" if new_val else "disabled"

    await interaction.response.send_message(
        f"✅ VIP voice welcome {status}",
        ephemeral=True
    )

bot.run(TOKEN)




















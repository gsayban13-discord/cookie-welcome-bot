import discord
from discord.ext import commands
from discord import app_commands
from welcome_card import create_welcome_card
from datetime import datetime, timedelta, timezone
import asyncio

GUILD_ID = 1459935661116100730

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==============================
    # 🎂 BIRTHDAY COMMANDS
    # ==============================

    @app_commands.command(name="setbirthdaychannel", description="Set birthday channel")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def setbirthdaychannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"birthday_channel": channel.id}},
            upsert=True
        )
        await interaction.followup.send("✅ Birthday channel set!")

    @app_commands.command(name="setbirthdayrole", description="Set birthday role")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def setbirthdayrole(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer(ephemeral=True)
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"birthday_role": role.id}},
            upsert=True
        )
        await interaction.followup.send("✅ Birthday role set!")

    @app_commands.command(name="deletebirthday", description="Delete a user's birthday")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def deletebirthday(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)
        result = await self.bot.db.birthdays.delete_one(
            {"guild_id": interaction.guild.id, "user_id": user.id}
        )
        if result.deleted_count == 0:
            return await interaction.followup.send("❌ No birthday found for that user.")
        await interaction.followup.send(f"🗑️ Birthday deleted for {user.mention}.")

    @app_commands.command(name="testbirthday", description="Test birthday greeting")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def testbirthday(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)
        settings = await self.bot.settings_col.find_one({"guild_id": interaction.guild.id}) or {}
        channel_id = settings.get("birthday_channel")
        if not channel_id:
            return await interaction.followup.send("❌ Birthday channel not set.")
        
        channel = interaction.guild.get_channel(channel_id)
        await channel.send(f"🎉 Happy Birthday {user.mention}! (Test Mode)")
        await interaction.followup.send("✅ Birthday test sent!")

    # ==============================
    # 👋 WELCOME SYSTEM
    # ==============================

    @app_commands.command(name="setchannel", description="Set welcome channel")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def setchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"welcome_channel": channel.id}},
            upsert=True
        )
        await interaction.followup.send("✅ Welcome channel set!")

    @app_commands.command(name="setrole", description="Set auto role")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def setrole(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer(ephemeral=True)
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"auto_role": role.id}},
            upsert=True
        )
        await interaction.followup.send("✅ Role set!")

    # ==============================
    # 📝 LOGGER
    # ==============================

    @app_commands.command(name="setlogchannel", description="Set logger channel")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def setlogchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"log_channel": channel.id, "logger_enabled": 1}},
            upsert=True
        )
        await interaction.followup.send("✅ Log channel set!")

    @app_commands.command(name="togglelogger", description="Toggle logger")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def togglelogger(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        settings = await self.bot.settings_col.find_one({"guild_id": interaction.guild.id}) or {}
        new_val = 0 if settings.get("logger_enabled") else 1
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"logger_enabled": new_val}},
            upsert=True
        )
        await interaction.followup.send(f"✅ Logger {'enabled' if new_val else 'disabled'}!")

    # ==============================
    # 🎤 VOICE VIP SETTINGS
    # ==============================

    @app_commands.command(name="setvoicevip", description="Set VIP user")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def setvoicevip(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"voice_vip_user": user.id}},
            upsert=True
        )
        await interaction.followup.send(f"✅ VIP set to {user.mention}!")

    @app_commands.command(name="setvoicemsg", description="Set VIP join message")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def setvoicemsg(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer(ephemeral=True)
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"voice_vip_message": message}},
            upsert=True
        )
        await interaction.followup.send("✅ Join message set!")

    @app_commands.command(name="setvoicecammsg", description="Set VIP camera message")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def setvoicecammsg(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer(ephemeral=True)
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"voice_vip_cam_message": message}},
            upsert=True
        )
        await interaction.followup.send("✅ Camera message set!")

    @app_commands.command(name="togglevoicevip", description="Toggle VIP voice alerts")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def togglevoicevip(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        settings = await self.bot.settings_col.find_one({"guild_id": interaction.guild.id}) or {}
        new_val = 0 if settings.get("voice_vip_enabled") else 1
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"voice_vip_enabled": new_val}},
            upsert=True
        )
        await interaction.followup.send(f"✅ Voice VIP {'enabled' if new_val else 'disabled'}!")

    # ==============================
    # 🎶 MUSIC SETTINGS
    # ==============================

    @app_commands.command(name="setmusicchannel", description="Set music channel")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def setmusicchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"music_channel": channel.id}},
            upsert=True
        )
        await interaction.followup.send("✅ Music channel set!")

    @app_commands.command(name="togglemusic", description="Toggle music")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def togglemusic(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        settings = await self.bot.settings_col.find_one({"guild_id": interaction.guild.id}) or {}
        new_val = 0 if settings.get("music_enabled") else 1
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"music_enabled": new_val}},
            upsert=True
        )
        await interaction.followup.send(f"✅ Music {'enabled' if new_val else 'disabled'}!")

    # ==============================
    # 📊 POLL SETTINGS
    # ==============================

    @app_commands.command(name="setpollchannel", description="Set poll channel")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def setpollchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"poll_channel": channel.id}},
            upsert=True
        )
        await interaction.followup.send("✅ Poll channel set!")

    @app_commands.command(name="togglepoll", description="Toggle polls")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def togglepoll(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        settings = await self.bot.settings_col.find_one({"guild_id": interaction.guild.id}) or {}
        new_val = 0 if settings.get("poll_enabled") else 1
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"poll_enabled": new_val}},
            upsert=True
        )
        await interaction.followup.send(f"✅ Polls {'enabled' if new_val else 'disabled'}!")

    # ==============================
    # 🆕 PATCH TRACKING
    # ==============================

    @app_commands.command(name="setpatchchannel", description="Set patch channel")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def setpatchchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"patch_channel": channel.id}},
            upsert=True
        )
        await interaction.followup.send("✅ Patch channel set!")

    @app_commands.command(name="addleaguepatch", description="Track League patches")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def addleaguepatch(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$push": {"patch_games": {"type": "league", "name": "League of Legends", "last_patch": None}}},
            upsert=True
        )
        await interaction.followup.send("🧠 League tracking enabled!")

    @app_commands.command(name="addvalorantpatch", description="Track Valorant patches")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def addvalorantpatch(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$push": {"patch_games": {"type": "valorant", "name": "Valorant", "last_patch": None}}},
            upsert=True
        )
        await interaction.followup.send("🎯 Valorant tracking enabled!")

    @app_commands.command(name="removepatchgame", description="Stop tracking a game")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def removepatchgame(self, interaction: discord.Interaction, game: str):
        await interaction.response.defer(ephemeral=True)
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$pull": {"patch_games": {"name": {"$regex": f"^{game}$", "$options": "i"}}}}
        )
        await interaction.followup.send(f"🗑 Removed tracking for {game}.")

    # ==============================
    # 🛠️ PREVIEW & INFO
    # ==============================

    @app_commands.command(name="showwelcomepreview", description="Preview welcome card")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def showwelcomepreview(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer()
        card = await create_welcome_card(user)
        await interaction.followup.send(file=discord.File(card, "welcome.png"))

    @app_commands.command(name="showsettings", description="View all settings")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def showsettings(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        s = await self.bot.settings_col.find_one({"guild_id": interaction.guild.id}) or {}
        embed = discord.Embed(title="⚙️ Current Settings", color=discord.Color.blue())
        embed.add_field(name="Welcome", value=f"Ch: <#{s.get('welcome_channel')}> | Role: <@&{s.get('auto_role')}>", inline=False)
        embed.add_field(name="Logger", value=f"Enabled: {s.get('logger_enabled')} | Ch: <#{s.get('log_channel')}>", inline=False)
        embed.add_field(name="Music/Polls", value=f"Music: {s.get('music_enabled')} | Polls: {s.get('poll_enabled')}", inline=False)
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Settings(bot))

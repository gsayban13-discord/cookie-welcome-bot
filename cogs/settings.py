import discord
from discord.ext import commands
from discord import app_commands
from welcome_card import create_welcome_card

GUILD_ID = 1459935661116100730


class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---------- SET WELCOME CHANNEL ----------
    @app_commands.command(name="setchannel", description="Set welcome channel")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def setchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"welcome_channel": channel.id}},
            upsert=True
        )
        await interaction.response.send_message("✅ Welcome channel set!", ephemeral=True)

    # ---------- SET ROLE ----------
    @app_commands.command(name="setrole", description="Set auto role")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def setrole(self, interaction: discord.Interaction, role: discord.Role):
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"auto_role": role.id}},
            upsert=True
        )
        await interaction.response.send_message("✅ Role set!", ephemeral=True)

    # ---------- LOGGER ----------
    @app_commands.command(name="setlogchannel", description="Set logger channel")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def setlogchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"log_channel": channel.id, "logger_enabled": 1}},
            upsert=True
        )
        await interaction.response.send_message("✅ Log channel set!", ephemeral=True)

    @app_commands.command(name="togglelogger", description="Toggle logger")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def togglelogger(self, interaction: discord.Interaction):
        settings = await self.bot.settings_col.find_one({"guild_id": interaction.guild.id}) or {}
        new_val = 0 if settings.get("logger_enabled") else 1

        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"logger_enabled": new_val}},
            upsert=True
        )

        await interaction.response.send_message("✅ Logger toggled!", ephemeral=True)

    # ---------- TIKTOK ----------
    @app_commands.command(name="settiktok", description="Set TikTok username")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def settiktok(self, interaction: discord.Interaction, username: str):
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"tiktok_username": username}},
            upsert=True
        )
        await interaction.response.send_message("✅ TikTok saved!", ephemeral=True)

    @app_commands.command(name="settiktokchannel", description="Set TikTok alert channel")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def settiktokchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"tiktok_channel": channel.id}},
            upsert=True
        )
        await interaction.response.send_message("✅ TikTok channel set!", ephemeral=True)

    # ---------- VOICE VIP ----------
    @app_commands.command(name="setvoicevip", description="Set VIP user")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def setvoicevip(self, interaction: discord.Interaction, user: discord.Member):
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"voice_vip_user": user.id}},
            upsert=True
        )
        await interaction.response.send_message("✅ VIP user set!", ephemeral=True)

    @app_commands.command(name="setvoicemsg", description="Set VIP voice message")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def setvoicemsg(self, interaction: discord.Interaction, message: str):
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"voice_vip_message": message}},
            upsert=True
        )
        await interaction.response.send_message("✅ VIP message saved!", ephemeral=True)

    @app_commands.command(name="setvoicecammsg", description="Set VIP camera ON message")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def setvoicecammsg(self, interaction: discord.Interaction, message: str):
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"voice_vip_cam_message": message}},
            upsert=True
        )
        await interaction.response.send_message("✅ VIP camera message saved!", ephemeral=True)

    @app_commands.command(name="togglevoicevip", description="Toggle VIP voice")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def togglevoicevip(self, interaction: discord.Interaction):
        settings = await self.bot.settings_col.find_one({"guild_id": interaction.guild.id}) or {}
        new_val = 0 if settings.get("voice_vip_enabled") else 1

        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"voice_vip_enabled": new_val}},
            upsert=True
        )

        await interaction.response.send_message("✅ Voice VIP toggled!", ephemeral=True)

    # ---------- DEBUG ----------
    @app_commands.command(name="showwelcomepreview", description="Preview welcome card")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def showwelcomepreview(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer()
        card = await create_welcome_card(user)
        await interaction.followup.send(
            f"Preview for {user.mention}",
            file=discord.File(card, "welcome.png")
        )

    @app_commands.command(name="showsettings", description="View bot settings")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def showsettings(self, interaction: discord.Interaction):

        settings = await self.bot.settings_col.find_one({"guild_id": interaction.guild.id}) or {}

        embed = discord.Embed(title="⚙️ Bot Settings", color=discord.Color.purple())

        embed.add_field(
            name="👋 Welcome",
            value=f"Channel: {settings.get('welcome_channel', 'Not set')}\n"
                  f"Role: {settings.get('auto_role', 'Not set')}",
            inline=False
        )

        embed.add_field(
            name="📝 Logger",
            value=f"Enabled: {settings.get('logger_enabled', 0)}\n"
                  f"Channel: {settings.get('log_channel', 'Not set')}",
            inline=False
        )

        embed.add_field(
            name="🎵 TikTok",
            value=f"User: {settings.get('tiktok_username', 'Not set')}\n"
                  f"Channel: {settings.get('tiktok_channel', 'Not set')}",
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="showliveannouncement", description="Preview TikTok live announcement")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def showliveannouncement(self, interaction: discord.Interaction):

        settings = await self.bot.settings_col.find_one({"guild_id": interaction.guild.id}) or {}
        username = settings.get("tiktok_username")

        if not username:
            await interaction.response.send_message("❌ TikTok username not set.", ephemeral=True)
            return

        await interaction.response.defer()

        from utils.tiktok_scraper import fetch_tiktok_page
        is_live, thumbnail, url = await fetch_tiktok_page(username)

        embed = discord.Embed(
            title="🔴 LIVE ON TIKTOK!",
            description=f"**{username}** is streaming right now!",
            color=discord.Color.red()
        )

        embed.add_field(
            name="🎥 Join the stream now!",
            value=f"[Watch here]({url})",
            inline=False
        )

        embed.set_footer(text="TikTok Live Debug Preview")

        if thumbnail:
            embed.set_image(url=thumbnail)

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Settings(bot))

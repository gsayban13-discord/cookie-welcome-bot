import discord
from discord.ext import commands
from discord import app_commands
from welcome_card import create_welcome_card

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
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"birthday_channel": channel.id}},
            upsert=True
        )
        await interaction.response.send_message("✅ Birthday channel set!", ephemeral=True)

    @app_commands.command(name="setbirthdayrole", description="Set birthday role")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def setbirthdayrole(self, interaction: discord.Interaction, role: discord.Role):
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"birthday_role": role.id}},
            upsert=True
        )
        await interaction.response.send_message("✅ Birthday role set!", ephemeral=True)

    @app_commands.command(name="deletebirthday", description="Delete a user's birthday")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def deletebirthday(self, interaction: discord.Interaction, user: discord.Member):

        result = await self.bot.db.birthdays.delete_one(
            {"guild_id": interaction.guild.id, "user_id": user.id}
        )

        if result.deleted_count == 0:
            await interaction.response.send_message(
                "❌ No birthday found for that user.",
                ephemeral=True
            )
            return

        birthday_cog = self.bot.get_cog("Birthday")
        if birthday_cog:
            await birthday_cog.update_birthday_list(interaction.guild)

        await interaction.response.send_message(
            f"🗑️ Birthday deleted for {user.mention}.",
            ephemeral=True
        )

    # ⭐ NEW COMMAND — TEST BIRTHDAY
    @app_commands.command(name="testbirthday", description="Test birthday greeting for a user")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def testbirthday(self, interaction: discord.Interaction, user: discord.Member):

        settings = await self.bot.settings_col.find_one(
            {"guild_id": interaction.guild.id}
        ) or {}

        channel_id = settings.get("birthday_channel")
        role_id = settings.get("birthday_role")

        if not channel_id:
            await interaction.response.send_message(
                "❌ Birthday channel not set.",
                ephemeral=True
            )
            return

        channel = interaction.guild.get_channel(channel_id)
        role = interaction.guild.get_role(role_id) if role_id else None

        entry = await self.bot.db.birthdays.find_one(
            {"guild_id": interaction.guild.id, "user_id": user.id}
        )

        if not entry:
            await interaction.response.send_message(
                "❌ That user has no saved birthday.",
                ephemeral=True
            )
            return

        from datetime import datetime, timedelta, timezone
        PH_TZ = timezone(timedelta(hours=8))
        today = datetime.now(PH_TZ)

        age_msg = ""
        if entry.get("year"):
            age = today.year - entry["year"]
            age_msg = f"You are now **{age}** years old! 🎂"

        await channel.send(
            f"🎉 Happy Birthday {user.mention}!\n{age_msg}"
        )

        if role:
            await user.add_roles(role)

            async def remove_later():
                import asyncio
                await asyncio.sleep(86400)
                await user.remove_roles(role)

            self.bot.loop.create_task(remove_later())

        await interaction.response.send_message(
            "✅ Birthday test sent!",
            ephemeral=True
        )

    # ==============================
    # 👋 WELCOME SYSTEM
    # ==============================

    @app_commands.command(name="setchannel", description="Set welcome channel")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def setchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"welcome_channel": channel.id}},
            upsert=True
        )
        await interaction.response.send_message("✅ Welcome channel set!", ephemeral=True)

    @app_commands.command(name="setrole", description="Set auto role")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def setrole(self, interaction: discord.Interaction, role: discord.Role):
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"auto_role": role.id}},
            upsert=True
        )
        await interaction.response.send_message("✅ Role set!", ephemeral=True)

    # ==============================
    # 🇯🇵 VOICE TRANSLATOR SETTINGS
    # ==============================
    
    @app_commands.command(name="settranslatechannel", description="Set translation subtitle channel")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def settranslatechannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
    
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"translate_channel": channel.id}},
            upsert=True
        )
    
        await interaction.response.send_message("✅ Translation channel set!", ephemeral=True)
    
    
    @app_commands.command(name="starttranslate", description="Start Japanese voice translation")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def starttranslate(self, interaction: discord.Interaction):
    
        if not interaction.user.voice:
            await interaction.response.send_message(
                "❌ Join a voice channel first.", ephemeral=True
            )
            return
    
        cog = self.bot.get_cog("VoiceTranslate")
    
        if not cog:
            await interaction.response.send_message(
                "❌ Translator cog not loaded.", ephemeral=True
            )
            return
    
        await cog.start_translation(
            interaction.guild,
            interaction.user.voice.channel
        )
    
        await interaction.response.send_message(
            "🎧 Voice translator started!"
        )
    
    
    @app_commands.command(name="stoptranslate", description="Stop Japanese translation")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def stoptranslate(self, interaction: discord.Interaction):
    
        cog = self.bot.get_cog("VoiceTranslate")
    
        if cog:
            await cog.stop_translation(interaction.guild)
    
        await interaction.response.send_message(
            "🛑 Voice translator stopped."
        )

    
    # ==============================
    # 📝 LOGGER
    # ==============================

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

    # ==============================
    # 🎵 TIKTOK SETTINGS
    # ==============================

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

    # ==============================
    # 🎤 VOICE VIP SETTINGS
    # ==============================

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

    # ==============================
    # 🎶 MUSIC SETTINGS
    # ==============================

    @app_commands.command(name="setmusicchannel", description="Set the text channel for music commands")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def setmusicchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"music_channel": channel.id}},
            upsert=True
        )
        await interaction.response.send_message("✅ Music channel set!", ephemeral=True)

    @app_commands.command(name="togglemusic", description="Enable or disable the music feature")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def togglemusic(self, interaction: discord.Interaction):
        settings = await self.bot.settings_col.find_one({"guild_id": interaction.guild.id}) or {}
        new_val = 0 if settings.get("music_enabled") else 1

        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"music_enabled": new_val}},
            upsert=True
        )

        status = "enabled" if new_val else "disabled"
        await interaction.response.send_message(f"✅ Music feature {status}!", ephemeral=True)

    # ==============================
    # 📊 POLL SETTINGS
    # ==============================

    @app_commands.command(name="setpollchannel", description="Set the channel where polls can be created")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def setpollchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"poll_channel": channel.id}},
            upsert=True
        )
        await interaction.response.send_message("✅ Poll channel set!", ephemeral=True)

    @app_commands.command(name="togglepoll", description="Enable or disable the poll feature")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def togglepoll(self, interaction: discord.Interaction):
        settings = await self.bot.settings_col.find_one({"guild_id": interaction.guild.id}) or {}
        new_val = 0 if settings.get("poll_enabled") else 1

        await self.bot.settings_col.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"poll_enabled": new_val}},
            upsert=True
        )

        status = "enabled" if new_val else "disabled"
        await interaction.response.send_message(f"✅ Poll feature {status}!", ephemeral=True)

    # ==============================
    # 🧪 DEBUG / PREVIEW
    # ==============================

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

        embed.add_field(
            name="🎶 Music",
            value=f"Enabled: {settings.get('music_enabled', 0)}\n"
                  f"Channel: {settings.get('music_channel', 'Not set')}",
            inline=False
        )

        embed.add_field(
            name="📊 Poll",
            value=f"Enabled: {settings.get('poll_enabled', 0)}\n"
                  f"Channel: {settings.get('poll_channel', 'Not set')}",
            inline=False
        )

        patch_games = settings.get("patch_games", [])

        if patch_games:
            games = "\n".join(g["name"] for g in patch_games)
        else:
            games = "None"
        
        embed.add_field(
            name="🆕 Patch Tracking",
            value=f"Channel: {settings.get('patch_channel','Not set')}\nGames:\n{games}",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


        # ==============================
        # 🆕 PATCH TRACKING
        # ==============================
    
        @app_commands.command(name="setpatchchannel", description="Set patch alert channel")
        @app_commands.guilds(discord.Object(id=GUILD_ID))
        async def setpatchchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
    
            await self.bot.settings_col.update_one(
                {"guild_id": interaction.guild.id},
                {"$set": {"patch_channel": channel.id}},
                upsert=True
            )
    
            await interaction.response.send_message(
                "✅ Patch channel set!",
                ephemeral=True
            )
    
    
        # ------------------------------
        # ADD LEAGUE PATCH
        # ------------------------------
    
        @app_commands.command(name="addleaguepatch", description="Track League patches")
        @app_commands.guilds(discord.Object(id=GUILD_ID))
        async def addleaguepatch(self, interaction: discord.Interaction):
    
            settings = await self.bot.settings_col.find_one(
                {"guild_id": interaction.guild.id}
            ) or {}
    
            games = settings.get("patch_games", [])
    
            if any(g["name"] == "League of Legends" for g in games):
                await interaction.response.send_message(
                    "⚠ League of Legends is already being tracked.",
                    ephemeral=True
                )
                return
    
            await self.bot.settings_col.update_one(
                {"guild_id": interaction.guild.id},
                {
                    "$push": {
                        "patch_games": {
                            "type": "league",
                            "name": "League of Legends",
                            "last_patch": None
                        }
                    }
                },
                upsert=True
            )
    
            await interaction.response.send_message(
                "🧠 League patch tracking enabled!",
                ephemeral=True
            )
    
    
        # ------------------------------
        # ADD VALORANT PATCH
        # ------------------------------
    
        @app_commands.command(name="addvalorantpatch", description="Track Valorant patches")
        @app_commands.guilds(discord.Object(id=GUILD_ID))
        async def addvalorantpatch(self, interaction: discord.Interaction):
    
            settings = await self.bot.settings_col.find_one(
                {"guild_id": interaction.guild.id}
            ) or {}
    
            games = settings.get("patch_games", [])
    
            if any(g["name"] == "Valorant" for g in games):
                await interaction.response.send_message(
                    "⚠ Valorant is already being tracked.",
                    ephemeral=True
                )
                return
    
            await self.bot.settings_col.update_one(
                {"guild_id": interaction.guild.id},
                {
                    "$push": {
                        "patch_games": {
                            "type": "valorant",
                            "name": "Valorant",
                            "last_patch": None
                        }
                    }
                },
                upsert=True
            )
    
            await interaction.response.send_message(
                "🔫 Valorant patch tracking enabled!",
                ephemeral=True
            )
    
    
        # ------------------------------
        # REMOVE PATCH GAME
        # ------------------------------
    
        @app_commands.command(name="removepatchgame", description="Stop tracking a patch game")
        @app_commands.guilds(discord.Object(id=GUILD_ID))
        async def removepatchgame(self, interaction: discord.Interaction, game: str):
    
            settings = await self.bot.settings_col.find_one(
                {"guild_id": interaction.guild.id}
            ) or {}
    
            games = settings.get("patch_games", [])
    
            match = None
    
            for g in games:
                if g["name"].lower() == game.lower():
                    match = g
                    break
    
            if not match:
                await interaction.response.send_message(
                    "❌ That game is not currently being tracked.",
                    ephemeral=True
                )
                return
    
            await self.bot.settings_col.update_one(
                {"guild_id": interaction.guild.id},
                {
                    "$pull": {
                        "patch_games": {"name": match["name"]}
                    }
                }
            )
    
            await interaction.response.send_message(
                f"🗑 Removed patch tracking for **{match['name']}**.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Settings(bot))

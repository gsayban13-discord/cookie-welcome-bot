import asyncio
from collections import defaultdict, deque

import discord
from discord.ext import commands
from discord import app_commands

GUILD_ID = 1459935661116100730


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = defaultdict(deque)

    async def _is_enabled(self, interaction: discord.Interaction) -> bool:
        settings = await self.bot.settings_col.find_one({"guild_id": interaction.guild.id}) or {}

        if not settings.get("music_enabled"):
            await interaction.response.send_message(
                "❌ Music is disabled. Use `/togglemusic` first.", ephemeral=True
            )
            return False

        allowed_channel = settings.get("music_channel")
        if allowed_channel and interaction.channel.id != allowed_channel:
            await interaction.response.send_message(
                f"❌ Use music commands in <#{allowed_channel}>.", ephemeral=True
            )
            return False

        return True

    async def _play_next(self, guild: discord.Guild):
        voice_client = guild.voice_client
        if not voice_client:
            return

        queue = self.queues[guild.id]
        if not queue:
            await voice_client.disconnect()
            return

        track = queue.popleft()

        def after_playing(error):
            if error:
                print(f"Music playback error: {error}")
            fut = asyncio.run_coroutine_threadsafe(self._play_next(guild), self.bot.loop)
            try:
                fut.result()
            except Exception as exc:
                print(f"Music queue error: {exc}")

        source = discord.FFmpegPCMAudio(track["url"])
        voice_client.play(source, after=after_playing)

        if track.get("text_channel"):
            channel = guild.get_channel(track["text_channel"])
            if channel:
                await channel.send(f"🎶 Now playing: {track['title']}")

    @app_commands.command(name="play", description="Play a direct audio stream URL")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def play(self, interaction: discord.Interaction, url: str, title: str = "Requested Track"):
        if not await self._is_enabled(interaction):
            return

        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message(
                "❌ Join a voice channel first.", ephemeral=True
            )
            return

        voice_channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client

        if voice_client and voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)
        elif not voice_client:
            voice_client = await voice_channel.connect()

        self.queues[interaction.guild.id].append(
            {"url": url, "title": title, "text_channel": interaction.channel.id}
        )

        if voice_client.is_playing() or voice_client.is_paused():
            await interaction.response.send_message(f"✅ Queued: **{title}**")
            return

        await interaction.response.send_message(f"✅ Added to queue: **{title}**")
        await self._play_next(interaction.guild)

    @app_commands.command(name="skip", description="Skip the current track")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def skip(self, interaction: discord.Interaction):
        if not await self._is_enabled(interaction):
            return

        voice_client = interaction.guild.voice_client
        if not voice_client or not voice_client.is_connected():
            await interaction.response.send_message("❌ Not connected to voice.", ephemeral=True)
            return

        if not voice_client.is_playing():
            await interaction.response.send_message("❌ Nothing is currently playing.", ephemeral=True)
            return

        voice_client.stop()
        await interaction.response.send_message("⏭️ Skipped.")

    @app_commands.command(name="stop", description="Stop music and clear queue")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def stop(self, interaction: discord.Interaction):
        if not await self._is_enabled(interaction):
            return

        voice_client = interaction.guild.voice_client
        self.queues[interaction.guild.id].clear()

        if not voice_client or not voice_client.is_connected():
            await interaction.response.send_message("✅ Queue cleared.")
            return

        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()

        await voice_client.disconnect()
        await interaction.response.send_message("⏹️ Stopped and disconnected.")

    @app_commands.command(name="queue", description="Show queued tracks")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def queue(self, interaction: discord.Interaction):
        if not await self._is_enabled(interaction):
            return

        queue = self.queues[interaction.guild.id]
        if not queue:
            await interaction.response.send_message("📭 Queue is empty.", ephemeral=True)
            return

        lines = [f"{i}. {item['title']}" for i, item in enumerate(queue, start=1)]
        await interaction.response.send_message("\n".join(lines))


async def setup(bot):
    await bot.add_cog(Music(bot))

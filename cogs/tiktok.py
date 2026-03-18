import discord
from discord.ext import commands
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, LiveEndEvent

import asyncio
import time


class TikTok(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.clients = {}
        self.live_status = {}  # username -> bool
        self.stream_start = {}

    # =============================
    # START LISTENER
    # =============================
    async def start_listener(self, guild_id, username, channel_id):

        if username in self.clients:
            print(f"[TikTok] Already tracking @{username}")
            return

        print(f"[TikTok] Starting listener for @{username}")

        client = TikTokLiveClient(unique_id=username)
        self.clients[username] = client
        self.live_status[username] = False

        # -------------------------
        # WHEN STREAM STARTS
        # -------------------------
        @client.on(ConnectEvent)
        async def on_connect(event):
            await self.handle_live_start(username, guild_id, channel_id, client)

        # -------------------------
        # WHEN STREAM ENDS
        # -------------------------
        @client.on(LiveEndEvent)
        async def on_live_end(event):
            await self.handle_live_end(username, guild_id, channel_id)

        # -------------------------
        # START LOOP (AUTO-RETRY)
        # -------------------------
        self.bot.loop.create_task(
            self.run_client(client, username, guild_id, channel_id)
        )

    # =============================
    # MAIN LOOP (AUTO RECONNECT)
    # =============================
    async def run_client(self, client, username, guild_id, channel_id):

        from TikTokLive.client.errors import UserOfflineError
    
        while True:
            try:
                print(f"[TikTok] Connecting to @{username}...")
                await client.start()
    
                # ✅ If it connects successfully, just wait here
                while True:
                    await asyncio.sleep(60)
    
            except UserOfflineError:
                print(f"[TikTok] @{username} is offline, retrying in 30s...")
                await asyncio.sleep(30)
    
            except Exception as e:
                print(f"[TikTok] Error for @{username}: {e}")
                await asyncio.sleep(10)

    # =============================
    # HANDLE LIVE START
    # =============================
    async def handle_live_start(self, username, guild_id, channel_id, client):

        if self.live_status.get(username):
            return  # already announced

        self.live_status[username] = True
        self.stream_start[username] = time.time()

        guild = self.bot.get_guild(guild_id)
        if not guild:
            return

        channel = guild.get_channel(channel_id)
        if not channel:
            return

        room = client.room_info or {}

        title = room.get("title", "TikTok LIVE")
        viewers = room.get("user_count", "Unknown")
        thumbnail = room.get("cover")

        embed = discord.Embed(
            title="🔴 LIVE ON TIKTOK!",
            description=f"**{username}** is now streaming!",
            color=discord.Color.red()
        )

        embed.add_field(name="📺 Title", value=title, inline=False)
        embed.add_field(name="👥 Viewers", value=viewers, inline=True)
        embed.add_field(
            name="🎥 Watch",
            value=f"https://www.tiktok.com/@{username}/live",
            inline=False
        )

        if thumbnail:
            embed.set_image(url=thumbnail)

        await channel.send(
            content="@everyone",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(everyone=True)
        )

        print(f"[TikTok] ALERT SENT for @{username}")

    # =============================
    # HANDLE LIVE END
    # =============================
    async def handle_live_end(self, username, guild_id, channel_id):

        if not self.live_status.get(username):
            return

        self.live_status[username] = False

        guild = self.bot.get_guild(guild_id)
        if not guild:
            return

        channel = guild.get_channel(channel_id)
        if not channel:
            return

        start = self.stream_start.get(username)
        duration = "Unknown"

        if start:
            seconds = int(time.time() - start)
            duration = f"{seconds // 60} minutes"

        embed = discord.Embed(
            title="⚫ TikTok Stream Ended",
            description=f"**{username}** has ended the stream.",
            color=discord.Color.dark_gray()
        )

        embed.add_field(name="⏱ Duration", value=duration)

        await channel.send(embed=embed)

        print(f"[TikTok] END detected for @{username}")

    # =============================
    # LOAD ON READY
    # =============================
    @commands.Cog.listener()
    async def on_ready(self):

        await self.bot.wait_until_ready()

        print("[TikTok] Loading saved streamers...")

        async for settings in self.bot.settings_col.find({"tiktok_username": {"$exists": True}}):

            username = settings.get("tiktok_username")
            guild_id = settings.get("guild_id")
            channel_id = settings.get("tiktok_channel")

            if username and channel_id:
                await self.start_listener(guild_id, username, channel_id)


async def setup(bot):
    await bot.add_cog(TikTok(bot))

import discord
from discord.ext import commands
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, DisconnectEvent, LiveEndEvent
import asyncio
import time


class TikTok(commands.Cog):

    async def safe_start(self, client, username):
        from TikTokLive.client.errors import UserOfflineError
    
        try:
            await client.start()
        except UserOfflineError:
            print(f"TikTok user @{username} is offline. Waiting...")
        except Exception as e:
            print(f"TikTok error for {username}: {e}")
        
        def __init__(self, bot):
            self.bot = bot
            self.clients = {}
            self.stream_start = {}

    async def start_listener(self, guild_id, username, channel_id):

        if username in self.clients:
            return

        client = TikTokLiveClient(unique_id=username)
        self.clients[username] = client

        # =============================
        # STREAM START
        # =============================
        @client.on(ConnectEvent)
        async def on_connect(event):

            guild = self.bot.get_guild(guild_id)
            if not guild:
                return

            channel = guild.get_channel(channel_id)
            if not channel:
                return

            self.stream_start[username] = time.time()

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

        # =============================
        # STREAM END
        # =============================
        @client.on(LiveEndEvent)
        async def on_live_end(event):

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
                minutes = seconds // 60
                duration = f"{minutes} minutes"

            embed = discord.Embed(
                title="⚫ TikTok Stream Ended",
                description=f"**{username}** has ended the stream.",
                color=discord.Color.dark_gray()
            )

            embed.add_field(name="⏱ Duration", value=duration)

            await channel.send(embed=embed)

        # =============================
        # DISCONNECT LOG
        # =============================
        @client.on(DisconnectEvent)
        async def on_disconnect(event):
            print(f"{username} disconnected from TikTok Live")

        asyncio.create_task(self.safe_start(client, username))

    # =============================
    # LOAD LISTENERS ON BOT READY
    # =============================
    @commands.Cog.listener()
    async def on_ready(self):

        await self.bot.wait_until_ready()

        async for settings in self.bot.settings_col.find({"tiktok_username": {"$exists": True}}):

            username = settings["tiktok_username"]
            guild_id = settings["guild_id"]
            channel_id = settings.get("tiktok_channel")

            if username and channel_id:
                await self.start_listener(guild_id, username, channel_id)


async def setup(bot):
    await bot.add_cog(TikTok(bot))



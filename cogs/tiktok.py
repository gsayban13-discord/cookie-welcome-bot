import discord
from discord.ext import commands
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, DisconnectEvent
import asyncio


class TikTok(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.clients = {}

    async def start_listener(self, guild_id, username, channel_id):

        if username in self.clients:
            return

        client = TikTokLiveClient(unique_id=username)
        self.clients[username] = client

        @client.on(ConnectEvent)
        async def on_connect(event):

            guild = self.bot.get_guild(guild_id)
            if not guild:
                return

            channel = guild.get_channel(channel_id)
            if not channel:
                return

            embed = discord.Embed(
                title="🔴 LIVE ON TIKTOK!",
                description=f"**{username}** just went LIVE!",
                color=discord.Color.red()
            )

            embed.add_field(
                name="🎥 Watch the stream",
                value=f"https://www.tiktok.com/@{username}/live",
                inline=False
            )

            await channel.send(
                content="@everyone",
                embed=embed,
                allowed_mentions=discord.AllowedMentions(everyone=True)
            )

        @client.on(DisconnectEvent)
        async def on_disconnect(event):
            print(f"{username} stream ended.")

        asyncio.create_task(client.start())

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

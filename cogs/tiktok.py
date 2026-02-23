import discord
from discord.ext import commands, tasks
from utils.tiktok_scraper import fetch_tiktok_page
import time
import asyncio

COOLDOWN = 3600      # 1 hour cooldown between announcements
VERIFY_DELAY = 120   # 2 minutes verification

class TikTok(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.check_tiktok.start()
        self.verifying_live = {}
        self.last_announced = {}

    def cog_unload(self):
        self.check_tiktok.cancel()

    @tasks.loop(minutes=3)
    async def check_tiktok(self):
        settings_col = self.bot.settings_col

        async for settings in settings_col.find({"tiktok_username": {"$exists": True}}):

            guild = self.bot.get_guild(settings["guild_id"])
            if not guild:
                continue

            username = settings["tiktok_username"]
            channel_id = settings.get("tiktok_channel")
            was_live = settings.get("tiktok_live", 0)

            try:
                is_live, thumbnail, url = await fetch_tiktok_page(username)

                current_time = time.time()

                # --- LIVE DETECTED ---
                if is_live:

                    if username in self.verifying_live:
                        continue

                    if username in self.last_announced:
                        if current_time - self.last_announced[username] < COOLDOWN:
                            continue

                    self.verifying_live[username] = True

                    await asyncio.sleep(VERIFY_DELAY)

                    still_live, thumbnail, url = await fetch_tiktok_page(username)

                    if still_live:
                        channel = guild.get_channel(channel_id)

                        if channel:
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

                            if thumbnail:
                                embed.set_image(url=thumbnail)

                            await channel.send(
                                content=f"@everyone\n\n{url}",
                                embed=embed,
                                allowed_mentions=discord.AllowedMentions(everyone=True)
                            )

                        await settings_col.update_one(
                            {"guild_id": guild.id},
                            {"$set": {"tiktok_live": 1}}
                        )

                        self.last_announced[username] = current_time

                    del self.verifying_live[username]

                # --- USER WENT OFFLINE ---
                elif not is_live and was_live:
                    await settings_col.update_one(
                        {"guild_id": guild.id},
                        {"$set": {"tiktok_live": 0}}
                    )

            except Exception as e:
                print("TikTok error:", e)

    @check_tiktok.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(TikTok(bot))

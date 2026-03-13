import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
from bs4 import BeautifulSoup

STEAM_API = "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid={appid}&count=1"

VALORANT_URL = "https://playvalorant.com/en-us/news/game-updates/"
LEAGUE_URL = "https://www.leagueoflegends.com/en-us/news/game-updates/"


class PatchBot(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.check_patches.start()

    def cog_unload(self):
        self.check_patches.cancel()

    # -----------------------------
    # STEAM PATCH
    # -----------------------------

    async def fetch_steam_patch(self, appid):

        url = STEAM_API.format(appid=appid)

        try:
            async with self.session.get(url) as resp:
                data = await resp.json()
        except:
            return None

        news = data.get("appnews", {}).get("newsitems", [])

        if not news:
            return None

        item = news[0]

        return {
            "id": item["gid"],
            "title": item["title"],
            "url": item["url"],
            "summary": item.get("contents", "")[:300]
        }

    # -----------------------------
    # RIOT SCRAPER
    # -----------------------------

    async def scrape_patch_page(self, url):

        try:
            async with self.session.get(url) as resp:
                html = await resp.text()
        except:
            return None

        soup = BeautifulSoup(html, "html.parser")

        article = soup.find("a", href=True)

        if not article:
            return None

        title = article.text.strip()
        link = article["href"]

        if not link.startswith("http"):
            link = "https://playvalorant.com" + link

        return {
            "id": link,
            "title": title,
            "url": link
        }

    # -----------------------------
    # LOOP
    # -----------------------------

    @tasks.loop(minutes=5)
    async def check_patches(self):

        await self.bot.wait_until_ready()

        async for settings in self.bot.settings_col.find({"patch_games": {"$exists": True}}):

            guild = self.bot.get_guild(settings["guild_id"])
            if not guild:
                continue

            channel = guild.get_channel(settings.get("patch_channel"))

            if not channel:
                continue

            for game in settings["patch_games"]:

                patch = None

                if game["type"] == "steam":
                    patch = await self.fetch_steam_patch(game["appid"])

                elif game["type"] == "valorant":
                    patch = await self.scrape_patch_page(VALORANT_URL)

                elif game["type"] == "league":
                    patch = await self.scrape_patch_page(LEAGUE_URL)

                if not patch:
                    continue

                if patch["id"] == game.get("last_patch"):
                    continue

                await self.bot.settings_col.update_one(
                    {
                        "guild_id": guild.id,
                        "patch_games.name": game["name"]
                    },
                    {
                        "$set": {
                            "patch_games.$.last_patch": patch["id"]
                        }
                    }
                )

                embed = discord.Embed(
                    title="🆕 Patch Released",
                    description=f"**{game['name']}**",
                    color=discord.Color.green()
                )

                embed.add_field(
                    name="Patch Title",
                    value=patch["title"],
                    inline=False
                )

                embed.add_field(
                    name="Read Patch Notes",
                    value=patch["url"],
                    inline=False
                )

                await channel.send(embed=embed)

                await asyncio.sleep(1)


async def setup(bot):
    await bot.add_cog(PatchBot(bot))

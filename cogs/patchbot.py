import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
from bs4 import BeautifulSoup

STEAM_API = "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid={appid}&count=1"

VALORANT_URL = "https://playvalorant.com/en-us/news/game-updates/"
LEAGUE_URL = "https://www.leagueoflegends.com/en-us/news/game-updates/"

VALORANT_BASE = "https://playvalorant.com"
LEAGUE_BASE = "https://www.leagueoflegends.com"


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
            "summary": item.get("contents", "")[:400]
        }

    # -----------------------------
    # RIOT PATCH SCRAPER
    # -----------------------------

    async def scrape_patch_page(self, url):

        try:
            async with self.session.get(url) as resp:
                html = await resp.text()
        except:
            return None

        soup = BeautifulSoup(html, "html.parser")

        articles = soup.find_all("a", href=True)

        for article in articles:

            title = article.get_text(" ", strip=True).lower()

            # Only allow real patch notes
            if "patch" not in title:
                continue

            if "notes" not in title:
                continue

            # Ignore trailers/dev blogs
            bad_words = [
                "trailer",
                "dev",
                "diary",
                "cinematic",
                "music",
                "skins",
                "event"
            ]

            if any(bad in title for bad in bad_words):
                continue

            link = article["href"]

            if "valorant" in url:
                if not link.startswith("http"):
                    link = VALORANT_BASE + link

            if "leagueoflegends" in url:
                if not link.startswith("http"):
                    link = LEAGUE_BASE + link

            clean_title = article.get_text(" ", strip=True)

            return {
                "id": link,
                "title": clean_title,
                "url": link
            }

        return None

    # -----------------------------
    # PATCH SUMMARY SCRAPER
    # -----------------------------

    async def extract_patch_summary(self, url):

        try:
            async with self.session.get(url) as resp:
                html = await resp.text()
        except:
            return None

        soup = BeautifulSoup(html, "html.parser")

        paragraphs = soup.find_all("p")

        summary_lines = []

        for p in paragraphs:

            text = p.get_text(" ", strip=True)

            if len(text) < 40:
                continue

            summary_lines.append(text)

            if len(summary_lines) == 3:
                break

        if not summary_lines:
            return None

        summary = "\n• " + "\n• ".join(summary_lines)

        return summary[:700]

    # -----------------------------
    # MAIN LOOP
    # -----------------------------

    @tasks.loop(seconds=45)
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
                summary = None
    
                # -------------------
                # STEAM
                # -------------------
    
                if game["type"] == "steam":
                    patch = await self.fetch_steam_patch(game["appid"])
    
                # -------------------
                # VALORANT
                # -------------------
    
                elif game["type"] == "valorant":
                    patch = await self.scrape_patch_page(VALORANT_URL)
    
                # -------------------
                # LEAGUE
                # -------------------
    
                elif game["type"] == "league":
                    patch = await self.scrape_patch_page(LEAGUE_URL)
    
                if not patch:
                    continue
    
                # If patch already announced skip heavy scraping
                if patch["id"] == game.get("last_patch"):
                    continue
    
                # Only now fetch summary (heavy operation)
                if game["type"] in ["valorant", "league"]:
                    summary = await self.extract_patch_summary(patch["url"])
                else:
                    summary = patch.get("summary")
    
                # Save patch ID
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
                    description=f"🎮 **{game['name']}**",
                    color=discord.Color.green()
                )
    
                embed.add_field(
                    name="📄 Patch",
                    value=patch["title"],
                    inline=False
                )
    
                if summary:
                    embed.add_field(
                        name="📋 Patch Summary",
                        value=summary,
                        inline=False
                    )
    
                embed.add_field(
                    name="🔗 Full Patch Notes",
                    value=f"[Read the full patch notes]({patch['url']})",
                    inline=False
                )
    
                embed.set_footer(text="Cookie Bot • Game Patch Tracker")
    
                await channel.send(embed=embed)
    
                await asyncio.sleep(2)  # safety delay between games


async def setup(bot):
    await bot.add_cog(PatchBot(bot))

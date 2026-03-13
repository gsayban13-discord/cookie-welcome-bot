import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import re
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
        asyncio.create_task(self.session.close())

    # -----------------------------
    # PATCH NUMBER EXTRACTOR
    # -----------------------------

    def extract_patch_number(self, title):

        match = re.search(r"\d+\.\d+", title)

        if match:
            return match.group(0)

        return None

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

            if "patch" not in title or "notes" not in title:
                continue

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

            if "valorant" in url and not link.startswith("http"):
                link = VALORANT_BASE + link

            if "leagueoflegends" in url and not link.startswith("http"):
                link = LEAGUE_BASE + link

            clean_title = article.get_text(" ", strip=True)

            return {
                "id": link,
                "title": clean_title,
                "url": link
            }

        return None

    # -----------------------------
    # AI STYLE PATCH SUMMARY
    # -----------------------------

    async def extract_patch_summary(self, url):

        try:
            async with self.session.get(url) as resp:
                html = await resp.text()
        except:
            return None

        soup = BeautifulSoup(html, "html.parser")

        paragraphs = soup.find_all("p")

        text_blocks = []

        for p in paragraphs:

            text = p.get_text(" ", strip=True)

            if len(text) < 40:
                continue

            text_blocks.append(text)

        if not text_blocks:
            return None

        keywords = [
            "update",
            "improve",
            "fix",
            "adjust",
            "balance",
            "change",
            "bug",
            "new"
        ]

        summary = []

        for line in text_blocks:

            lower = line.lower()

            if any(word in lower for word in keywords):
                summary.append(line)

            if len(summary) == 4:
                break

        if not summary:
            summary = text_blocks[:3]

        formatted = "\n• " + "\n• ".join(summary)

        return formatted[:800]

    # -----------------------------
    # PATCH BANNER IMAGE
    # -----------------------------

    async def extract_patch_image(self, url):

        try:
            async with self.session.get(url) as resp:
                html = await resp.text()
        except:
            return None

        soup = BeautifulSoup(html, "html.parser")

        images = soup.find_all("img")

        for img in images:

            src = img.get("src")

            if not src:
                continue

            if any(x in src.lower() for x in ["icon", "logo", "sprite"]):
                continue

            if "1920" in src or "1080" in src or "header" in src or "patch" in src:

                if src.startswith("//"):
                    src = "https:" + src

                return src

        for img in images:

            src = img.get("src")

            if src and src.startswith("http"):
                return src

        return None

    # -----------------------------
    # MAIN LOOP (FAST DETECTION)
    # -----------------------------

    @tasks.loop(seconds=20)
    async def check_patches(self):

        await self.bot.wait_until_ready()

        await asyncio.sleep(2)

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
                image = None

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

                if game["type"] in ["valorant", "league"]:

                    summary = await self.extract_patch_summary(patch["url"])
                    image = await self.extract_patch_image(patch["url"])

                else:

                    summary = patch.get("summary")

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

                patch_number = self.extract_patch_number(patch["title"])

                if patch_number:
                    title = f"🆕 {game['name']} Patch {patch_number}"
                else:
                    title = patch["title"]

                if game["type"] == "valorant":
                    color = discord.Color.from_rgb(255, 70, 85)
                elif game["type"] == "league":
                    color = discord.Color.from_rgb(200, 155, 60)
                else:
                    color = discord.Color.green()

                embed = discord.Embed(
                    title=title,
                    url=patch["url"],
                    color=color
                )

                if game["type"] == "valorant":

                    embed.set_author(
                        name="Valorant",
                        icon_url="https://seeklogo.com/images/V/valorant-logo-FAB2CA0E55-seeklogo.com.png"
                    )

                elif game["type"] == "league":

                    embed.set_author(
                        name="League of Legends",
                        icon_url="https://seeklogo.com/images/L/league-of-legends-logo-4E20C0E6B6-seeklogo.com.png"
                    )

                if summary:
                    embed.description = summary

                if image:
                    embed.set_image(url=image)

                embed.set_footer(text="Cookie Bot • Game Patch Tracker")

                await channel.send(embed=embed)

                await asyncio.sleep(2)


async def setup(bot):
    await bot.add_cog(PatchBot(bot))

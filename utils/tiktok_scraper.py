import re
import aiohttp


def extract_thumbnail(html: str):
    patterns = [
        r'property="og:image" content="([^"]+)"',
        r'property=\'og:image\' content=\'([^\']+)\'',
        r'name="og:image" content="([^"]+)"',
        r'name=\'og:image\' content=\'([^\']+)\''
    ]

    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            return match.group(1)

    return None


async def fetch_tiktok_page(username: str):
    url = f"https://www.tiktok.com/@{username}/live"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            html = await resp.text()

    is_live = "LIVE" in html
    thumbnail = extract_thumbnail(html)

    return is_live, thumbnail, url

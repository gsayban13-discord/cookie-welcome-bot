from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import os


async def create_welcome_card(member, bg_path=None):

    width, height = 900, 300

    # Use custom background if exists
    if bg_path and os.path.exists(bg_path):
        bg = Image.open(bg_path).convert("RGB")
        bg = bg.resize((width, height))
    else:
        bg = Image.new("RGB", (width, height), "#ffd6e7")

    draw = ImageDraw.Draw(bg)

    # Avatar
    avatar_url = member.display_avatar.url
    response = requests.get(avatar_url)
    avatar = Image.open(BytesIO(response.content)).convert("RGBA")
    avatar = avatar.resize((180, 180))

    mask = Image.new("L", avatar.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, 180, 180), fill=255)
    avatar.putalpha(mask)

    bg.paste(avatar, (60, 60), avatar)

    # Fonts
    try:
        font_big = ImageFont.truetype("arial.ttf", 60)
        font_small = ImageFont.truetype("arial.ttf", 35)
    except:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    draw.text((300, 80), "Welcome!", fill="white", font=font_big)
    draw.text((300, 150), member.name, fill="white", font=font_small)
    draw.text((300, 200),
              f"Member #{member.guild.member_count}",
              fill="white", font=font_small)

    path = "welcome.png"
    bg.save(path)
    return path

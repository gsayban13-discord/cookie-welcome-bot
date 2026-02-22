from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import os


async def create_welcome_card(member, bg_path=None):

    width, height = 900, 300

    # ---------------- BACKGROUND ----------------
    bg_path = "backgrounds/welcome.png"

    if os.path.exists(bg_path):
        bg = Image.open(bg_path).convert("RGB")
        bg = bg.resize((width, height))
    else:
        bg = Image.new("RGB", (width, height), "#ffd6e7")

    draw = ImageDraw.Draw(bg)
    # ---------------- AVATAR ----------------
    avatar_url = member.display_avatar.url
    response = requests.get(avatar_url)
    avatar = Image.open(BytesIO(response.content)).convert("RGBA")
    avatar = avatar.resize((180, 180))

    mask = Image.new("L", avatar.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, 180, 180), fill=255)
    avatar.putalpha(mask)

    bg.paste(avatar, (60, 60), avatar)

    # ---------------- TEXT ----------------
    name_text = member.name
    count_text = f"Member #{member.guild.member_count}"

    try:
        font_name = ImageFont.truetype("arial.ttf", 40)
        font_small = ImageFont.truetype("arial.ttf", 24)
    except:
        font_name = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Position near avatar, middle area
    text_x = 330
    name_y = 130
    count_y = 175

    text_color = "#3b2a2a"

    draw.text((text_x, name_y), name_text, fill=text_color, font=font_name)
    draw.text((text_x, count_y), count_text, fill=text_color, font=font_small)

    # ---------------- SAVE ----------------
    path = "welcome.png"
    bg.save(path)

    return path



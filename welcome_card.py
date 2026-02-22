from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import os


async def create_welcome_card(member, bg_path=None):

    width, height = 900, 300

    # Background
    if bg_path and os.path.exists(bg_path):
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

    # ---------------- FONTS ----------------
    try:
        font_name = ImageFont.truetype("arial.ttf", 42)
        font_small = ImageFont.truetype("arial.ttf", 28)
    except:
        font_name = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # ---------------- TEXT (CENTERED ON TABLE AREA) ----------------
    name_text = member.name
    count_text = f"Member #{member.guild.member_count}"

    # Calculate center positions
    name_bbox = draw.textbbox((0, 0), name_text, font=font_name)
    name_width = name_bbox[2] - name_bbox[0]

    count_bbox = draw.textbbox((0, 0), count_text, font=font_small)
    count_width = count_bbox[2] - count_bbox[0]

    # Table area center (right side of image)
    center_x = 600

    # Draw texts centered
    draw.text(
        (center_x - name_width // 2, 175),
        name_text,
        fill="white",
        font=font_name
    )

    draw.text(
        (center_x - count_width // 2, 220),
        count_text,
        fill="white",
        font=font_small
    )

    path = "welcome.png"
    bg.save(path)
    return path

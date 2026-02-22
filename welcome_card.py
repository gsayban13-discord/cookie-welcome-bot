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
        font_name = ImageFont.truetype("arial.ttf", 50)   # bigger
        font_small = ImageFont.truetype("arial.ttf", 28)
    except:
        font_name = ImageFont.load_default()
        font_small = ImageFont.load_default()

    text_x = 330
    name_y = 120
    count_y = 180

    main_color = "#3b2a2a"
    outline_color = "white"

    def draw_text_with_outline(draw, pos, text, font, fill, outline):
        x, y = pos
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                if dx != 0 or dy != 0:
                    draw.text((x+dx, y+dy), text, font=font, fill=outline)
        draw.text((x, y), text, font=font, fill=fill)

    draw_text_with_outline(draw, (text_x, name_y), name_text, font_name, main_color, outline_color)
    draw_text_with_outline(draw, (text_x, count_y), count_text, font_small, main_color, outline_color)

    # ---------------- SAVE ----------------
    path = "welcome.png"
    bg.save(path)

    return path




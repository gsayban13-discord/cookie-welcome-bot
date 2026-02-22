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

    font_path = "fonts/Poppins-SemiBold.ttf"

    try:
        font_name = ImageFont.truetype(font_path, 60)   # BIG username
        font_small = ImageFont.truetype(font_path, 32)  # member count
    except:
        font_name = ImageFont.load_default()
        font_small = ImageFont.load_default()

    text_x = 320
    name_y = 115
    count_y = 185

    main_color = "#3b2a2a"
    shadow_color = (0, 0, 0, 120)  # soft shadow

    def draw_soft_shadow(draw, pos, text, font):
        x, y = pos
        draw.text((x+3, y+3), text, font=font, fill=shadow_color)

    draw_soft_shadow(draw, (text_x, name_y), name_text, font_name)
    draw_soft_shadow(draw, (text_x, count_y), count_text, font_small)

    draw.text((text_x, name_y), name_text, fill=main_color, font=font_name)
    draw.text((text_x, count_y), count_text, fill=main_color, font=font_small)

    # ---------------- SAVE ----------------
    path = "welcome.png"
    bg.save(path)

    return path





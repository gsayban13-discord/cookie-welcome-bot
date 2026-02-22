import discord
from discord.ext import commands
import random
from welcome_card import create_welcome_card


AI_MESSAGES = [
    "🌸 A new cutie has arrived! Welcome {user}!",
    "✨ Everyone say hiiii to {user}!",
    "💖 {user} just joined the cookie family!",
    "🎀 Welcome {user}! Hope you love it here!",
    "🐾 A wild {user} appeared!",
    "🍪 Fresh cookie delivered! Welcome {user}!",
    "🌷 {user} joined the cookie paradise!",
    "🍓 Sweet news! {user} just popped into the server!",
    "🌈 Yayyy! {user} is here — let’s give them a warm welcome!",
    "🧁 A sprinkle of joy! Welcome to the server, {user}!",
    "🍪 Cookie radar detected a new friend: {user}!",
    "🌟 Look who just arrived — it’s {user}! Say hi!",
    "💫 The cookie universe welcomes {user}!",
    "🐣 A new member hatched! Welcome {user}!",
    "🍭 Sugar rush alert! {user} just joined!",
    "🎉 Everyone clap! {user} made it into the cookie club!",
    "🌼 Hello hello {user}! We saved you some cookies!",
    "🍩 Donut worry — {user} is finally here!",
    "🌸 The server feels brighter now that {user} joined!",
    "✨ New friend unlocked: {user}!",
    "🐾 Another adorable human spotted: {user}!",
    "🍪 Warm cookies and warm welcomes for {user}!",
    "💖 {user} just walked into the cookie kingdom!",
]


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):

        settings_col = self.bot.settings_col
        settings = await settings_col.find_one({"guild_id": member.guild.id}) or {}

        channel_id = settings.get("welcome_channel")
        role_id = settings.get("auto_role")

        # Auto role
        if role_id:
            role = member.guild.get_role(role_id)
            if role:
                await member.add_roles(role)

        # Send welcome message
        if channel_id:
            channel = member.guild.get_channel(channel_id)
            if channel:
                card = await create_welcome_card(member)
                message = random.choice(AI_MESSAGES).format(user=member.mention)

                await channel.send(
                    message,
                    file=discord.File(card, "welcome.png")
                )


async def setup(bot):
    await bot.add_cog(Welcome(bot))

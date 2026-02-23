import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
from dateutil import parser
import asyncio


# Philippines timezone (UTC+8)
PH_TZ = timezone(timedelta(hours=8))


class Birthday(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_birthdays.start()

    # =============================
    # LISTEN FOR BIRTHDAY MESSAGES
    # =============================
    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot or not message.guild:
            return

        settings = await self.bot.settings_col.find_one(
            {"guild_id": message.guild.id}
        ) or {}

        channel_id = settings.get("birthday_channel")

        if not channel_id or message.channel.id != channel_id:
            return

        try:
            parsed = parser.parse(message.content, fuzzy=True)

            month = parsed.month
            day = parsed.day

            # Only store year if user actually typed it
            year = parsed.year if parsed.year != datetime.now().year else None

        except:
            return  # ignore invalid messages

        # Save birthday
        await self.bot.db.birthdays.update_one(
            {"guild_id": message.guild.id, "user_id": message.author.id},
            {"$set": {
                "month": month,
                "day": day,
                "year": year
            }},
            upsert=True
        )

        await message.reply("🎂 Birthday saved!", delete_after=8)

        await self.update_birthday_list(message.guild)

    # =============================
    # UPDATE SORTED EMBED LIST
    # =============================
    async def update_birthday_list(self, guild):

        settings = await self.bot.settings_col.find_one(
            {"guild_id": guild.id}
        ) or {}

        channel_id = settings.get("birthday_channel")
        if not channel_id:
            return

        channel = guild.get_channel(channel_id)

        cursor = self.bot.db.birthdays.find({"guild_id": guild.id})
        data = await cursor.to_list(length=None)

        # Sort by month/day
        data.sort(key=lambda x: (x["month"], x["day"]))

        embed = discord.Embed(
            title="🎂 Server Birthdays",
            color=discord.Color.pink()
        )

        lines = []

        for entry in data:
            member = guild.get_member(entry["user_id"])
            if not member:
                continue

            date_str = datetime(2000, entry["month"], entry["day"]).strftime("%b %d")

            age_text = ""
            if entry.get("year"):
                age = datetime.now(PH_TZ).year - entry["year"]
                age_text = f" ({age})"

            lines.append(f"{date_str} — {member.display_name}{age_text}")

        embed.description = "\n".join(lines) if lines else "No birthdays saved."

        # Find existing embed message
        async for msg in channel.history(limit=50):
            if msg.author == self.bot.user and msg.embeds:
                await msg.edit(embed=embed)
                return

        await channel.send(embed=embed)

    # =============================
    # MIDNIGHT WAIT HELPER
    # =============================
    async def wait_until_midnight(self):
        now = datetime.now(PH_TZ)
        tomorrow = now.date() + timedelta(days=1)
        midnight = datetime.combine(tomorrow, datetime.min.time(), tzinfo=PH_TZ)
        seconds = (midnight - now).total_seconds()
        await asyncio.sleep(seconds)

    # =============================
    # DAILY BIRTHDAY CHECK TASK
    # =============================
    @tasks.loop(hours=24)
    async def check_birthdays(self):

        await self.bot.wait_until_ready()

        today = datetime.now(PH_TZ)

        for guild in self.bot.guilds:

            settings = await self.bot.settings_col.find_one(
                {"guild_id": guild.id}
            ) or {}

            channel_id = settings.get("birthday_channel")
            role_id = settings.get("birthday_role")

            if not channel_id:
                continue

            channel = guild.get_channel(channel_id)
            role = guild.get_role(role_id) if role_id else None

            cursor = self.bot.db.birthdays.find({"guild_id": guild.id})
            data = await cursor.to_list(length=None)

            for entry in data:

                if entry["month"] == today.month and entry["day"] == today.day:

                    member = guild.get_member(entry["user_id"])
                    if not member:
                        continue

                    age_msg = ""
                    if entry.get("year"):
                        age = today.year - entry["year"]
                        age_msg = f"You are now **{age}** years old! 🎂"

                    await channel.send(
                        f"🎉 Happy Birthday {member.mention}!\n{age_msg}"
                    )

                    if role:
                        await member.add_roles(role)
                        self.bot.loop.create_task(
                            self.remove_role_later(member, role)
                        )

    @check_birthdays.before_loop
    async def before_check_birthdays(self):
        await self.wait_until_midnight()

    # =============================
    # REMOVE ROLE AFTER 24 HOURS
    # =============================
    async def remove_role_later(self, member, role):
        await asyncio.sleep(86400)
        await member.remove_roles(role)


async def setup(bot):
    await bot.add_cog(Birthday(bot))

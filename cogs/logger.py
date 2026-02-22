import discord
from discord.ext import commands


class Logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---------------- MESSAGE DELETE ----------------
    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        settings = await self.bot.settings_col.find_one({"guild_id": guild.id}) or {}

        if not settings.get("logger_enabled"):
            return

        log_channel = guild.get_channel(settings.get("log_channel"))
        if not log_channel:
            return

        if not payload.cached_message:
            return

        msg = payload.cached_message

        # Ignore bots
        if msg.author.bot:
            return

        embed = discord.Embed(
            title="🗑️ Message Deleted",
            color=discord.Color.red()
        )

        embed.add_field(name="Author", value=msg.author.mention)
        embed.add_field(name="Channel", value=f"<#{payload.channel_id}>")

        if msg.content:
            embed.add_field(name="Content", value=msg.content[:1000], inline=False)

        # Attachments
        if msg.attachments:
            files = []
            image_url = None

            for att in msg.attachments:
                files.append(att.filename)

                if att.content_type and "image" in att.content_type:
                    image_url = att.url

            embed.add_field(name="Attachments", value="\n".join(files), inline=False)

            if image_url:
                embed.set_image(url=image_url)

        await log_channel.send(embed=embed)

    # ---------------- MESSAGE EDIT ----------------
    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        settings = await self.bot.settings_col.find_one({"guild_id": guild.id}) or {}

        if not settings.get("logger_enabled"):
            return

        log_channel = guild.get_channel(settings.get("log_channel"))
        if not log_channel:
            return

        if not payload.cached_message:
            return

        before = payload.cached_message

        if before.author.bot:
            return

        after = payload.data.get("content")

        if not after or before.content == after:
            return

        embed = discord.Embed(
            title="✏️ Message Edited",
            color=discord.Color.orange()
        )

        embed.add_field(name="Author", value=before.author.mention)
        embed.add_field(name="Channel", value=f"<#{payload.channel_id}>")
        embed.add_field(name="Before", value=before.content[:1000], inline=False)
        embed.add_field(name="After", value=after[:1000], inline=False)

        if before.attachments:
            files = []
            image_url = None

            for att in before.attachments:
                files.append(f"[{att.filename}]({att.url})")

                if att.content_type and "image" in att.content_type:
                    image_url = att.url

            embed.add_field(name="Attachments", value="\n".join(files), inline=False)

            if image_url:
                embed.set_image(url=image_url)

        await log_channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Logger(bot))

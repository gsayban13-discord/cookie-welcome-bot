import discord
from discord.ext import commands


class VoiceVIP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):

        # Only trigger when joining a channel
        if before.channel is None and after.channel is not None:

            settings = await self.bot.settings_col.find_one(
                {"guild_id": member.guild.id}
            ) or {}

            if not settings.get("voice_vip_enabled"):
                return

            if member.id != settings.get("voice_vip_user"):
                return

            msg = settings.get("voice_vip_message", "🎤 {user} joined voice!")

            msg = msg.replace("{user}", member.mention)
            msg = msg.replace("{channel}", after.channel.name)

            try:
                await after.channel.send(msg, delete_after=20)
            except:
                fallback = member.guild.get_channel(settings.get("log_channel"))
                if fallback:
                    await fallback.send(msg, delete_after=20)


async def setup(bot):
    await bot.add_cog(VoiceVIP(bot))

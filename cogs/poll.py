import discord
from discord.ext import commands
from discord import app_commands

GUILD_ID = 1459935661116100730
NUMBER_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


class Poll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _is_enabled(self, interaction: discord.Interaction) -> bool:
        settings = await self.bot.settings_col.find_one({"guild_id": interaction.guild.id}) or {}

        if not settings.get("poll_enabled"):
            await interaction.response.send_message(
                "❌ Polls are disabled. Use `/togglepoll` first.", ephemeral=True
            )
            return False

        allowed_channel = settings.get("poll_channel")
        if allowed_channel and interaction.channel.id != allowed_channel:
            await interaction.response.send_message(
                f"❌ Use poll commands in <#{allowed_channel}>.", ephemeral=True
            )
            return False

        return True

    @app_commands.command(name="poll", description="Create a quick reaction poll")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def poll(
        self,
        interaction: discord.Interaction,
        question: str,
        option1: str,
        option2: str,
        option3: str = None,
        option4: str = None,
        option5: str = None,
        option6: str = None,
        option7: str = None,
        option8: str = None,
        option9: str = None,
        option10: str = None,
    ):
        if not await self._is_enabled(interaction):
            return

        options = [
            option1,
            option2,
            option3,
            option4,
            option5,
            option6,
            option7,
            option8,
            option9,
            option10,
        ]
        options = [opt for opt in options if opt]

        if len(options) < 2:
            await interaction.response.send_message(
                "❌ You need at least 2 options.", ephemeral=True
            )
            return

        description = "\n".join(
            f"{NUMBER_EMOJIS[idx]} {option}" for idx, option in enumerate(options)
        )

        embed = discord.Embed(
            title=f"📊 {question}",
            description=description,
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=f"Poll by {interaction.user.display_name}")

        await interaction.response.send_message("✅ Poll created!")
        poll_message = await interaction.channel.send(embed=embed)

        for idx in range(len(options)):
            await poll_message.add_reaction(NUMBER_EMOJIS[idx])


async def setup(bot):
    await bot.add_cog(Poll(bot))

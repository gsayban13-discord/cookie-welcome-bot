import discord
from discord.ext import commands


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =============================
    # 🔨 BAN COMMAND (?ban user reason)
    # =============================
    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):

        # ❌ Self ban
        if member == ctx.author:
            return await ctx.send("❌ You can't ban yourself.")

        # ❌ Role hierarchy
        if member.top_role >= ctx.author.top_role:
            return await ctx.send("❌ You can't ban someone with equal or higher role.")

        if member.top_role >= ctx.guild.me.top_role:
            return await ctx.send("❌ I can't ban this user (role too high).")

        # =============================
        # 📩 DM USER BEFORE BAN
        # =============================
        try:
            dm_embed = discord.Embed(
                title="🔨 You have been banned",
                color=discord.Color.red()
            )
            dm_embed.add_field(name="Server", value=ctx.guild.name)
            dm_embed.add_field(name="Reason", value=reason, inline=False)

            await member.send(embed=dm_embed)
        except:
            pass  # user has DMs off

        # =============================
        # 🔨 BAN
        # =============================
        try:
            await member.ban(reason=f"{ctx.author} | {reason}")

            embed = discord.Embed(
                title="🔨 User Banned",
                color=discord.Color.red()
            )
            embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention)
            embed.add_field(name="Reason", value=reason, inline=False)

            await ctx.send(embed=embed)

            # =============================
            # 📝 LOGGER INTEGRATION
            # =============================
            settings = await self.bot.settings_col.find_one({"guild_id": ctx.guild.id}) or {}
            log_channel_id = settings.get("log_channel")

            if settings.get("logger_enabled") and log_channel_id:
                log_channel = ctx.guild.get_channel(log_channel_id)

                if log_channel:
                    await log_channel.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Failed to ban user: {e}")

    # =============================
    # 🔨 BAN BY ID (user not in server)
    # =============================
    @commands.command(name="banid")
    @commands.has_permissions(ban_members=True)
    async def banid(self, ctx, user_id: int, *, reason: str = "No reason provided"):

        try:
            user = await self.bot.fetch_user(user_id)

            await ctx.guild.ban(user, reason=f"{ctx.author} | {reason}")

            await ctx.send(f"🔨 Banned user ID `{user_id}`")

        except Exception as e:
            await ctx.send(f"❌ Failed: {e}")

    # =============================
    # ⚠️ ERROR HANDLING
    # =============================
    @ban.error
    @banid.error
    async def ban_error(self, ctx, error):

        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this.")

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Usage: `?ban @user reason`")

        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Invalid user.")

        else:
            await ctx.send(f"❌ Error: {error}")


async def setup(bot):
    await bot.add_cog(Moderation(bot))

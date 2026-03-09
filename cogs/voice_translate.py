import discord
from discord.ext import commands
import tempfile
import wave
import numpy as np

from faster_whisper import WhisperModel
from deep_translator import GoogleTranslator
from discord.ext import voice_recv


class VoiceTranslate(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.translating = {}
        self.model = WhisperModel("tiny", compute_type="int8")
        self.translator = GoogleTranslator(source="ja", target="en")

    # -----------------------------
    # START LISTENING
    # -----------------------------
    async def start_translation(self, guild, voice_channel):

        vc = guild.voice_client

        if vc:
            await vc.disconnect()

        vc = await voice_channel.connect(cls=voice_recv.VoiceRecvClient, self_deaf=False)

        sink = voice_recv.BasicSink(self.process_audio)
        vc.listen(sink)

        print("Voice listener started")

        self.translating[guild.id] = True

    # -----------------------------
    # STOP LISTENING
    # -----------------------------
    async def stop_translation(self, guild):

        vc = guild.voice_client

        if vc:
            await vc.disconnect()

        self.translating.pop(guild.id, None)

    # -----------------------------
    # AUDIO PROCESSING
    # -----------------------------
    async def process_audio(self, user, data):
        
        print("Audio received from:", user)
        
        if not data:
            return

        pcm = np.frombuffer(data.pcm, dtype=np.int16)

        if len(pcm) < 8000:
            return

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:

            wf = wave.open(f.name, "wb")
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(48000)
            wf.writeframes(pcm.tobytes())
            wf.close()

            segments, _ = self.model.transcribe(
                f.name,
                language="ja",
                beam_size=5
            )

            text = ""
            for seg in segments:
                text += seg.text

        if not text.strip():
            return

        translated = self.translator.translate(text)

        for guild in self.bot.guilds:

            if guild.id not in self.translating:
                continue

            settings = await self.bot.settings_col.find_one({"guild_id": guild.id}) or {}

            channel_id = settings.get("translate_channel")

            if not channel_id:
                channel = guild.system_channel
            else:
                channel = guild.get_channel(channel_id)

            if channel:
                await channel.send(
                    f"🇯🇵 **{user.display_name}:** {text}\n"
                    f"🇺🇸 **Translation:** {translated}"
                )


async def setup(bot):
    await bot.add_cog(VoiceTranslate(bot))

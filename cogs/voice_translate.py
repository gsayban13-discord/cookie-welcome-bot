import discord
from discord.ext import commands
from discord.ext import voice_recv
import asyncio
import numpy as np
import tempfile
import wave
import time

from faster_whisper import WhisperModel
from deep_translator import GoogleTranslator


class VoiceTranslate(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.translating = {}
        self.audio_buffers = {}
        self.last_audio = {}

        self.model = WhisperModel(
            "tiny",
            device="cpu",
            compute_type="int8"
        )

        self.translator = GoogleTranslator(source="ja", target="en")

    # -----------------------------
    # START TRANSLATION
    # -----------------------------
    async def start_translation(self, guild, voice_channel):

        vc = guild.voice_client

        if vc:
            await vc.disconnect()

        vc = await voice_channel.connect(
            cls=voice_recv.VoiceRecvClient,
            self_deaf=False,
            self_mute=False
        )

        sink = voice_recv.BasicSink(self.process_audio)
        vc.listen(sink)

        self.translating[guild.id] = True
        self.audio_buffers[guild.id] = b""

        print("Voice listener started")

    # -----------------------------
    # STOP TRANSLATION
    # -----------------------------
    async def stop_translation(self, guild):

        vc = guild.voice_client

        if vc:
            await vc.disconnect()

        self.translating.pop(guild.id, None)
        self.audio_buffers.pop(guild.id, None)

    # -----------------------------
    # AUDIO CALLBACK
    # -----------------------------
    def process_audio(self, user, data):

        if not data or not data.pcm:
            return

        guild_id = user.guild.id

        if guild_id not in self.translating:
            return

        print("Audio packet from:", user)

        # append audio
        self.audio_buffers[guild_id] += data.pcm
        self.last_audio[guild_id] = time.time()

        # process every ~3 seconds
        if len(self.audio_buffers[guild_id]) < 48000 * 2 * 3:
            return

        audio_data = self.audio_buffers[guild_id]
        self.audio_buffers[guild_id] = b""

        asyncio.run_coroutine_threadsafe(
            self.transcribe_audio(user, audio_data),
            self.bot.loop
        )

    # -----------------------------
    # TRANSCRIBE + TRANSLATE
    # -----------------------------
    async def transcribe_audio(self, user, pcm_data):

        pcm = np.frombuffer(pcm_data, dtype=np.int16)

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
                beam_size=3
            )

        text = "".join(seg.text for seg in segments).strip()

        if not text:
            return

        try:
            translated = self.translator.translate(text)
        except:
            translated = "Translation error"

        guild = user.guild

        settings = await self.bot.settings_col.find_one(
            {"guild_id": guild.id}
        ) or {}

        channel_id = settings.get("translate_channel")

        if channel_id:
            channel = guild.get_channel(channel_id)
        else:
            channel = guild.system_channel

        if not channel:
            return

        await channel.send(
            f"🇯🇵 **{user.display_name}:** {text}\n"
            f"🇺🇸 **Translation:** {translated}"
        )


async def setup(bot):
    await bot.add_cog(VoiceTranslate(bot))

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


BUFFER_SECONDS = 2.5
SAMPLE_RATE = 48000


class VoiceTranslate(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.translating = {}
        self.buffers = {}
        self.processing = {}

        self.model = WhisperModel(
            "tiny",
            device="cpu",
            compute_type="int8"
        )

        self.translator = GoogleTranslator(source="auto", target="en")

    # -----------------------
    # START TRANSLATION
    # -----------------------

    async def start_translation(self, guild, voice_channel):

        vc = guild.voice_client

        if vc:
            await vc.disconnect()

        vc = await voice_channel.connect(cls=voice_recv.VoiceRecvClient)

        await vc.guild.change_voice_state(
            channel=voice_channel,
            self_deaf=False,
            self_mute=False
        )

        sink = voice_recv.BasicSink(self.process_audio)
        vc.listen(sink)

        self.translating[guild.id] = True
        self.buffers[guild.id] = bytearray()
        self.processing[guild.id] = False

        print(f"[Voice] Listener started in {guild.name}")

    # -----------------------
    # STOP
    # -----------------------

    async def stop_translation(self, guild):

        vc = guild.voice_client

        if vc:
            await vc.disconnect()

        self.translating.pop(guild.id, None)
        self.buffers.pop(guild.id, None)
        self.processing.pop(guild.id, None)

    # -----------------------
    # AUDIO RECEIVE
    # -----------------------

    def process_audio(self, user, data):

        if not data or not data.pcm:
            return

        guild = user.guild

        if guild.id not in self.translating:
            return

        buffer = self.buffers.setdefault(guild.id, bytearray())
        buffer.extend(data.pcm)

        required = int(SAMPLE_RATE * 2 * BUFFER_SECONDS)

        if len(buffer) < required:
            return

        if self.processing[guild.id]:
            return

        pcm_data = bytes(buffer)
        self.buffers[guild.id] = bytearray()
        self.processing[guild.id] = True

        asyncio.run_coroutine_threadsafe(
            self.transcribe(user, pcm_data),
            self.bot.loop
        )

    # -----------------------
    # TRANSCRIBE
    # -----------------------

    async def transcribe(self, user, pcm_data):

        try:

            pcm = np.frombuffer(pcm_data, dtype=np.int16)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:

                wf = wave.open(f.name, "wb")
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(pcm.tobytes())
                wf.close()

                segments, info = self.model.transcribe(
                    f.name,
                    beam_size=3
                )

            text = "".join(s.text for s in segments).strip()

            if not text:
                return

            try:
                translated = self.translator.translate(text)
            except:
                translated = "Translation failed"

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
                f"🎤 **{user.display_name}**\n"
                f"🗣 {text}\n"
                f"🌎 {translated}"
            )

        finally:
            self.processing[user.guild.id] = False


async def setup(bot):
    await bot.add_cog(VoiceTranslate(bot))

import discord
from discord.ext import commands
from discord.ext import voice_recv

import asyncio
import numpy as np
import tempfile
import wave
import queue
import threading

from faster_whisper import WhisperModel
from deep_translator import GoogleTranslator


BUFFER_SECONDS = 2
SAMPLE_RATE = 48000


class VoiceTranslate(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.active = {}
        self.audio_buffers = {}
        self.jobs = queue.Queue()

        self.model = WhisperModel(
            "tiny",
            device="cpu",
            compute_type="int8"
        )

        self.translator = GoogleTranslator(source="auto", target="en")

        worker = threading.Thread(target=self.worker_loop, daemon=True)
        worker.start()

    # -----------------------
    # START
    # -----------------------

    async def start_translation(self, guild, channel):

        vc = guild.voice_client

        if vc:
            await vc.disconnect()

        vc = await channel.connect(cls=voice_recv.VoiceRecvClient)

        await vc.guild.change_voice_state(
            channel=channel,
            self_deaf=False,
            self_mute=False
        )

        sink = voice_recv.BasicSink(self.process_audio)
        vc.listen(sink)

        self.active[guild.id] = True
        self.audio_buffers[guild.id] = bytearray()

        print(f"[Voice] Listening in {guild.name}")

    # -----------------------
    # STOP
    # -----------------------

    async def stop_translation(self, guild):

        vc = guild.voice_client

        if vc:
            await vc.disconnect()

        self.active.pop(guild.id, None)
        self.audio_buffers.pop(guild.id, None)

    # -----------------------
    # RECEIVE AUDIO
    # -----------------------

    def process_audio(self, user, data):

        if not data or not data.pcm:
            return

        guild = user.guild

        if guild.id not in self.active:
            return

        buffer = self.audio_buffers.setdefault(guild.id, bytearray())
        buffer.extend(data.pcm)

        required = int(SAMPLE_RATE * 2 * BUFFER_SECONDS)

        if len(buffer) < required:
            return

        pcm = bytes(buffer)
        self.audio_buffers[guild.id] = bytearray()

        self.jobs.put((user, pcm))

    # -----------------------
    # WORKER
    # -----------------------

    def worker_loop(self):

        while True:

            user, pcm = self.jobs.get()

            try:
                asyncio.run(self.transcribe(user, pcm))
            except Exception as e:
                print("Voice worker error:", e)

    # -----------------------
    # TRANSCRIBE
    # -----------------------

    async def transcribe(self, user, pcm_data):

        pcm = np.frombuffer(pcm_data, dtype=np.int16)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:

            wf = wave.open(f.name, "wb")
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(pcm.tobytes())
            wf.close()

            segments, _ = self.model.transcribe(
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


async def setup(bot):
    await bot.add_cog(VoiceTranslate(bot))

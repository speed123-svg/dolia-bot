import asyncio
import os

import aiohttp
import discord
import wavelink
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

LAVALINK_URI = os.getenv("LAVALINK_URI", "http://localhost:2333")
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
_music_loaded = False
_commands_synced = False
_startup_complete = False

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(
    command_prefix="d!",
    intents=intents,
    help_command=None,
    description="Dolia — Song-Weaver of the Scarlet Kingdom",
)


async def connect_lavalink(max_attempts=10, delay_seconds=5):
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"[Dolia] Connecting to Lavalink ({attempt}/{max_attempts}) at {LAVALINK_URI}")
            node = wavelink.Node(
                uri=LAVALINK_URI,
                password=LAVALINK_PASSWORD,
            )
            await wavelink.Pool.connect(nodes=[node], client=bot)
            print("[Dolia] Lavalink connected")
            return
        except Exception as exc:
            print(f"[Dolia] Lavalink connection failed: {exc}")
            if attempt == max_attempts:
                raise
            await asyncio.sleep(delay_seconds)


async def wait_for_lavalink(max_attempts=20, delay_seconds=3):
    info_url = f"{LAVALINK_URI.rstrip('/')}/v4/info"
    headers = {
        "Authorization": LAVALINK_PASSWORD,
    }

    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for attempt in range(1, max_attempts + 1):
            try:
                print(f"[Dolia] Waiting for Lavalink HTTP readiness ({attempt}/{max_attempts}) at {info_url}")
                async with session.get(info_url, headers=headers) as response:
                    if response.status == 200:
                        print("[Dolia] Lavalink HTTP endpoint is ready")
                        return
                    print(f"[Dolia] Lavalink readiness check returned HTTP {response.status}")
            except Exception as exc:
                print(f"[Dolia] Lavalink readiness check failed: {exc}")

            if attempt == max_attempts:
                raise RuntimeError("Lavalink HTTP endpoint did not become ready in time")

            await asyncio.sleep(delay_seconds)


@bot.event
async def on_ready():
    print(f"[Dolia] Logged in as {bot.user}")
    node = wavelink.Node(
        uri=LAVALINK_URI,
        password=os.getenv("LAVALINK_PASSWORD"),
    )
    await wavelink.Pool.connect(nodes=[node], client=bot)
    print("[Dolia] Lavalink connected ✓")
    await bot.load_extension("music")
    print("[Dolia] Music cog loaded ✓")
    await bot.tree.sync()
    print("[Dolia] Slash commands synced ✓")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="the melody between worlds 🎶",
        )
    )
    print("[Dolia] Ready ✨")


@bot.event
async def on_ready():
    global _startup_complete

    print(f"[Dolia] Logged in as {bot.user}")

    if _startup_complete:
        print("[Dolia] Ready event received again; startup already completed.")
        return

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="the melody between worlds",
        )
    )
    _startup_complete = True
    print("[Dolia] Ready")


async def run_bot():
    global _music_loaded, _commands_synced

    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN is missing")

    if not LAVALINK_PASSWORD:
        raise RuntimeError("LAVALINK_PASSWORD is missing")

    print("[Dolia] Starting bot process")

    async with bot:
        await wait_for_lavalink()
        await connect_lavalink()

        if not _music_loaded:
            await bot.load_extension("music")
            _music_loaded = True
            print("[Dolia] Music cog loaded")

        if not _commands_synced:
            await bot.tree.sync()
            _commands_synced = True
            print("[Dolia] Slash commands synced")

        print("[Dolia] Connecting to Discord")
        await bot.start(DISCORD_TOKEN)


async def main():
    async with bot:
        await bot.start(os.getenv("DISCORD_TOKEN"))


asyncio.run(run_bot())

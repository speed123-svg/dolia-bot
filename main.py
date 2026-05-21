import asyncio
import logging
import os

import aiohttp
import discord
import wavelink
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

LAVALINK_URI = os.getenv("LAVALINK_URI", "http://localhost:2333").rstrip("/")
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
STATUS_TEXT = os.getenv("STATUS_TEXT", "The melody between worlds").strip()
STATUS_TYPE = os.getenv("STATUS_TYPE", "custom").strip().lower()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip().upper()

LOGGER = logging.getLogger(__name__)

_music_loaded = False
_commands_synced = False
_lavalink_connected = False

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(
    command_prefix="d!",
    intents=intents,
    help_command=None,
    description="Dolia - Song-Weaver of the Scarlet Kingdom",
)


def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger("discord").setLevel(logging.INFO)
    logging.getLogger("wavelink").setLevel(logging.INFO)


async def send_error_response(interaction, message: str) -> None:
    embed = discord.Embed(
        title="A Discordant Wave",
        description=message,
        color=0x2F6FB3,
    )

    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
    except discord.HTTPException:
        LOGGER.exception("Failed to send command error response")


@bot.tree.error
async def on_app_command_error(interaction, error):
    command_name = interaction.command.qualified_name if interaction.command else "unknown"
    guild_id = interaction.guild.id if interaction.guild else None
    channel_id = interaction.channel.id if interaction.channel else None
    user_id = interaction.user.id if interaction.user else None

    LOGGER.error(
        "App command failed: command=%s guild=%s channel=%s user=%s",
        command_name,
        guild_id,
        channel_id,
        user_id,
        exc_info=(type(error), error, error.__traceback__),
    )
    await send_error_response(
        interaction,
        "Dolia hit an internal error while handling that command. Please try again in a moment.",
    )


async def wait_for_lavalink(max_attempts: int = 20, delay_seconds: int = 3) -> None:
    info_url = f"{LAVALINK_URI}/v4/info"
    headers = {"Authorization": LAVALINK_PASSWORD}

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
                print(f"[Dolia] Lavalink readiness check failed: {exc!r}")

            if attempt == max_attempts:
                raise RuntimeError("Lavalink HTTP endpoint did not become ready in time")

            await asyncio.sleep(delay_seconds)


async def connect_lavalink() -> None:
    print(f"[Dolia] Connecting to Lavalink at {LAVALINK_URI}")
    node = wavelink.Node(
        uri=LAVALINK_URI,
        password=LAVALINK_PASSWORD,
    )
    await wavelink.Pool.connect(nodes=[node], client=bot)
    print("[Dolia] Lavalink connected")


async def ensure_startup() -> None:
    global _music_loaded, _commands_synced, _lavalink_connected

    if not _music_loaded:
        await bot.load_extension("music")
        _music_loaded = True
        print("[Dolia] Music cog loaded")

    if not _lavalink_connected:
        await wait_for_lavalink()
        await connect_lavalink()
        _lavalink_connected = True

    if not _commands_synced:
        await bot.tree.sync()
        _commands_synced = True
        print("[Dolia] Slash commands synced")


def build_presence_activity():
    if not STATUS_TEXT:
        raise RuntimeError("STATUS_TEXT must not be empty")

    if STATUS_TYPE == "custom":
        return discord.CustomActivity(name=STATUS_TEXT)

    activity_types = {
        "playing": discord.ActivityType.playing,
        "listening": discord.ActivityType.listening,
        "watching": discord.ActivityType.watching,
        "competing": discord.ActivityType.competing,
    }
    activity_type = activity_types.get(STATUS_TYPE, discord.ActivityType.playing)
    return discord.Activity(type=activity_type, name=STATUS_TEXT)


@bot.event
async def on_ready():
    print(f"[Dolia] Logged in as {bot.user}")

    if not _lavalink_connected:
        await ensure_startup()

    await bot.change_presence(status=discord.Status.idle, activity=build_presence_activity())

    print("[Dolia] Ready")


async def main() -> None:
    configure_logging()

    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN is missing")
    if not LAVALINK_PASSWORD:
        raise RuntimeError("LAVALINK_PASSWORD is missing")

    print("[Dolia] Starting bot process")
    async with bot:
        print("[Dolia] Connecting to Discord")
        await bot.start(DISCORD_TOKEN)


asyncio.run(main())

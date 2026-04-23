from datetime import UTC, datetime

import discord

DOLIA_BLUE = 0x4A90E2
DOLIA_DEEP = 0x2F6FB3
DOLIA_FOOTER = "Dolia | Oceanic Songkeeper of the Moonlit Tide"
DOLIA_IDLE_THUMB = "https://i.imgur.com/DoliaThumbnail.png"


def format_duration(length_ms):
    if not length_ms:
        return "Live"

    total_seconds = int(length_ms // 1000)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def track_thumbnail(track):
    if getattr(track, "artwork", None):
        return track.artwork

    source = (getattr(track, "source", "") or "").lower()
    identifier = getattr(track, "identifier", None)
    if identifier and "youtube" in source:
        return f"https://i.ytimg.com/vi/{identifier}/hqdefault.jpg"

    return DOLIA_IDLE_THUMB


def loop_mode_label(mode):
    names = {
        "normal": "Off",
        "loop": "Track",
        "loop_all": "Queue",
    }
    return names.get(getattr(mode, "name", "normal"), "Off")


def control_panel_embed(player, guild, *, note=None):
    embed = discord.Embed(
        title="Dolia's Oceanic Control Panel",
        color=DOLIA_BLUE,
        timestamp=datetime.now(UTC),
    )

    current = getattr(player, "current", None) if player else None
    queue = getattr(player, "queue", None)
    queue_count = len(queue) if queue else 0
    upcoming_tracks = queue[:5] if queue_count else []

    if current:
        requester_id = getattr(current.extras, "requester_id", None)
        requester = guild.get_member(requester_id) if requester_id else None
        requester_text = requester.mention if requester else "Unknown traveler"

        embed.description = (
            f"**[{current.title}]({current.uri or 'https://youtube.com'})**\n"
            f"*by {current.author}*\n\n"
            f"{note or '🌊 Dolia keeps the current melody gliding across the tide.'}"
        )
        embed.set_thumbnail(url=track_thumbnail(current))
        embed.add_field(name="Duration", value=format_duration(current.length), inline=True)
        embed.add_field(name="Requester", value=requester_text, inline=True)
        embed.add_field(name="Position", value="Now Playing", inline=True)
        embed.add_field(name="Queue", value=str(queue_count), inline=True)
        embed.add_field(name="Volume", value=f"{getattr(player, 'volume', 100)}%", inline=True)
        embed.add_field(name="Loop", value=loop_mode_label(player.queue.mode), inline=True)

        if upcoming_tracks:
            lines = [f"`{index}.` {track.title}" for index, track in enumerate(upcoming_tracks, start=1)]
            embed.add_field(name="Up Next", value="\n".join(lines), inline=False)
    else:
        embed.description = note or "🌊 The tide is calm. No melody is flowing right now."
        embed.set_thumbnail(url=DOLIA_IDLE_THUMB)
        embed.add_field(name="Queue", value=str(queue_count), inline=True)
        embed.add_field(name="Loop", value="Off", inline=True)
        embed.add_field(name="Volume", value="100%", inline=True)

    embed.set_footer(text=DOLIA_FOOTER)
    return embed


def queue_embed(queue_list, guild, current=None, *, total_count=None):
    embed = discord.Embed(
        title="Dolia's Songbook",
        description="🌊 The melodies waiting beneath the tide.",
        color=DOLIA_BLUE,
        timestamp=datetime.now(UTC),
    )

    if current:
        requester_id = getattr(current.extras, "requester_id", None)
        requester = guild.get_member(requester_id) if requester_id else None
        requester_text = requester.mention if requester else "Unknown traveler"
        embed.add_field(
            name="Now Playing",
            value=(
                f"**[{current.title}]({current.uri or 'https://youtube.com'})**\n"
                f"`{format_duration(current.length)}` | Requested by {requester_text}"
            ),
            inline=False,
        )

    queue_total = len(queue_list) if total_count is None else total_count

    if queue_list:
        lines = []
        for index, track in enumerate(queue_list, start=1):
            requester_id = getattr(track.extras, "requester_id", None)
            requester = guild.get_member(requester_id) if requester_id else None
            requester_text = requester.display_name if requester else "Unknown traveler"
            lines.append(
                f"`{index}.` **{track.title}**\n"
                f"{format_duration(track.length)} | requested by {requester_text}"
            )
        embed.add_field(name="Queued Melodies", value="\n".join(lines), inline=False)
        if queue_total > len(queue_list):
            embed.add_field(
                name="More Waiting",
                value=f"And **{queue_total - len(queue_list)}** more melodies beyond this page.",
                inline=False,
            )
    else:
        embed.add_field(name="Queued Melodies", value="No verses are waiting.", inline=False)

    embed.set_footer(text=DOLIA_FOOTER)
    return embed


def search_embed(query, tracks):
    lines = []
    for index, track in enumerate(tracks[:10], start=1):
        lines.append(
            f"`{index}.` **{track.title}**\n"
            f"{track.author} | {format_duration(track.length)}"
        )

    embed = discord.Embed(
        title="Choose a Melody",
        description="\n".join(lines),
        color=DOLIA_BLUE,
        timestamp=datetime.now(UTC),
    )
    embed.add_field(name="Search", value=query, inline=False)
    embed.set_footer(text="Select one result below to let Dolia carry it forward.")
    return embed


def status_embed(title, description):
    embed = discord.Embed(
        title=title,
        description=description,
        color=DOLIA_DEEP,
        timestamp=datetime.now(UTC),
    )
    embed.set_footer(text=DOLIA_FOOTER)
    return embed


def error_embed(message):
    embed = discord.Embed(
        title="A Discordant Wave",
        description=message,
        color=DOLIA_DEEP,
        timestamp=datetime.now(UTC),
    )
    embed.set_footer(text=DOLIA_FOOTER)
    return embed


def help_embed():
    embed = discord.Embed(
        title="Dolia's Command Grimoire",
        description="✨ The ocean answers to these commands.",
        color=DOLIA_BLUE,
        timestamp=datetime.now(UTC),
    )
    embed.set_thumbnail(url=DOLIA_IDLE_THUMB)
    embed.add_field(
        name="Commands",
        inline=False,
        value=(
            "`/play` Search for a melody\n"
            "`/pause` Hold the tide\n"
            "`/resume` Wake the tide\n"
            "`/skip` Turn to the next verse\n"
            "`/stop` Silence the waters\n"
            "`/queue` View the waiting songbook\n"
            "`/volume` Adjust resonance\n"
            "`/loop` Change loop mode\n"
            "`/nowplaying` Reveal the current melody\n"
            "`/help` Open this grimoire"
        ),
    )
    embed.set_footer(text=DOLIA_FOOTER)
    return embed

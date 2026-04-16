import random

PLAY_LINES = [
    "🎶 Dolia hums softly as a new melody begins...",
    "🌊 Dolia gathers the tide and lets a fresh song rise from the deep.",
    "✨ A silver note stirs across the water as Dolia begins your chosen melody.",
]

QUEUE_LINES = [
    "🌊 Dolia tucks that melody into her songbook for the next tide.",
    "🎵 Another verse joins the current, waiting for its turn to bloom.",
    "✨ Dolia sets that song beside the others, ready for the waves to carry it onward.",
]

STOP_LINES = [
    "🌊 The waves fall silent... the music has ended.",
    "✨ Dolia lets the final note dissolve into the seafoam hush.",
    "🎵 The tide grows still as Dolia closes her songbook for now.",
]

SKIP_LINES = [
    "⏭️ Dolia turns the page and calls the next melody forward.",
    "🌊 One wave retreats, and another song rises behind it.",
    "✨ Dolia releases the fading refrain and beckons the next one near.",
]

PAUSE_LINES = [
    "⏯️ Dolia cups the melody gently in her hands and lets it rest.",
    "🌊 The tide pauses mid-breath, waiting for your signal to continue.",
]

RESUME_LINES = [
    "🎶 Dolia exhales, and the melody flows once more.",
    "✨ The sleeping note awakens and returns to the water's glow.",
]

LOOP_TRACK_LINES = [
    "🔁 Dolia binds this melody to the tide so it may return again and again.",
    "🌊 This song now circles endlessly beneath moonlit waters.",
]

LOOP_QUEUE_LINES = [
    "🔁 Dolia enchants the whole songbook so no page is ever truly the last.",
    "✨ The full procession of melodies now moves in an endless current.",
]

LOOP_OFF_LINES = [
    "🌊 The circle is broken, and the tide may drift forward once more.",
    "✨ Dolia loosens the enchantment and lets the music travel onward.",
]

NOT_IN_VC_LINES = [
    "🌊 Dolia cannot reach you from afar. Step into a voice channel first.",
    "✨ Your voice is not yet within Dolia's waters. Join a voice channel and call again.",
]

NO_TRACK_LINES = [
    "✨ Dolia could not find that melody in her world...",
    "🌊 The sea answered with silence. No such melody could be found.",
]

NOT_PLAYING_LINES = [
    "🌊 No melody is flowing through Dolia's waters right now.",
    "✨ The songbook is quiet. Summon a melody first.",
]

SEARCH_LINES = [
    "🔍 Dolia listened to the tide and found these possible melodies.",
    "🌊 The sea returned several echoes. Choose the one you seek.",
]

VOLUME_LINES = [
    "🔊 Dolia adjusts the swell of the tide to match your wish.",
    "✨ The resonance shifts, softer or brighter at your command.",
]

TRACK_END_LINES = [
    "🌊 The final ripple fades, and Dolia waits for the next song.",
    "✨ That melody has returned to the deep.",
]

QUEUE_ENDED_LINES = [
    "🌊 The final ripple fades. Dolia's queue has ended, and the sea is quiet once more.",
    "✨ The last melody sinks beneath the tide. Dolia's songbook now rests in silence.",
]

TRACK_ERROR_LINES = [
    "⚠️ Dolia felt that melody break apart before it could fully bloom.",
    "🌊 The current shattered around that song. Dolia could not carry it onward.",
]

IDLE_LINES = [
    "🌊 Dolia waits beside still waters for the next melody.",
    "✨ The ocean sleeps until another song is called forth.",
]


def say(lines):
    return random.choice(lines)

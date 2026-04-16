# Railway Deploy

This repo is set up for two Railway services:

1. `dolia-bot`
2. `dolia-lavalink`

## Required secrets

Set these in Railway for the bot service:

- `DISCORD_TOKEN`
- `LAVALINK_PASSWORD`
- `LAVALINK_URI`

Set this in the Lavalink service:

- `LAVALINK_PASSWORD`
- `YOUTUBE_REFRESH_TOKEN` optional but recommended if you use the `TV` client
- `YOUTUBE_PO_TOKEN` recommended for YouTube playback stability
- `YOUTUBE_VISITOR_DATA` recommended for YouTube playback stability
- `YOUTUBE_CIPHER_URL` recommended to avoid current YouTube cipher breakages
- `YOUTUBE_CIPHER_PASSWORD` if your cipher service requires auth

## Bot service

- Root directory: `/`
- Builder: `Dockerfile`

Environment variables:

- `DISCORD_TOKEN=<your token>`
- `LAVALINK_PASSWORD=<same password used by lavalink>`
- `LAVALINK_URI=http://dolia-lavalink.railway.internal:<lavalink PORT>`

## Lavalink service

- Root directory: `/`
- Builder: `lavalink/Dockerfile`

Environment variables:

- `LAVALINK_PASSWORD=<same password used by bot>`
- `YOUTUBE_REFRESH_TOKEN=<youtube refresh token, optional>`
- `YOUTUBE_PO_TOKEN=<po token, recommended>`
- `YOUTUBE_VISITOR_DATA=<visitor data, recommended>`
- `YOUTUBE_CIPHER_URL=<remote cipher server url, recommended>`
- `YOUTUBE_CIPHER_PASSWORD=<remote cipher password, optional>`

## Notes

- Keep `.env` out of git. Use Railway variables in production.
- The bot and Lavalink should be in the same Railway project so private networking works.
- Railway injects `PORT` for the running container. Do not hardcode `2333` unless the service is actually listening there.
- Your current Railway log shows Lavalink responding on `http://dolia-lavalink.railway.internal:8080`, so the bot service should use that port unless the Lavalink service changes.
- SoundCloud playback working while YouTube fails usually means Discord voice and the bot are healthy, but the Lavalink YouTube plugin needs extra auth/cipher configuration.
- Railway private DNS uses the format `<service-name>.railway.internal`.

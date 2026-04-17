# Railway Deploy

This setup now uses three Railway services:

1. `dolia-bot`
2. `dolia-lavalink`
3. `dolia-cipher`

## Required secrets

Set these in Railway for the bot service:

- `DISCORD_TOKEN`
- `LAVALINK_PASSWORD`
- `LAVALINK_URI`

Set this in the Lavalink service:

- `LAVALINK_PASSWORD`
- `YOUTUBE_REFRESH_TOKEN` optional but recommended if you use the `TV` client
- `YOUTUBE_PO_TOKEN` required for the confirmed working YouTube setup
- `YOUTUBE_VISITOR_DATA` required for the confirmed working YouTube setup
- `YOUTUBE_CIPHER_URL` required to use the remote cipher service
- `YOUTUBE_CIPHER_PASSWORD` if your cipher service requires auth

Set these in the cipher service:

- Whatever your cipher container requires to start
- The password must match `YOUTUBE_CIPHER_PASSWORD` if auth is enabled

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
- `JAVA_TOOL_OPTIONS=-Xms128m -Xmx384m -XX:+UseG1GC -XX:+ExitOnOutOfMemoryError -Djava.awt.headless=true`
- `YOUTUBE_REFRESH_TOKEN=<youtube refresh token, optional>`
- `YOUTUBE_PO_TOKEN=<po token>`
- `YOUTUBE_VISITOR_DATA=<visitor data>`
- `YOUTUBE_CIPHER_URL=http://dolia-cipher.railway.internal:8080`
- `YOUTUBE_CIPHER_PASSWORD=<remote cipher password, optional>`

## Cipher service

- Service name: `dolia-cipher`
- Private URL from Lavalink: `http://dolia-cipher.railway.internal:8080`

This service is what fixes the recent YouTube cipher/signature failures. Keep it in the same Railway project as Lavalink so the internal hostname resolves.

## Confirmed working Lavalink env

The YouTube playback fix was confirmed with this variable set on the Lavalink service:

- `YOUTUBE_PO_TOKEN`
- `YOUTUBE_VISITOR_DATA`
- `YOUTUBE_CIPHER_URL=http://dolia-cipher.railway.internal:8080`
- `YOUTUBE_CIPHER_PASSWORD`

## Notes

- Keep `.env` out of git. Use Railway variables in production.
- Keep the bot, Lavalink, and cipher services in the same Railway project so private networking works.
- If Railway is still killing Lavalink for memory after this change, raise the service memory limit or lower `-Xmx` further. A good starting rule is to keep heap at roughly 60-75% of the container memory so native memory, threads, and buffers still have headroom.
- Railway injects `PORT` for the running container. Do not hardcode `2333` unless the service is actually listening there.
- Your current Railway log shows Lavalink responding on `http://dolia-lavalink.railway.internal:8080`, so the bot service should use that port unless the Lavalink service changes.
- If YouTube starts failing again with signature or login errors, check the PO token, visitor data, and cipher service reachability first.
- Railway private DNS uses the format `<service-name>.railway.internal`.

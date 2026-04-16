# Railway Deploy

This repo is set up for two Railway services:

1. `dolia-bot`
2. `dolia-lavalink`

## Before you push

1. Initialize git in `d:\dolia-bot`
2. Commit the project
3. Push to GitHub

## Required secrets

Set these in Railway for the bot service:

- `DISCORD_TOKEN`
- `LAVALINK_PASSWORD`
- `LAVALINK_URI`

Set this in Railway for the Lavalink service:

- `LAVALINK_PASSWORD`

## Service 1: Bot

- Root directory: `/`
- Builder: Dockerfile
- Dockerfile path: `Dockerfile`

Environment variables:

- `DISCORD_TOKEN=<your token>`
- `LAVALINK_PASSWORD=<same password used by lavalink>`
- `LAVALINK_URI=http://dolia-lavalink.railway.internal:2333`

## Service 2: Lavalink

- Root directory: `/`
- Builder: Dockerfile
- Dockerfile path: `lavalink/Dockerfile`

Environment variables:

- `SERVER_PORT=2333`
- `LAVALINK_PASSWORD=<same password used by bot>`

## Notes

- Keep `.env` out of git. Use Railway variables in production.
- The bot and Lavalink should be in the same Railway project so private networking is easy.
- If you change the password, update it in both services.
- Railway private DNS uses the format `<service-name>.railway.internal`.

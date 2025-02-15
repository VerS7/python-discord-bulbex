# python-discord-bulbex

Discord bot with VKontakte/Yandex music
Discord bot with VKontakte / Yandex music

## Build & Deploy

```bash
docker build -t discord-bulbex .
```

```bash
docker run --name <name> \
           --env-file <.env file> \
           --restart=always \
           -v ./logs:/app/logs \
           -d discord-bulbex
```

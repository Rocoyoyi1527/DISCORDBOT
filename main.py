import discord
from discord.ext import commands
import yt_dlp as youtube_dl  # Reemplaza youtube_dl por yt_dlp
import asyncio
import os

# Configura el bot con permisos de intención
intents = discord.Intents.default()
intents.message_content = True  # FIX: Habilita la intención correcta

bot = commands.Bot(command_prefix='!!', intents=intents)

# Cola de reproducción
queue = []
is_playing = False
voice_client = None

# Ruta al archivo de cookies (asegúrate de que esté correctamente en tu entorno)
cookie_file_path = 'cookies.txt'  # Actualiza esta ruta

# Configura yt_dlp (reemplazo de youtube_dl)
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'cookiefile': cookie_file_path,  # Aquí agregamos el archivo de cookies
}

# Configura la ruta de ffmpeg
ffmpeg_path = '/nix/store/3zc5jbvqzrn8zmva4fx5p0nh4yy03wk4-ffmpeg-6.1.1-bin/bin/ffmpeg'  # Asegúrate de poner la ruta correcta de ffmpeg


async def play_next(ctx):
    """Reproduce la siguiente canción en la cola."""
    global is_playing, queue, voice_client

    if queue:
        is_playing = True
        url = queue.pop(0)

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info['url']

        if voice_client and voice_client.is_connected():
            voice_client.play(discord.FFmpegPCMAudio(url2,
                                                     executable=ffmpeg_path),
                              after=lambda e: asyncio.run_coroutine_threadsafe(
                                  play_next(ctx), bot.loop))
        else:
            await ctx.send("❌ Error: No estoy en un canal de voz.")
            is_playing = False
    else:
        is_playing = False


@bot.command()
async def play(ctx, url: str):
    """Reproduce una canción desde YouTube."""
    global is_playing, voice_client

    if ctx.author.voice is None:
        await ctx.send(
            "🔊 Debes estar en un canal de voz para usar este comando.")
        return

    channel = ctx.author.voice.channel
    if not ctx.voice_client:
        voice_client = await channel.connect()
    else:
        voice_client = ctx.voice_client

    queue.append(url)
    await ctx.send(f"🎵 Añadido a la cola: {url}")

    if not is_playing:
        await play_next(ctx)


@bot.command()
async def pause(ctx):
    """Pausa la reproducción."""
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.send("⏸️ Música pausada.")


@bot.command()
async def resume(ctx):
    """Reanuda la reproducción."""
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.send("▶️ Música reanudada.")


@bot.command()
async def stop(ctx):
    """Detiene la reproducción y limpia la cola."""
    global queue
    queue = []
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send("⏹️ Música detenida.")


@bot.command()
async def leave(ctx):
    """Hace que el bot salga del canal de voz."""
    global voice_client, is_playing, queue
    queue = []
    is_playing = False
    if voice_client:
        await voice_client.disconnect()
        await ctx.send("👋 Saliendo del canal de voz.")
        voice_client = None


@bot.event
async def on_ready():
    """Se ejecuta cuando el bot está listo."""
    print(f'✅ Conectado como {bot.user}')
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send(
                    "✅ ¡Estoy en línea y listo para reproducir música!")
                return


TOKEN = os.getenv("DISCORD_TOKEN")  # Obtiene el token de los Secrets
bot.run(TOKEN)

import os
import asyncio
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
from dotenv import load_dotenv

# Carpeta de audios
AUDIO_FOLDER = "./audios"

intents = discord.Intents.default()
bot = commands.Bot(intents=intents)

load_dotenv()
token = os.getenv("DISCORD_TOKEN")
if not token:
    print("Error: El token de Discord no es válido")
    exit(1)

@bot.event
async def on_ready():
    print(f"Bot conectado como: {bot.user}")

def listar_mp3():
    """Retorna la lista de archivos .mp3 dentro de la carpeta AUDIO_FOLDER."""
    archivos = []
    if os.path.isdir(AUDIO_FOLDER):
        for f in os.listdir(AUDIO_FOLDER):
            if f.lower().endswith(".mp3"):
                archivos.append(f)
    return archivos

# Función que se usará para autocompletar el nombre del archivo
async def autocomplete_mp3(ctx: discord.AutocompleteContext):
    """Retorna sugerencias de archivos .mp3 que coincidan con lo que el usuario va tecleando."""
    texto_usuario = ctx.value.lower()
    all_mp3 = listar_mp3()
    sugerencias = [f for f in all_mp3 if texto_usuario in f.lower()]
    return sugerencias[:25]

# Cambiamos el nombre del comando a "dale"
@bot.slash_command(
    name="dale", 
    description="Reproduce un archivo de audio de la carpeta 'audios'"
)
@discord.option(
    "filename",
    description="Selecciona el archivo MP3 a reproducir",
    required=True,
    autocomplete=autocomplete_mp3  # Enlaza la función de autocompletado
)
async def dale(
    ctx: discord.ApplicationContext,
    filename: str
):
    """Reproduce el archivo .mp3 indicado, se une al canal de voz y se desconecta al finalizar."""
    voice_state = ctx.author.voice
    if not voice_state or not voice_state.channel:
        return await ctx.respond("¡Debes estar en un canal de voz!")

    voice_client = ctx.voice_client
    if not voice_client or not voice_client.is_connected():
        await voice_state.channel.connect()
        voice_client = ctx.voice_client
    else:
        if voice_client.channel.id != voice_state.channel.id:
            await voice_client.move_to(voice_state.channel)

    # Verificar que el archivo exista
    ruta_archivo = os.path.join(AUDIO_FOLDER, filename)
    if not os.path.isfile(ruta_archivo):
        return await ctx.respond(f"El archivo `{filename}` no existe en `{AUDIO_FOLDER}`.")

    if voice_client.is_playing():
        return await ctx.respond("Ya estoy reproduciendo algo. Espera a que termine.")

    # Preparar la reproducción
    source = FFmpegPCMAudio(ruta_archivo)

    # Callback para desconectarse al terminar
    def after_play(error):
        if error:
            print(f"Error al reproducir: {error}")
        coro = voice_client.disconnect()
        asyncio.run_coroutine_threadsafe(coro, bot.loop)

    voice_client.play(source, after=after_play)

    await ctx.respond(f"Reproduciendo **{filename}**... (Me saldré al terminar.)")

bot.run(token)

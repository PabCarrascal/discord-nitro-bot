import os
import asyncio
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
from dotenv import load_dotenv

# Carga las variables definidas en el archivo .env
load_dotenv()
# Leer la variable DISCORD_TOKEN que debe estar en el .env
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

AUDIO_FOLDER = "/home/ftp-usr/discord-bot-audios"

intents = discord.Intents.default()
bot = commands.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f"Bot conectado como: {bot.user}")

def listar_mp3():
    """Retorna la lista de archivos .mp3 dentro de AUDIO_FOLDER."""
    archivos = []
    if os.path.isdir(AUDIO_FOLDER):
        for nombre in os.listdir(AUDIO_FOLDER):
            if nombre.lower().endswith(".mp3"):
                archivos.append(nombre)
    return archivos

# Función de autocompletado
async def autocomplete_mp3(ctx: discord.AutocompleteContext):
    """Filtra los archivos .mp3 según lo que el usuario escribe."""
    texto_usuario = ctx.value.lower()
    todos_los_mp3 = listar_mp3()
    sugerencias = [f for f in todos_los_mp3 if texto_usuario in f.lower()]
    return sugerencias[:25]

@bot.slash_command(
    name="dale",
    description="Reproduce un archivo MP3 de la carpeta /home/ftp-usr/discord-bot-audios"
)
@discord.option(
    "filename",
    description="Selecciona el archivo MP3 a reproducir",
    required=True,
    autocomplete=autocomplete_mp3
)
async def dale(
    ctx: discord.ApplicationContext,
    filename: str
):
    await ctx.defer(ephemeral=True)

    voice_state = ctx.author.voice
    if not voice_state or not voice_state.channel:
        return await ctx.followup.send("¡Debes estar en un canal de voz para usar /dale!")

    voice_client = ctx.voice_client
    if not voice_client or not voice_client.is_connected():
        await voice_state.channel.connect()
        voice_client = ctx.voice_client
    elif voice_client.channel.id != voice_state.channel.id:
        await voice_client.move_to(voice_state.channel)

    ruta_archivo = os.path.join(AUDIO_FOLDER, filename)
    if not os.path.isfile(ruta_archivo):
        return await ctx.followup.send(f"El archivo `{filename}` no existe en `{AUDIO_FOLDER}`.")

    if voice_client.is_playing():
        return await ctx.followup.send("Ya estoy reproduciendo un audio. Espera a que termine.")

    source = FFmpegPCMAudio(ruta_archivo)

    def after_play(error):
        if error:
            print(f"[ERROR] Reproduciendo audio: {error}")
        coro = voice_client.disconnect()
        asyncio.run_coroutine_threadsafe(coro, bot.loop)

    voice_client.play(source, after=after_play)

    await ctx.followup.send(
        f"Reproduciendo **{filename}** en tu canal. Me desconectaré al terminar.", 
        ephemeral=True
    )

bot.run(DISCORD_TOKEN)

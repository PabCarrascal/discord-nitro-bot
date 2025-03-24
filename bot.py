import os
import asyncio
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio

# Carpeta donde se encuentran los archivos .mp3
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
    return sugerencias[:25]  # máximo 25 sugerencias

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
    """
    Slash command que reproduce el archivo MP3 (filename) en el canal de voz.
    Se usa defer(ephemeral=True) para no mostrar mensaje público en el chat.
    """
    # 1) Indica a Discord que estás procesando y que la respuesta será efímera (invisible al resto).
    await ctx.defer(ephemeral=True)

    # 2) Verificar que el usuario esté en un canal de voz
    voice_state = ctx.author.voice
    if not voice_state or not voice_state.channel:
        # Respondemos de forma efímera (sólo lo ve la persona que ejecutó)
        return await ctx.followup.send("¡Debes unirte a un canal de voz antes de usar /dale!")

    # 3) Conectarnos al canal de voz (o movernos si ya estamos en otro)
    voice_client = ctx.voice_client
    if not voice_client or not voice_client.is_connected():
        await voice_state.channel.connect()
        voice_client = ctx.voice_client
    elif voice_client.channel.id != voice_state.channel.id:
        await voice_client.move_to(voice_state.channel)

    # 4) Verificar que el archivo exista
    ruta_archivo = os.path.join(AUDIO_FOLDER, filename)
    if not os.path.isfile(ruta_archivo):
        return await ctx.followup.send(f"El archivo `{filename}` no existe en `{AUDIO_FOLDER}`.")

    # 5) Si ya está reproduciendo algo, avisa
    if voice_client.is_playing():
        return await ctx.followup.send("Ya estoy reproduciendo un audio. Espera a que termine.")

    source = FFmpegPCMAudio(ruta_archivo)

    def after_play(error):
        if error:
            print(f"[ERROR] Reproduciendo audio: {error}")
        coro = voice_client.disconnect()
        asyncio.run_coroutine_threadsafe(coro, bot.loop)

    voice_client.play(source, after=after_play)

    # 6) Si no quieres enviar ningún mensaje final, no hagas followup.send()
    #    Sin embargo, es buena práctica avisar al menos al usuario que se está reproduciendo
    #    pero en modo efímero, para que no aparezca en el canal público:

    await ctx.followup.send(f"Reproduciendo **{filename}** en tu canal. Me saldré al terminar.", ephemeral=True)

# Inicia el bot (reemplaza con tu token real)
bot.run("TU_TOKEN_AQUI")

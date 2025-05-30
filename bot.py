import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import asyncio

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

try:
    source_channels_str = os.getenv("FROM_CHANNEL_IDS", "").split(',')
    SOURCE_CHANNEL_IDS = [int(cid.strip()) for cid in source_channels_str if cid.strip()] 

    DESTINATION_CHANNEL_ID = int(os.getenv("TO_CHANNEL_ID"))
except (TypeError, ValueError) as e:
    print(f"Error: Pastikan semua Channel ID (FROM_CHANNEL_IDS, TO_CHANNEL_ID) "
          f"ada di file .env dan berupa angka yang valid. Detail error: {e}")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True      
intents.presences = True           
intents.members = True              
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

tree = bot.tree

@bot.event
async def on_ready():
    print(f"Bot {bot.user} sudah online")
    print(f"Memantau pesan dari Channel IDs: {SOURCE_CHANNEL_IDS}")
    print(f"Meneruskan ke Channel ID: {DESTINATION_CHANNEL_ID}")

    try:
        await tree.sync() 
        print("Slash commands synced globally.")
    except Exception as e:
        print(f"Gagal melakukan sinkronisasi slash commands: {e}")

@bot.event
async def on_message(message: discord.Message): 
    if message.author == bot.user:
        return

    if message.channel.id == DESTINATION_CHANNEL_ID:
        return

    if message.channel.id in SOURCE_CHANNEL_IDS:
        destination_channel = bot.get_channel(DESTINATION_CHANNEL_ID)

        if not destination_channel:
            print(f"Channel tujuan dengan ID {DESTINATION_CHANNEL_ID} tidak ditemukan atau bot tidak bisa mengaksesnya!")
            return
        

        forward_message_content = f"**{message.author.display_name}:** "
        files_to_send = []

        if message.content:
            forward_message_content += message.content

        if message.attachments:
            for attachment in message.attachments:
                try:
                    discord_file = await attachment.to_file()
                    files_to_send.append(discord_file)
                except discord.HTTPException as e:
                    print(f"Error HTTP saat mengunduh/memproses attachment {attachment.filename}: {e}")
                except Exception as e:
                    print(f"Gagal memproses attachment {attachment.filename}: {e}")
        
        if not message.content and not files_to_send:
            return

        try:
            await destination_channel.send(content=forward_message_content, files=files_to_send)
            print(f"Pesan dari {message.author.display_name} di #{message.channel.name} ({message.guild.name}) "
                  f"berhasil diteruskan ke #{destination_channel.name}.")
        except discord.Forbidden:
            print(f"Bot tidak punya izin (Forbidden) kirim pesan/file di channel {destination_channel.name}!")
        except Exception as e:
            print(f"Gagal meneruskan pesan dan attachment: {e}")

    await bot.process_commands(message)


@tree.command(name="joinvc", description="Membuat bot bergabung ke voice channel tertentu")
@app_commands.describe(
    channel_id="ID dari voice channel yang ingin digabungkan"
)
async def joinvc(interaction: discord.Interaction, channel_id: str):
    await interaction.response.defer(ephemeral=True) # Mengirim respons defer

    guild = interaction.guild
    if not guild:
        await interaction.followup.send("Perintah ini hanya bisa digunakan di dalam server Discord.")
        return

    try:
        vc_id = int(channel_id)
        voice_channel = guild.get_channel(vc_id)
    except ValueError:
        await interaction.followup.send("ID channel tidak valid. Pastikan ID channel berupa angka.")
        return
    
    if not isinstance(voice_channel, discord.VoiceChannel):
        await interaction.followup.send("ID yang diberikan bukan ID voice channel yang valid di server ini.")
        return
        
    if guild.voice_client: 
        if guild.voice_client.channel == voice_channel:
            await interaction.followup.send(f"Bot sudah terhubung ke voice channel {voice_channel.mention}.")
            return
        else:
            await interaction.followup.send(f"Bot terhubung ke {guild.voice_client.channel.mention}. Memutuskan koneksi sebelum bergabung ke channel baru...")
            await guild.voice_client.disconnect()
            
    permissions = voice_channel.permissions_for(guild.me)
    if not permissions.connect:
        await interaction.followup.send(f"Bot tidak memiliki izin untuk terhubung ke voice channel {voice_channel.mention}. Mohon berikan izin 'Connect'.")
        return
    if not permissions.speak:
        await interaction.followup.send(f"Bot tidak memiliki izin untuk berbicara di voice channel {voice_channel.mention}. Mohon berikan izin 'Speak'.")
        return

    try:
        await voice_channel.connect()
        await interaction.followup.send(f"Berhasil bergabung ke voice channel {voice_channel.mention}!")
    except discord.ClientException as e:
        await interaction.followup.send(f"Gagal bergabung ke voice channel: {e}. Pastikan bot tidak sudah terhubung ke channel lain atau tidak memiliki izin.")
    except Exception as e:
        await interaction.followup.send(f"Terjadi kesalahan tidak terduga saat bergabung ke VC: {e}")


@tree.command(name="msg", description="Kirim pesan teks ke channel tertentu.")
@app_commands.describe(
    channel_id="ID dari channel tujuan (teks)",
    message_content="Pesan yang ingin dikirim"
)
async def msg(interaction: discord.Interaction, channel_id: str, message_content: str):
    await interaction.response.defer(ephemeral=True) # Defer respons

    try:
        target_channel_id = int(channel_id)
        target_channel = bot.get_channel(target_channel_id)
    except ValueError:
        await interaction.followup.send("ID channel tidak valid. Pastikan ID channel berupa angka.")
        return
    
    if not target_channel:
        await interaction.followup.send("Channel tujuan tidak ditemukan atau bot tidak memiliki akses ke channel tersebut.")
        return

    permissions = target_channel.permissions_for(interaction.guild.me)
    if not permissions.send_messages:
        await interaction.followup.send(f"Bot tidak memiliki izin untuk mengirim pesan di channel {target_channel.mention}.")
        return

    try:
        await target_channel.send(message_content)
        await interaction.followup.send(f"Pesan berhasil dikirim ke {target_channel.mention}.", ephemeral=True)
        print(f"Pesan '{message_content}' berhasil dikirim ke #{target_channel.name} oleh {interaction.user.display_name}.")
    except discord.Forbidden:
        await interaction.followup.send(f"Bot tidak memiliki izin untuk mengirim pesan ke channel {target_channel.mention}.")
        print(f"ERROR: Bot tidak bisa mengirim pesan ke #{target_channel.name} karena izin Forbidden.")
    except Exception as e:
        await interaction.followup.send(f"Terjadi kesalahan saat mengirim pesan: {e}", ephemeral=True)
        print(f"ERROR: Gagal mengirim pesan ke #{target_channel.name}: {e}")


@tree.command(name="msgimg", description="Kirim pesan disertai gambar/video ke channel tertentu.")
@app_commands.describe(
    channel_id="ID dari channel tujuan (teks)",
    attachment="Gambar atau video yang ingin dikirim", 
    message_content="Pesan opsional yang menyertai gambar/video"
)
async def msgimg(interaction: discord.Interaction, channel_id: str, attachment: discord.Attachment, message_content: str = None):
    await interaction.response.defer(ephemeral=True) # Defer respons

    try:
        target_channel_id = int(channel_id)
        target_channel = bot.get_channel(target_channel_id)
    except ValueError:
        await interaction.followup.send("ID channel tidak valid. Pastikan ID channel berupa angka.")
        return
    
    if not target_channel:
        await interaction.followup.send("Channel tujuan tidak ditemukan atau bot tidak memiliki akses ke channel tersebut.")
        return

    permissions = target_channel.permissions_for(interaction.guild.me)
    if not permissions.send_messages or not permissions.attach_files:
        await interaction.followup.send(f"Bot tidak memiliki izin untuk mengirim pesan dan/atau melampirkan file di channel {target_channel.mention}.")
        return


    if not (attachment.content_type and (attachment.content_type.startswith('image/') or attachment.content_type.startswith('video/'))):
        await interaction.followup.send("File yang diupload bukan gambar atau video. Fitur ini hanya mendukung gambar/video.", ephemeral=True)
        return

    try:
        discord_file = await attachment.to_file()

        await target_channel.send(content=message_content, file=discord_file)
        await interaction.followup.send(f"Gambar/video dan pesan berhasil dikirim ke {target_channel.mention}.", ephemeral=True)
        print(f"Attachment '{attachment.filename}' berhasil dikirim ke #{target_channel.name} oleh {interaction.user.display_name}.")

    except discord.HTTPException as e:
        await interaction.followup.send(f"Gagal mengunggah file ke Discord: {e}", ephemeral=True)
        print(f"ERROR: Gagal mengunggah file '{attachment.filename}' ke #{target_channel.name}: {e}")
    except Exception as e:
        await interaction.followup.send(f"Terjadi kesalahan tidak terduga saat mengirim gambar/video: {e}", ephemeral=True)
        print(f"ERROR: Terjadi kesalahan saat mengirim gambar/video '{attachment.filename}': {e}")

@tree.command(name="leavevc", description="Membuat bot meninggalkan voice channel saat ini.")
async def leavevc(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True) # Defer respons

    guild = interaction.guild
    if not guild:
        await interaction.followup.send("Perintah ini hanya bisa digunakan di dalam server Discord.")
        return

   
    if guild.voice_client: 
        try:
            channel_name = guild.voice_client.channel.name
            await guild.voice_client.disconnect()
            await interaction.followup.send(f"Bot berhasil meninggalkan voice channel **{channel_name}**.")
            print(f"Bot meninggalkan voice channel: {channel_name} di {guild.name}.")
        except Exception as e:
            await interaction.followup.send(f"Terjadi kesalahan saat meninggalkan voice channel: {e}")
            print(f"ERROR: Gagal meninggalkan voice channel di {guild.name}: {e}")
    else:
        await interaction.followup.send("Bot tidak terhubung ke voice channel manapun di server ini.")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
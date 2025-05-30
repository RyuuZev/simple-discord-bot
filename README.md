# Bot Discord Simpel

Bot ini adalah sebuah bot sederhana yang fungsinya sebagai berikut

- Mengirim pesan
- Mengirim gambar
- Forward attachment dari beberapa channel ke channel khusus
- Join ke voice untuk menemani kamu

## Requirement

- Visual Code Studio
- Python
- [Token bot discord](https://discord.com/developers/applications/) 

## Cara Install

### Step pertama

Buka terminal dan jalankan kode
```
pip install discord.py python-dotenv PyNaCl
```
Setelah diinstall lalu jalankan kode berikut ini agar package tidak hilang
```
pip freeze > requirements.txt
```

### 

### Hal yang perlu diperhatikan

Pastikan saat kamu menambahkan bot discord ke server bagian scope: bot dan applications.commands. dipilih.
Di bagian "Bot Permissions", pilih "Send Messages", "Embed Links", "Attach Files", "Read Message History", "Manage Webhooks", dan "Connect".


"""
Sığınak Bot - Ana Giriş Noktası (main.py)
=========================================
Sığınak Veba RP Bot v5.4 - Cogs mimarisi + v. prefix komutları + cache temizleme + db-sifirla

Çalıştırma:
    export DISCORD_TOKEN=...
    export YEDEK_KANAL_ID=...    (opsiyonel)
    python main.py

Bot başladığında:
1. Veritabanını yükler
2. Tüm cog'ları yükler (16 cog - prefix dahil)
3. Eski Discord slash komut cache'ini temizler (command not found fix)
4. Yeni slash komutlarını Discord'a senkronize eder
5. Otomatik task'ları başlatır (yedekleme, vergi, gazete, açlık)
6. Keep-alive Flask sunucusunu başlatır (Render uyku modunu önlemek için)

Önemli:
- v. prefix komutları için Discord Developer Portal'da "Message Content Intent" açılmalı!
- Slash komutları için herhangi bir ek ayar gerekmez.

Prefix Komut Örnekleri:
    v.kayit Johann Bauer 25 Bavyera
    v.profil
    v.pazar Silah
    v.gez "Terkedilmiş Köy"
    v.db-sifirla EVET  (sadece admin)
"""

import os
import sys
import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands, tasks

# --- Keep alive web sunucusu (Render free tier için) ---
from keep_alive import keep_alive

# --- Veritabanı ---
from veritabani import verileri_yukle, db_ilkle, verileri_kaydet, db

# --- Loglama ayarı ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("siginak-bot")


# ====================================================
# BOT YAPILANDIRMASI
# ====================================================
# commands.Bot kullanıyoruz çünkü cog'lar bunu gerektirir.
# Slash komutları hala app_commands ile çalışır.
intents = discord.Intents.default()
intents.members = True         # Rol işlemleri için gerekli
intents.message_content = True  # v. prefix komutları için GEREKLİ (Discord Developer Portal'da da açılmalı!)

bot = commands.Bot(
    command_prefix="v.",  # v. prefix komutları için (örn: v.kayit, v.profil)
    intents=intents,
    help_command=None     # /destek ve /rehber komutları yardımı sağlar
)


# ====================================================
# COG LİSTESİ - Bot açılışında sırayla yüklenir
# ====================================================
COG_LISTESI = [
    "cogs.kayit",
    "cogs.meslek",
    "cogs.pazar",
    "cogs.savas",
    "cogs.kesif",
    "cogs.yonetim",
    "cogs.simya",
    "cogs.kilise",
    "cogs.kolluk",
    "cogs.uretim",
    "cogs.ambar",
    "cogs.maliye",
    "cogs.cevre",
    "cogs.rehber",
    "cogs.sistem",
    "cogs.prefix",
]


# ====================================================
# BOT HAZIR OLDUĞUNDA
# ====================================================
@bot.event
async def on_ready():
    log.info("=" * 60)
    log.info(f"🤖 {bot.user.name} (ID: {bot.user.id}) çevrimiçi!")
    log.info("=" * 60)

    # Veritabanını hazırla
    verileri_yukle()
    db_ilkle()
    log.info(f"📊 Veritabanı yüklendi: {len(db.get('sakinler', {}))} sakin")

    # Tüm cog'ları yükle
    yuklenen = 0
    hatalar = []
    for cog_adi in COG_LISTESI:
        try:
            await bot.load_extension(cog_adi)
            yuklenen += 1
            log.info(f"  ✅ Yüklendi: {cog_adi}")
        except Exception as e:
            hatalar.append((cog_adi, str(e)))
            log.error(f"  ❌ HATA: {cog_adi} -> {e}")

    log.info(f"📦 Toplam {yuklenen}/{len(COG_LISTESI)} cog yüklendi.")
    if hatalar:
        log.warning(f"⚠️ {len(hatalar)} cog yüklenemedi!")
        for isim, hata in hatalar:
            log.warning(f"   {isim}: {hata[:100]}")

    # Sistem cog'ını başlat (yedek kanalı ayarla + geri yükleme)
    try:
        sistem_cog = bot.get_cog("SistemCog")
        if sistem_cog:
            sistem_cog.yedek_kanal_ayarla()
            await sistem_cog.yedekten_geri_yukle()
            log.info(f"📦 Yedekleme kanalı ayarlandı: {sistem_cog.yedek_kanal_id}")
    except Exception as e:
        log.error(f"❌ Sistem cog başlatma hatası: {e}")

    # SLASH KOMUT SENKRONİZASYONU
    # Eski komutları Discord'dan temizlemek yerine güvenli sync yapıyoruz.
    # clear_commands(guild=None) kullanırsak bot'un kendi ağacı da boşalır ve
    # ikinci sync Discord'a boş liste gönderir → tüm komutlar kaybolur!
    # Bu yüzden sadece sync() yapıyoruz, Discord eski/komut adlarını otomatik günceller.
    try:
        log.info(f"📥 Slash komutları Discord'a senkronize ediliyor... (bot ağacında {len(bot.tree.get_commands())} komut var)")
        synced = await bot.tree.sync()
        log.info(f"✔️ {len(synced)} slash komutu Discord'a senkronize edildi.")
        
        # Eğer 0 komut sync edildiyse, bir şeyler ters gitmiş olabilir
        if len(synced) == 0:
            log.warning("⚠️ Hiç komut sync edilmedi! Cog'lar kontrol edilmeli.")
        else:
            # Komut adlarını listele (debug için)
            komut_adlari = [cmd.name for cmd in synced[:5]]
            log.info(f"📋 İlk 5 komut: {', '.join(komut_adlari)}...")
    except Exception as e:
        log.error(f"❌ Senkronizasyon hatası: {e}")

    # Aktiflik göstergesi
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"Sığınakta {len(db.get('sakinler', {}))} sakin"
        )
    )
    log.info("=" * 60)
    log.info("🟢 Bot tamamen hazır!")
    log.info("=" * 60)


# ====================================================
# HATA YAKALAMA
# ====================================================
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Slash komut hatası yakalama."""
    hata_mesaji = str(error)

    # Yetki hataları
    if isinstance(error, app_commands.MissingPermissions):
        hata_mesaji = f"❌ Bu komut için yetkiniz yok! Gerekli: {', '.join(error.missing_permissions)}"
    elif isinstance(error, app_commands.CommandOnCooldown):
        hata_mesaji = f"⏱️ Bu komut bekleme süresinde! {error.retry_after:.1f} saniye sonra tekrar deneyin."
    elif isinstance(error, app_commands.BotMissingPermissions):
        hata_mesaji = f"❌ Botun yetkisi yok! Gerekli: {', '.join(error.missing_permissions)}"

    log.error(f"Slash komut hatası: {error}")

    try:
        if interaction.response.is_done():
            await interaction.followup.send(hata_mesaji, ephemeral=True)
        else:
            await interaction.response.send_message(hata_mesaji, ephemeral=True)
    except Exception:
        pass


# ====================================================
# BOTU ÇALIŞTIR
# ====================================================
async def main():
    # Keep-alive Flask sunucusunu ayrı thread'de başlat
    keep_alive()
    log.info("🌐 Keep-alive sunucusu başlatıldı (port 8080)")

    # Token kontrolü
    token = os.environ.get("DISCORD_TOKEN", "")
    if not token:
        log.error("❌ DISCORD_TOKEN ortam değişkeni bulunamadı!")
        log.error("   Lütfen .env dosyasına veya Render ortam değişkenlerine DISCORD_TOKEN ekleyin.")
        sys.exit(1)

    # Botu çalıştır
    async with bot:
        try:
            await bot.start(token)
        except KeyboardInterrupt:
            log.info("🛑 Bot kapatılıyor...")
            await bot.close()
        except Exception as e:
            log.error(f"❌ Bot çalışma hatası: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())

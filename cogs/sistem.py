"""
Cog: Sistem (Yedekleme & Açlık)
==============================
Otomatik Task'lar:
- 1 saatte bir yedekleme (Discord kanalına JSON gönderir)
- 24 saatte bir açlık/susuzluk düşürür (su -10, su 0 ise sağlık -15)

Bot açılışında YEDEK_KANAL_ID env var'dan okunur, db boşsa son yedekten geri yükler.
"""

import discord
from discord.ext import commands, tasks
import json
import io
import os
import datetime

from veritabani import db, verileri_kaydet, haber_ekle
from kanallar import YEDEKLEME_KANAL_ID, ACLUK_RAPOR_KANAL_ID


class SistemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.yedek_kanal_id = None

        # Task'ları başlat
        self.otomatik_yedekleme_task.start()
        self.acluk_suyu_dusur_task.start()

    def cog_unload(self):
        self.otomatik_yedekleme_task.cancel()
        self.acluk_suyu_dusur_task.cancel()

    # ====================================================
    # YEDEKLEME FONKSİYONLARI
    # ====================================================
    async def yedekle(self):
        if self.yedek_kanal_id is None:
            return
        try:
            kanal = self.bot.get_channel(self.yedek_kanal_id)
            if kanal is None:
                return
            veri_json = json.dumps(db, ensure_ascii=False, indent=4)
            zaman = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
            dosya = discord.File(io.BytesIO(veri_json.encode('utf-8')), filename=f"yedek_{zaman}.json")
            await kanal.send(content=f"📦 **Otomatik Yedek** — {zaman}", file=dosya)
            print(f"✅ Yedek gönderildi: yedek_{zaman}.json")
        except Exception as e:
            print(f"❌ Yedekleme hatası: {e}")

    async def yedekten_geri_yukle(self):
        if self.yedek_kanal_id is None:
            return
        try:
            # Sadece db boşsa geri yükle
            if len(db.get("sakinler", {})) > 0:
                return
            kanal = self.bot.get_channel(self.yedek_kanal_id)
            if kanal is None:
                return
            async for mesaj in kanal.history(limit=10):
                if mesaj.attachments:
                    ek = mesaj.attachments[0]
                    if ek.filename.endswith('.json'):
                        icerik = await ek.read()
                        veri = json.loads(icerik.decode('utf-8'))
                        db.clear()
                        db.update(veri)
                        verileri_kaydet()
                        print(f"✅ Yedekten geri yüklendi: {ek.filename}")
                        return
        except Exception as e:
            print(f"❌ Yedekten geri yükleme hatası: {e}")

    def yedek_kanal_ayarla(self):
        """Env var'dan YEDEK_KANAL_ID okur, yoksa kanallar.py'deki default'u kullanır."""
        yedek_kanal_str = os.environ.get("YEDEK_KANAL_ID", "")
        if yedek_kanal_str:
            try:
                self.yedek_kanal_id = int(yedek_kanal_str)
                return
            except ValueError:
                pass
        # Default: kanallar.py'den
        self.yedek_kanal_id = YEDEKLEME_KANAL_ID

    # ====================================================
    # 1 SAATLİK OTOMATİK YEDEKLEME
    # ====================================================
    @tasks.loop(hours=1)
    async def otomatik_yedekleme_task(self):
        await self.yedekle()
        # Yedeklemeden sonra botun watching durumunu güncelle
        try:
            sakin_sayisi = len([s for s in db.get("sakinler", {}).values() if s.get("durum") != "Ölü"])
            await self.bot.change_presence(
                status=discord.Status.online,
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name=f"Sığınakta {sakin_sayisi} sakin"
                )
            )
        except Exception:
            pass

    @otomatik_yedekleme_task.before_loop
    async def before_yedek_task(self):
        await self.bot.wait_until_ready()
        if self.yedek_kanal_id is None:
            self.yedek_kanal_ayarla()

    # ====================================================
    # 24 SAATLİK AÇLIK/SUSUZLUK DÜŞÜRME
    # ====================================================
    @tasks.loop(hours=24)
    async def acluk_suyu_dusur_task(self):
        # İlk turu atla (bot başlar başlamaz açlık düşmesin)
        if not hasattr(self.acluk_suyu_dusur_task, '_ilk_calisma_tamamlandi'):
            self.acluk_suyu_dusur_task._ilk_calisma_tamamlandi = True
            return

        ac_kalan = 0
        susuzluk_hasari = 0

        for s_id, veri in db["sakinler"].items():
            if veri.get("durum") in ("Canlı", "Sağlıklı", "Enfekte"):
                # Su seviyesi -10
                eski_su = veri.get("su", 100)
                veri["su"] = max(0, eski_su - 10)

                # Su 0 ise sağlık hasarı
                if veri["su"] == 0:
                    eski_saglik = veri.get("saglik", 100)
                    veri["saglik"] = max(0, eski_saglik - 15)
                    susuzluk_hasari += 1

                    # Sağlık 0 ise ölüm!
                    if veri["saglik"] == 0:
                        # v5.9: Türkçe karakter "Ölü" - önceden "Öldü" yazılmıştı
                        veri["durum"] = "Ölü"
                        veri["meslek_anahtar"] = "gezgin"
                        veri["meslek_isim"] = "Gezgin (Öldü)"
                        veri["cuzdan"] = 0
                        veri["envanter"] = {}
                else:
                    ac_kalan += 1

        verileri_kaydet()

        # Açlık raporu kriz kanalına (eğer açlık varsa)
        if susuzluk_hasari > 0:
            kanal = self.bot.get_channel(ACLUK_RAPOR_KANAL_ID)
            if kanal:
                embed = discord.Embed(title="💀 SIĞINAK AÇLIK RAPORU", color=0xC0392B)
                embed.description = (
                    f"⏰ **Dönem:** 24 Saatlik Açlık/Susuzluk Döngüsü\n\n"
                    f"💧 **Su Seviyesi Düşen Sakin:** `{ac_kalan + susuzluk_hasari}`\n"
                    f"💀 **Susuzluktan Hasar Alan:** `{susuzluk_hasari}`\n\n"
                    f"⚠️ **Sakinler suya ve gıdaya erişim sağlamazsa ölmeye başlayacaklar!**\n"
                    f"💡 `/tuket` komutuyla gıda tüketerek suyunuzu yenileyin."
                )
                try:
                    await kanal.send(embed=embed)
                except Exception:
                    pass
            haber_ekle(f"💀 Açlık döngüsü! {susuzluk_hasari} sakin susuzluktan hasar aldı.")

    @acluk_suyu_dusur_task.before_loop
    async def before_acluk_task(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    cog = SistemCog(bot)
    await bot.add_cog(cog)

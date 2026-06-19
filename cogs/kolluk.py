"""
Cog: Kolluk, Savunma, İdari Kısıtlama
=====================================
Komutlar:
- /muhafiz-paneli (panel)
- /hucreye-at (kolluk)
- /hucreden-cikar (kolluk)
- /karantina-al (kolluk/karantinacı)
- /karantina-kaldir (kolluk/simyacı)
- /sokak-yasagi (başkan)
- /savunmayi-guclendir (başkan, +15 tahkimat)
- /darbe (isyan, başkan devirme)
- /nobet (muhafız nöbet tutar, XP+hurda kazanır, 4 saat CD)
"""

import discord
from discord import app_commands
from discord.ext import commands
import random
import datetime

from veritabani import db, verileri_kaydet, olu_kontrolu, xp_ekle, haber_ekle
from cogs.simya import MESLEK_GRUPLARI


KARANTINACI_ROL_ID = 1508540605259714700


class KollukCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ====================================================
    # /muhafiz-paneli
    # ====================================================
    @app_commands.command(name="muhafiz-paneli", description="[KOLLUK] Sığınak içi asayiş, hücre cezaları ve kelepçe işlemlerini yönetir.")
    async def muhafiz_paneli(self, interaction: discord.Interaction):
        u_id = str(interaction.user.id)
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return
        meslek = db["sakinler"].get(u_id, {}).get("meslek_anahtar", "")

        if meslek not in MESLEK_GRUPLARI["kolluk"]:
            await interaction.response.send_message("❌ Silah taşımaya ve asayişi sağlamaya yetkiniz yok!", ephemeral=True)
            return

        embed = discord.Embed(title="🛡️ SIĞINAK ASAYİŞ VE KOLLUK KOMUTANLIĞI", color=0x2980B9)
        embed.description = (
            "⚔️ **Kolluk Kuvveti Operasyon Arayüzü:**\n\n"
            "🔒 `/hucreye-at [@sakin]` -> Asayişi bozan, darbeci veya kurallara uymayan sakini zindana kapatır.\n"
            "🔓 `/hucreden-cikar [@sakin]` -> Sakinin cezasını sonlandırır.\n"
            "🛡️ `/nobet` -> Nöbet tut, XP ve hurda kazan (4 saat CD).\n\n"
            f"🛡️ **Mevcut Muhafız Tahkimatı:** `{db['savunma_sistemi'].get('muhafiz_tahkimati', 10)}/100`"
        )
        await interaction.response.send_message(embed=embed)

    # ====================================================
    # /hucreye-at
    # ====================================================
    @app_commands.command(name="hucreye-at", description="[KOLLUK] Kurallara uymayan sakini asayişi sağlamak adına hücreye kapatır.")
    @app_commands.describe(hedef="Zindana atılacak suçlu sakin")
    async def hucreye_at(self, interaction: discord.Interaction, hedef: discord.Member):
        u_id = str(interaction.user.id)
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return
        h_id = str(hedef.id)
        meslek = db["sakinler"].get(u_id, {}).get("meslek_anahtar", "")

        if meslek not in MESLEK_GRUPLARI["kolluk"]:
            await interaction.response.send_message("❌ Tutuklama yetkiniz yok!", ephemeral=True)
            return

        if h_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Bu kişi sığınakta yaşamıyor!", ephemeral=True)
            return

        if db["sakinler"][h_id].get("durum") == "Ölü":
            await interaction.response.send_message("❌ Ölü birini hücreye atmanın anlamı yok!", ephemeral=True)
            return

        if db["sakinler"][h_id].get("durum") == "Hücrede":
            await interaction.response.send_message("❌ Bu sakin zaten hücrede!", ephemeral=True)
            return

        # Başkan hücreye atılamaz
        if db["sakinler"][h_id].get("meslek_anahtar") == "belediye_baskani":
            await interaction.response.send_message("❌ Belediye Başkanını hücreye atamazsın!", ephemeral=True)
            return

        db["sakinler"][h_id]["durum"] = "Hücrede"
        verileri_kaydet()

        embed = discord.Embed(title="🔒 ZİNDANA ATILDI", color=0xE74C3C)
        embed.description = (
            f"🛡️ **Tutuklayan Muhafız:** {interaction.user.mention}\n"
            f"👤 **Tutuklanan:** {hedef.mention}\n\n"
            f"Sığınak düzenini bozduğu gerekçesiyle **Zindana (Hücreye)** kapatıldı!"
        )
        await interaction.response.send_message(embed=embed)
        haber_ekle(f"🔒 {db['sakinler'][h_id]['isim']} muhafız tarafından hücreye atıldı.")

    # ====================================================
    # /hucreden-cikar
    # ====================================================
    @app_commands.command(name="hucreden-çıkar", description="[KOLLUK] Hücredeki bir sakini serbest bırakır.")
    @app_commands.describe(hedef="Tahliye edilecek sakin")
    async def hucreden_cikar(self, interaction: discord.Interaction, hedef: discord.Member):
        u_id = str(interaction.user.id)
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return
        h_id = str(hedef.id)
        meslek = db["sakinler"].get(u_id, {}).get("meslek_anahtar", "")

        if meslek not in MESLEK_GRUPLARI["kolluk"]:
            await interaction.response.send_message("❌ Tahliye yetkiniz yok!", ephemeral=True)
            return

        if db["sakinler"].get(h_id, {}).get("durum") != "Hücrede":
            await interaction.response.send_message("❌ Bu sakin zaten hücrede değil!", ephemeral=True)
            return

        db["sakinler"][h_id]["durum"] = "Canlı"
        verileri_kaydet()

        await interaction.response.send_message(
            f"🔓 {hedef.mention} hücreden çıkarıldı, sığınak sokaklarına geri döndü."
        )
        haber_ekle(f"🔓 {db['sakinler'][h_id]['isim']} hücreden tahliye edildi.")

    # ====================================================
    # /karantina-al
    # ====================================================
    @app_commands.command(name="karantina-al", description="[KOLLUK / KARANTİNACI] Enfekte olmuş (vebalı) bir sakini zorla karantina çadırına kapatır.")
    @app_commands.describe(hedef_sakin="Karantinaya alınacak enfekte üye")
    async def karantina_al(self, interaction: discord.Interaction, hedef_sakin: discord.Member):
        u_id = str(interaction.user.id)
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return
        h_id = str(hedef_sakin.id)

        if u_id not in db["sakinler"] or h_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Sicil kayıtlarında hata var!", ephemeral=True)
            return

        yetkili_meslek = db["sakinler"][u_id].get("meslek_anahtar", "")
        has_karantinaci_role = any(rol.id == KARANTINACI_ROL_ID for rol in interaction.user.roles)

        if yetkili_meslek not in ["belediye_baskani", "baskan_yardimcisi", "muhafiz_komutani", "muhafiz"] and not has_karantinaci_role:
            await interaction.response.send_message(
                "❌ Karantina operasyonu yürütme yetkiniz yok! Sadece Karantinacılar ve Muhafızlar uygulayabilir.",
                ephemeral=True
            )
            return

        if db["sakinler"][h_id].get("durum") != "Enfekte":
            await interaction.response.send_message(
                "❌ Bu sakin zaten sağlıklı, suçsuz yere karantinaya tıkamazsın!",
                ephemeral=True
            )
            return

        db["sakinler"][h_id]["durum"] = "Karantinada"
        if h_id not in db["idari_kisitlamalar"]["karantina_cadiri"]:
            db["idari_kisitlamalar"]["karantina_cadiri"].append(h_id)
        verileri_kaydet()

        embed = discord.Embed(title="☣️ ZORUNLU BİYOLOJİK TECRİT OPERASYONU", color=0xE67E22)
        embed.description = (
            f"🚨 **Kolluk Kuvveti:** {interaction.user.mention}\n"
            f"👤 **Tecrit Edilen Sakin:** {hedef_sakin.mention}\n\n"
            f"⛺ {hedef_sakin.mention}, enfeksiyon belirtileri gösterdiği gerekçesiyle **Zorla Karantina Çadırına** kapatılmıştır!\n"
            f"🔒 Simyacılar tarafından tedavi edilene (`/tedavi-et`) kadar hareketleri kısıtlanmıştır."
        )
        await interaction.response.send_message(embed=embed)
        haber_ekle(f"☣️ {db['sakinler'][h_id]['isim']} karantinaya alındı.")

    # ====================================================
    # /karantina-kaldir
    # ====================================================
    @app_commands.command(name="karantina-kaldır", description="[KOLLUK/BAŞ SİMYACI] Tedavi olmuş veya karantina süresi dolmuş sakini çadırdan çıkarır.")
    @app_commands.describe(hedef_sakin="Karantinadan çıkarılacak üye")
    async def karantina_kaldir(self, interaction: discord.Interaction, hedef_sakin: discord.Member):
        u_id = str(interaction.user.id)
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return
        h_id = str(hedef_sakin.id)

        yetkili_meslek = db["sakinler"].get(u_id, {}).get("meslek_anahtar", "")
        has_karantinaci_role = any(rol.id == KARANTINACI_ROL_ID for rol in interaction.user.roles)

        if yetkili_meslek not in ["belediye_baskani", "muhafiz_komutani", "bas_simyaci", "simyaci"] and not has_karantinaci_role:
            await interaction.response.send_message("❌ Karantina tahliye kararnamesi imzalama yetkiniz yok!", ephemeral=True)
            return

        if db["sakinler"][h_id].get("durum") != "Karantinada":
            await interaction.response.send_message("❌ Bu sakin zaten karantina çadırında değil!", ephemeral=True)
            return

        db["sakinler"][h_id]["durum"] = "Sağlıklı"
        if h_id in db["idari_kisitlamalar"]["karantina_cadiri"]:
            db["idari_kisitlamalar"]["karantina_cadiri"].remove(h_id)
        verileri_kaydet()

        embed = discord.Embed(title="🟢 TECRİT VE KARANTİNA TAHLİYE RAPORU", color=0x2ECC71)
        embed.description = (
            f"📜 **Tahliye Eden Yetkili:** {interaction.user.mention}\n"
            f"👤 **Serbest Bırakılan Sakin:** {hedef_sakin.mention}\n\n"
            f"✔️ {hedef_sakin.mention} üzerindeki biyolojik risk kalkmış, karantinadan salınmıştır!"
        )
        await interaction.response.send_message(embed=embed)

    # ====================================================
    # /sokak-yasagi
    # ====================================================
    @app_commands.command(name="sokak-yasagi", description="[BAŞKAN] Sığınak genelinde sokağa çıkma yasağını açar veya kapatır.")
    @app_commands.describe(durum="Yasak Açılsın mı? (True: Evet / False: Hayır)")
    async def sokak_yasagi(self, interaction: discord.Interaction, durum: bool):
        u_id = str(interaction.user.id)
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return

        if db["sakinler"].get(u_id, {}).get("meslek_anahtar") != "belediye_baskani":
            await interaction.response.send_message("❌ Sokağa çıkma yasağı ilan etme yetkisi sadece Belediye Başkanına aittir!", ephemeral=True)
            return

        db["idari_kisitlamalar"]["sokaga_cikma_yasagi"] = durum
        verileri_kaydet()

        embed = discord.Embed(title="🚨 SIĞINAKTA SIKIYÖNETİM", color=0xC0392B if durum else 0x2ECC71)

        if durum:
            embed.description = (
                f"📢 **Belediye Başkanı {interaction.user.mention}** sığınak genelinde **Sokağa Çıkma Yasağı** ilan etti!\n\n"
                f"🚫 **Kilitlenen Eylemler:** Tüm sığınak sakinlerinin dış dünya gezileri, pazar alım-satımları, düelloları ve takas kanalları askıya alınmıştır."
            )
            haber_ekle("🚨 Sokağa çıkma yasağı ilan edildi!")
        else:
            embed.description = (
                f"🔓 **Belediye Başkanı {interaction.user.mention}** sokağa çıkma yasağını kaldırdı!\n\n"
                f"🌾 Sığınak meydanı, pazar alanı ve dış dünya keşif rotaları yeniden tüm sakinlerin erişimine açılmıştır."
            )
            haber_ekle("🔓 Sokağa çıkma yasağı kaldırıldı.")

        await interaction.response.send_message(embed=embed)

    # ====================================================
    # /savunmayi-guclendir
    # ====================================================
    @app_commands.command(name="savunmayı-güçlendir", description="[BAŞKAN] Darbe ve isyanlara karşı muhafız tahkimatını artır (500 Hurda, +15 tahkimat).")
    async def savunma_guclendir(self, interaction: discord.Interaction):
        u_id = str(interaction.user.id)
        if db["sakinler"].get(u_id, {}).get("meslek_anahtar") != "belediye_baskani":
            await interaction.response.send_message("❌ Sadece belediye başkanı savunma emirleri verebilir!", ephemeral=True)
            return

        if db["sistem_ayarlari"]["kasa_hurda"] < 500:
            await interaction.response.send_message("❌ Sığınak kasasında 500 Hurda yok!", ephemeral=True)
            return

        mevcut_tahkimat = db["savunma_sistemi"]["muhafiz_tahkimati"]
        if mevcut_tahkimat >= 100:
            await interaction.response.send_message("❌ Muhafız tahkimatı zaten maksimum (%100)!", ephemeral=True)
            return

        db["sistem_ayarlari"]["kasa_hurda"] -= 500
        db["savunma_sistemi"]["muhafiz_tahkimati"] = min(100, mevcut_tahkimat + 15)
        verileri_kaydet()

        await interaction.response.send_message(
            f"🛡️ Muhafız tahkimatı güçlendirildi! Yeni Savunma Puanı: `{db['savunma_sistemi']['muhafiz_tahkimati']}/100`"
        )
        haber_ekle("🛡️ Başkan muhafız tahkimatını güçlendirdi (+15).")

    # ====================================================
    # /darbe - İsyancıların başkanı devirme girişimi
    # ====================================================
    @app_commands.command(name="darbe", description="[İSYAN] Belediye başkanına karşı isyan başlat ve darbe girişiminde bulun!")
    async def darbe_baslat(self, interaction: discord.Interaction):
        u_id = str(interaction.user.id)
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return

        if db["sakinler"].get(u_id, {}).get("durum") == "Ölü":
            await interaction.response.send_message("❌ Ölü biri darbe başlatamaz!", ephemeral=True)
            return

        baskan_id = None
        for s_id, veri in db["sakinler"].items():
            if veri.get("meslek_anahtar") == "belediye_baskani":
                baskan_id = s_id
                break

        if not baskan_id or baskan_id == u_id:
            await interaction.response.send_message("❌ Şu an ortada devrilmeye değer bir başkan yok!", ephemeral=True)
            return

        # Darbe başarı şansı
        itibar_puan = db["sistem_ayarlari"].get("kasa_hurda", 0) / 10
        savunma = db["savunma_sistemi"]["muhafiz_tahkimati"]
        basari_sansi = 10 + (100 - min(itibar_puan, 100)) + (50 - savunma)
        basari_sansi = max(5, min(basari_sansi, 90))

        zar = random.randint(1, 100)

        if zar <= basari_sansi:
            # DARBE BAŞARILI
            db["sakinler"][baskan_id]["meslek_anahtar"] = "gezgin"
            db["sakinler"][baskan_id]["meslek_isim"] = "Gezgin (Devrildi)"
            db["sakinler"][u_id]["meslek_anahtar"] = "belediye_baskani"
            db["sakinler"][u_id]["meslek_isim"] = "Belediye Başkanı"
            db["sistem_ayarlari"]["kasa_hurda"] = max(0, db["sistem_ayarlari"].get("kasa_hurda", 0) // 2)
            verileri_kaydet()

            embed = discord.Embed(title="🔥 İHTİLAL! SIĞINAKTA DARBE BAŞARILI!", color=0xE74C3C)
            embed.description = (
                f"📢 **{interaction.user.mention}** önderliğindeki isyancılar başkanlık sarayına baskın yaptı!\n\n"
                f"👑 Eski başkan tahttan indirildi! Yeni belediye başkanı: **{interaction.user.mention}**\n"
                f"⚠️ Sığınak hazinesinin yarısı yağmalandı!"
            )
            await interaction.response.send_message(embed=embed)
            haber_ekle(f"🔥 DARBE! {db['sakinler'][u_id]['isim']} başkanlığı devraldı.")
        else:
            embed = discord.Embed(title="🛡️ DARBE GİRİŞİMİ BASTIRILDI!", color=0x3498DB)
            embed.description = (
                f"⚔️ **{interaction.user.mention}** darbe yapmaya çalıştı ancak muhafızlar tarafından bozguna uğratıldı!\n\n"
                f"📉 **Başarı Şansı:** `%{basari_sansi}` | **Zar:** `{zar}`\n\n"
                f"⚠️ *Başkan isyancıları 'Vatan Haini' ilan etti!*"
            )
            await interaction.response.send_message(embed=embed)
            haber_ekle(f"🛡️ Darbe girişimi bastırıldı! Girişen: {db['sakinler'][u_id]['isim']}")

    # ====================================================
    # /nobet - Muhafız nöbet tutar
    # ====================================================
    @app_commands.command(name="nobet", description="[MUHAFIZ] Nöbet tut, XP ve hurda kazan (4 saat cooldown).")
    async def nobet_tut(self, interaction: discord.Interaction):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Sicil kaydın yok!", ephemeral=True)
            return
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return

        sakin = db["sakinler"][u_id]
        meslek = sakin.get("meslek_anahtar", "")

        if meslek not in MESLEK_GRUPLARI["kolluk"]:
            await interaction.response.send_message("❌ Sadece muhafız sınıfı nöbet tutabilir!", ephemeral=True)
            return

        # 4 saat cooldown
        son_nobet = sakin.get("son_nobet")
        if son_nobet:
            fark = datetime.datetime.now() - datetime.datetime.fromisoformat(son_nobet)
            if fark.total_seconds() < 14400:  # 4 saat
                kalan_saat = int((14400 - fark.total_seconds()) / 3600)
                kalan_dk = int(((14400 - fark.total_seconds()) % 3600) / 60)
                await interaction.response.send_message(
                    f"❌ Nöbet yorgunluğu geçmedi! `{kalan_saat} saat {kalan_dk} dk` beklemelisin.",
                    ephemeral=True
                )
                return

        # Nöbet sonuçları - mesleğe göre çarpan
        taban_hurda = random.randint(40, 80)
        taban_xp = 20

        if meslek == "muhafiz_komutani":
            taban_hurda = int(taban_hurda * 1.5)
            taban_xp = 35
        elif meslek == "muhafiz":
            taban_hurda = int(taban_hurda * 1.2)
            taban_xp = 25

        # Şans faktörü: bazen küçük olay
        olay_zari = random.randint(1, 10)
        ek_metin = ""
        if olay_zari <= 2:
            # Vardiyada suçlu yakaladı, bonus
            bonus = random.randint(30, 60)
            taban_hurda += bonus
            ek_metin = f"\n🚨 **Vardiya Olayı:** Sur kenarında dolaşan bir hırsızı yakaladın! `+{bonus} Hurda` ikramiye!"
        elif olay_zari >= 9:
            # Sıkıcı nöbet, daha az ödül
            taban_hurda = int(taban_hurda * 0.7)
            ek_metin = "\n😴 **Sıkıcı Nöbet:** Hiçbir şey olmadı, sadece üşüdün. Ödül azaldı."

        # Ödül ver
        sakin["cuzdan"] = sakin.get("cuzdan", 0) + taban_hurda
        atlamalar = xp_ekle(u_id, taban_xp)
        sakin["son_nobet"] = datetime.datetime.now().isoformat()
        verileri_kaydet()

        embed = discord.Embed(title="🛡️ NÖBET RAPORU", color=0x3498DB)
        embed.description = (
            f"👤 **Muhafız:** {interaction.user.mention} ({sakin.get('meslek_isim', 'Muhafız')})\n"
            f"⏰ **Vardiye Süresi:** 4 saat (simüle)\n\n"
            f"💰 **Kazanılan Hurda:** `+{taban_hurda}`\n"
            f"⭐ **Kazanılan XP:** `+{taban_xp}`"
            f"{ek_metin}\n\n"
            f"⏱️ *Bir sonraki nöbet için 4 saat beklemelisin.*"
        )

        if atlamalar:
            embed.add_field(
                name="🎉 Seviye Atlamaları",
                value="\n".join([f"• Seviye {a['seviye']}! +{a['odul']} Hurda" for a in atlamalar]),
                inline=False
            )

        await interaction.response.send_message(embed=embed)
        haber_ekle(f"🛡️ {sakin['isim']} nöbet tuttu ve {taban_hurda} hurda kazandı.")


async def setup(bot):
    await bot.add_cog(KollukCog(bot))

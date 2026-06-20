"""
Cog: Ambar (Köy Ortak Deposu)
============================
Komutlar:
- /ambar (stok listesi)
- /ambara-bagis (envanterden ambara bağış, +2 hurda/adet itibar)
- /ambardan-al (ihtiyaç sahipleri ücretsiz alır, max 5/adet)
"""

import discord
from discord import app_commands
from discord.ext import commands

from veritabani import db, verileri_kaydet, olu_kontrolu, haber_ekle


# Ambar eşya eşleştirme matrisi
ESYA_HARITASI = {
    "erzak": "erzak", "yemek": "erzak", "gıda": "erzak",
    "tıbbi": "tibbi_malzeme", "ilaç": "tibbi_malzeme", "medkit": "tibbi_malzeme", "tibbi_malzeme": "tibbi_malzeme",
    "odun": "odun", "tahta": "odun",
    "kömür": "komur", "komur": "komur"
}

ESYA_ETIKET = {
    "erzak": "🌾 Erzak/Gıda",
    "tibbi_malzeme": "⚕️ Tıbbi Malzeme/İlaç",
    "odun": "🪵 Odun/Kereste",
    "komur": "🪨 Kömür/Cevher"
}


class AmbarCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ====================================================
    # /ambar - Stok listele
    # ====================================================
    @app_commands.command(name="ambar", description="[AMBAR] Sığınak ortak köy ambarındaki mevcut yiyecek, ilaç ve hammadde stoklarını listeler.")
    async def ambar_listele(self, interaction: discord.Interaction):
        stoklar = db["koy_ambari"]["stoklar"]

        embed = discord.Embed(title="🏡 SIĞINAK KOLEKTİF KÖY AMBARI STOK RAPORU", color=0x34495E)

        ambar_text = "📋 **Mevcut Ortak Stok Bilgileri:**\n\n"
        for anahtar, etiket in ESYA_ETIKET.items():
            miktar = stoklar.get(anahtar, 0)
            ambar_text += f"{etiket}: `{miktar} Adet`\n"

        embed.description = ambar_text
        embed.set_footer(
            text=f"Sığınak Seviyesi: {db['sistem_ayarlari'].get('koy_seviyesi', 1)} | Toplam Yapılan Bağış: {db['koy_ambari'].get('toplam_bagis_sayisi', 0)}"
        )
        await interaction.response.send_message(embed=embed)

    # ====================================================
    # /ambara-bagis
    # ====================================================
    @app_commands.command(name="ambara-bagis", description="[AMBAR] Kendi envanterinizden köy ambarına eşya bağışlayarak toplumsal itibarınızı artırır.")
    @app_commands.describe(esya_ad="Bağışlanacak malzeme (erzak, odun, kömür, ilaç)", adet="Bağışlanacak miktar")
    async def ambara_bagis_yap(self, interaction: discord.Interaction, esya_ad: str, adet: int):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Sicil kütüğünde kaydın yok!", ephemeral=True)
            return
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return

        sakin = db["sakinler"][u_id]

        if adet <= 0:
            await interaction.response.send_message("❌ Bağış miktarı pozitif bir sayı olmalıdır!", ephemeral=True)
            return

        temiz_ad = ESYA_HARITASI.get(esya_ad.lower().strip())
        if not temiz_ad:
            await interaction.response.send_message(
                "❌ Geçersiz eşya adı! Bağışlanabilir malzemeler: `erzak`, `ilaç`, `odun`, `kömür`",
                ephemeral=True
            )
            return

        if "envanter" not in sakin:
            sakin["envanter"] = {}

        mevcut_stok = sakin["envanter"].get(temiz_ad, 0)
        if mevcut_stok < adet:
            await interaction.response.send_message(
                f"❌ Envanterinizde yeterli malzeme yok! Mevcut: `{mevcut_stok}` adet {esya_ad}.",
                ephemeral=True
            )
            return

        # Transfer
        sakin["envanter"][temiz_ad] -= adet
        if sakin["envanter"][temiz_ad] == 0:
            del sakin["envanter"][temiz_ad]
        db["koy_ambari"]["stoklar"][temiz_ad] = db["koy_ambari"]["stoklar"].get(temiz_ad, 0) + adet
        db["koy_ambari"]["toplam_bagis_sayisi"] += 1

        # İtibar ödülü
        itibar_bonusu = adet * 2
        sakin["cuzdan"] = sakin.get("cuzdan", 0) + itibar_bonusu
        sakin["itibar"] = min(100, sakin.get("itibar", 50) + adet)
        verileri_kaydet()

        embed = discord.Embed(title="🤝 AMBARA YÜCE BAĞIŞ PROTOKOLÜ", color=0x2ECC71)
        embed.description = (
            f"👤 **Hayırsever Sakin:** {interaction.user.mention}\n"
            f"📦 **Köy Ambarına Teslim Edilen:** `{adet} Adet {ESYA_ETIKET[temiz_ad]}`\n\n"
            f"📈 **Toplumsal İtibar Ödülü:** `+{itibar_bonusu} Hurda` ve `+{adet} İtibar Puanı`"
        )
        await interaction.response.send_message(embed=embed)
        haber_ekle(f"🤝 {sakin['isim']} köy ambarına {adet} adet {ESYA_ETIKET[temiz_ad]} bağışladı.")

    @ambara_bagis_yap.autocomplete("esya_ad")
    async def ambara_bagis_autocomplete(self, interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=f"{etiket} ({anahtar})", value=anahtar)
            for anahtar, etiket in ESYA_ETIKET.items() if current.lower() in etiket.lower() or current.lower() in anahtar.lower()
        ][:25]

    # ====================================================
    # /ambardan-al
    # ====================================================
    @app_commands.command(name="ambardan-al", description="[AMBAR] İhtiyaç sahibi sakinlerin ambardan ücretsiz malzeme almasını sağlar.")
    @app_commands.describe(esya_ad="Alınacak malzeme (erzak, odun, kömür, ilaç)", adet="Alınacak miktar (max 5)")
    async def ambardan_malzeme_al(self, interaction: discord.Interaction, esya_ad: str, adet: int):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Sığınak siciliniz bulunamadı!", ephemeral=True)
            return
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return

        sakin = db["sakinler"][u_id]

        if sakin.get("durum") == "Sürgün":
            await interaction.response.send_message("❌ Sürgün edilmiş bir suçlu olarak köy ambarına yaklaşamazsınız!", ephemeral=True)
            return

        if adet <= 0:
            await interaction.response.send_message("❌ Geçersiz adet miktarı!", ephemeral=True)
            return

        if adet > 5:
            await interaction.response.send_message("❌ Suistimali önlemek adına tek seferde ambardan en fazla `5` adet malzeme çekebilirsiniz!", ephemeral=True)
            return

        temiz_ad = ESYA_HARITASI.get(esya_ad.lower().strip())
        if not temiz_ad:
            await interaction.response.send_message(
                "❌ Geçersiz eşya adı! İstenebilecek malzemeler: `erzak`, `ilaç`, `odun`, `kömür`",
                ephemeral=True
            )
            return

        # Sosyal yardım uygunluk: cüzdanı 400+ ve sağlıklı olan alamaz
        cuzdan_durumu = sakin.get("cuzdan", 0)
        saglik_durumu = sakin.get("durum", "Canlı")
        if cuzdan_durumu > 400 and saglik_durumu in ["Sağlıklı", "Canlı"]:
            await interaction.response.send_message(
                "❌ Durumunuz gayet iyi! Ambar havuzu sadece ihtiyaç sahipleri içindir. Lütfen pazarı kullanın.",
                ephemeral=True
            )
            return

        stoklar = db["koy_ambari"]["stoklar"]
        if stoklar.get(temiz_ad, 0) < adet:
            await interaction.response.send_message(
                f"❌ Köy ambarında yeterli stok kalmamış! Mevcut {ESYA_ETIKET[temiz_ad]} stoku: `{stoklar.get(temiz_ad, 0)}`",
                ephemeral=True
            )
            return

        stoklar[temiz_ad] -= adet
        if "envanter" not in sakin:
            sakin["envanter"] = {}
        sakin["envanter"][temiz_ad] = sakin["envanter"].get(temiz_ad, 0) + adet
        verileri_kaydet()

        embed = discord.Embed(title="📦 SOSYAL YARDIM VE AMBAR TEDARİĞİ", color=0x3498DB)
        embed.description = (
            f"📢 Sığınak Sosyal Yardımlaşma Fonu devrede!\n\n"
            f"👤 **Teslim Alan Sakin:** {interaction.user.mention}\n"
            f"📦 **Tedarik Edilen Malzeme:** `{adet} Adet {ESYA_ETIKET[temiz_ad]}`\n\n"
            f"ℹ️ *Malzemeler envanterinize eklenmiştir.*"
        )
        await interaction.response.send_message(embed=embed)

    @ambardan_malzeme_al.autocomplete("esya_ad")
    async def ambardan_al_autocomplete(self, interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=f"{etiket} ({anahtar})", value=anahtar)
            for anahtar, etiket in ESYA_ETIKET.items() if current.lower() in etiket.lower() or current.lower() in anahtar.lower()
        ][:25]


async def setup(bot):
    await bot.add_cog(AmbarCog(bot))

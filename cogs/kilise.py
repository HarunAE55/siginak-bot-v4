"""
Cog: Kilise & Engizisyon
========================
Komutlar:
- /rahip-paneli (panel)
- /afaroz-et (sapkını dinden çıkar, şans düşürür)
- /buyuk-kilise-cani (3 günde 1, herkese +10 moral)
- /kedileri-yok-et (tehlikeli karar, fare nüfusu patlar, veba tetiklenir)
- /kutsa (rahip kutsama ile enfeksiyon azaltır veya sağlık iyileştirir)
"""

import discord
from discord import app_commands
from discord.ext import commands
import datetime

from veritabani import db, verileri_kaydet, olu_kontrolu, haber_ekle
from kanallar import SIMYACININ_MEKTUPLARI

RAHIP_ROL_ID = 1515026155969843401


class KiliseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ====================================================
    # /rahip-paneli
    # ====================================================
    @app_commands.command(name="rahip-paneli", description="[RAHİP] Teokratik engizisyon yönetim paneline erişir.")
    async def rahip_paneli(self, interaction: discord.Interaction):
        if not any(rol.id == RAHIP_ROL_ID for rol in interaction.user.roles):
            await interaction.response.send_message("❌ Sadece Rahip sınıfı bu panele erişebilir!", ephemeral=True)
            return

        kilise = db["kilise_sistemi"]
        embed = discord.Embed(title="⛪ ENGİZİSYON YÖNETİM PANELİ", color=0x9B59B6)
        embed.description = (
            "Rahip, sığınağın ruhani lideri olarak şu emirleri verebilirsin:\n\n"
            "1. `/afaroz-et [@sakin] [neden]` — Bir sapkını dinden çıkar, şansını düşürür.\n"
            "2. `/buyuk-kilise-cani` — Sığınak halkının moralini +10 artırır (3 gün CD).\n"
            "3. `/kedileri-yok-et` — İnanç adına kedileri yak (DİKKAT: Veba riski!).\n"
            "4. `/kutsa [@sakin]` — Bir sakini kutsa, enfeksiyonunu azaltır.\n\n"
            f"📊 **Kilise Durumu:**\n"
            f"• Fare Nüfusu: `{kilise.get('fare_nufusu', 10)}`\n"
            f"• Kedi Katliamı Yapıldı: `{'Evet' if kilise.get('kedi_katliami_yapildi') else 'Hayır'}`\n"
            f"• Son Çan Çalınma: `{kilise.get('son_can_calinma', 'Hiç')}`"
        )
        await interaction.response.send_message(embed=embed)

    # ====================================================
    # /afaroz-et
    # ====================================================
    @app_commands.command(name="afaroz-et", description="[RAHİP] Sapkın bir sakini dinden çıkar ve şansını düşürür.")
    @app_commands.describe(hedef="Afaroz edilecek sakin", neden="Afaroz sebebi")
    async def afaroz_et(self, interaction: discord.Interaction, hedef: discord.Member, neden: str):
        if not any(rol.id == RAHIP_ROL_ID for rol in interaction.user.roles):
            await interaction.response.send_message("❌ Rahip değilsin!", ephemeral=True)
            return

        s_id = str(hedef.id)
        if s_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Bu kişi sığınakta yaşamıyor!", ephemeral=True)
            return

        # Afaroz etkisi: şans çarpanını düşür
        mevcut_sans = db["sakinler"][s_id].get("sans_carpani", 1.0)
        db["sakinler"][s_id]["sans_carpani"] = max(0.1, mevcut_sans - 0.5)
        verileri_kaydet()

        embed = discord.Embed(title="🚫 AFAROZ KARARNAMESİ", color=0x7F8C8D)
        embed.description = (
            f"⛪ **Rahip {interaction.user.mention}** tarafından afaroz edildin!\n\n"
            f"👤 **Afaroz Edilen:** {hedef.mention}\n"
            f"📜 **Neden:** *{neden}*\n\n"
            f"📉 **Etki:** Şans çarpanın `-{0.5}` azaltıldı (yeni: `{db['sakinler'][s_id]['sans_carpani']:.1f}`). Kilise yardımları kesildi."
        )
        await interaction.response.send_message(embed=embed)
        haber_ekle(f"🚫 {db['sakinler'][s_id]['isim']} afaroz edildi. Neden: {neden}")

    # ====================================================
    # /buyuk-kilise-cani
    # ====================================================
    @app_commands.command(name="buyuk-kilise-cani", description="[RAHİP] 3 günde bir çalınır, herkesin moralini +10 artırır.")
    async def kilise_cani(self, interaction: discord.Interaction):
        if not any(rol.id == RAHIP_ROL_ID for rol in interaction.user.roles):
            await interaction.response.send_message("❌ Sadece rahip kilise çanını çalabilir!", ephemeral=True)
            return

        simdi = datetime.datetime.now()
        son_calinma = db["kilise_sistemi"]["son_can_calinma"]

        if son_calinma:
            fark = simdi - datetime.datetime.fromisoformat(son_calinma)
            if fark.days < 3:
                kalan_saat = int((3 * 86400 - fark.total_seconds()) / 3600)
                await interaction.response.send_message(
                    f"🔔 Kilise çanı henüz soğumadı! Kalan süre: `{kalan_saat} saat`.",
                    ephemeral=True
                )
                return

        # Tüm sakinlere moral takviyesi (ölüler ve hücredekiler hariç)
        sayac = 0
        for s_id, veri in db["sakinler"].items():
            if veri.get("durum") not in ("Ölü", "Hücrede"):
                veri["moral"] = min(100, veri.get("moral", 50) + 10)
                sayac += 1

        db["kilise_sistemi"]["son_can_calinma"] = simdi.isoformat()
        verileri_kaydet()

        embed = discord.Embed(title="🔔 BÜYÜK KİLİSE ÇANI ÇALINDI!", color=0xF1C40F)
        embed.description = (
            f"⛪ **Rahip {interaction.user.mention}** sığınak halkı için büyük kilise çanını çaldı!\n\n"
            f"😊 **{sayac} sakin** moral buldu, moral seviyeleri +10 arttı!\n"
            f"⏱️ *Bir sonraki çan için 3 gün beklemelisin.*"
        )
        await interaction.response.send_message(embed=embed)
        haber_ekle(f"🔔 Büyük Kilise Çanı çalındı! {sayac} sakinin morali yükseldi.")

    # ====================================================
    # /kedileri-yok-et
    # ====================================================
    @app_commands.command(name="kedileri-yok-et", description="[RAHİP] İnanç adına! Fare nüfusunu artırıp vebayı tetikleyen karar.")
    async def kedileri_yak(self, interaction: discord.Interaction):
        if not any(rol.id == RAHIP_ROL_ID for rol in interaction.user.roles):
            await interaction.response.send_message("❌ Bu karar sadece rahip tarafından alınabilir!", ephemeral=True)
            return

        rahip_id = str(interaction.user.id)
        if db["sakinler"].get(rahip_id, {}).get("durum") == "Ölü":
            await interaction.response.send_message("❌ Ölü biri kedi yakamaz!", ephemeral=True)
            return

        if db["kilise_sistemi"]["kedi_katliami_yapildi"]:
            await interaction.response.send_message("❌ Kediler zaten çoktan yakıldı!", ephemeral=True)
            return

        db["kilise_sistemi"]["kedi_katliami_yapildi"] = True
        db["kilise_sistemi"]["fare_nufusu"] *= 10

        # Sadece Canlı sakinleri enfekte et
        sayac = 0
        for s_id, veri in db["sakinler"].items():
            if veri.get("durum") == "Canlı":
                veri["durum"] = "Enfekte"
                sayac += 1

        # Rahibin itibarı düşer
        db["sakinler"][rahip_id]["itibar"] = max(0, db["sakinler"][rahip_id].get("itibar", 50) - 30)
        verileri_kaydet()

        embed = discord.Embed(title="🔥 KECDİLER YAKILDI!", color=0xC0392B)
        embed.description = (
            f"🔥 **Rahip {interaction.user.mention}** sığınak meydanında feci bir karar aldı!\n\n"
            f"🐱 Kediler yakıldı... Fare nüfusu sığınağı ele geçirdi!\n"
            f"🦠 **{sayac}** Canlı sakin anında **Enfekte** durumuna düştü!\n"
            f"📉 Rahibin itibarı `-30` azaldı."
        )
        await interaction.response.send_message(embed=embed)
        haber_ekle(f"🔥 Rahip kedileri yaktı! {sayac} sakin enfekte oldu. Fare nüfusu patladı.")

    # ====================================================
    # /kutsa - Rahip bir sakini kutsar
    # ====================================================
    @app_commands.command(name="kutsa", description="[RAHİP] Bir sakini kutsa, enfeksiyonunu azaltır ve sağlığını iyileştirir (3 saat CD).")
    @app_commands.describe(hedef="Kutsanacak sakin")
    async def kutsa(self, interaction: discord.Interaction, hedef: discord.Member):
        if not any(rol.id == RAHIP_ROL_ID for rol in interaction.user.roles):
            await interaction.response.send_message("❌ Kutsama yetkisi sadece Rahibe aittir!", ephemeral=True)
            return

        rahip_id = str(interaction.user.id)
        # RAHİP KAYITLI MI KONTROL ET (KeyError fix)
        if rahip_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Rahip olarak kayıtlı değilsin! Önce `/kayit` ol.", ephemeral=True)
            return

        if db["sakinler"][rahip_id].get("durum") == "Ölü":
            await interaction.response.send_message("❌ Ölü rahip kutsayamaz!", ephemeral=True)
            return

        # 3 saat cooldown
        son_kutsama = db["sakinler"][rahip_id].get("son_kutsama")
        if son_kutsama:
            fark = datetime.datetime.now() - datetime.datetime.fromisoformat(son_kutsama)
            if fark.total_seconds() < 10800:  # 3 saat
                kalan_dk = int((10800 - fark.total_seconds()) / 60)
                await interaction.response.send_message(
                    f"❌ Kutsama gücün henüz geri toplandı! `{kalan_dk} dakika` beklemelisin.",
                    ephemeral=True
                )
                return

        h_id = str(hedef.id)
        if h_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Bu kişi sığınakta yaşamıyor!", ephemeral=True)
            return

        hedef_sakin = db["sakinler"][h_id]
        if hedef_sakin.get("durum") == "Ölü":
            await interaction.response.send_message("❌ Ölüyü kutsayamazsın!", ephemeral=True)
            return

        # Kutsama etkisi: enfeksiyon -20, sağlık +15
        eski_enf = hedef_sakin.get("enfeksiyon", 0)
        hedef_sakin["enfeksiyon"] = max(0, eski_enf - 20)
        hedef_sakin["saglik"] = min(100, hedef_sakin.get("saglik", 100) + 15)
        hedef_sakin["moral"] = min(100, hedef_sakin.get("moral", 50) + 5)

        # Eğer tamamen enfeksiyon temizlendiyse ve durum Enfekte ise, iyileştir
        if hedef_sakin["enfeksiyon"] == 0 and hedef_sakin.get("durum") == "Enfekte":
            hedef_sakin["durum"] = "Sağlıklı"

        db["sakinler"][rahip_id]["son_kutsama"] = datetime.datetime.now().isoformat()
        verileri_kaydet()

        embed = discord.Embed(title="✨ KUTSAMA TÖRENİ", color=0xF1C40F)
        embed.description = (
            f"⛪ **Rahip {interaction.user.mention}** bir kutsama töreni gerçekleştirdi!\n\n"
            f"👤 **Kutsanan:** {hedef.mention}\n"
            f"📉 **Enfeksiyon:** `{eski_enf}` → `{hedef_sakin['enfeksiyon']}` (-20)\n"
            f"❤️ **Sağlık:** +15\n"
            f"😊 **Moral:** +5\n\n"
            f"⏱️ *Sonraki kutsama için 3 saat beklemelisin.*"
        )
        await interaction.response.send_message(embed=embed)
        haber_ekle(f"✨ Rahip {hedef.display_name} adlı sakini kutsadı.")


async def setup(bot):
    await bot.add_cog(KiliseCog(bot))

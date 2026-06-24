"""
Cog: Çevre & RP Owner Paneli
============================
Komutlar:
- /hava-durumu-degis (admin, mevsim değiştir)
- /sunucu-yonetimi (SADECE RP Owner - tanrısal kontrol paneli)
  - Kraliyet Acil Desteği butonu
  - Tüm Sığınağa Enfeksiyon Bulaştır butonu
  - Hava Durumu seçim menüsü
  - Salgın Kuvveti seçim menüsü
"""

import discord
from discord import app_commands
from discord.ext import commands

from veritabani import db, verileri_kaydet, haber_ekle, RP_OWNER_ROL_ID


class CevreCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ====================================================
    # /hava-durumu-degis - Admin
    # ====================================================
    @app_commands.command(name="hava-durumu-degis", description="[ADMİN] Sığınağın mevsimini ve hava durumunu değiştirir.")
    @app_commands.describe(yeni_hava="İlkbahar, Yaz, Yağmurlu, Kış")
    @app_commands.choices(yeni_hava=[
        app_commands.Choice(name="🌱 İlkbahar", value="İlkbahar"),
        app_commands.Choice(name="☀️ Yaz", value="Yaz"),
        app_commands.Choice(name="🌧️ Yağmurlu", value="Yağmurlu"),
        app_commands.Choice(name="❄️ Kış", value="Kış")
    ])
    async def hava_durumu_degis(self, interaction: discord.Interaction, yeni_hava: str):
        from veritabani import admin_mi
        if not admin_mi(interaction):
            await interaction.response.send_message(
                "❌ Bu komut sadece yetkili ekibe özeldir!",
                ephemeral=True
            )
            return

        db["cevre_durumu"]["hava_durumu"] = yeni_hava
        verileri_kaydet()

        embed = discord.Embed(title="🌤️ HAVA DURUMU RAPORU", color=0x3498DB)
        mesajlar = {
            "İlkbahar": "🌱 **Bereketli Yağmurlar Başladı (İlkbahar)!** Toprak canlandı, dengeli hammadde akışı.",
            "Yaz": "☀️ **Sığınak Semalarında Güneş Açtı (Yaz)!** Çiftçilerin üretimi %50 daha verimli.",
            "Yağmurlu": "🌧️ **Yağmurlu Havalar Başladı!** Dışarı çalışma verimi düştü.",
            "Kış": "❄️ **Buzul Kış Şartları Bastırdı!** Çiftçi üretimi durdu, dış çalışma çok zorlu."
        }
        embed.description = mesajlar.get(yeni_hava, f"Hava durumu **{yeni_hava}** olarak güncellendi.")
        await interaction.response.send_message(embed=embed)
        haber_ekle(f"🌤️ Sığınak hava durumu {yeni_hava} olarak değiştirildi.")

    # ====================================================
    # /sunucu-yonetimi - SADECE RP OWNER
    # ====================================================
    @app_commands.command(name="sunucu-yonetimi", description="[OWNER] Sadece RP Owner rolüne sahip yetkililerin açabileceği tanrısal kontrol panelidir.")
    async def sunucu_yonetimi_paneli(self, interaction: discord.Interaction):
        from veritabani import admin_mi
        if not admin_mi(interaction):
            await interaction.response.send_message(
                "❌ Bu komut sadece yönetici ekibine özeldir!",
                ephemeral=True
            )
            return

        embed = discord.Embed(title="⚡ MUTLAK HAKİMİYET VE SUNUCU YÖNETİM PANELİ", color=0x1ABC9C)
        embed.description = (
            f"**Makam:** Kurucu Konseyi / Sunucu Sahibi\n"
            f"--- \n"
            f"🌍 **Mevcut Hava Durumu:** `{db['cevre_ayarlari'].get('hava_durumu', 'Güneşli')}`\n"
            f"🌤️ **Mevsim (Üretim):** `{db['cevre_durumu'].get('hava_durumu', 'İlkbahar')}`\n"
            f"☣️ **Salgın Varyant Gücü:** `Seviye {db['cevre_ayarlari'].get('salgin_kuvveti', 1)}`\n"
            f"💰 **Mevcut Sığınak Kasası:** `{db['sistem_ayarlari'].get('KASA_AKÇE_PLACEHOLDER', 0)} Akçe`\n"
            f"🧱 **Sur Seviyesi:** `{db['sistem_ayarlari'].get('sur_seviyesi', 1)}`\n"
            f"🏡 **Köy Seviyesi:** `{db['sistem_ayarlari'].get('koy_seviyesi', 1)}`\n\n"
            f"⚠️ *Aşağıdaki menüleri ve butonları kullanarak iklim döngüsünü manipüle edebilir, salgının gücünü değiştirebilir veya sığınağa kraliyet desteği indirebilirsin.*"
        )

        view = RpOwnerPaneliView(RP_OWNER_ROL_ID)
        view.add_item(HavaDurumuSecimi())
        view.add_item(SalginKuvvetiSecimi())

        await interaction.response.send_message(embed=embed, view=view)


# ====================================================
# VIEW - RP OWNER PANELİ
# ====================================================
class RpOwnerPaneliView(discord.ui.View):
    def __init__(self, owner_rol_id):
        super().__init__(timeout=300)
        self.owner_rol_id = owner_rol_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not any(rol.id == self.owner_rol_id for rol in interaction.user.roles):
            await interaction.response.send_message(
                "❌ Bu panele dokunma yetkiniz yok! Sadece RP Owner / Sunucu Sahibi erişebilir.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="👑 Kraliyet Acil Desteği Gönder", style=discord.ButtonStyle.success, custom_id="kraliyet_destek_btn")
    async def kraliyet_destegi(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Kaynak transferi
        db["koy_ambari"]["stoklar"]["odun"] = db["koy_ambari"]["stoklar"].get("odun", 0) + 2000
        db["koy_ambari"]["stoklar"]["komur"] = db["koy_ambari"]["stoklar"].get("komur", 0) + 1000
        db["sistem_ayarlari"]["KASA_AKÇE_PLACEHOLDER"] = db["sistem_ayarlari"].get("KASA_AKÇE_PLACEHOLDER", 0) + 500
        db["sistem_ayarlari"]["sur_seviyesi"] = db["sistem_ayarlari"].get("sur_seviyesi", 1) + 1
        verileri_kaydet()

        embed = discord.Embed(title="🎺 KRALİYET ELÇİSİ SIĞINAĞA ULAŞTI!", color=0x2ECC71)
        embed.description = (
            f"🏰 **RP Owner {interaction.user.mention}** emir verdi ve Kraliyet Muhafız Alayı sığınağın imdadına yetişti!\n\n"
            f"📦 **Ambara Eklenen Lojistik Destek:**\n"
            f"• 🪵 `+2000 Odun`\n"
            f"• 🪨 `+1000 Kömür`\n"
            f"• 🪙 `+500 Akçe` (Askeri Fon)\n\n"
            f"🛡️ **Takviye Birlikler:** Sur Savunma Seviyesi `+1` arttırılarak **Seviye {db['sistem_ayarlari']['sur_seviyesi']}** yapıldı!"
        )
        await interaction.response.send_message(embed=embed)
        haber_ekle("🎺 Kraliyet elçisi sığınağa ulaştı! +2000 odun, +1000 kömür, +500 akçe destek.")

    @discord.ui.button(label="☣️ Tüm Sığınağa Enfeksiyon Bulaştır", style=discord.ButtonStyle.danger, custom_id="enfeksiyon_bulastir_btn")
    async def toplu_enfeksiyon(self, interaction: discord.Interaction, button: discord.ui.Button):
        sayac = 0
        for s_id, veri in db["sakinler"].items():
            if veri.get("durum") not in ("Ölü", "Hücrede", "Karantinada", "Sürgün"):
                veri["durum"] = "Enfekte"
                sayac += 1

        db["biyolaboratuvar"]["virus_ilerlemesi"] = min(db["biyolaboratuvar"].get("virus_ilerlemesi", 0) + 15, 100)
        verileri_kaydet()

        embed = discord.Embed(title="🚨 SALGIN KONTROLDEN ÇIKTI: BİYOLOJİK ATTACK!", color=0x962D2D)
        embed.description = (
            f"☣️ **Hava Filtreleri Sabote Edildi!**\n\n"
            f"Kurucu irade tarafından salgın dalgası tetiklendi! Sığınaktaki **{sayac}** aktif sakin anında **Enfekte** durumuna düştü!\n\n"
            f"🧪 **Virüs Mutasyon İlerlemesi:** `+15` tırmanarak **%{db['biyolaboratuvar']['virus_ilerlemesi']}** oldu!\n"
            f"⚕️ *Simyacılar acilen panzehir üretmezse toplu ölümler başlayacak!*"
        )
        await interaction.response.send_message(embed=embed)
        haber_ekle(f"☣️ RP Owner salgın tetikledi! {sayac} sakin enfekte oldu.")


class HavaDurumuSecimi(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="☀️ Güneşli (Yaz)", description="Çiftçilerin ekin üretimi tavan yapar.", emoji="☀️", value="Yaz"),
            discord.SelectOption(label="🌧️ Yağmurlu (İlkbahar)", description="Toprak sulanır, odun üretimi dengelenir.", emoji="🌧️", value="İlkbahar"),
            discord.SelectOption(label="⛈️ Fırtınalı (Sonbahar)", description="Dışarı keşfe çıkma riskleri artar.", emoji="⛈️", value="Sonbahar"),
            discord.SelectOption(label="❄️ Buzul Kış (Kış)", description="Çiftçi üretimi durur! Ambarlardan tüketim başlar.", emoji="❄️", value="Kış")
        ]
        super().__init__(placeholder="🌍 Dinamik Hava Durumu ve Mevsim Döngüsü Ayarla...", min_values=1, max_values=1, options=options, custom_id="hava_durumu_select")

    async def callback(self, interaction: discord.Interaction):
        secilen_hava = self.values[0]
        # v5.9 FIX: Türkçe karakterli değerler kullanılıyor (orman_kes/tarla_calis ile uyumlu)
        hava_eslesme = {
            "Yaz": ("Güneşli", "Yaz"),
            "İlkbahar": ("Yağmurlu", "İlkbahar"),
            "Sonbahar": ("Fırtınalı", "Yağmurlu"),
            "Kış": ("Karlı", "Kış")
        }
        cevre_hava, mevsim = hava_eslesme.get(secilen_hava, (secilen_hava, secilen_hava))
        db["cevre_ayarlari"]["hava_durumu"] = cevre_hava
        db["cevre_durumu"]["hava_durumu"] = mevsim
        verileri_kaydet()

        embed = discord.Embed(title="🌍 MEVSİM VE İKLİM DÖNGÜSÜ DEĞİŞTİ", color=0x3498DB)
        mesajlar = {
            "Yaz": "☀️ **Yaz Mevsimi!** Çiftçilerin üretimi %50 daha verimli.",
            "İlkbahar": "🌧️ **İlkbahar!** Bereketli yağmurlar, dengeli üretim.",
            "Sonbahar": "⛈️ **Sonbahar!** Fırtınalar, dış dünya riskli.",
            "Kış": "❄️ **Kış!** Çiftçi üretimi durdu, dış çalışma çok zorlu."
        }
        embed.description = mesajlar.get(secilen_hava, f"Hava durumu değişti: {secilen_hava}")
        await interaction.response.send_message(embed=embed)
        haber_ekle(f"🌍 RP Owner mevsimi {mevsim} olarak değiştirdi.")


class SalginKuvvetiSecimi(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Düşük Salgın Hızı", description="Virüs yavaş yayılır.", emoji="🟢", value="1"),
            discord.SelectOption(label="Orta Seviye Pandemi", description="Standart enfeksiyon çarpanları.", emoji="🟡", value="2"),
            discord.SelectOption(label="Kıyamet Senaryosu (Hardcore)", description="Zombiler kudurur!", emoji="🔴", value="3")
        ]
        super().__init__(placeholder="☣️ Salgın Gücü ve Enfeksiyon Katsayısı Ayarla...", min_values=1, max_values=1, options=options, custom_id="salgin_kuvveti_select")

    async def callback(self, interaction: discord.Interaction):
        kuvvet = int(self.values[0])
        db["cevre_ayarlari"]["salgin_kuvveti"] = kuvvet
        db["cevre_ayarlari"]["enfeksiyon_orani"] = kuvvet * 15
        verileri_kaydet()

        embed = discord.Embed(title="☣️ ENFEKSİYON VARYANT AYARLARI GÜNCELLENDİ", color=0x9B59B6)
        if kuvvet == 3:
            embed.description = "🔴 **SALGIN SEVİYESİ: KIYAMET (HARDCORE)!** Virüs mutasyona uğradı!"
            embed.color = 0xC0392B
        elif kuvvet == 2:
            embed.description = "🟡 **SALGIN SEVİYESİ: ORTA.** Standart enfeksiyon oranları aktif."
        else:
            embed.description = "🟢 **SALGIN SEVİYESİ: DÜŞÜK.** Virüs yavaş yayılıyor."
        await interaction.response.send_message(embed=embed)
        haber_ekle(f"☣️ Salgın kuvveti Seviye {kuvvet} olarak ayarlandı.")


async def setup(bot):
    await bot.add_cog(CevreCog(bot))

"""
Cog: Maliye & Vergi
===================
Komutlar:
- /maliye-yonetim (Vergi Müfettişi paneli, oran ayarlama modal)

Otomatik Task: 5 saatte bir otomatik vergi tahsilati (her canlı sakinden veba_vergisi kesilir)
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks

from veritabani import db, verileri_kaydet, haber_ekle, VERGI_MEMURU_ROL_ID
from kanallar import VERGI_RAPOR_KANAL_ID


class MaliyeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Task'ı başlat
        self.otomatik_vergi_tahsilati.start()

    def cog_unload(self):
        self.otomatik_vergi_tahsilati.cancel()

    # ====================================================
    # 5 SAATTE BİR OTOMATİK VERGİ TAHSİLATI
    # ====================================================
    @tasks.loop(hours=5)
    async def otomatik_vergi_tahsilati(self):
        maliye = db["maliye_ayarlari"]
        kesilecek_tutar = maliye["veba_vergisi"]
        toplam_toplanan = 0
        kesilen_sayac = 0

        for s_id, veri in db["sakinler"].items():
            if veri.get("durum") not in ("Ölü", "Sürgün"):
                mevcut_cuzdan = veri.get("cuzdan", 0)
                if mevcut_cuzdan >= kesilecek_tutar:
                    veri["cuzdan"] -= kesilecek_tutar
                    toplam_toplanan += kesilecek_tutar
                    kesilen_sayac += 1
                elif mevcut_cuzdan > 0:
                    veri["cuzdan"] = 0
                    toplam_toplanan += mevcut_cuzdan
                    kesilen_sayac += 1

        db["sistem_ayarlari"]["KASA_AKÇE_PLACEHOLDER"] = db["sistem_ayarlari"].get("KASA_AKÇE_PLACEHOLDER", 0) + toplam_toplanan
        maliye["toplam_tahsilat"] = maliye.get("toplam_tahsilat", 0) + toplam_toplanan
        verileri_kaydet()

        # Log kanalına rapor
        kanal = self.bot.get_channel(VERGI_RAPOR_KANAL_ID)
        if kanal:
            embed = discord.Embed(title="📜 SIĞINAK MALİYE BAKANLIĞI RESMİ TAHSİLAT RAPORU", color=0xE74C3C)
            embed.description = (
                f"⏰ **Dönem:** 5 Saatlik Otomatik Vergi Tahsilatı\n\n"
                f"💰 **Kesilen Sakin Sayısı:** `{kesilen_sayac}`\n"
                f"🪙 **Toplam Tahsil Edilen:** `{toplam_toplanan} Akçe`\n"
                f"🏛️ **Ortak Kasaya Aktarıldı.**\n\n"
                f"📈 **Tarih Boyunca Toplam Toplanan Vergi:** `{maliye['toplam_tahsilat']} Akçe`"
            )
            try:
                await kanal.send(embed=embed)
            except Exception:
                pass

    @otomatik_vergi_tahsilati.before_loop
    async def before_vergi_task(self):
        await self.bot.wait_until_ready()

    # ====================================================
    # /maliye-yonetim
    # ====================================================
    @app_commands.command(name="maliye-yonetim", description="[MÜFETTİŞ] Sadece Vergi Müfettişinin erişebileceği, sığınak vergi ve stopaj paneli.")
    async def vergi_yonetim_paneli(self, interaction: discord.Interaction):
        if not any(rol.id == VERGI_MEMURU_ROL_ID for rol in interaction.user.roles):
            await interaction.response.send_message(
                "❌ Sığınak hazinesini ve vergi sistemini sadece resmi Vergi Memuru/Müfettişi denetleyebilir!",
                ephemeral=True
            )
            return

        maliye = db["maliye_ayarlari"]

        embed = discord.Embed(title="🏛️ SIĞINAK MALİ KONTROL VE DENETİM MERKEZİ", color=0xE67E22)
        embed.description = (
            f"**Resmi Müfettiş:** {interaction.user.mention}\n"
            f"--- \n"
            f"🦠 **Mevcut Veba Vergisi Oranı:** `{maliye['veba_vergisi']} Akçe / 5 Saat`\n"
            f"⚖️ **Pazar Ticaret Kesintisi:** `%{maliye['ticaret_kesintisi']}`\n"
            f"💰 **Başkanlık Ortak Kasası (Mevcut):** `{db['sistem_ayarlari'].get('KASA_AKÇE_PLACEHOLDER', 0)} Akçe`\n"
            f"📊 **Tarih Boyunca Toplam Toplanan Vergi:** `{maliye['toplam_tahsilat']} Akçe`\n\n"
            f"⚠️ *Aşağıdaki butona basarak veba vergisini ve pazar kesinti oranlarını anlık değiştirebilirsin.*"
        )

        view = VergiPaneliView(VERGI_MEMURU_ROL_ID)
        await interaction.response.send_message(embed=embed, view=view)


class VergiPaneliView(discord.ui.View):
    def __init__(self, mufettis_rol_id):
        super().__init__(timeout=180)
        self.mufettis_rol_id = mufettis_rol_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not any(rol.id == self.mufettis_rol_id for rol in interaction.user.roles):
            await interaction.response.send_message(
                "❌ Bu mali verilere erişim yetkiniz yok! Sadece Vergi Memuru/Müfettişi bu paneli açabilir.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="⚙️ Oranları Dinamik Düzenle", style=discord.ButtonStyle.primary)
    async def oranlari_duzenle(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VergiAyariModal())


class VergiAyariModal(discord.ui.Modal, title="⚖️ Vergi Oranı Ayarlama"):
    veba_input = discord.ui.TextInput(
        label="Veba Vergisi (Akçe / 5 Saat)",
        placeholder="Örn: 20",
        max_length=4,
        default=str(db.get("maliye_ayarlari", {}).get("veba_vergisi", 20))
    )
    ticaret_input = discord.ui.TextInput(
        label="Ticaret Kesinti Oranı (Yüzde %)",
        placeholder="Örn: 10",
        max_length=2,
        default=str(db.get("maliye_ayarlari", {}).get("ticaret_kesintisi", 10))
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            yeni_veba = int(self.veba_input.value)
            yeni_ticaret = int(self.ticaret_input.value)

            if yeni_veba < 0 or yeni_ticaret < 0 or yeni_ticaret > 50:
                await interaction.response.send_message(
                    "❌ Geçersiz değerler! Ticaret vergisi en fazla %50 olabilir.",
                    ephemeral=True
                )
                return

            db["maliye_ayarlari"]["veba_vergisi"] = yeni_veba
            db["maliye_ayarlari"]["ticaret_kesintisi"] = yeni_ticaret
            verileri_kaydet()

            embed = discord.Embed(title="📈 EKONOMİK REFORMA GİDİLDİ", color=0xF1C40F)
            embed.description = (
                f"📋 **Vergi Memuru {interaction.user.mention}** sığınak mali politikasını güncelledi!\n\n"
                f"🦠 **Yeni Dönemsel Veba Vergisi:** `{yeni_veba} Akçe` (5 saatte bir tahsil edilir)\n"
                f"⚖️ **Yeni Pazar/Ticaret Stopajı:** `%{yeni_ticaret}` (Bot alım-satımlarından kesilir)"
            )
            await interaction.response.send_message(embed=embed)
            haber_ekle(f"📈 Vergi oranları güncellendi: Veba={yeni_veba}h, Ticaret=%{yeni_ticaret}.")
        except ValueError:
            await interaction.response.send_message("❌ Lütfen sadece sayısal değerler girin!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(MaliyeCog(bot))

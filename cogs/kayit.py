"""
Cog: Kayıt & Profil
==================
Komutlar:
- /kayıt (herkese açık)
- /profil (herkese açık)
- /envanter (herkese açık)
- /biyografi-yaz (herkese açık)
- /xp_kazan_test (sadece admin)
- /owner-kayit (sadece RP Owner - başkasını zorla kaydeder)
- /kayit-sil (sadece RP Owner - kaydı siler)
"""

import discord
from discord import app_commands
from discord.ext import commands
import random

from veritabani import (
    db, verileri_kaydet, olu_kontrolu, bar_olustur,
    sakin_olustur_defaults, sakin_sil, xp_ekle,
    RP_OWNER_ROL_ID, SECOND_OWNER_ROL_ID,
)
from kanallar import KAYIT_LOG


class KayitCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ====================================================
    # /kayıt - Herkese açık sicil kaydı
    # ====================================================
    @app_commands.command(name="kayıt", description="[SİCİL] Sığınak nüfus kütüğüne adınızı, yaşınızı ve memleketinizi işler.")
    @app_commands.describe(
        isim="Karakterinizin adı",
        soyisim="Karakterinizin soyadı",
        yas="Karakterinizin yaşı (10-40 arası)",
        memleket="Karakterinizin memleketi"
    )
    async def kayit_ol(self, interaction: discord.Interaction, isim: str, soyisim: str, yas: int, memleket: str):
        u_id = str(interaction.user.id)

        if yas > 40 or yas < 10:
            await interaction.response.send_message(
                "❌ Sığınak kuralları gereği 10-40 yaş arasında olmalısınız!",
                ephemeral=True
            )
            return

        if u_id in db["sakinler"]:
            if db["sakinler"][u_id].get("durum") != "Ölü":
                await interaction.response.send_message(
                    "❌ Sığınak sicil kütüğünde zaten aktif bir kaydınız mevcut!",
                    ephemeral=True
                )
                return

        # Yeni sakin oluşturma (xp_ekle ile seviye atlamayı otomatik işler)
        baslangic_atak = random.randint(10, 20)
        sakin_olustur_defaults(u_id, isim, soyisim, yas, memleket, baslangic_atak)
        verileri_kaydet()

        embed = discord.Embed(title="📝 SIĞINAK SİCİL DEFTERİ — RESMİ SAKİN KAYDI", color=0x34495E)
        embed.description = (
            f"Sığınak nüfus kütüğüne kaydınız işlendi!\n\n"
            f"**Kimlik Kartı Detayları:**\n"
            f"• **Ad Soyad:** `{isim} {soyisim}`\n"
            f"• **Yaş / Memleket:** `{yas} / {memleket}`\n\n"
            f"**Mühürlenen Başlangıç Statüleri:**\n"
            f"• **Rastgele Atak Gücü:** `⚔️ {baslangic_atak}`\n"
            f"• **Sığınak Yardımı:** `500 Hurda` ve `20 XP`\n\n"
            f"💡 *Karakterinin hikayesini yazmak için `/biyografi-yaz` komutunu kullanabilirsin.*"
        )
        await interaction.response.send_message(embed=embed)

        # Kayıt log kanalına da yaz
        try:
            kanal = self.bot.get_channel(KAYIT_LOG)
            if kanal:
                log_embed = discord.Embed(title="📝 Yeni Sakin Kaydı", color=0x2ECC71)
                log_embed.description = (
                    f"👤 **Kullanıcı:** {interaction.user.mention}\n"
                    f"🎭 **Karakter:** `{isim} {soyisim}`\n"
                    f"🎂 **Yaş:** `{yas}`\n"
                    f"📍 **Memleket:** `{memleket}`\n"
                    f"⚔️ **Başlangıç Atak:** `{baslangic_atak}`"
                )
                await kanal.send(embed=log_embed)
        except Exception:
            pass

    # ====================================================
    # /profil - Detaylı karakter kartı
    # ====================================================
    @app_commands.command(name="profil", description="[STATÜ] Detaylı sığınak hayatta kalma istatistiklerinizi ve barlarını listeler.")
    async def profil_goster(self, interaction: discord.Interaction):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            await interaction.response.send_message(
                "❌ Sığınak sicil kütüğünde kaydınız bulunmuyor!",
                ephemeral=True
            )
            return
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return

        sakin = db["sakinler"][u_id]

        # Durum emojisi
        durum = sakin.get("durum", "Canlı")
        durum_emoji = {
            "Canlı": "🟢",
            "Sağlıklı": "🟢",
            "Enfekte": "🟡",
            "Karantinada": "🟠",
            "Hücrede": "🔴",
            "Ölü": "💀",
            "Sürgün": "🔵"
        }.get(durum, "⚪")

        embed = discord.Embed(
            title=f"👤 {sakin['isim'].upper()} {sakin['soyisim'].upper()} — SİCİL KARTI",
            color=0x3498DB
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        # Kimlik bilgileri
        embed.add_field(name=f"{durum_emoji} Durum", value=f"`{durum}`", inline=True)
        embed.add_field(name="💼 Aktif Meslek", value=f"`{sakin.get('meslek_isim', 'Gezgin')}`", inline=True)
        embed.add_field(name="🏅 Seviye / XP", value=f"`Seviye {sakin.get('seviye', 1)}` / `{sakin.get('xp', 0)} XP`", inline=True)

        embed.add_field(name="💰 Cüzdan", value=f"`{sakin.get('cuzdan', 0)} Hurda`", inline=True)
        embed.add_field(name="⚔️ Atak Gücü", value=f"`{sakin.get('atak', 10)}`", inline=True)
        embed.add_field(name="🛡️ Defans Gücü", value=f"`{sakin.get('defans', 0)}`", inline=True)

        embed.add_field(name="🎂 Yaş", value=f"`{sakin.get('yas', '?')}`", inline=True)
        embed.add_field(name="📍 Memleket", value=f"`{sakin.get('memleket', 'Bilinmiyor')}`", inline=True)
        embed.add_field(name="🎯 İtibar", value=f"`{sakin.get('itibar', 50)}`", inline=True)

        # Barlar
        embed.add_field(name="❤️ Sağlık", value=bar_olustur(sakin.get("saglik", 100)), inline=False)
        embed.add_field(name="💧 Su ve Besin", value=bar_olustur(sakin.get("su", 100)), inline=False)
        embed.add_field(name="🧠 Akıl Sağlığı", value=bar_olustur(sakin.get("akil_sagligi", 100)), inline=False)
        embed.add_field(name="☣️ Enfeksiyon Yükü", value=bar_olustur(sakin.get("enfeksiyon", 0)), inline=False)
        embed.add_field(name="😊 Moral", value=bar_olustur(sakin.get("moral", 50)), inline=False)

        # Biyografi
        biyografi = sakin.get("biyografi", "").strip()
        if biyografi:
            embed.add_field(
                name="📖 Biyografi",
                value=f"*{biyografi[:1000]}*" if len(biyografi) <= 1000 else f"*{biyografi[:1000]}...*",
                inline=False
            )
        else:
            embed.add_field(
                name="📖 Biyografi",
                value="*Karakterinin hikayesi henüz yazılmadı. `/biyografi-yaz` komutuyla ekleyebilirsin.*",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    # ====================================================
    # /envanter - Sırt çantası
    # ====================================================
    @app_commands.command(name="envanter", description="[ÇANTA] Sırt çantanızda taşıdığınız tüm teçhizatları listeler.")
    async def envanter_goster(self, interaction: discord.Interaction):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            await interaction.response.send_message(
                "❌ Önce sığınağa kayıt olmalısınız!",
                ephemeral=True
            )
            return
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return

        sakin = db["sakinler"][u_id]
        envanter_verisi = sakin.get("envanter", {})

        embed = discord.Embed(title=f"🎒 {sakin['isim'].upper()} SIRT ÇANTASI", color=0xF39C12)

        icerik = ""
        for esya, adet in envanter_verisi.items():
            if adet > 0:
                icerik += f"• 📦 **{esya}**: `{adet} Adet`\n"

        embed.description = icerik if icerik else "*Sırt çantan bomboş, pazardan alışveriş yapmalısın!*"
        await interaction.response.send_message(embed=embed)

    # ====================================================
    # /biyografi-yaz - Karakter hikayesi (3 gün CD)
    # ====================================================
    @app_commands.command(name="biyografi-yaz", description="[PROFİL] Karakterinin biyografisini yaz veya güncelle (max 1000 karakter, 3 günde 1 değiştirilebilir).")
    @app_commands.describe(metin="Karakterinin hikayesi (max 1000 karakter)")
    async def biyografi_yaz(self, interaction: discord.Interaction, metin: str):
        import datetime as dt

        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            await interaction.response.send_message(
                "❌ Önce sığınağa kayıt olmalısın!",
                ephemeral=True
            )
            return
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return

        if len(metin) > 1000:
            await interaction.response.send_message(
                f"❌ Biyografi çok uzun! Max 1000 karakter, sizin yazdığınız: `{len(metin)}`",
                ephemeral=True
            )
            return

        if len(metin.strip()) < 10:
            await interaction.response.send_message(
                "❌ Biyografi en az 10 karakter olmalı!",
                ephemeral=True
            )
            return

        # 3 gün cooldown (ilk yazımda yok)
        son_degisim = db["sakinler"][u_id].get("son_biyografi_degisimi")
        if son_degisim:
            fark = dt.datetime.now() - dt.datetime.fromisoformat(son_degisim)
            if fark.total_seconds() < 259200:  # 3 gün
                kalan_saat = int((259200 - fark.total_seconds()) / 3600)
                await interaction.response.send_message(
                    f"❌ Biyografini kısa süre önce değiştirdin! {kalan_saat} saat beklemelisin.",
                    ephemeral=True
                )
                return

        db["sakinler"][u_id]["biyografi"] = metin.strip()
        db["sakinler"][u_id]["son_biyografi_degisimi"] = dt.datetime.now().isoformat()
        verileri_kaydet()

        embed = discord.Embed(title="📖 BİYOGRAFİ GÜNCELLENDİ", color=0x9B59B6)
        embed.description = (
            f"Karakterinin hikayesi sicil kütüğüne işlendi!\n\n"
            f"**Yeni Biyografi:**\n*{metin.strip()}*\n\n"
            f"⏱️ *Bir sonraki değişiklik 3 gün sonra yapılabilir.*"
        )
        await interaction.response.send_message(embed=embed)

    # ====================================================
    # /xp_kazan_test - SADECE ADMIN (suiistimali kapatır)
    # ====================================================
    @app_commands.command(name="xp_kazan_test", description="[TEST] Test amaçlı XP ekler. SADECE SUNUCU YÖNETİCİLERİ kullanabilir.")
    @app_commands.describe(miktar="Eklenecek XP miktarı", hedef="XP verilecek üye (boşsa kendin)")
    async def xp_kazan_test(self, interaction: discord.Interaction, miktar: int, hedef: discord.Member = None):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Bu test komutunu sadece sunucu yöneticileri kullanabilir!",
                ephemeral=True
            )
            return

        if miktar <= 0 or miktar > 10000:
            await interaction.response.send_message(
                "❌ Miktar 1-10000 arası olmalı!",
                ephemeral=True
            )
            return

        hedef_user = hedef if hedef else interaction.user
        h_id = str(hedef_user.id)

        if h_id not in db["sakinler"]:
            await interaction.response.send_message(
                "❌ Hedef sakin kayıtlı değil!",
                ephemeral=True
            )
            return

        atlamalar = xp_ekle(h_id, miktar)
        verileri_kaydet()

        embed = discord.Embed(title="🧪 TEST: XP Eklendi", color=0xE67E22)
        embed.description = f"👤 **Hedef:** {hedef_user.mention}\n📈 **Eklenen XP:** `{miktar}`"
        if atlamalar:
            embed.description += "\n\n🎉 **SEVİYE ATLAMALAR:**\n"
            for a in atlamalar:
                embed.description += f"• Seviye {a['seviye']}! +{a['odul']} Hurda ödülü\n"
        embed.set_footer(text="Bu komut sadece yöneticilere açıktır.")
        await interaction.response.send_message(embed=embed)

    # ====================================================
    # /owner-kayit - RP Owner başkasını zorla kaydeder
    # ====================================================
    @app_commands.command(name="owner-kayit", description="[OWNER] Sadece RP Owner: Belirtilen üyeyi sığınağa zorla kaydeder.")
    @app_commands.describe(
        uye="Kaydedilecek üye",
        isim="Karakter adı",
        soyisim="Karakter soyadı",
        yas="Yaş (10-40)",
        memleket="Memleket",
        baslangic_hurda="Başlangıç hurda miktarı (varsayılan: 500)"
    )
    async def owner_kayit(self, interaction: discord.Interaction, uye: discord.Member, isim: str, soyisim: str, yas: int, memleket: str, baslangic_hurda: int = 500):
        # RP Owner rol kontrolü
        if not any(rol.id == RP_OWNER_ROL_ID for rol in interaction.user.roles):
            await interaction.response.send_message(
                "❌ Bu komut sadece RP Owner rolüne sahip yetkililer tarafından kullanılabilir!",
                ephemeral=True
            )
            return

        if yas > 40 or yas < 10:
            await interaction.response.send_message(
                "❌ Yaş 10-40 arası olmalı!",
                ephemeral=True
            )
            return

        u_id = str(uye.id)

        # Eğer kayıtlıysa ve hayattaysa uyar
        if u_id in db["sakinler"] and db["sakinler"][u_id].get("durum") != "Ölü":
            await interaction.response.send_message(
                f"❌ {uye.mention} zaten aktif bir sicile sahip! Önce `/kayit-sil` ile mevcut kaydı silin.",
                ephemeral=True
            )
            return

        baslangic_atak = random.randint(10, 20)
        sakin_olustur_defaults(u_id, isim, soyisim, yas, memleket, baslangic_atak)
        # Özel başlangıç hurda
        db["sakinler"][u_id]["cuzdan"] = baslangic_hurda
        verileri_kaydet()

        embed = discord.Embed(title="👑 OWNER KAYDI", color=0xF1C40F)
        embed.description = (
            f"**RP Owner** {interaction.user.mention} tarafından zorla kayıt işlemi gerçekleştirildi!\n\n"
            f"👤 **Kaydedilen Üye:** {uye.mention}\n"
            f"🎭 **Karakter:** `{isim} {soyisim}`\n"
            f"🎂 **Yaş:** `{yas}`\n"
            f"📍 **Memleket:** `{memleket}`\n"
            f"⚔️ **Başlangıç Atak:** `{baslangic_atak}`\n"
            f"💰 **Başlangıç Hurda:** `{baslangic_hurda}`"
        )
        await interaction.response.send_message(embed=embed)

    # ====================================================
    # /kayit-sil - RP Owner kaydı siler
    # ====================================================
    @app_commands.command(name="kayit-sil", description="[OWNER] Sadece RP Owner: Belirtilen üyenin sicil kaydını tamamen siler.")
    @app_commands.describe(uye="Kaydı silinecek üye", onay="Silmeyi onaylamak için 'EVET' yazın")
    async def kayit_sil(self, interaction: discord.Interaction, uye: discord.Member, onay: str):
        if not any(rol.id == RP_OWNER_ROL_ID for rol in interaction.user.roles):
            await interaction.response.send_message(
                "❌ Bu komut sadece RP Owner rolüne sahip yetkililer tarafından kullanılabilir!",
                ephemeral=True
            )
            return

        if onay.upper() != "EVET":
            await interaction.response.send_message(
                "❌ Onaylamak için `onay` parametresine tam olarak `EVET` yazmalısınız. Bu işlem geri alınamaz!",
                ephemeral=True
            )
            return

        u_id = str(uye.id)
        if u_id not in db["sakinler"]:
            await interaction.response.send_message(
                f"❌ {uye.mention} zaten sicil kütüğünde kayıtlı değil!",
                ephemeral=True
            )
            return

        silinen_isim = db["sakinler"][u_id].get("isim", "?")
        silinen_soyisim = db["sakinler"][u_id].get("soyisim", "?")
        sakin_sil(u_id)

        embed = discord.Embed(title="🗑️ SİCİL KAYDI SİLİNDİ", color=0xE74C3C)
        embed.description = (
            f"**RP Owner** {interaction.user.mention} tarafından sicil kaydı silindi!\n\n"
            f"👤 **Etkilenen Üye:** {uye.mention}\n"
            f"🎭 **Silinen Karakter:** `{silinen_isim} {silinen_soyisim}`\n\n"
            f"⚠️ *Bu işlem geri alınamaz. Üye yeniden `/kayıt` olmak zorundadır.*"
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(KayitCog(bot))

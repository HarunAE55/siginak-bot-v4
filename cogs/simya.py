"""
Cog: Simya & Sağlık
==================
Komutlar:
- /deney (simyacı virüs deneyi, %10/85/5)
- /laboratuvar-gelistir (başkan/baş simyacı, 500 hurda/seviye, max 3)
- /doktor-paneli (panel gösterir)
- /asi-uret (doktor, 2 tibbi malzeme → 1 aşı)
- /tedavi-et (doktor, aşı ile hasta iyileştirir)
"""

import discord
from discord import app_commands
from discord.ext import commands
import random

from veritabani import (
    db, verileri_kaydet, olu_kontrolu, olum_protokolu,
    OlumEkraniView, xp_ekle, haber_ekle
)


# Yetkili meslek grupları
MESLEK_GRUPLARI = {
    "tibbi": ["bas_doktor", "doktor", "karantinaci"],
    "kolluk": ["muhafiz_komutani", "muhafiz", "nisanci", "izci"],
    "uretici": ["ciftci", "coban", "demirci", "oduncu", "madenci", "degirmenci", "hanci"],
}


class SimyaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ====================================================
    # /deney - Simyacı virüs deneyi
    # ====================================================
    @app_commands.command(name="deney", description="[SİMYA] Sığınak laboratuvarında virüs panzehiri veya mutasyon için tehlikeli deneyler yürütür.")
    async def deney_yap(self, interaction: discord.Interaction):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Sicil kütüğünde kaydın yok!", ephemeral=True)
            return
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return

        sakin = db["sakinler"][u_id]
        meslek = sakin.get("meslek_anahtar", "")

        if meslek not in ["bas_simyaci", "simyaci"]:
            await interaction.response.send_message(
                "❌ Laboratuvar kapıları mühürlü! Sadece Baş Simyacı veya Simyacılar deney yapabilir.",
                ephemeral=True
            )
            return

        lab = db["biyolaboratuvar"]
        ilerleme = lab["virus_ilerlemesi"]
        seviye = lab["lab_seviyesi"]

        # Risk algoritması
        temel_basari = 10
        temel_olum = 5
        basari_bonusu = (seviye - 1) * 25
        guncel_basari = min(temel_basari + basari_bonusu, 70)

        if ilerleme >= 50:
            guncel_olum = 15
        elif ilerleme >= 25:
            guncel_olum = 10
        else:
            guncel_olum = temel_olum

        zar = random.randint(1, 100)
        lab["toplam_deney"] += 1

        embed = discord.Embed(title="🧪 LABORATUVAR DENEY RAPORU", color=0x95A5A6)
        embed.set_author(name=f"Simyacı: {sakin['isim']}", icon_url=interaction.user.display_avatar.url)

        # 1. SENARYO: PATLAMA VE ÖLÜM
        if zar <= guncel_olum:
            ganimet_metni = olum_protokolu(u_id, olum_sebebi="diger")
            lab["virus_ilerlemesi"] = 0

            try:
                roller = [1508539755304845352]
                for r_id in roller:
                    rol = interaction.guild.get_role(r_id)
                    if rol in interaction.user.roles:
                        await interaction.user.remove_roles(rol)
            except:
                pass

            embed.title = "💥 LABORATUVARDA DEHŞETVERİCİ PATLAMA!"
            embed.color = 0xC0392B
            embed.description = (
                f"☣️ **Deney Esnasında Tüpler Reaksiyona Girdi!**\n\n"
                f"💀 {interaction.user.mention} yaptığı tehlikeli kimyasal kombinasyon yüzünden laboratuvarı havaya uçurdu ve **HAYATINI KAYBETTİ!**\n\n"
                f"🚨 **KRİTİK DURUM:** Tüm virüs ve panzehir araştırma verileri yanarak **SIFIRLANDI (0%)!**\n\n"
                f"📦 **Miras Aktarımı:**\n"
                f"{ganimet_metni if ganimet_metni else 'Aktarılacak bir şey kalmamıştı.'}"
            )
            await interaction.response.send_message(embed=embed)

            olum_embed = discord.Embed(title="💀 HAYATIN SONA ERDİ", color=0x7F8C8D)
            olum_embed.description = (
                f"{interaction.user.mention} Laboratuvarda patlamada can verdin.\n\n"
                f"⚰️ Eşyaların sığınak kasasına aktarıldı.\n"
                f"🔄 Yeniden hayata dönmek için `/kayit` komutunu kullan."
            )
            await interaction.channel.send(embed=olum_embed, view=OlumEkraniView(interaction.user))
            haber_ekle(f"💥 {sakin['isim']} laboratuvar patlamasında öldü! Virüs araştırması sıfırlandı.")
            return

        # 2. SENARYO: BAŞARILI DENEY
        elif zar <= (guncel_olum + guncel_basari):
            lab["virus_ilerlemesi"] = min(ilerleme + 5, 100)
            yeni_ilerleme = lab["virus_ilerlemesi"]
            atlamalar = xp_ekle(u_id, 30)
            verileri_kaydet()

            embed.title = "✅ DENEY BAŞARIYLA TAMAMLANDI!"
            embed.color = 0x2ECC71

            desc = (
                f"🔬 Simyacının formülü kararlı bir şekilde birleşti!\n\n"
                f"📈 **Virüs Araştırma İlerlemesi:** `%{ilerleme}` -> `%{yeni_ilerleme}` (+%5)\n"
                f"🧬 **Laboratuvar Güvenlik Sınıfı:** `Seviye {seviye}`\n"
                f"⭐ **+30 XP** kazanıldı.\n"
            )
            if atlamalar:
                desc += "\n🎉 **SEVİYE ATLAMALAR:**\n"
                for a in atlamalar:
                    desc += f"• Seviye {a['seviye']}! +{a['odul']} Hurda ödülü\n"

            if yeni_ilerleme >= 100:
                desc += "\n☣️ **KATASTROFİK SEVİYE:** Virüs haritası %100 tamamlandı!"
                embed.color = 0x8E44AD
            elif yeni_ilerleme >= 50:
                desc += "\n⚠️ **MUTASYON BELİRTİLERİ BAŞLADI:** Ölüm riski %15'e fırladı!"
                embed.color = 0xD35400
            else:
                desc += "\nℹ️ Araştırmalar stabil ilerliyor."

            embed.description = desc
            await interaction.response.send_message(embed=embed)
            haber_ekle(f"🧪 {sakin['isim']} başarılı deney yaptı. Virüs ilerlemesi: %{yeni_ilerleme}")

        # 3. SENARYO: BAŞARISIZ DENEY
        else:
            verileri_kaydet()
            embed.title = "❌ DENEY BAŞARISIZ OLDU"
            embed.color = 0xF39C12
            embed.description = (
                f"🧪 Kimyasal elementler nötr kaldı. Deney başarısız oldu.\n\n"
                f"📊 **Mevcut İlerleme:** `%{ilerleme}`\n"
                f"⚡ *Neyse ki herhangi bir patlama veya zehirlenme yaşanmadı.*"
            )
            await interaction.response.send_message(embed=embed)

    # ====================================================
    # /laboratuvar-gelistir
    # ====================================================
    @app_commands.command(name="laboratuvar-gelistir", description="[BAŞKAN/SİMYACI] Kasadan hurda harcayarak laboratuvar güvenlik seviyesini artırır.")
    async def lab_gelistir(self, interaction: discord.Interaction):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Sicil kaydınız yok!", ephemeral=True)
            return
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return

        sakin = db["sakinler"][u_id]
        meslek = sakin.get("meslek_anahtar", "")

        if meslek not in ["belediye_baskani", "bas_simyaci"]:
            await interaction.response.send_message(
                "❌ Laboratuvar fonlama yetkisi sadece Belediye Başkanı veya Baş Simyacıya aittir!",
                ephemeral=True
            )
            return

        lab = db["biyolaboratuvar"]
        mevcut_seviye = lab.get("lab_seviyesi", 1)

        if mevcut_seviye >= 3:
            await interaction.response.send_message(
                "🔬 Laboratuvar zaten en üst teknolojik sınıra (`Seviye 3`) ulaşmış durumda!",
                ephemeral=True
            )
            return

        maliyet = 500
        if db["sistem_ayarlari"]["kasa_hurda"] < maliyet:
            await interaction.response.send_message(
                f"❌ Ortak kasada yeterli ödenek yok! Gereken: `{maliyet}`, Kasada: `{db['sistem_ayarlari']['kasa_hurda']}`",
                ephemeral=True
            )
            return

        db["sistem_ayarlari"]["kasa_hurda"] -= maliyet
        lab["lab_seviyesi"] += 1
        verileri_kaydet()

        embed = discord.Embed(title="🔬 BİYOLABORATUVAR YÜKSELTİLDİ!", color=0x27AE60)
        embed.description = (
            f"🛠️ Sığınak bilim üssü devlet ödeneğiyle modernize edildi!\n\n"
            f"📦 **Yeni Teknolojik Seviye:** `Seviye {lab['lab_seviyesi']}`\n"
            f"💰 **Harcanan Bütçe:** `{maliyet} Hurda`\n"
            f"📉 **Kalan Sığınak Ortak Kasası:** `{db['sistem_ayarlari']['kasa_hurda']} Hurda`"
        )
        await interaction.response.send_message(embed=embed)

    # ====================================================
    # /doktor-paneli
    # ====================================================
    @app_commands.command(name="doktor-paneli", description="[DOKTOR] Muayene, acil aşı üretimi ve veba tedavi protokollerini yönetir.")
    async def doktor_paneli(self, interaction: discord.Interaction):
        u_id = str(interaction.user.id)
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return
        meslek = db["sakinler"].get(u_id, {}).get("meslek_anahtar", "")

        if meslek not in MESLEK_GRUPLARI["tibbi"]:
            await interaction.response.send_message(
                "❌ Bu paneli açmaya tıbbi yetkiniz yetmiyor!",
                ephemeral=True
            )
            return

        embed = discord.Embed(title="🏥 SIĞINAK MERKEZ HASTANESİ VE BAŞHEKİMLİK", color=0x1ABC9C)
        embed.description = (
            "🩺 **Tıbbi Personel Yetki Arayüzü:**\n\n"
            "💉 `/asi-uret` -> Ambar hammaddelerini kullanarak salgın için acil aşı sentezler.\n"
            "💊 `/tedavi-et [@sakin]` -> Enfekte veya karantinadaki bir sakini iyileştirir.\n\n"
            f"📦 **Mevcut Aşı Stoku:** `{db['cevre_durumu'].get('karantina_asi_stoku', 0)}`\n"
            f"⚕️ **Mevcut Tıbbi Malzeme:** `{db['koy_ambari']['stoklar'].get('tibbi_malzeme', 0)}`"
        )
        await interaction.response.send_message(embed=embed)

    # ====================================================
    # /asi-uret
    # ====================================================
    @app_commands.command(name="asi-uret", description="[DOKTOR] Sığınak ortak ambarından 2 tıbbi malzeme kullanarak 1 aşı üretir.")
    async def asi_uret(self, interaction: discord.Interaction):
        u_id = str(interaction.user.id)
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return
        meslek = db["sakinler"].get(u_id, {}).get("meslek_anahtar", "")

        if meslek not in MESLEK_GRUPLARI["tibbi"]:
            await interaction.response.send_message("❌ Aşı sentezleme yetkiniz yok!", ephemeral=True)
            return

        stoklar = db["koy_ambari"]["stoklar"]
        if stoklar.get("tibbi_malzeme", 0) < 2:
            await interaction.response.send_message(
                "❌ Laboratuvarda aşı üretmek için köy ambarında en az `2` adet Tıbbi Malzeme olmalıdır!",
                ephemeral=True
            )
            return

        stoklar["tibbi_malzeme"] -= 2
        db["cevre_durumu"]["karantina_asi_stoku"] += 1
        atlamalar = xp_ekle(u_id, 10)
        verileri_kaydet()

        msg = f"🧪 Başarıyla 1 adet Antiviral Aşı üretildi! Toplam Aşı Stoku: `{db['cevre_durumu']['karantina_asi_stoku']}` (+10 XP)"
        if atlamalar:
            msg += "\n\n🎉 **SEVİYE ATLAMALAR:**"
            for a in atlamalar:
                msg += f"\n• Seviye {a['seviye']}! +{a['odul']} Hurda"
        await interaction.response.send_message(msg)

    # ====================================================
    # /tedavi-et
    # ====================================================
    @app_commands.command(name="tedavi-et", description="[DOKTOR] Enfekte olmuş bir sakini aşı kullanarak tamamen iyileştirir.")
    @app_commands.describe(hedef="Tedavi edilecek hasta sakin")
    async def tedavi_et(self, interaction: discord.Interaction, hedef: discord.Member):
        u_id = str(interaction.user.id)
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return
        h_id = str(hedef.id)
        meslek = db["sakinler"].get(u_id, {}).get("meslek_anahtar", "")

        if meslek not in MESLEK_GRUPLARI["tibbi"]:
            await interaction.response.send_message("❌ Tedavi uygulama yetkiniz yok!", ephemeral=True)
            return

        if db["cevre_durumu"]["karantina_asi_stoku"] <= 0:
            await interaction.response.send_message(
                "❌ Sığınak tıp merkezinde hiç aşı kalmamış! Önce `/asi-uret` ile aşı üretmelisiniz.",
                ephemeral=True
            )
            return

        if h_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Bu kişi sığınakta yaşamıyor!", ephemeral=True)
            return

        if db["sakinler"].get(h_id, {}).get("durum") not in ["Enfekte", "Karantinada"]:
            await interaction.response.send_message("❌ Bu sakin zaten sağlıklı, aşıyı israf etme!", ephemeral=True)
            return

        # İyileştirme
        db["cevre_durumu"]["karantina_asi_stoku"] -= 1
        db["sakinler"][h_id]["durum"] = "Sağlıklı"
        db["sakinler"][h_id]["enfeksiyon"] = 0
        atlamalar = xp_ekle(u_id, 25)
        verileri_kaydet()

        msg = f"🟢 {hedef.mention} başarıyla tedavi edildi ve sağlığına kavuştu! Kalan Aşı: `{db['cevre_durumu']['karantina_asi_stoku']}` (+25 XP)"
        if atlamalar:
            msg += "\n\n🎉 **SEVİYE ATLAMALAR:**"
            for a in atlamalar:
                msg += f"\n• Seviye {a['seviye']}! +{a['odul']} Hurda"
        await interaction.response.send_message(msg)
        haber_ekle(f"💊 {db['sakinler'][u_id]['isim']} bir hastayı tedavi etti.")


async def setup(bot):
    await bot.add_cog(SimyaCog(bot))

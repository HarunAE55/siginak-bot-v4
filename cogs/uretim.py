"""
Cog: Üretim & Çalışma
=====================
Komutlar:
- /ciftci-paneli (panel)
- /tarla-calis (çiftçi/çoban/değirmenci/hancı, 30 dk CD, hava durumuna göre çarpan)
- /maden-kaz (madenci/demirci, 30 dk CD)
- /orman-kes (oduncu/hancı, 30 dk CD)
- /tuket (envanterden gıda tüket, su+saglik restore)

Önemli: Tüm çalışma komutları xp_ekle() kullanır - seviye atlama otomatik çalışır.
"""

import discord
from discord import app_commands
from discord.ext import commands
import random
import datetime

from veritabani import db, verileri_kaydet, olu_kontrolu, xp_ekle, haber_ekle
from cogs.simya import MESLEK_GRUPLARI


# Ambar eşya eşleştirme
ESYA_HARITASI = {
    "erzak": "erzak", "yemek": "erzak", "gıda": "erzak",
    "tıbbi": "tibbi_malzeme", "ilaç": "tibbi_malzeme", "medkit": "tibbi_malzeme", "tibbi_malzeme": "tibbi_malzeme",
    "odun": "odun", "tahta": "odun",
    "kömür": "komur", "komur": "komur"
}


class UretimCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ====================================================
    # /ciftci-paneli
    # ====================================================
    @app_commands.command(name="ciftci-paneli", description="[ÜRETİCİ] Çiftçi, Madenci, Demirci, Çoban ve Oduncuların üretim ekranı.")
    async def ciftci_paneli(self, interaction: discord.Interaction):
        u_id = str(interaction.user.id)
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return
        meslek = db["sakinler"].get(u_id, {}).get("meslek_anahtar", "")

        if meslek not in MESLEK_GRUPLARI["uretici"]:
            await interaction.response.send_message("❌ Sığınakta kayıtlı tescilli bir üretici değilsiniz!", ephemeral=True)
            return

        hava = db["cevre_durumu"].get("hava_durumu", "İlkbahar")
        embed = discord.Embed(title="🌾 SIĞINAK ÜRETİM MERKEZİ", color=0xF1C40F)
        embed.description = (
            f"👋 Merhaba **{db['sakinler'][u_id].get('isim', 'Üretici')}**!\n\n"
            f"🌤️ **Mevcut Hava Durumu:** `{hava}`\n\n"
            f"📋 **Yapabileceğin İşler:**\n"
            f"• `/tarla-calis` — Tarlada çalış, erzak üret (Çiftçi/Çoban/Değirmenci/Hancı)\n"
            f"• `/maden-kaz` — Madende kömür çıkar (Madenci/Demirci)\n"
            f"• `/orman-kes` — Ormanda odun kes (Oduncu/Hancı)\n"
            f"• `/tuket [esya]` — Envanterinden gıda tüket, su ve sağlığını yenile\n\n"
            f"⏱️ *Her çalışma komutu 30 dakika cooldown'a sahiptir.*"
        )
        await interaction.response.send_message(embed=embed)

    # ====================================================
    # /tarla-calis
    # ====================================================
    @app_commands.command(name="tarla-calis", description="[ÜRETİCİ] Tarlada çalış, erzak üret. (30 dk CD)")
    async def tarla_calis(self, interaction: discord.Interaction):
        u_id = str(interaction.user.id)
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return
        sakin = db["sakinler"].get(u_id, {})

        if sakin.get("durum") == "Hücrede":
            await interaction.response.send_message("❌ Hücrede olan biri tarlada çalışamaz!", ephemeral=True)
            return

        if sakin.get("meslek_anahtar") not in ["ciftci", "coban", "degirmenci", "hanci"]:
            await interaction.response.send_message("❌ Toprakla uğraşacak ekipmanınız veya tarım izniniz yok!", ephemeral=True)
            return

        # 30 dk cooldown
        son_calisma = sakin.get("son_calisma")
        if son_calisma:
            fark = datetime.datetime.now() - datetime.datetime.fromisoformat(son_calisma)
            if fark.total_seconds() < 1800:
                kalan_dk = int((1800 - fark.total_seconds()) / 60)
                await interaction.response.send_message(
                    f"❌ Dinlenmeniz gerekiyor! Tarlada tekrar çalışmak için `{kalan_dk} dakika` bekleyin.",
                    ephemeral=True
                )
                return

        # Hava durumu çarpanı
        hava = db["cevre_durumu"]["hava_durumu"]
        taban_erzak = random.randint(10, 20)
        carpan = 1.0
        if hava == "İlkbahar":
            carpan = 1.5
        elif hava == "Yaz":
            carpan = 2.0
        elif hava == "Yağmurlu":
            carpan = 0.7
        elif hava == "Kış":
            carpan = 0.3

        nihai_erzak = int(taban_erzak * carpan)
        kazanilan_hurda = nihai_erzak * 3
        kazanilan_xp = 15

        db["koy_ambari"]["stoklar"]["erzak"] = db["koy_ambari"]["stoklar"].get("erzak", 0) + nihai_erzak
        sakin["cuzdan"] = sakin.get("cuzdan", 0) + kazanilan_hurda
        atlamalar = xp_ekle(u_id, kazanilan_xp)
        sakin["son_calisma"] = datetime.datetime.now().isoformat()
        verileri_kaydet()

        embed = discord.Embed(title="🌾 HASAT TAMAMLANDI!", color=0x2ECC71)
        embed.description = (
            f"🌤️ **Mevsim/Hava:** `{hava}` (Çarpan: x{carpan})\n"
            f"📦 **Köy Ambarına Eklenen Erzak:** `+{nihai_erzak} Adet`\n"
            f"💰 **Kişisel Kazancınız:** `+{kazanilan_hurda} Hurda` | `+{kazanilan_xp} XP`"
        )
        if atlamalar:
            embed.add_field(
                name="🎉 Seviye Atlamaları",
                value="\n".join([f"• Seviye {a['seviye']}! +{a['odul']} Hurda" for a in atlamalar]),
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    # ====================================================
    # /maden-kaz
    # ====================================================
    @app_commands.command(name="maden-kaz", description="[ÜRETİCİ] Madende kaz, kömür çıkar. (30 dk CD)")
    async def maden_kaz(self, interaction: discord.Interaction):
        u_id = str(interaction.user.id)
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return
        sakin = db["sakinler"].get(u_id, {})

        if sakin.get("durum") == "Hücrede":
            await interaction.response.send_message("❌ Hücrede olan biri madene inemez!", ephemeral=True)
            return

        if sakin.get("meslek_anahtar") not in ["madenci", "demirci"]:
            await interaction.response.send_message("❌ Kazmanız yok, madene inemezsiniz!", ephemeral=True)
            return

        # 30 dk cooldown
        son_calisma = sakin.get("son_calisma")
        if son_calisma:
            fark = datetime.datetime.now() - datetime.datetime.fromisoformat(son_calisma)
            if fark.total_seconds() < 1800:
                kalan_dk = int((1800 - fark.total_seconds()) / 60)
                await interaction.response.send_message(
                    f"❌ Dinlenmeniz gerekiyor! Madene tekrar inmek için `{kalan_dk} dakika` bekleyin.",
                    ephemeral=True
                )
                return

        hava = db["cevre_durumu"]["hava_durumu"]
        taban_komur = random.randint(8, 15)
        carpan = 1.0
        if hava == "Kış":
            carpan = 0.6
        elif hava == "Yağmurlu":
            carpan = 0.8

        nihai_komur = int(taban_komur * carpan)
        kazanilan_hurda = nihai_komur * 4
        kazanilan_xp = 20

        db["koy_ambari"]["stoklar"]["komur"] = db["koy_ambari"]["stoklar"].get("komur", 0) + nihai_komur
        sakin["cuzdan"] = sakin.get("cuzdan", 0) + kazanilan_hurda
        atlamalar = xp_ekle(u_id, kazanilan_xp)
        sakin["son_calisma"] = datetime.datetime.now().isoformat()
        verileri_kaydet()

        embed = discord.Embed(title="⛏️ MADEN KAZISI BAŞARILI!", color=0x95A5A6)
        embed.description = (
            f"🪨 **Köy Ambarına Eklenen Kömür:** `+{nihai_komur} Adet`\n"
            f"💰 **Kişisel Kazancınız:** `+{kazanilan_hurda} Hurda` | `+{kazanilan_xp} XP`"
        )
        if atlamalar:
            embed.add_field(
                name="🎉 Seviye Atlamaları",
                value="\n".join([f"• Seviye {a['seviye']}! +{a['odul']} Hurda" for a in atlamalar]),
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    # ====================================================
    # /orman-kes
    # ====================================================
    @app_commands.command(name="orman-kes", description="[ÜRETİCİ] Ormanda odun kes. (30 dk CD)")
    async def orman_kes(self, interaction: discord.Interaction):
        u_id = str(interaction.user.id)
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return
        sakin = db["sakinler"].get(u_id, {})

        if sakin.get("durum") == "Hücrede":
            await interaction.response.send_message("❌ Hücrede olan biri odun kesemez!", ephemeral=True)
            return

        if sakin.get("meslek_anahtar") not in ["oduncu", "hanci"]:
            await interaction.response.send_message("❌ Baltanız yok, odun kesemezsiniz!", ephemeral=True)
            return

        # 30 dk cooldown
        son_calisma = sakin.get("son_calisma")
        if son_calisma:
            fark = datetime.datetime.now() - datetime.datetime.fromisoformat(son_calisma)
            if fark.total_seconds() < 1800:
                kalan_dk = int((1800 - fark.total_seconds()) / 60)
                await interaction.response.send_message(
                    f"❌ Dinlenmeniz gerekiyor! Ormanda tekrar çalışmak için `{kalan_dk} dakika` bekleyin.",
                    ephemeral=True
                )
                return

        hava = db["cevre_durumu"]["hava_durumu"]
        taban_odun = random.randint(12, 22)
        carpan = 1.0
        if hava == "Kış":
            carpan = 0.2
        elif hava == "Yağmurlu":
            carpan = 0.5
        elif hava == "Yaz":
            carpan = 1.3

        nihai_odun = int(taban_odun * carpan)
        kazanilan_hurda = nihai_odun * 2
        kazanilan_xp = 15

        db["koy_ambari"]["stoklar"]["odun"] = db["koy_ambari"]["stoklar"].get("odun", 0) + nihai_odun
        sakin["cuzdan"] = sakin.get("cuzdan", 0) + kazanilan_hurda
        atlamalar = xp_ekle(u_id, kazanilan_xp)
        sakin["son_calisma"] = datetime.datetime.now().isoformat()
        verileri_kaydet()

        embed = discord.Embed(title="🪵 ODUN KESİMİ TAMAMLANDI!", color=0x27AE60)
        embed.description = (
            f"🪓 **Köy Ambarına Eklenen Odun:** `+{nihai_odun} Adet`\n"
            f"💰 **Kişisel Kazancınız:** `+{kazanilan_hurda} Hurda` | `+{kazanilan_xp} XP`"
        )
        if atlamalar:
            embed.add_field(
                name="🎉 Seviye Atlamaları",
                value="\n".join([f"• Seviye {a['seviye']}! +{a['odul']} Hurda" for a in atlamalar]),
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    # ====================================================
    # /tuket - Envanterden gıda tüket
    # ====================================================
    @app_commands.command(name="tuket", description="[GENEL] Envanterinizdeki bir gıdayı tüketerek su ve sağlığınızı yeniler.")
    @app_commands.describe(esya_ad="Tüketilecek eşya (envanterden)")
    async def tuket(self, interaction: discord.Interaction, esya_ad: str):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Sicil kaydın yok!", ephemeral=True)
            return
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return

        sakin = db["sakinler"][u_id]
        envanter = sakin.get("envanter", {})

        mevcut = envanter.get(esya_ad, 0)
        if mevcut < 1:
            await interaction.response.send_message(
                f"❌ Envanterinizde `{esya_ad}` bulunmuyor!",
                ephemeral=True
            )
            return

        # Eşyanın tipini ve bonusunu katalogdan bul
        from cogs.pazar import TAM_PAZAR
        urun = None
        for kod, veri in TAM_PAZAR.items():
            if veri["isim"].lower() == esya_ad.lower():
                urun = veri
                esya_ad = veri["isim"]  # düzelt
                break

        if not urun:
            await interaction.response.send_message(
                "❌ Bu eşya katalogda tanınmıyor, tüketilemez!",
                ephemeral=True
            )
            return

        # Sadece Gıda ve Medikal tüketilebilir
        if urun["tip"] not in ["Gıda", "Medikal"]:
            await interaction.response.send_message(
                f"❌ `{esya_ad}` tüketilebilir bir gıda/medikal değil! (Tip: {urun['tip']})",
                ephemeral=True
            )
            return

        # Tüket ve etki uygula
        envanter[esya_ad] -= 1
        if envanter[esya_ad] == 0:
            del envanter[esya_ad]

        b_turu = urun["bonus_turu"]
        b_degeri = urun["bonus_degeri"]
        etkiler = []

        if b_turu == "Su Seviyesi":
            sakin["su"] = min(100, sakin.get("su", 100) + b_degeri)
            etkiler.append(f"💧 Su +{b_degeri}")
        elif b_turu == "Sağlık Takviyesi":
            sakin["saglik"] = min(100, sakin.get("saglik", 100) + b_degeri)
            etkiler.append(f"❤️ Sağlık +{b_degeri}")
        elif b_turu == "Akıl Sağlığı":
            sakin["akil_sagligi"] = min(100, max(0, sakin.get("akil_sagligi", 100) + b_degeri))
            etkiler.append(f"🧠 Akıl +{b_degeri}")
        elif b_turu == "Enfeksiyon Direnci":
            sakin["enfeksiyon"] = max(0, sakin.get("enfeksiyon", 0) - b_degeri)
            etkiler.append(f"☣️ Enfeksiyon -{b_degeri}")

        verileri_kaydet()

        embed = discord.Embed(title="🍽️ TÜKETİLDİ", color=0xF39C12)
        embed.description = (
            f"👤 **Tüketen:** {interaction.user.mention}\n"
            f"📦 **Tüketilen:** `1 Adet {esya_ad}`\n\n"
            f"**Etkiler:**\n" + "\n".join([f"• {e}" for e in etkiler])
        )
        await interaction.response.send_message(embed=embed)

    @tuket.autocomplete("esya_ad")
    async def tuket_autocomplete(self, interaction: discord.Interaction, current: str):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            return []
        # Sadece Gıda ve Medikal tipindeki eşyaları öner
        from cogs.pazar import TAM_PAZAR
        tuketilebilir_isimler = {v["isim"] for v in TAM_PAZAR.values() if v["tip"] in ["Gıda", "Medikal"]}

        sakin_envanter = db["sakinler"][u_id].get("envanter", {})
        return [
            app_commands.Choice(name=f"{esya} ({adet} Adet)", value=esya)
            for esya, adet in sakin_envanter.items()
            if adet > 0 and esya in tuketilebilir_isimler and current.lower() in esya.lower()
        ][:25]



    # ====================================================
    # /kullan - /tuket ile aynı (fix: kendi logic'i)
    # ====================================================
    @app_commands.command(name="kullan", description="[GENEL] Envanterinizdeki bir eşyayı kullanır/tüketir.")
    @app_commands.describe(esya_ad="Kullanılacak/tüketilecek eşya (envanterden)")
    async def kullan(self, interaction: discord.Interaction, esya_ad: str):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Sicil kaydın yok!", ephemeral=True)
            return
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return

        sakin = db["sakinler"][u_id]
        envanter = sakin.get("envanter", {})

        mevcut = envanter.get(esya_ad, 0)
        if mevcut < 1:
            await interaction.response.send_message(f"❌ Envanterinizde `{esya_ad}` bulunmuyor!", ephemeral=True)
            return

        from cogs.pazar import TAM_PAZAR
        urun = None
        for kod, veri in TAM_PAZAR.items():
            if veri["isim"].lower() == esya_ad.lower():
                urun = veri
                esya_ad = veri["isim"]
                break

        if not urun:
            await interaction.response.send_message("❌ Bu eşya katalogda tanınmıyor!", ephemeral=True)
            return

        if urun["tip"] not in ["Gıda", "Medikal"]:
            await interaction.response.send_message(f"❌ `{esya_ad}` tüketilebilir bir gıda/medikal değil!", ephemeral=True)
            return

        envanter[esya_ad] -= 1
        if envanter[esya_ad] == 0:
            del envanter[esya_ad]

        b_turu = urun["bonus_turu"]
        b_degeri = urun["bonus_degeri"]
        etkiler = []

        if b_turu == "Su Seviyesi":
            sakin["su"] = min(100, sakin.get("su", 100) + b_degeri)
            etkiler.append(f"💧 Su +{b_degeri}")
        elif b_turu == "Sağlık Takviyesi":
            sakin["saglik"] = min(100, sakin.get("saglik", 100) + b_degeri)
            etkiler.append(f"❤️ Sağlık +{b_degeri}")
        elif b_turu == "Akıl Sağlığı":
            sakin["akil_sagligi"] = min(100, max(0, sakin.get("akil_sagligi", 100) + b_degeri))
            etkiler.append(f"🧠 Akıl +{b_degeri}")
        elif b_turu == "Enfeksiyon Direnci":
            sakin["enfeksiyon"] = max(0, sakin.get("enfeksiyon", 0) - b_degeri)
            etkiler.append(f"☣️ Enfeksiyon -{b_degeri}")

        verileri_kaydet()

        embed = discord.Embed(title="🍽️ TÜKETİLDİ", color=0xF39C12)
        embed.description = (
            f"👤 **Tüketen:** {interaction.user.mention}\n"
            f"📦 **Tüketilen:** `1 Adet {esya_ad}`\n\n"
            f"**Etkiler:**\n" + "\n".join([f"• {e}" for e in etkiler])
        )
        await interaction.response.send_message(embed=embed)

    @kullan.autocomplete("esya_ad")
    async def kullan_autocomplete(self, interaction: discord.Interaction, current: str):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            return []
        from cogs.pazar import TAM_PAZAR
        tuketilebilir = {v["isim"] for v in TAM_PAZAR.values() if v["tip"] in ["Gıda", "Medikal"]}
        env = db["sakinler"][u_id].get("envanter", {})
        return [
            app_commands.Choice(name=f"{esya} ({adet} Adet)", value=esya)
            for esya, adet in env.items()
            if adet > 0 and esya in tuketilebilir and current.lower() in esya.lower()
        ][:25]

    # ====================================================
    # /tuccar-paneli - Tüccar para kazanma
    # ====================================================
    @app_commands.command(name="tuccar-paneli", description="[TÜCCAR] Ticaret paneli. Ambardan ucuz al, pahalı sat.")
    async def tuccar_paneli(self, interaction: discord.Interaction):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Sicil kaydın yok!", ephemeral=True)
            return
        if db["sakinler"][u_id].get("meslek_anahtar") != "tuccar":
            await interaction.response.send_message("❌ Bu panel sadece Tüccar mesleğine ait!", ephemeral=True)
            return
        stoklar = db["koy_ambari"]["stoklar"]
        embed = discord.Embed(title="💰 TÜCCAR TİCARET PANELİ", color=0xF1C40F)
        embed.description = (
            f"📊 **Ambar Stokları:**\n"
            f"• 🌾 Erzak: `{stoklar.get('erzak', 0)}` (Alış: 20h / Satış: 35h)\n"
            f"• 🪵 Odun: `{stoklar.get('odun', 0)}` (Alış: 15h / Satış: 25h)\n"
            f"• 🪨 Kömür: `{stoklar.get('komur', 0)}` (Alış: 25h / Satış: 40h)\n"
            f"• ⚕️ Tıbbi: `{stoklar.get('tibbi_malzeme', 0)}` (Alış: 50h / Satış: 80h)\n\n"
            f"💡 **Komutlar:**\n"
            f"• `/tuccar-al <esya> <adet>` — Ambardan ucuz al\n"
            f"• `/tuccar-sat <esya> <adet>` — Ambara pahalı sat (kar!)\n\n"
            f"💰 **Cüzdan:** `{db['sakinler'][u_id].get('cuzdan', 0)} Hurda`"
        )
        await interaction.response.send_message(embed=embed)

    # ====================================================
    # /tuccar-al
    # ====================================================
    @app_commands.command(name="tuccar-al", description="[TÜCCAR] Ambardan ucuz fiyatla malzeme al.")
    @app_commands.describe(esya="Alınacak malzeme", adet="Adet")
    @app_commands.choices(esya=[
        app_commands.Choice(name="🌾 Erzak", value="erzak"),
        app_commands.Choice(name="🪵 Odun", value="odun"),
        app_commands.Choice(name="🪨 Kömür", value="komur"),
        app_commands.Choice(name="⚕️ Tıbbi Malzeme", value="tibbi_malzeme"),
    ])
    async def tuccar_al(self, interaction: discord.Interaction, esya: str, adet: int):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Sicil kaydın yok!", ephemeral=True)
            return
        if db["sakinler"][u_id].get("meslek_anahtar") != "tuccar":
            await interaction.response.send_message("❌ Sadece Tüccar!", ephemeral=True)
            return
        if adet <= 0 or adet > 20:
            await interaction.response.send_message("❌ 1-20 adet!", ephemeral=True)
            return
        fiyatlar = {"erzak": 20, "odun": 15, "komur": 25, "tibbi_malzeme": 50}
        birim = fiyatlar.get(esya, 20)
        toplam = birim * adet
        sakin = db["sakinler"][u_id]
        if sakin["cuzdan"] < toplam:
            await interaction.response.send_message(f"❌ Yetersiz! Gereken: `{toplam}`", ephemeral=True)
            return
        stoklar = db["koy_ambari"]["stoklar"]
        if stoklar.get(esya, 0) < adet:
            await interaction.response.send_message(f"❌ Stok yok! Mevcut: `{stoklar.get(esya, 0)}`", ephemeral=True)
            return
        sakin["cuzdan"] -= toplam
        stoklar[esya] -= adet
        if "envanter" not in sakin:
            sakin["envanter"] = {}
        sakin["envanter"][esya] = sakin["envanter"].get(esya, 0) + adet
        verileri_kaydet()
        await interaction.response.send_message(f"✅ `{adet} Adet {esya}` ambardan `{toplam} Hurda`'ya alındı!")

    # ====================================================
    # /tuccar-sat
    # ====================================================
    @app_commands.command(name="tuccar-sat", description="[TÜCCAR] Envanterdeki malzemeyi ambara karla sat.")
    @app_commands.describe(esya="Satılacak malzeme", adet="Adet")
    @app_commands.choices(esya=[
        app_commands.Choice(name="🌾 Erzak", value="erzak"),
        app_commands.Choice(name="🪵 Odun", value="odun"),
        app_commands.Choice(name="🪨 Kömür", value="komur"),
        app_commands.Choice(name="⚕️ Tıbbi Malzeme", value="tibbi_malzeme"),
    ])
    async def tuccar_sat(self, interaction: discord.Interaction, esya: str, adet: int):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Sicil kaydın yok!", ephemeral=True)
            return
        if db["sakinler"][u_id].get("meslek_anahtar") != "tuccar":
            await interaction.response.send_message("❌ Sadece Tüccar!", ephemeral=True)
            return
        if adet <= 0:
            await interaction.response.send_message("❌ Geçersiz adet!", ephemeral=True)
            return
        sakin = db["sakinler"][u_id]
        envanter = sakin.get("envanter", {})
        if envanter.get(esya, 0) < adet:
            await interaction.response.send_message(f"❌ Envanterinde yeterli yok! Mevcut: `{envanter.get(esya, 0)}`", ephemeral=True)
            return
        fiyatlar = {"erzak": 35, "odun": 25, "komur": 40, "tibbi_malzeme": 80}
        birim = fiyatlar.get(esya, 35)
        toplam = birim * adet
        envanter[esya] -= adet
        if envanter[esya] == 0:
            del envanter[esya]
        sakin["cuzdan"] += toplam
        db["koy_ambari"]["stoklar"][esya] = db["koy_ambari"]["stoklar"].get(esya, 0) + adet
        verileri_kaydet()
        await interaction.response.send_message(f"✅ `{adet} Adet {esya}` ambara `{toplam} Hurda`'ya satıldı!")

    # ====================================================
    # /muhafiz-donanim - Muhafız defans eşyası
    # ====================================================
    @app_commands.command(name="muhafiz-donanim", description="[MUHAFIZ] Defans ekipmanı al (göğüslük, kalkan vb.).")
    @app_commands.choices(esya=[
        app_commands.Choice(name="🛡️ Deri Göğüslük (+5 Def, 200h)", value="gogusluk"),
        app_commands.Choice(name="🛡️ Demir Kalkan (+10 Def, 500h)", value="kalkan"),
        app_commands.Choice(name="🛡️ Çelik Zırh (+20 Def, 1200h)", value="zirh"),
        app_commands.Choice(name="🛡️ Komutan Plakası (+30 Def, 2500h)", value="plaka"),
    ])
    async def muhafiz_donanim(self, interaction: discord.Interaction, esya: str):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Sicil kaydın yok!", ephemeral=True)
            return
        meslek = db["sakinler"][u_id].get("meslek_anahtar", "")
        if meslek not in ["muhafiz_komutani", "muhafiz", "nisanci", "izci"]:
            await interaction.response.send_message("❌ Sadece muhafız sınıfı!", ephemeral=True)
            return
        donanim = {
            "gogusluk": {"isim": "Deri Göğüslük", "defans": 5, "fiyat": 200},
            "kalkan": {"isim": "Demir Kalkan", "defans": 10, "fiyat": 500},
            "zirh": {"isim": "Çelik Zırh", "defans": 20, "fiyat": 1200},
            "plaka": {"isim": "Komutan Plakası", "defans": 30, "fiyat": 2500},
        }
        item = donanim.get(esya)
        if not item:
            await interaction.response.send_message("❌ Geçersiz!", ephemeral=True)
            return
        sakin = db["sakinler"][u_id]
        if sakin["cuzdan"] < item["fiyat"]:
            await interaction.response.send_message(f"❌ Yetersiz! Gereken: `{item['fiyat']}`", ephemeral=True)
            return
        sakin["cuzdan"] -= item["fiyat"]
        sakin["defans"] = sakin.get("defans", 0) + item["defans"]
        verileri_kaydet()
        embed = discord.Embed(title="🛡️ EKİPMAN ALINDI!", color=0x2980B9)
        embed.description = f"🛡️ **Ekipman:** `{item['isim']}`\n⚡ **Defans:** `+{item['defans']}`\n💰 **Ödenen:** `{item['fiyat']} Hurda`\n🛡️ **Toplam Defans:** `{sakin['defans']}`"
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(UretimCog(bot))

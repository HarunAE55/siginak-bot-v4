"""
Cog: Meslek Sistemi
==================
Komutlar:
- /meslek-sec (herkese açık, 3 günde 1 değiştirilebilir)
- /meslek-yonetim (herkese açık, mesleğe özel panel gösterir)
"""

import discord
from discord import app_commands
from discord.ext import commands
import datetime

from veritabani import db, verileri_kaydet, olu_kontrolu


# ====================================================
# MESLEK VERİTABANI - Discord rol ID'leri ile eşleşir
# ====================================================
# "atama": True olanlar sadece Belediye Başkanı /tayin-et ile verilir
# "atama": False olanlar herkes /meslek-sec ile seçebilir
MESLEK_VERILERI = {
    # Yönetim
    "belediye_baskani": {"id": 1508463895692447926, "isim": "Belediye Başkanı", "tur": "Yönetim", "atama": True},
    "baskan_yardimcisi": {"id": 1508535553434587238, "isim": "Başkan Yardımcısı", "tur": "Yönetim", "atama": True},
    "vergi_mufettisi": {"id": 1508536734709973032, "isim": "Vergi Müfettişi", "tur": "Yönetim", "atama": True},
    # Sağlık
    "bas_simyaci": {"id": 1508539755304845352, "isim": "Baş Simyacı", "tur": "Sağlık", "atama": True},
    "simyaci": {"id": 1508539888696430663, "isim": "Simyacı", "tur": "Sağlık", "atama": False},
    "bas_doktor": {"id": 1508540001804226703, "isim": "Baş Doktor", "tur": "Sağlık", "atama": True},
    "doktor": {"id": 1508540501253558573, "isim": "Doktor", "tur": "Sağlık", "atama": False},
    "karantinaci": {"id": 1508540605259714700, "isim": "Karantinacı", "tur": "Sağlık", "atama": False},
    # Savunma
    "muhafiz_komutani": {"id": 1508543542153187478, "isim": "Muhafızlar Komutanı", "tur": "Savunma", "atama": True},
    "muhafiz": {"id": 1508543643131314396, "isim": "Muhafız", "tur": "Savunma", "atama": False},
    "nisanci": {"id": 1508543751222464593, "isim": "Nişancı", "tur": "Savunma", "atama": False},
    "izci": {"id": 1508543970660319366, "isim": "İzci", "tur": "Savunma", "atama": False},
    # Üretim
    "ciftci": {"id": 1508555554589638656, "isim": "Çiftçi", "tur": "Üretim", "atama": False},
    "coban": {"id": 1508555705504764005, "isim": "Çoban", "tur": "Üretim", "atama": False},
    "demirci": {"id": 1508555928029630484, "isim": "Demirci", "tur": "Üretim", "atama": False},
    "oduncu": {"id": 1508556205059215370, "isim": "Oduncu", "tur": "Üretim", "atama": False},
    "madenci": {"id": 1508556646295670890, "isim": "Madenci", "tur": "Üretim", "atama": False},
    "tuccar": {"id": 1508556806174015578, "isim": "Tüccar", "tur": "Üretim", "atama": False},
    "degirmenci": {"id": 1508557253534548099, "isim": "Değirmenci", "tur": "Üretim", "atama": False},
    "hanci": {"id": 1508557453556580382, "isim": "Hancı", "tur": "Üretim", "atama": False},
    # Özel
    "gezgin": {"id": 1515024992708988940, "isim": "Gezgin", "tur": "Özel", "atama": False},
    "avci": {"id": 1515025127539216504, "isim": "Avcı", "tur": "Özel", "atama": False},
    "arastirmaci": {"id": 1515025236771209358, "isim": "Araştırmacı", "tur": "Özel", "atama": False},
    "kraliyet_elcisi": {"id": 1515025324708991086, "isim": "Kraliyet Elçisi", "tur": "Özel", "atama": True},
    # Din
    "rahip": {"id": 1515026155969843401, "isim": "Rahip", "tur": "Din", "atama": False},
    "mezarci": {"id": 1515026257874522282, "isim": "Mezarcı", "tur": "Din", "atama": False}
}


class MeslekCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ====================================================
    # /meslek-sec
    # ====================================================
    @app_commands.command(name="meslek-sec", description="[MESLEK] Sığınakta icra edeceğiniz serbest iş kolunuzu tesciller.")
    @app_commands.describe(secim="Seçmek istediğiniz meslek")
    async def meslek_sec(self, interaction: discord.Interaction, secim: str):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Önce sığınağa kayıt olmalısın!", ephemeral=True)
            return
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return

        secim_temiz = secim.lower().strip()
        if secim_temiz not in MESLEK_VERILERI:
            await interaction.response.send_message(
                "❌ Sığınak tüzüğünde böyle bir iş kolu bulunamadı!",
                ephemeral=True
            )
            return

        meslek_veri = MESLEK_VERILERI[secim_temiz]
        if meslek_veri["atama"]:
            await interaction.response.send_message(
                f"❌ `{meslek_veri['isim']}` mesleği sadece Belediye Başkanı tarafından atanabilir!",
                ephemeral=True
            )
            return

        mevcut_meslek = db["sakinler"][u_id].get("meslek_anahtar", "gezgin")
        if secim_temiz == mevcut_meslek:
            await interaction.response.send_message(
                "❌ Zaten bu mesleği icra ediyorsun!",
                ephemeral=True
            )
            return

        # 3 gün cooldown
        son_degisim = db["sakinler"][u_id].get("son_meslek_degisimi")
        if son_degisim:
            fark = datetime.datetime.now() - datetime.datetime.fromisoformat(son_degisim)
            if fark.total_seconds() < 259200:  # 3 gün = 259200 saniye
                kalan_saat = int((259200 - fark.total_seconds()) / 3600)
                await interaction.response.send_message(
                    f"❌ Meslek değiştirebilmek için {kalan_saat} saat daha beklemelisin!",
                    ephemeral=True
                )
                return

        db["sakinler"][u_id]["meslek_anahtar"] = secim_temiz
        db["sakinler"][u_id]["meslek_isim"] = meslek_veri["isim"]
        db["sakinler"][u_id]["son_meslek_degisimi"] = datetime.datetime.now().isoformat()
        verileri_kaydet()

        await interaction.response.send_message(
            f"💼 **MESLEK DEĞİŞİKLİĞİ:** Yeni mesleğin resmen **{meslek_veri['isim']}** olarak tescillendi."
        )

    @meslek_sec.autocomplete("secim")
    async def meslek_sec_autocomplete(self, interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=f"{v['isim']} ({v['tur']})", value=k)
            for k, v in MESLEK_VERILERI.items()
            if not v["atama"] and current.lower() in v["isim"].lower()
        ][:25]

    # ====================================================
    # /meslek-yonetim
    # ====================================================
    @app_commands.command(name="meslek-yonetim", description="[MESLEK] İcra ettiğiniz sığınak mesleğine ait özel iş kolu yönetim panelini tetikler.")
    async def meslek_yonetim(self, interaction: discord.Interaction):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Sicil kütüğünde kaydın yok!", ephemeral=True)
            return
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return

        sakin = db["sakinler"][u_id]
        meslek = sakin.get("meslek_anahtar", "gezgin")
        m_isim = sakin.get("meslek_isim", "Gezgin")

        embed = discord.Embed(title=f"🛠️ {m_isim.upper()} FAALİYET VE YÖNETİM PANELİ", color=0x9B59B6)

        paneller = {
            "belediye_baskani": "👑 **SIĞINAK YÜCE KABİNE PANELİ**\n• Vergi Oranları Koridoru: Sabit %20\n• Sığınak Güvenlik Defansı: `[🟩🟩🟩🟩🟩🟩🟩🟩🟩⬛] %90`\n• Ambar Ödenek Durumu: `45.000 Akçe`",
            "baskan_yardimcisi": "📜 **BAŞKAN YARDIMCILIĞI BÜROSU**\n• Onay Bekleyen Sakin Dilekçeleri: `0`\n• İç Düzen Koruma Kararnameleri: Aktif.",
            "vergi_mufettisi": "⚖️ **MERKEZİ MALİYE DENETİM MASASI**\n• Sığınak Enflasyon Katsayısı: `1.0`\n• Karapara ve Kaçak Akçe İncelemesi: Temiz.",
            "bas_simyaci": "🔮 **KADİM SİMYA LABORATUVARI**\n• İksir Kazanı Sıcaklığı: `180°C`\n• Mevcut Simya Karışım Formülü: *Cıva Esansı Birleşimi*",
            "simyaci": "🔮 **KADİM SİMYA LABORATUVARI**\n• İksir Kazanı Sıcaklığı: `180°C`\n• Mevcut Simya Karışım Formülü: *Cıva Esansı Birleşimi*",
            "bas_doktor": "🩺 **SIĞINAK REVİR BAŞHEKİMLİĞİ**\n• Yatak Doluluk Oranı: `2 / 10`\n• Karantina Altındaki Sakin Sayısı: `0`.",
            "doktor": "🩺 **SIĞINAK REVİR BAŞHEKİMLİĞİ**\n• Yatak Doluluk Oranı: `2 / 10`\n• Karantina Altındaki Sakin Sayısı: `0`.",
            "karantinaci": "☣️ **SALGIN TECRİT VE DEZENFEKSİYON BİRİMİ**\n• Sığınak Hava Filtre Kalitesi: `%94`\n• Atık Radyasyon İzolasyonu: Güvenli.",
            "muhafiz_komutani": "⚔️ **MUHAFIZ ALAY KOMUTANLIĞI STRATEJİ ODASI**\n• Nöbetçi Muhafız Hattı: Tam Kadro\n• Cephanelik Ok ve Barut Rezervi: Tam Dolu.",
            "muhafiz": "🛡️ **NİZAM MUHAFIZ DEVRİYE RAPORU**\n• Bölge Güvenlik Durumu: Sakin ve Tehdit Yok.\n• Emir Komuta Hattı: Komutana Bağlı.",
            "nisanci": "🏹 **SUR ÜSTÜ NİŞANCI MEVZİSİ**\n• Arbalet Gerginlik Ayarı: Tam Performans\n• Görüş Mesafesi: Açık ve Net.",
            "izci": "🧭 **KAYIP DEHLİZLER KEŞİF DEFTERİ**\n• Haritalandırılan Mağara Tüneli: `12 / 50`\n• Dış Dünya Radyasyon Sızıntı Raporu: Stabil.",
            "ciftci": "🌾 **SERA VE TARIM ARAZİSİ ANALİZİ**\n• Toprak Nem Oranı: `🟩🟩🟩🟩🟩🟩⬛⬛⬛⬛ %60`\n• Hasada Kalan Gün: `2 Tur`.",
            "coban": "🐏 **SIĞINAK MANDIRA VE SÜRÜ SAYIMI**\n• Sürüdeki Küçükbaş Sayısı: `24 Baş`\n• Günlük Süt ve Yün Verimliliği: Yüksek.",
            "demirci": "🔥 **ÖRSLÜ DEMİRCİ OCAĞI KÖRÜĞÜ**\n• Ocak Sıcaklığı: Yüksek Kor Derecesi\n• Üretim Sırası: Ağır Çelik Plaka Göğüslük.",
            "oduncu": "🪵 **HİDROLİK KERESTE BİÇME ATÖLYESİ**\n• Tomruk Stok Seviyesi: `120 Adet Meşe`\n• Testere Diş Kalınlığı: Keskin.",
            "madenci": "⛏️ **DERİN MADEN OCAĞI ŞAFTI**\n• Kazılan Derinlik: `-340 Metre`\n• Tespit Edilen Damar: Yoğun Demir Cevheri.",
            "tuccar": "💰 **TİCARET ODASI VE BAKİYE SİCİLİ**\n• Kredi Skoru: Kusursuz\n• Pazar Tezgah Vergisi Muafiyeti: Aktif (%20 İndirimli).",
            "degirmenci": "⚙️ **HİDROLİK TAŞ DEĞİRMEN ÇARKALARI**\n• Öğütülen Buğday Miktarı: `450 Kg`\n• Çark Dönüş Devri: Dengeli.",
            "hanci": "🍺 **SIĞINAK HAN MAHMUR RAPORU**\n• Masalardaki Sakin Sayısı: `14 Sakin`\n• Boş Oda Durumu: `4 / 12 Oda Boş`.",
            "gezgin": "👣 **AVARE GEZGİN YOL HARİTASI**\n• Adımlanan Koridor Sayısı: Bilinmiyor\n• Günlük Serbest Keşif İzni: Sınırsız.",
            "avci": "🎯 **YABAN AV PARSEL TAKİP DEFTERİ**\n• Kurulan Tuzak Sayısı: `3 Adet`\n• Avlanan Son Canlı: Yaban Domuzu.",
            "arastirmaci": "🔬 **KAYIP TEKNOLOJİ TEZGAHI ANALİZİ**\n• Çözülen Şifreli Devre Kartı: `%45`\n• Eski Dünya Arşiv Kaydı: Okunuyor.",
            "kraliyet_elcisi": "👑 **DİPLOMATİK ELÇİLİK MÜHÜR ODASI**\n• Gelen Dış Mektuplar: `Yolsuzluk Yok`\n• Diplomatik Dokunulmazlık Durumu: Geçerli.",
            "rahip": "⛪ **KUTSAL MANASTIR DUA KÜRSÜSÜ**\n• İbadete Gelen Cemaat Huzuru: Sakin\n• Bağış Kutusu Akçe Seviyesi: `230 Akçe`.",
            "mezarci": "🪦 **SIĞINAK ŞEHİTLİK VE MEZARLIK SİCİLİ**\n• Boş Mezar Hazırlığı: `5 Adet`\n• Defin İşlemi Bekleyen Kadavra: Yok.",
        }

        embed.description = paneller.get(meslek, "🧭 Serbest meslek alanı, özel bir panel tetiklenmedi.")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(MeslekCog(bot))

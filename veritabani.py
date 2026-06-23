"""
Sığınak Bot - Merkezi Veritabanı Modülü
=======================================
JSON tabanlı kalıcı veritabanı + tüm yardımcı fonksiyonlar burada.
Tüm cog'lar bu modülü import eder: `from veritabani import db, verileri_kaydet, ...`
"""

import json
import os
import datetime
import io
import discord

# ====================================================
# 1. VERİTABANI ÇEKİRDEĞİ
# ====================================================

DATA_FILE = "siginak_temel_veri.json"

# Global veritabanı dict'i. Tüm modüller bunu paylaşır.
db: dict = {}


def verileri_yukle():
    """Diskten veritabanını yükler. Dosya yoksa veya bozuksa varsayılan şema döner."""
    global db
    varsayilan_yapi = {
        "sakinler": {},
        "sistem_ayarlari": {
            "KASA_AKÇE_PLACEHOLDER": 50000,
            "toplam_kayitli_sakin": 0,
            "sur_seviyesi": 1,
            "koy_seviyesi": 1
        }
    }
    if not os.path.exists(DATA_FILE):
        # Yeni dosya oluştur - db.clear() + update kullanarak tüm referansları güncelle
        db.clear()
        db.update(varsayilan_yapi)
        verileri_kaydet()
        return
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            yuklenen = json.load(f)
        # db'yi temizle ve yüklenen verilerle doldur (referans korunur)
        db.clear()
        db.update(yuklenen)
        # Eksik temel alanları tamamla
        if "sakinler" not in db:
            db["sakinler"] = {}
        if "sistem_ayarlari" not in db:
            db["sistem_ayarlari"] = varsayilan_yapi["sistem_ayarlari"]
        for k in varsayilan_yapi["sistem_ayarlari"]:
            if k not in db["sistem_ayarlari"]:
                db["sistem_ayarlari"][k] = varsayilan_yapi["sistem_ayarlari"][k]
    except Exception as e:
        print(f"⚠️ Veritabanı yükleme hatası: {e} - Varsayılan şema yükleniyor.")
        db.clear()
        db.update(varsayilan_yapi)


def verileri_kaydet():
    """Veritabanını atomik olarak diske yazar (.tmp -> os.replace)."""
    try:
        gecici_dosya = DATA_FILE + ".tmp"
        with open(gecici_dosya, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=4)
        os.replace(gecici_dosya, DATA_FILE)
    except Exception as e:
        print(f"❌ Veritabanı yazılırken kritik hata: {e}")


def db_ilkle():
    """Veritabanında eksik olan tüm tabloları varsayılan değerlerle oluşturur.
    Bot her açılışta çağrılmalı - eski sürümlerden gelen eksik alanları tamamlar."""
    defaults = {
        "biyolaboratuvar": {
            "virus_ilerlemesi": 0,
            "lab_seviyesi": 1,
            "toplam_deney": 0
        },
        "maliye_ayarlari": {
            "veba_vergisi": 20,
            "ticaret_kesintisi": 10,
            "toplam_tahsilat": 0
        },
        "mahkeme_kayitlari": {
            "toplam_idam": 0,
            "toplam_surgun": 0,
            "aktif_dava": {}
        },
        "koy_ambari": {
            "stoklar": {
                "erzak": 50,
                "tibbi_malzeme": 10,
                "odun": 100,
                "komur": 50
            },
            "toplam_bagis_sayisi": 0
        },
        "savunma_sistemi": {
            "muhafiz_tahkimati": 10
        },
        "idari_kisitlamalar": {
            "sokaga_cikma_yasagi": False,
            "karantina_modu": False,
            "karantina_cadiri": []
        },
        "kilise_sistemi": {
            "son_can_calinma": None,
            "fare_nufusu": 10,
            "kedi_katliami_yapildi": False
        },
        "cevre_ayarlari": {
            "hava_durumu": "Güneşli",
            "salgin_kuvveti": 1,
            "enfeksiyon_orani": 10
        },
        "cevre_durumu": {
            "hava_durumu": "İlkbahar",
            "karantina_asi_stoku": 5
        },
        "aktif_secim": {
            "durum": "kapali",
            "adaylar": {},
            "oylar": {}
        },
        "sefer_sistemi": {
            "sefer_zorlugu": 1,
            "sur_seviyesi": 1,
            "sur_canı": 500,
            "maks_sur_canı": 500,
            "son_baskin_timestamp": None
        },
        "gazete_sistemi": {
            "haber_kanali_id": None,
            "son_gazete_timestamp": None,
            "olay_gunlugu": []
        },
        "acik_arttirmalar": {},
    }
    degisiklik = False
    for key, val in defaults.items():
        if key not in db:
            db[key] = val
            degisiklik = True
    if degisiklik:
        verileri_kaydet()


# ====================================================
# 2. YARDIMCI FONKSİYONLAR
# ====================================================

def bar_olustur(mevcut, maksimum=100, uzunluk=10):
    """İlerleme barı oluşturur. Örn: [🟩🟩🟩⬛⬛⬛⬛⬛⬛⬛] %30"""
    yuzde = max(0, min(mevcut, maksimum)) / maksimum
    dolu = int(yuzde * uzunluk)
    bos = uzunluk - dolu
    return f"[{'🟩' * dolu}{'⬛' * bos}] %{int(max(0, min(mevcut, maksimum)))}"


def olu_kontrolu(sakin_id: str):
    """Sakin ölüyse hata mesajı döner, değilse None."""
    if db["sakinler"].get(sakin_id, {}).get("durum") == "Ölü":
        return "💀 Sığınak sicilinde **ÖLÜ** olarak kayıtlısın! Hiçbir komutu kullanamazsın. Yeniden doğmak için `/kayit` ol."
    return None


def sokak_ve_karantina_kontrolu(sakin_id: str):
    """Ölü/karantinada/sokak yasağı kontrolü. Hata mesajı veya None döner."""
    sakin = db["sakinler"].get(sakin_id, {})
    durum = sakin.get("durum")

    if durum == "Ölü":
        return "💀 Sığınak sicilinde **ÖLÜ** olarak kayıtlısın! Hiçbir komutu kullanamazsın. Yeniden doğmak için `/kayit` ol."
    if durum == "Karantinada":
        return "☣️ Karantina çadırında tecrit altındasınız! Dışarı çıkmanız ve komut kullanmanız yasaktır."
    if durum == "Hücrede":
        return "🔒 Zindandasın! Hücreden çıkana kadar hiçbir komut kullanamazsın."

    if db["idari_kisitlamalar"]["sokaga_cikma_yasagi"]:
        meslek = sakin.get("meslek_anahtar", "")
        if meslek not in ["belediye_baskani", "baskan_yardimcisi", "muhafiz_komutani", "muhafiz", "karantinaci"]:
            return "🚨 Sığınakta **Sokağa Çıkma Yasağı** ilan edilmiştir! Gezi, pazar, takas ve düello komutları dondurulmuştur."
    return None


def olum_protokolu(olen_id: str, olum_sebebi: str = "diger", kazanan_id: str = None):
    """Merkezi ölüm protokolü. Ölen kişinin eşya/para aktarımını yönetir.

    olum_sebebi: "duello" = kazanan rakibe gider, diğer = kasaya gider.
    Dönüş: ganimet metni (string).
    """
    if olen_id not in db["sakinler"]:
        return ""
    olen = db["sakinler"][olen_id]
    olen["durum"] = "Ölü"
    olen["saglik"] = 0
    olen["meslek_anahtar"] = "gezgin"
    olen["meslek_isim"] = "Gezgin (Ölü)"

    olen_env = olen.get("envanter", {})
    olen_akçe = olen.get("cuzdan", 0)
    olen_banka = olen.get("banka", 0)
    toplam_para = olen_akçe + olen_banka
    ganimet_metni = ""

    # Pazar kataloğunu gecici olarak import et (döngüsel import önlemek için lokal)
    try:
        from cogs.pazar import TAM_PAZAR
    except ImportError:
        TAM_PAZAR = {}

    if olum_sebebi == "duello" and kazanan_id and kazanan_id in db["sakinler"]:
        kazanan = db["sakinler"][kazanan_id]
        kazanan_env = kazanan.get("envanter", {})

        for esya, adet in list(olen_env.items()):
            if adet > 0:
                kazanan_env[esya] = kazanan_env.get(esya, 0) + adet
                ganimet_metni += f"  • {esya} ({adet} Adet) → Kazanana aktarıldı\n"

        if toplam_para > 0:
            kazanan["cuzdan"] = kazanan.get("cuzdan", 0) + toplam_para
            ganimet_metni += f"  • {toplam_para} Akçe → Kazanana aktarıldı\n"
    else:
        if toplam_para > 0:
            db["sistem_ayarlari"]["KASA_AKÇE_PLACEHOLDER"] = db["sistem_ayarlari"].get("KASA_AKÇE_PLACEHOLDER", 0) + toplam_para
            ganimet_metni += f"  • {toplam_para} Akçe → Sığınak kasasına aktarıldı\n"

        satistan_gelen = 0
        cope_giden = []
        for esya, adet in list(olen_env.items()):
            if adet > 0:
                esya_degeri = 0
                for kod, veri in TAM_PAZAR.items():
                    if veri["isim"] == esya:
                        esya_degeri = veri["fiyat"]
                        break

                if esya_degeri > 0:
                    satis_fiyat = int(esya_degeri * 0.5) * adet
                    satistan_gelen += satis_fiyat
                    ganimet_metni += f"  • {esya} ({adet} Adet) → Kasaya satıldı (+{satis_fiyat} Akçe)\n"
                else:
                    cope_giden.append(f"  • {esya} ({adet} Adet) → Çöpe atıldı (değersiz)\n")

        if satistan_gelen > 0:
            db["sistem_ayarlari"]["KASA_AKÇE_PLACEHOLDER"] = db["sistem_ayarlari"].get("KASA_AKÇE_PLACEHOLDER", 0) + satistan_gelen

        if cope_giden:
            ganimet_metni += "".join(cope_giden)

    # Ölenin envanteri ve parası sıfırlanır
    olen["envanter"] = {}
    olen["cuzdan"] = 0
    olen["banka"] = 0
    verileri_kaydet()

    return ganimet_metni


def xp_ekle(u_id: str, miktar: int):
    """Sakine XP ekler ve seviye atlama kontrolü yapar.
    Atlama gerçekleşirse liste döner: [{"seviye": N, "odul": H}]
    Atlama yoksa boş liste döner.
    """
    if u_id not in db["sakinler"]:
        return []
    if miktar <= 0:
        return []

    sakin = db["sakinler"][u_id]
    sakin["xp"] = sakin.get("xp", 0) + miktar
    atlamalar = []
    while sakin["xp"] >= 100:
        sakin["xp"] -= 100
        sakin["seviye"] = sakin.get("seviye", 1) + 1
        odul = sakin["seviye"] * 25
        sakin["cuzdan"] = sakin.get("cuzdan", 0) + odul
        atlamalar.append({"seviye": sakin["seviye"], "odul": odul})
    return atlamalar


def haber_ekle(metin: str):
    """Sığınak gazete sistemi olay günlüğüne haber ekler."""
    zaman = datetime.datetime.now().strftime("%H:%M")
    db["gazete_sistemi"]["olay_gunlugu"].append(f"[{zaman}] - {metin}")
    verileri_kaydet()


def sakin_olustur_defaults(u_id: str, isim: str, soyisim: str, yas: int, memleket: str, baslangic_atak: int = None):
    """Yeni bir sakin kaydı oluşturur ve db'ye yazar.Kaydetmez - çağıran verileri_kaydet() yapmalı."""
    import random
    if baslangic_atak is None:
        baslangic_atak = random.randint(10, 20)

    db["sakinler"][u_id] = {
        "isim": isim,
        "soyisim": soyisim,
        "yas": yas,
        "memleket": memleket,
        "biyografi": "",  # /biyografi-yaz ile doldurulur
        "cuzdan": 500,
        "banka": 0,
        "koy_ambari": {},
        "envanter": {},
        "laboratuvar_durumu": "Temiz",
        "selection_data": None,
        "atak": baslangic_atak,
        "defans": 0,
        "saglik": 100,
        "su": 100,
        "enfeksiyon": 0,
        "akil_sagligi": 100,
        "moral": 50,
        "itibar": 50,
        "sans_carpani": 1.0,
        "seviye": 1,
        "xp": 20,
        "durum": "Canlı",
        "meslek_anahtar": "gezgin",
        "meslek_isim": "Gezgin",
        "son_calisma": None,
        "son_meslek_degisimi": None,
        "son_gezi": None,        # /gez cooldown için
        "son_nobet": None,       # /nobet cooldown için
    }
    db["sistem_ayarlari"]["toplam_kayitli_sakin"] = db["sistem_ayarlari"].get("toplam_kayitli_sakin", 0) + 1
    return db["sakinler"][u_id]


def sakin_sil(u_id: str) -> bool:
    """Sakini veritabanından tamamen siler. True dönerse silindi."""
    if u_id in db["sakinler"]:
        del db["sakinler"][u_id]
        verileri_kaydet()
        return True
    return False


def yetkili_mi(interaction: discord.Interaction, rol_idleri: list) -> bool:
    """Kullanıcının herhangi bir rolü listedeki ID'lerden birine uyuyor mu?"""
    return any(rol.id in rol_idleri for rol in interaction.user.roles)


# ====================================================
# 4. UI VIEW - ÖLÜM EKRANI (Ölen kişiye yeniden kayıt butonu)
# ====================================================
class OlumEkraniView(discord.ui.View):
    """Ölen kişiye gösterilen buton. Tıklayınca kayıt bilgisi verir."""

    def __init__(self, olen_user):
        super().__init__(timeout=300)  # 5 dk
        self.olen_user = olen_user

    @discord.ui.button(label="📝 Yeniden Kayıt Ol", style=discord.ButtonStyle.success)
    async def yeniden_kayit_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.olen_user.id:
            await interaction.response.send_message("❌ Bu buton ölen kişiye özel!", ephemeral=True)
            return
        await interaction.response.send_message(
            "📝 **Yeniden Doğuş:** Sığınak kapıları sana tekrar açılıyor!\n"
            "Hayatına sıfırdan başlamak için `/kayit` komutunu kullan:\n"
            "`/kayit isim: soyisim: yaş: memleket:`",
            ephemeral=True
        )
        self.stop()


# ====================================================
# 3. ROL ID'leri (Sabit - Sunucuya özel - v5.7 Güncel)
# ====================================================

# Sunucu Yönetimi
RP_OWNER_ROL_ID = 1470544130559049921        # ♔ • RP Owner
SECOND_OWNER_ROL_ID = 1470743025280880743     # ♕ • Second Owner
ADMINISTRATOR_ROL_ID = 1518268192395497544    # 👑 • Administrator
ADMIN_ROL_ID = 1518268274687873145           # 🛡️ • Admin
YETKILI_EKIP_ROL_ID = 1518378716533882921    # 🎩 • Yetkili Ekip
VEBA_BOT_ROL_ID = 1516186216276431062        # 🤖 • Veba 1320

# Yetkili Rolleri
KAYIT_EKIBI_ROL_ID = 1470748590917025842      # 🪪 • Kayıt Ekibi
KIDEMLI_MODERATOR_ROL_ID = 1518267799200338091 # 🛡️ • Kıdemli Moderatör
MODERATOR_ROL_ID = 1492516693921234964        # ⚖️ • Moderatör
PARTNER_SORUMLUSU_ROL_ID = 1515767601069031424 # 🤝 • Partner Sorumlusu
GAZETECI_ROL_ID = 1492555591007211781         # 📰 • Gazeteci
HARITACI_ROL_ID = 1497684152512676030         # 🗺️ • Haritacı
SUNUCU_EKIBI_ROL_ID = 1470743726958706831     # 🎩 • Sunucu Ekibi
OZEL_UYE_ROL_ID = 1518271196154691644         # 💎 • Özel Üye
ILK_UYE_ROL_ID = 1494999628515643455          # 🌹 • İlk Üye

# RP Yönetim
BELEDIYE_BASKANI_ROL_ID = 1508463895692447926
BASKAN_YARDIMCISI_ROL_ID = 1508535553434587238
VERGI_MEMURU_ROL_ID = 1508536734709973032

# RP Sağlık
BAS_SIMYACI_ROL_ID = 1508539755304845352
SIMYACI_ROL_ID = 1508539888696430663
BAS_DOKTOR_ROL_ID = 1508540001804226703
DOKTOR_ROL_ID = 1508540501253558573
KARANTINACI_ROL_ID = 1508540605259714700

# RP Savunma
MUHAFIZ_KOMUTANI_ROL_ID = 1508543542153187478
MUHAFIZ_ROL_ID = 1508543643131314396
NISANCI_ROL_ID = 1508543751222464593
IZCI_ROL_ID = 1508543970660319366

# RP Üretim
CIFTCI_ROL_ID = 1508555554589638656
COBAN_ROL_ID = 1508555705504764005
DEMIRCI_ROL_ID = 1508555928029630484
ODUNCU_ROL_ID = 1508556205059215370
MADENCI_ROL_ID = 1508556646295670890
TUCCAR_ROL_ID = 1508556806174015578
DEGIRMENCI_ROL_ID = 1508557253534548099
HANCI_ROL_ID = 1508557453556580382

# RP Özel
GEZGIN_ROL_ID = 1515024992708988940
AVCI_ROL_ID = 1515025127539216504
ARASTIRMACI_ROL_ID = 1515025236771209358
KRALIYET_ELCISI_ROL_ID = 1515025324708991086

# RP Din
RAHIP_ROL_ID = 1515026155969843401
MEZARCI_ROL_ID = 1515026257874522282

# Üye Rolleri
UYE_ROL_ID = 1470747341005918228
BOT_ROL_ID = 1492819034305990737
KAYITSIZ_ROL_ID = 1470747472858058897


# ====================================================
# 5. YETKI KONTROL FONKSIYONLARI
# ====================================================

def admin_mi(interaction) -> bool:
    """Kullanıcı admin yetkisine sahip mi? (RP Owner, Administrator, Admin, Yetkili Ekip, veya Discord admin)"""
    if hasattr(interaction, 'user') and hasattr(interaction.user, 'guild_permissions'):
        if interaction.user.guild_permissions.administrator:
            return True
    rol_idleri = [RP_OWNER_ROL_ID, ADMINISTRATOR_ROL_ID, ADMIN_ROL_ID, YETKILI_EKIP_ROL_ID]
    if hasattr(interaction, 'user'):
        return any(rol.id in rol_idleri for rol in interaction.user.roles)
    return False


def rp_owner_mi(interaction) -> bool:
    """Kullanıcı RP Owner/Administrator/Admin mi?"""
    rol_idleri = [RP_OWNER_ROL_ID, ADMINISTRATOR_ROL_ID, ADMIN_ROL_ID]
    if hasattr(interaction, 'user'):
        return any(rol.id in rol_idleri for rol in interaction.user.roles)
    return False

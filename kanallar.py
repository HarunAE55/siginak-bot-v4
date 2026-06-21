"""
Sığınak Bot - RP Kanal ID'leri ve Eşlemeleri
============================================
Sunucudaki tüm RP kanallarının ID'leri burada.
Otomatik olaylar (zombi baskını, gazete, vergi raporu vb.) ilgili kanala gider.
"""

# ====================================================
# 1. SİSTEM KANALLARI
# ====================================================

DENEME_TEST = 1492884995176398981          # Sunucu yöneticilerinin konuştuğu kanal
LOG_KANAL_ID = 1515020105191391358          # Sunucu log kanalı
YEDEKLEME_KANAL_ID = 1516177967288422400    # Bot yedeklerini attığı kanal (env var olarak da ayarlanabilir)

# ====================================================
# 2. HOŞGELDİN & KAYIT
# ====================================================

KAYIT_ODASI = 1470543732913733726           # Sunucuya girenlerin kaydının yapıldığı kanal
KAYIT_LOG = 1470746590175039620             # Kaydı yapılan üyelerin logu

# ====================================================
# 3. BİLGİLENDİRME & DUYURU
# ====================================================

DUYURULAR = 1470774288108884009             # Sunucu ve RP duyuruları
GUNCELLEMELER = 1470774969624428758         # Sunucu ve RP güncellemeleri
BOT_GUNCELLEMESI = 1497904630644871188      # Bot hakkında güncelleme

# ====================================================
# 4. RP BİLGİ KANALLARI
# ====================================================

RP_KURALLARI = 1470778314158510244
RP_ROLLERI = 1499662682133889044
ANA_HIKAYE = 1470775371904581694
KOY_BILGISI = 1470780833563414610
KOY_HALKI = 1470778406588256430
KOY_KAYNAKLARI = 1479091466813964318
HARITA = 1480186194469060770

# ====================================================
# 5. RP ETKİNLİK & HABERLEŞME KANALLARI (Otomatik olaylar buraya gider)
# ====================================================

SALGIN = 1497688450277834822                # 🦠 Veba/salgin eventleri (zombi baskını vb.)
BELEDIYE_DUYURULARI = 1515026699073360053   # 📯 Belediye başkanının duyuruları
SIMYACININ_MEKTUPLARI = 1515026778953875586 # 📜 Simyacı olayları
EVENTLER = 1515026896486797425              # 📍 RP yöneticisi eventleri
DER_BEOBACHTER = 1480185914650267781        # 📜 Haber kanalı (otomatik gazete buraya)

# ====================================================
# 6. KRALIYET KANALLARI
# ====================================================

KRALIYET_FERMANLARI = 1480180024777773218
KRALIYET_DURUMU = 1492745842623385791
KRALIYET_KAYNAKLARI = 1507712245604286625

# ====================================================
# 7. KÖY GİRİŞİ KANALLARI
# ====================================================

ZAYIF_SURLAR = 1508542217969467445
TOPRAK_YOL = 1508857245830484282
BOS_EV_1 = 1508857306467794944              # Sahipsiz boş ev
NEGANIN_EVI = 1508857354043785269
DISARIYA_GIDEN_YOL = 1508647813301669979
TARLA_YOLU = 1508647960680857660
TARLA = 1508648065307902022
TARLANIN_YANINDAKI_BOS_EV_1 = 1508648128935493774
TARLANIN_YANINDAKI_BOS_EV_2 = 1508648210514579598
SURLARIN_CEVRESI = 1508648316831793242
UZUN_YOL = 1508648627734708394

# ====================================================
# 8. DOĞU KESİM KANALLARI
# ====================================================

MEYDANA_GIDEN_YOL = 1508751818128363561
MEYDAN_AGACI = 1508860255293931690
MEYDANDAKI_STANDLAR = 1508860387666165791
MEYDANDAKI_MUSTAKIL_EV = 1508860460986798080
SURLARIN_DIBINDEKI_BOS_KULUBE = 1508860537809797320
KOY_EVLERI_YOLU = 1508751879272665128
BOS_MUSTAKIL_EV = 1508751939297480764
BOS_KOY_EVI_1 = 1508752036210937857
BOS_MUSTAKIL_EV_2 = 1508752179568316606
PAZAR_YOLU = 1508752111435776031
PAZAR_YERI = 1508752279174512730
BELEDIYE_BINASI_YOLU = 1508752747128950864
BELEDIYE_BINASI = 1508752930893991976
BASKAN_SALONU = 1508753021377708122
KARANTINA_KAMPI_YOLU = 1515060042187935836
KARANTINA_KAMPI = 1515060113029992591
KARANTINA_CADIRLARI = 1515060174396592258
MEZARLIK_YOLU = 1515060243451875328
MEZARLIK = 1515060310866788513

# ====================================================
# 9. BATI KESİM KANALLARI
# ====================================================

KISLA_YOLU = 1508757125294194708
KISLA_GIRISI = 1508860905906114570
YESIL_KISLA = 1508860968250380318
BATI_KOY_EVLERI_YOLU = 1508861006267285515
BATI_BOS_KOY_EVI = 1508861050697814178
ASKELADIN_MUSTAKIL_EVI = 1508757212149977088
BATI_BOS_KOY_EVI_2 = 1508757338243465216
KOY_EVLERININ_ORTASI = 1508757399958327366
HASTANE_YOLU = 1508757469424521266
HASTANE = 1508757518678229172
SAGLIK_CADIRLARI = 1508757657912086599
SIMYACININ_KULESI = 1508757828796551288
SIMYACININ_LABORATUVARI = 1508757917480910888
KULENIN_TEPESI = 1508758009164337238
DOGU_CIKISI_BATI = 1508758060842356787
KARANLIK_ORMAN_YOLU_BATI = 1508758137346330754

# ====================================================
# 10. KUZEY KESİM KANALLARI
# ====================================================

KUZEY_PAZAR_YOLU = 1508860650976182372
KUZEY_PAZAR = 1508755924947308634
HAN_YOLU = 1508860699303084232
HAN = 1508860745943879772
SU_KUYUSU = 1508860784338538698
IHTISAMLI_HANE = 1508755973764808754         # ⛪ Köyün ibadethanesi
MADEN_OCAGI_YOLU = 1508756044304744628
KUZEY_CIKISI = 1508756099073835192
MADEN_OCAGI = 1508756162693304381
ONDERIN_KOSKU = 1508756267508695061
IS_YOLU = 1508756360756596766
DEGIRMEN = 1508756451387244615
DEMIRCI = 1508756552079904910
AMBAR_VE_AHIRLAR = 1508756716513132605
DOGU_CIKISI_KUZEY = 1515064605628694728
KARANLIK_ORMAN_YOLU_KUZEY = 1515064668287406150

# ====================================================
# 11. KARANLIK ORMAN KANALLARI
# ====================================================

KARANLIK_ORMAN_KOY_YOLU = 1515069102530756769
ODUNCUNUN_YOLU = 1515069167164854374
ODUNCUNUN_YERI = 1515069184592056370
SIRLAR_MAGARASI = 1515069602042744964
BATAKLIK_YOLU = 1515069618765561886
GIZEMLI_BATAKLIK = 1515069633764261998
BILINMEYEN_YOL = 1515069648281014414
SIK_AGACLAR = 1515078812071759982
SESSIZ_UCURUM = 1515078867319263322

# ====================================================
# 12. EĞLENCE & DIĞER
# ====================================================

SOHBET = 1470755295591399597
BOT_KOMUT = 1470771946596864223
RP_ONERI = 1470772673494909073

# ====================================================
# 13. BÖLGE → RP KANALI EŞLEME (/gez için)
# ====================================================
# /gez komutunda her bölge bir RP kanalına karşılık gelir.
# Oyuncu gezdiğinde, sonuç hem komutun kullanıldığı kanala,
# hem de ilgili RP kanalına kısa bir bildiri olarak gönderilir.

GEZI_BOLGE_KANAL_ESLEME = {
    "Terkedilmiş Köy": BOS_EV_1,                    # 🏚️ Sahipsiz boş ev
    "Veba Mezarlığı": MEZARLIK,                     # ⚰️ Köy mezarlığı
    "Karanlık Koruluk": KARANLIK_ORMAN_YOLU_KUZEY,  # 🌲 Karanlık orman yolu
    "Yıkık Kilise": IHTISAMLI_HANE,                 # ⛪ İhtişamlı hane (ibadethane)
    "Dehliz Labirenti": SIRLAR_MAGARASI,            # 🕳️ Sırlar mağarası
    "Zombi Tarlası": GIZEMLI_BATAKLIK,              # 🧟 Gizemli bataklık
}


# ====================================================
# 14. OTOMATİK OLAY KANALLARI
# ====================================================
# Otomatik task'lar (vergi, gazete, baskın, açlık) hangi kanala mesaj atar?

# Vergi tahsilat raporu → LOG kanalı (sessiz, sadece log)
VERGI_RAPOR_KANAL_ID = LOG_KANAL_ID

# Gazete → DER_BEOBACHTER (haber kanalı)
GAZETE_KANAL_ID = DER_BEOBACHTER

# Zombi baskını → ZAYIF SURLAR (surların olduğu kanal)
BASKIN_KANAL_ID = ZAYIF_SURLAR

# Açlık/susuzluk genel uyarısı → SALGIN (kriz kanalı)
ACLUK_RAPOR_KANAL_ID = SALGIN

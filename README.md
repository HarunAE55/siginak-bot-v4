# 🦠 Sığınak Veba RP Bot v4.0

**Discord RPG/RP botu** — 1349 Bavyera Veba teması. Cogs mimarisi ile modüler yapı.

## 📦 Kurulum

### Gereksinimler
- Python 3.10+ (3.13+ için `audioop-lts` otomatik eklenir)
- Discord Bot Token ([Discord Developer Portal](https://discord.com/developers/applications))
- Render hesabı (ücretsiz tier yeterli) veya başka bir hosting

### Yerel Geliştirme

```bash
# 1. Repo'yu klonla
git clone <repo-url>
cd siginak-bot-v4

# 2. Sanal ortam oluştur (önerilir)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya: venv\Scripts\activate  # Windows

# 3. Bağımlılıkları yükle
pip install -r requirements.txt

# 4. Ortam değişkenlerini ayarla
export DISCORD_TOKEN=bot_tokenin_buraya
export YEDEK_KANAL_ID=1516177967288422400  # opsiyonel

# 5. Botu çalıştır
python main.py
```

### Render'a Deploy

1. Bu kodu GitHub'a pushla
2. Render'da "New → Web Service" oluştur
3. GitHub repo'nu bağla
4. Render `render.yaml`'ı otomatik okuyacak
5. Environment Variables sekmesinden:
   - `DISCORD_TOKEN` = bot token
   - `YEDEK_KANAL_ID` = yedek kanalı ID (opsiyonel)
6. Deploy!

UptimeRobot'a `https://your-app.onrender.com/health` URL'ini 5 dakikada bir ping atacak şekilde ayarla (Render free tier uyku modunu önlemek için).

## 📁 Proje Yapısı

```
siginak-bot-v4/
├── main.py                  # Bot giriş noktası, tüm cog'ları yükler
├── veritabani.py            # JSON DB + yardımcı fonksiyonlar (olum_protokolu, xp_ekle, vb.)
├── kanallar.py              # RP kanal ID'leri ve bölge→kanal eşlemesi
├── keep_alive.py            # Flask keep-alive (Render free tier için)
├── requirements.txt
├── render.yaml              # Render deploy config
├── .gitignore
└── cogs/
    ├── __init__.py
    ├── kayit.py             # /kayıt, /profil, /envanter, /biyografi-yaz, /owner-kayıt, /kayıt-sil, /xp_kazan_test
    ├── meslek.py            # /meslek-seç, /meslek-yönetim
    ├── pazar.py             # /pazar, /satinal, /bota-sat, /esya-sat, /takas-teklif, /acik-arttirma-baslat, /pey-ver
    ├── savas.py             # /duello, /sefer, /zombi-baskını-başlat
    ├── kesif.py             # /gez, /anıt
    ├── yonetim.py           # /secimi-başlat, /aday-ol, /yonetim, /tayin-et, /maas-ode, /toplu-maaş, /yargıla
    ├── simya.py             # /deney, /laboratuvar-geliştir, /doktor-paneli, /asi-uret, /tedavi-et
    ├── kilise.py            # /rahip-paneli, /afaroz-et, /buyuk-kilise-cani, /kedileri-yok-et, /kutsa
    ├── kolluk.py            # /muhafiz-paneli, /hucreye-at, /hucreden-çıkar, /karantina-al, /sokak-yasagi, /savunmayı-güçlendir, /darbe, /nobet
    ├── uretim.py            # /ciftci-paneli, /tarla-calis, /maden-kaz, /orman-kes, /tuket
    ├── ambar.py             # /ambar, /ambara-bağış, /ambardan-al
    ├── maliye.py            # /maliye-yönetim (+ 5h otomatik vergi)
    ├── cevre.py             # /hava-durumu-değiş, /sunucu-yönetimi (RP Owner)
    ├── rehber.py            # /destek, /rehber, /haber (+ 6h gazete)
    └── sistem.py            # 1h yedekleme + 24h açlık (otomatik task)
```

## 🎮 Komut Kategorileri

### 📝 Kayıt & Profil
- `/kayıt` — Sicil kütüğüne kaydol (10-40 yaş)
- `/profil` — Karakter kartın + barlar + biyografi
- `/envanter` — Sırt çantası
- `/biyografi-yaz [metin]` — Karakter hikayesi (max 1000 karakter, 3 günde 1)
- `/owner-kayıt [@üye] ...` — RP Owner: başkasını zorla kaydet
- `/kayıt-sil [@üye] EVET` — RP Owner: kaydı sil
- `/xp_kazan_test [miktar] [@üye]` — Sadece admin: test XP ekle

### 🛒 Pazar & Ticaret
- `/pazar [kategori]` — 7 kategori (Silah, Zırh, Medikal, Gıda, Hammadde, Teknoloji, Mistik)
- `/satinal [kod] [adet]` — Mesleğe göre %20 indirim
- `/bota-sat [esya] [adet]` — Kasaya sat (tüccar %20, diğer %25 vergi)
- `/esya-sat [@üye] [esya] [fiyat]` — Oyuncuya satış
- `/takas-teklif [@üye] [verilen] [istenen]` — Eşya takası
- `/acik-arttirma-baslat [esya] [açılış]` — 2 dk açık arttırma
- `/pey-ver [ilan_id] [teklif]` — Teklif ver
- `/tuket [esya]` — Gıda/Medikal tüket, su/sağlık yenile

### 🏛️ Siyaset & Yönetim
- `/secimi-başlat` — Sadece admin (15 dk aday + 45 dk oy = 1 saat)
- `/aday-ol [vaat]` — 500 hurda depozito
- `/yonetim` — Başkan paneli (sur/köy geliştir)
- `/tayin-et [@üye] [unvan]` — 5 kadroluk atama
- `/maas-ode`, `/meslek-maaş-öde`, `/toplu-maaş` — Maaş ödemeleri

### ⚖️ Yargı
- `/yargıla [@sanık] [suç]` — Başkan mahkeme açar
- `/hucreye-at`, `/hucreden-çıkar` — Muhafız
- `/sokak-yasagi [durum]` — Başkan
- `/darbe` — İsyancıların başkanı devirme girişimi

### ⛪ Kilise & Rahip
- `/rahip-paneli` — Panel
- `/afaroz-et [@üye] [neden]` — Şans düşür
- `/buyuk-kilise-cani` — 3 günde 1, +10 moral herkese
- `/kutsa [@üye]` — 3 saatte 1, enfeksiyon -20, sağlık +15
- `/kedileri-yok-et` ⚠️ — Tüm canlıları enfekte eder!

### 💊 Sağlık & Simya
- `/doktor-paneli` — Panel
- `/asi-uret` — 2 tıbbi malzeme → 1 aşı
- `/tedavi-et [@üye]` — 1 aşı ile hasta iyileştir
- `/deney` — Simyacı, %10 başarılı/%85 başarısız/%5-15 ölüm
- `/laboratuvar-geliştir` — Başkan/Baş Simyacı, 500 hurda/seviye (max 3)

### 🛡️ Kolluk & Savunma
- `/muhafiz-paneli` — Panel
- `/karantina-al [@üye]`, `/karantina-kaldır [@üye]` — Karantina
- `/savunmayı-güçlendir` — Başkan, 500 hurda +15 tahkimat
- `/nobet` ⭐ — Muhafız, 4 saatte 1, hurda + XP kazan

### 🌾 Üretim & Ambar
- `/ciftci-paneli` — Panel
- `/tarla-calis` — 30 dk CD (Çiftçi/Çoban/Değirmenci/Hancı)
- `/maden-kaz` — 30 dk CD (Madenci/Demirci)
- `/orman-kes` — 30 dk CD (Oduncu/Hancı)
- `/ambar` — Stok listesi
- `/ambara-bağış [esya] [adet]` — Bağış, +2 hurda/adet itibar
- `/ambardan-al [esya] [adet]` — Max 5/adet, fakirlere ücretsiz

### ⚔️ Savaş & Keşif
- `/duello [@rakip]` — Butonlu tur tabanlı, %20 kalıcı ölüm riski
- `/sefer` — Başkan, 10 kişilik manga, dış dünya
- `/zombi-baskını-başlat` ⭐ — **SADECE RP Owner**, manuel baskın (otomatik döngü kaldırıldı)
- `/gez [bolge]` — **6 saat cooldown**, %50 olumlu/%30 olumsuz/%20 gizemli, 30 olay
- `/anıt` — Şeref listesi ve şehitler

### 💰 Ekonomi & Çevre
- `/maliye-yönetim` — Vergi Memuru paneli
- `/hava-durumu-değiş [mevsim]` — Admin
- `/sunucu-yönetimi` — **SADECE RP Owner**: Kraliyet Desteği, Toplu Enfeksiyon, Hava/Salgın menüleri
- `/haber [kanal]` — Admin, gazete kanalı ayarla

### 📖 Rehber
- `/destek` — Tüm komutların özeti
- `/rehber` — Detaylı dropdown rehber (10 kategori)

## ⚙️ Otomatik Task'lar

| Sıklık | Task | İşlev |
|--------|------|-------|
| 1 saat | Yedekleme | YEDEK_KANAL_ID kanalına JSON yedek gönderir |
| 5 saat | Vergi Tahsilatı | Tüm canlı sakinlerden veba vergisi keser |
| 6 saat | Gazete | Haber kanalına son 6 saatlik olay bülteni |
| 24 saat | Açlık/Susuzluk | Su -10, su 0 ise sağlık -15, sağlık 0 ise ölüm |

## 🐛 Bilinen Hesaplamalar

- **XP/Seviye Atlama**: Otomatik. 100 XP = 1 seviye, her seviye ×25 hurda ödülü. Tüm XP kaynaklarında (üretim, tedavi, sefer, gezi, vb.) `xp_ekle()` fonksiyonu seviye atlamayı otomatik işler.
- **Açlık Sistemi**: 24 saatte -10 su, su 0 olunca -15 sağlık, sağlık 0 olunca ölüm.
- **Veritabanı Sıfırlama**: RP Owner `/kayıt-sil [@üye] EVET` ile tek tek, ya da `siginak_temel_veri.json` dosyası silinerek tamamen sıfırlanabilir.

## 🆕 v4.0 Yenilikler

- ✅ Cogs mimarisine geçiş (modüler, 15+ dosya)
- ✅ `/xp_kazan_test` artık **sadece admin** (suiistimal kapandı)
- ✅ `/gez`'de **6 saat cooldown** + %50/%30/%20 dağılım + 30 olay
- ✅ **Açlık sistemi**: 24 saatte -10 su, ölüm riski
- ✅ `/biyografi-yaz` ile karakter hikayesi
- ✅ Geliştirilmiş `/destek` ve dropdown'lı `/rehber`
- ✅ `/owner-kayıt` ve `/kayıt-sil` (RP Owner only)
- ✅ `/zombi-baskını-başlat` artık **manuel** (otomatik döngü kaldırıldı, sadece RP Owner)
- ✅ `/kutsa` (Rahip kutsama, 3 saat CD)
- ✅ `/nobet` (Muhafız, 4 saat CD, ödül)
- ✅ `/tuket` (envanterden gıda tüket)
- ✅ Pazar katalog bug fix: `/bota-sat`, `/esya-sat`, `/takas-teklif` artık `TAM_PAZAR` kullanıyor (01-45 arası eşyalar da işleniyor)
- ✅ `render.yaml` düzeltildi (`bot.py` → `main.py`)
- ✅ Kanal ID'leri `kanallar.py`'de toplandı, otomatik olaylar doğru kanala gidiyor
- ✅ Keşif sonuçları ilgili RP bölge kanalına da gönderiliyor

## 📞 İletişim

Sahip: HarunAE55 (harunenesavci55@gmail.com)
Repo: https://github.com/HarunAE55/siginak-bot

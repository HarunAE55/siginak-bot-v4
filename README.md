# 🦠 Sığınak Veba RP Bot v5.0

**Discord RPG/RP botu** — 1349 Bavyera Veba teması. Cogs mimarisi ile modüler yapı.

## 🆕 v5.0 Yenilikler

- ✅ **TÜM Türkçe karakterli komut adları ASCII'ye çevrildi** (Discord slash komutları Türkçe karakterleri desteklemiyor)
- ✅ Tüm 62 slash komutu çalışır durumda
- ✅ Cogs mimarisi (15 modül)
- ✅ `/xp_kazan_test` artık sadece admin
- ✅ XP/seviye atlama otomatik (tüm XP kaynaklarında)
- ✅ `/gez` 6 saat cooldown + 30 olay
- ✅ Açlık sistemi (24 saatte -10 su)
- ✅ `/biyografi-yaz`, `/kutsa`, `/nobet`, `/tuket` eklendi
- ✅ `/owner-kayit`, `/kayit-sil` (RP Owner only)
- ✅ `/zombi-baskini-baslat` manuel + RP Owner only
- ✅ Pazar katalog TAM_PAZAR fix
- ✅ Geliştirilmiş `/destek` ve dropdown'lı `/rehber`

## 📦 Kurulum

### Gereksinimler
- Python 3.10+ (3.13+ için `audioop-lts` otomatik eklenir)
- Discord Bot Token
- Render hesabı (ücretsiz tier)

### Yerel Geliştirme

```bash
git clone <repo-url>
cd siginak-bot-v5
pip install -r requirements.txt
export DISCORD_TOKEN=bot_tokenin_buraya
python main.py
```

### Render'a Deploy

1. Kodu GitHub'a pushla
2. Render'da "New → Web Service" oluştur
3. GitHub repo'nu bağla
4. Environment Variables:
   - `DISCORD_TOKEN` = bot token
5. Deploy!

## 📁 Proje Yapısı

```
siginak-bot-v5/
├── main.py                  # Bot giriş noktası
├── veritabani.py            # JSON DB + yardımcı fonksiyonlar
├── kanallar.py              # RP kanal ID'leri
├── keep_alive.py            # Flask keep-alive
├── requirements.txt
├── render.yaml
└── cogs/
    ├── kayit.py             # /kayit /profil /envanter /biyografi-yaz /owner-kayit /kayit-sil /xp_kazan_test
    ├── meslek.py            # /meslek-sec /meslek-yonetim
    ├── pazar.py             # /pazar /satinal /bota-sat /esya-sat /takas-teklif /acik-arttirma-baslat /pey-ver
    ├── savas.py             # /duello /sefer /zombi-baskini-baslat
    ├── kesif.py             # /gez /anit
    ├── yonetim.py           # /secimi-baslat /aday-ol /yonetim /tayin-et /maas-ode /meslek-maas-ode /toplu-maas /yargila
    ├── simya.py             # /deney /laboratuvar-gelistir /doktor-paneli /asi-uret /tedavi-et
    ├── kilise.py            # /rahip-paneli /afaroz-et /buyuk-kilise-cani /kedileri-yok-et /kutsa
    ├── kolluk.py            # /muhafiz-paneli /hucreye-at /hucreden-cikar /karantina-al /karantina-kaldir /sokak-yasagi /savunmayi-guclendir /darbe /nobet
    ├── uretim.py            # /ciftci-paneli /tarla-calis /maden-kaz /orman-kes /tuket
    ├── ambar.py             # /ambar /ambara-bagis /ambardan-al
    ├── maliye.py            # /maliye-yonetim (+ 5h otomatik vergi)
    ├── cevre.py             # /hava-durumu-degis /sunucu-yonetimi
    ├── rehber.py            # /destek /rehber /haber (+ 6h gazete)
    └── sistem.py            # 1h yedekleme + 24h açlık
```

## 🎮 Komut Listesi (62 komut, hepsi ASCII)

### 📝 Kayıt & Profil
- `/kayit` — Sicil kütüğüne kaydol (10-40 yaş)
- `/profil` — Karakter kartın + barlar + biyografi
- `/envanter` — Sırt çantası
- `/biyografi-yaz [metin]` — Karakter hikayesi (max 1000 karakter, 3 günde 1)
- `/owner-kayit [@üye] ...` — RP Owner: başkasını zorla kaydet
- `/kayit-sil [@üye] EVET` — RP Owner: kaydı sil
- `/xp_kazan_test [miktar] [@üye]` — Sadece admin: test XP ekle

### 🛒 Pazar & Ticaret
- `/pazar [kategori]` — 7 kategori
- `/satinal [kod] [adet]` — Mesleğe göre %20 indirim
- `/bota-sat [esya] [adet]` — Kasaya sat
- `/esya-sat [@üye] [esya] [fiyat]` — Oyuncuya satış
- `/takas-teklif [@üye] [verilen] [istenen]` — Eşya takası
- `/acik-arttirma-baslat [esya] [açılış]` — 2 dk açık arttırma
- `/pey-ver [ilan_id] [teklif]` — Teklif ver
- `/tuket [esya]` — Gıda/Medikal tüket

### 🏛️ Siyaset & Yönetim
- `/secimi-baslat` — Sadece admin
- `/aday-ol [vaat]` — 500 hurda depozito
- `/yonetim` — Başkan paneli
- `/tayin-et [@üye] [unvan]` — 5 kadroluk atama
- `/maas-ode [@üye] [miktar]` — Tek sakin maaş
- `/meslek-maas-ode [grup] [miktar]` — Meslek grubuna toplu maaş
- `/toplu-maas [miktar]` — Tüm sakinlere maaş

### ⚖️ Yargı
- `/yargila [@sanık] [suç]` — Başkan mahkeme açar
- `/hucreye-at [@üye]` — Muhafız
- `/hucreden-cikar [@üye]` — Muhafız
- `/sokak-yasagi [durum]` — Başkan
- `/darbe` — İsyancıların başkanı devirme

### ⛪ Kilise & Rahip
- `/rahip-paneli` — Panel
- `/afaroz-et [@üye] [neden]` — Şans düşür
- `/buyuk-kilise-cani` — 3 günde 1, +10 moral
- `/kutsa [@üye]` — 3 saatte 1, enfeksiyon -20, sağlık +15
- `/kedileri-yok-et` ⚠️ — Tüm canlıları enfekte eder

### 💊 Sağlık & Simya
- `/doktor-paneli` — Panel
- `/asi-uret` — 2 tıbbi malzeme → 1 aşı
- `/tedavi-et [@üye]` — 1 aşı ile hasta iyileştir
- `/deney` — Simyacı, %10/%85/%5-15
- `/laboratuvar-gelistir` — Başkan/Baş Simyacı, 500 hurda/seviye (max 3)

### 🛡️ Kolluk & Savunma
- `/muhafiz-paneli` — Panel
- `/karantina-al [@üye]` — Karantinaya al
- `/karantina-kaldir [@üye]` — Karantinadan çıkar
- `/savunmayi-guclendir` — Başkan, 500 hurda +15 tahkimat
- `/nobet` — Muhafız, 4 saat CD, ödül

### 🌾 Üretim & Ambar
- `/ciftci-paneli` — Panel
- `/tarla-calis` — 30 dk CD
- `/maden-kaz` — 30 dk CD
- `/orman-kes` — 30 dk CD
- `/ambar` — Stok listesi
- `/ambara-bagis [esya] [adet]` — Bağış
- `/ambardan-al [esya] [adet]` — Max 5/adet

### ⚔️ Savaş & Keşif
- `/duello [@rakip]` — %20 kalıcı ölüm riski
- `/sefer` — Başkan, 10 kişilik manga
- `/zombi-baskini-baslat` ⭐ — Sadece RP Owner, manuel baskın
- `/gez [bolge]` — 6 saat CD, %50/%30/%20
- `/anit` — Şeref listesi ve şehitler

### 💰 Ekonomi & Çevre
- `/maliye-yonetim` — Vergi Memuru paneli
- `/hava-durumu-degis [mevsim]` — Admin
- `/sunucu-yonetimi` — Sadece RP Owner
- `/haber [kanal]` — Admin, gazete kanalı

### 📖 Rehber
- `/destek` — Tüm komutların özeti
- `/rehber` — Detaylı dropdown rehber

## ⚙️ Otomatik Task'lar

| Sıklık | Task | İşlev |
|--------|------|-------|
| 1 saat | Yedekleme | YEDEK_KANAL_ID kanalına JSON yedek |
| 5 saat | Vergi Tahsilatı | Tüm canlı sakinlerden veba vergisi |
| 6 saat | Gazete | Haber kanalına son 6 saatlik olay bülteni |
| 24 saat | Açlık/Susuzluk | Su -10, su 0 ise sağlık -15, sağlık 0 ise ölüm |

## 🚀 Önemli Not

Eğer Discord'da eski Türkçe karakterli komutlar (/kayıt, /anıt, vb.) hala görünüyorsa:
1. Botu sunucudan at
2. Discord Developer Portal → OAuth2 → URL Generator ile yeni URL al
3. Tekrar sunucuya ekle

Bu, Discord'un komut cache'ini temizler.

## 📞 İletişim

Sahip: HarunAE55
Repo: https://github.com/HarunAE55/siginak-bot

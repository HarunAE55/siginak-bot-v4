# 🦠 Sığınak Veba RP Bot v5.1

**Discord RPG/RP botu** — 1349 Bavyera Veba teması. Cogs mimarisi, slash + v. prefix desteği.

## 🆕 v5.1 Yenilikler

- ✅ **v. prefix komut desteği eklendi!** Artık hem `/kayit` hem `v.kayit` çalışır
- ✅ **Discord cache temizleme** — Bot açılışta eski komutları Discord'dan silip yeniden yükler (command not found fix)
- ✅ **`/db-sifirla` admin komutu** — Veritabanını tek komutla sıfırla
- ✅ **`v.db-sifirla EVET` prefix versiyonu** da eklendi
- ✅ Tüm Türkçe karakterli komut adları ASCII'ye çevrildi (v5'ten)
- ✅ 63+ slash komutu + 17+ prefix komutu

## ⚠️ ÖNEMLİ: Message Content Intent

v. prefix komutlarının çalışması için Discord Developer Portal'da **Message Content Intent** açılmalı:

1. https://discord.com/developers/applications → botun
2. Sol menüden **"Bot"**
3. Aşağı in, **"Privileged Gateway Intents"** bölümünü bul
4. Şu 3 intent'i de **AÇIK** yap:
   - ✅ PRESENCE INTENT
   - ✅ SERVER MEMBERS INTENT
   - ✅ MESSAGE CONTENT INTENT ← En önemlisi!
5. **"Save Changes"** tıkla
6. Botu yeniden başlat (Render → Manual Restart)

⚠️ Message Content Intent kapalıysa `v.` prefix komutları çalışmaz, sadece `/` slash komutları çalışır.

## 📦 Kurulum

### Gereksinimler
- Python 3.10+ (3.13+ için `audioop-lts` otomatik eklenir)
- Discord Bot Token
- Render hesabı (ücretsiz tier)

### Yerel Geliştirme

```bash
git clone <repo-url>
cd siginak-bot-v5.1
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
siginak-bot-v5.1/
├── main.py                  # Bot giriş noktası + cache temizleme
├── veritabani.py            # JSON DB + yardımcı fonksiyonlar
├── kanallar.py              # RP kanal ID'leri
├── keep_alive.py            # Flask keep-alive
├── requirements.txt
├── render.yaml
└── cogs/
    ├── kayit.py             # /kayit /profil /envanter /biyografi-yaz /owner-kayit /kayit-sil /db-sifirla /xp_kazan_test
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
    ├── sistem.py            # 1h yedekleme + 24h açlık
    └── prefix.py            # v. prefix komutları (17 komut)
```

## 🎮 Komut Listesi

### Slash Komutları (63 adet)

#### 📝 Kayıt & Profil
- `/kayit` — Sicil kütüğüne kaydol (10-40 yaş)
- `/profil` — Karakter kartın + barlar + biyografi
- `/envanter` — Sırt çantası
- `/biyografi-yaz [metin]` — Karakter hikayesi (max 1000 karakter, 3 günde 1)
- `/owner-kayit [@üye] ...` — RP Owner: başkasını zorla kaydet
- `/kayit-sil [@üye] EVET` — RP Owner: kaydı sil
- `/db-sifirla EVET` — Admin: veritabanını tamamen sıfırla
- `/xp_kazan_test [miktar] [@üye]` — Sadece admin: test XP ekle

#### 🛒 Pazar & Ticaret
- `/pazar [kategori]` — 7 kategori
- `/satinal [kod] [adet]` — Mesleğe göre %20 indirim
- `/bota-sat [esya] [adet]` — Kasaya sat
- `/esya-sat [@üye] [esya] [fiyat]` — Oyuncuya satış
- `/takas-teklif [@üye] [verilen] [istenen]` — Eşya takası
- `/acik-arttirma-baslat [esya] [açılış]` — 2 dk açık arttırma
- `/pey-ver [ilan_id] [teklif]` — Teklif ver
- `/tuket [esya]` — Gıda/Medikal tüket

#### 🏛️ Siyaset & Yönetim
- `/secimi-baslat` — Sadece admin
- `/aday-ol [vaat]` — 500 hurda depozito
- `/yonetim` — Başkan paneli
- `/tayin-et [@üye] [unvan]` — 5 kadroluk atama
- `/maas-ode [@üye] [miktar]` — Tek sakin maaş
- `/meslek-maas-ode [grup] [miktar]` — Meslek grubuna toplu maaş
- `/toplu-maas [miktar]` — Tüm sakinlere maaş

#### ⚖️ Yargı
- `/yargila [@sanık] [suç]` — Başkan mahkeme açar
- `/hucreye-at [@üye]` — Muhafız
- `/hucreden-cikar [@üye]` — Muhafız
- `/sokak-yasagi [durum]` — Başkan
- `/darbe` — İsyancıların başkanı devirme

#### ⛪ Kilise & Rahip
- `/rahip-paneli` — Panel
- `/afaroz-et [@üye] [neden]` — Şans düşür
- `/buyuk-kilise-cani` — 3 günde 1, +10 moral
- `/kutsa [@üye]` — 3 saatte 1, enfeksiyon -20, sağlık +15
- `/kedileri-yok-et` ⚠️ — Tüm canlıları enfekte eder

#### 💊 Sağlık & Simya
- `/doktor-paneli` — Panel
- `/asi-uret` — 2 tıbbi malzeme → 1 aşı
- `/tedavi-et [@üye]` — 1 aşı ile hasta iyileştir
- `/deney` — Simyacı, %10/%85/%5-15
- `/laboratuvar-gelistir` — Başkan/Baş Simyacı, 500 hurda/seviye (max 3)

#### 🛡️ Kolluk & Savunma
- `/muhafiz-paneli` — Panel
- `/karantina-al [@üye]` — Karantinaya al
- `/karantina-kaldir [@üye]` — Karantinadan çıkar
- `/savunmayi-guclendir` — Başkan, 500 hurda +15 tahkimat
- `/nobet` — Muhafız, 4 saat CD, ödül

#### 🌾 Üretim & Ambar
- `/ciftci-paneli` — Panel
- `/tarla-calis` — 30 dk CD
- `/maden-kaz` — 30 dk CD
- `/orman-kes` — 30 dk CD
- `/ambar` — Stok listesi
- `/ambara-bagis [esya] [adet]` — Bağış
- `/ambardan-al [esya] [adet]` — Max 5/adet

#### ⚔️ Savaş & Keşif
- `/duello [@rakip]` — %20 kalıcı ölüm riski
- `/sefer` — Başkan, 10 kişilik manga
- `/zombi-baskini-baslat` ⭐ — Sadece RP Owner, manuel baskın
- `/gez [bolge]` — 6 saat CD, %50/%30/%20
- `/anit` — Şeref listesi ve şehitler

#### 💰 Ekonomi & Çevre
- `/maliye-yonetim` — Vergi Memuru paneli
- `/hava-durumu-degis [mevsim]` — Admin
- `/sunucu-yonetimi` — Sadece RP Owner
- `/haber [kanal]` — Admin, gazete kanalı

#### 📖 Rehber
- `/destek` — Tüm komutların özeti
- `/rehber` — Detaylı dropdown rehber

---

### Prefix Komutları (v. ile başlayan, 17 adet)

⚠️ **Message Content Intent açılmalı!** (Yukarıdaki talimata bak)

#### Kayıt & Profil
- `v.kayit isim soyisim yaş memleket` — Kayıt ol
  - Örnek: `v.kayit Harun Enes 25 Bavyera`
- `v.profil` — Karakter kartın
- `v.envanter` — Sırt çantası
- `v.biyografi-yaz [metin]` — Biyografi yaz
- `v.meslek-sec [meslek]` — Meslek seç
- `v.meslek-yonetim` — Meslek paneli

#### Pazar & Ticaret
- `v.pazar [kategori]` — Pazar gez (Silah, Zırh, Medikal, Gıda, Hammadde, Teknoloji, Mistik)
- `v.satinal [kod] [adet]` — Eşya al
- `v.bota-sat [esya] [adet]` — Kasaya sat
- `v.tuket [esya]` — Gıda tüket

#### Keşif & Anıt
- `v.gez [bolge]` — Dış dünyaya keşfe çık
  - Bölgeler: Terkedilmiş Köy, Veba Mezarlığı, Karanlık Koruluk, Yıkık Kilise, Dehliz Labirenti, Zombi Tarlası
- `v.anit` — Şeref listesi ve şehitler

#### Üretim & Ambar
- `v.ciftci-paneli` — Üretici paneli
- `v.tarla-calis` — Tarlada çalış (30 dk CD)
- `v.maden-kaz` — Madende kaz (30 dk CD)
- `v.orman-kes` — Ormanda odun kes (30 dk CD)
- `v.ambar` — Köy ambarı stokları

#### Rehber
- `v.destek` — Tüm komutların özeti
- `v.rehber` — Hızlı yardım

#### Admin
- `v.db-sifirla EVET` — Veritabanını sıfırla (sadece admin)

## ⚙️ Otomatik Task'lar

| Sıklık | Task | İşlev |
|--------|------|-------|
| 1 saat | Yedekleme | YEDEK_KANAL_ID kanalına JSON yedek |
| 5 saat | Vergi Tahsilatı | Tüm canlı sakinlerden veba vergisi |
| 6 saat | Gazete | Haber kanalına son 6 saatlik olay bülteni |
| 24 saat | Açlık/Susuzluk | Su -10, su 0 ise sağlık -15, sağlık 0 ise ölüm |

## 🗄️ Veritabanı Sıfırlama

### Yöntem 1: Slash Komutu (Sadece Admin)
```
/db-sifirla onay: EVET
```

### Yöntem 2: Prefix Komutu (Sadece Admin)
```
v.db-sifirla EVET
```

### Yöntem 3: Render Shell (Manuel)
1. Render dashboard → servisin → **"Shell"** sekmesi
2. Şu komutu çalıştır:
   ```bash
   rm -f siginak_temel_veri.json siginak_temel_veri.json.tmp
   ```
3. Render'dan **"Manual Restart"** yap

⚠️ **Önemli:** Yedekleme kanalındaki eski yedekleri de silmezsen, bot açılışta onları geri yükler!
1. Discord'da `yedekleme` kanalına git
2. Tüm `yedek_*.json` mesajlarını sil
3. Sonra botu yeniden başlat

## 🚀 Deploy Adımları

1. Bu kodu GitHub'a pushla
2. Render'da "New → Web Service" oluştur, GitHub'ı bağla
3. Environment Variables:
   - `DISCORD_TOKEN` = bot token
   - `YEDEK_KANAL_ID` = 1516177967288422400 (opsiyonel, default zaten)
4. Deploy!
5. UptimeRobot'a `https://your-app.onrender.com/health` URL'ini ekle, 5 dk'da bir ping atsın

## 📞 İletişim

Sahip: HarunAE55
Repo: https://github.com/HarunAE55/siginak-bot

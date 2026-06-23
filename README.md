# 🦠 Sığınak Veba RP Bot v5.5

**Discord RPG/RP botu** — 1349 Bavyera Veba teması. Cogs mimarisi, slash + v. prefix desteği.

## 🆕 v5.5 Yenilikler

- ✅ **Yeni roller eklendi**: Administrator, Admin, Yetkili Ekip, Özel Üye, Moderatör, Kıdemli Moderatör
- ✅ **`/kavga`** komutu eklendi — Ölümcül olmayan düello (RP kavgaları için)
- ✅ **Tüccar ticaret sistemi** — `/tuccar-paneli`, `/tuccar-al`, `/tuccar-sat` (ambardan ucuz al, pahalı sat = kar!)
- ✅ **`/muhafiz-donanim`** — Muhafızlara defans ekipmanları (göğüslük, kalkan, zırh, plaka)
- ✅ **`/akçe-gonder`** — Oyuncudan oyuncuya akçe transferi
- ✅ **`/kaynak-ekle`** — Admin komutu (odun, kömür, erzak, akçe ekleme)
- ✅ **`/kullan`** komutu düzeltildi (artık kendi logic'i var, /tuket ile aynı)
- ✅ **`/kutsa`** KeyError hatası düzeltildi (rahip kayıtlı mı kontrolü)
- ✅ **Seçim süreleri değişti**: 30 dk adaylık + 60 dk oylama = 1.5 saat
- ✅ **`/tayin-et`** komutuna Baş Doktor eklendi
- ✅ **Zombi baskını** artık Surlar kanalına gidiyor (Salgın değil)
- ✅ **`/gez`** 25 RP bölgesi (Discord limitine uygun)
- ✅ **Admin komutları** artık `Yetkili Ekip` rolü tarafından da kullanılabilir
- ✅ **Bot watching durumu** her saat yedeklemede güncelleniyor (aktif sakin sayısı)
- ✅ Yeni kanallar: Görüşme İsteği, Başkanın Makamı, Mahkeme Salonu
- ✅ 71 slash komutu + 20+ prefix komutu

## ⚠️ ÖNEMLİ: Message Content Intent

`v.` prefix komutlarının çalışması için Discord Developer Portal'da **Message Content Intent** açılmalı:

1. https://discord.com/developers/applications → botun
2. Sol menüden **"Bot"**
3. Aşağı in, **"Privileged Gateway Intents"** bölümünü bul
4. Şu 3 intent'i de **AÇIK** yap:
   - ✅ PRESENCE INTENT
   - ✅ SERVER MEMBERS INTENT
   - ✅ **MESSAGE CONTENT INTENT** ← En önemlisi!
5. **"Save Changes"** tıkla
6. Botu yeniden başlat (Render → Manual Restart)

## 📦 Kurulum

### Gereksinimler
- Python 3.10+ (3.13+ için `audioop-lts` otomatik eklenir)
- Discord Bot Token
- Render hesabı (ücretsiz tier)

### Yerel Geliştirme

```bash
git clone <repo-url>
cd siginak-bot-v5.5
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
siginak-bot-v5.5/
├── main.py                  # Bot giriş noktası + cache temizleme
├── veritabani.py            # JSON DB + yardımcı fonksiyonlar + rol ID'leri
├── kanallar.py              # RP kanal ID'leri
├── keep_alive.py            # Flask keep-alive
├── requirements.txt
├── render.yaml
└── cogs/
    ├── kayit.py             # /kayit /profil /envanter /biyografi-yaz /akçe-gonder /kaynak-ekle /kullan
    ├── meslek.py            # /meslek-sec /meslek-yonetim
    ├── pazar.py             # /pazar /satinal /bota-sat /esya-sat /takas-teklif /acik-arttirma-baslat /pey-ver /tuket
    ├── savas.py             # /duello /kavga /sefer /zombi-baskini-baslat
    ├── kesif.py             # /gez (25 bölge) /anit
    ├── yonetim.py           # /secimi-baslat /aday-ol /yonetim /tayin-et /maas-ode /meslek-maas-ode /toplu-maas /yargila
    ├── simya.py             # /deney /laboratuvar-gelistir /doktor-paneli /asi-uret /tedavi-et
    ├── kilise.py            # /rahip-paneli /afaroz-et /buyuk-kilise-cani /kedileri-yok-et /kutsa
    ├── kolluk.py            # /muhafiz-paneli /hucreye-at /hucreden-cikar /karantina-al /karantina-kaldir /sokak-yasagi /savunmayi-guclendir /darbe /nobet
    ├── uretim.py            # /ciftci-paneli /tarla-calis /maden-kaz /orman-kes /tuket /kullan /tuccar-paneli /tuccar-al /tuccar-sat /muhafiz-donanim
    ├── ambar.py             # /ambar /ambara-bagis /ambardan-al
    ├── maliye.py            # /maliye-yonetim (+ 5h otomatik vergi)
    ├── cevre.py             # /hava-durumu-degis /sunucu-yonetimi
    ├── rehber.py            # /destek /rehber /haber (+ 6h gazete)
    ├── sistem.py            # 1h yedekleme + 24h açlık
    └── prefix.py            # v. prefix komutları
```

## 🎮 Komut Listesi (71 slash + 20+ prefix = 91+ komut)

### 📝 Kayıt & Profil
- `/kayit` — Sicil kütüğüne kaydol (10-40 yaş)
- `/profil` — Karakter kartın + barlar + biyografi
- `/envanter` — Sırt çantası
- `/biyografi-yaz [metin]` — Karakter hikayesi (max 1000 karakter, 3 günde 1)
- `/akçe-gonder [@üye] [miktar]` — Oyuncuya akçe gönder
- `/owner-kayit [@üye] ...` — RP Owner: başkasını zorla kaydet
- `/kayit-sil [@üye] EVET` — RP Owner: kaydı sil
- `/db-sifirla EVET` — Yetkili Ekip: veritabanını sıfırla
- `/kaynak-ekle [kaynak] [miktar]` — Yetkili Ekip: kaynak ekle (odun, kömür, akçe)
- `/xp_kazan_test [miktar] [@üye]` — Yetkili Ekip: test XP ekle

### 🛒 Pazar & Ticaret
- `/pazar [kategori]` — 7 kategori (Silah, Zırh, Medikal, Gıda, Hammadde, Teknoloji, Mistik)
- `/satinal [kod] [adet]` — Mesleğe göre %20 indirim
- `/bota-sat [esya] [adet]` — Kasaya sat
- `/esya-sat [@üye] [esya] [fiyat]` — Oyuncuya satış
- `/takas-teklif [@üye] [verilen] [istenen]` — Eşya takası
- `/acik-arttirma-baslat [esya] [açılış]` — 2 dk açık arttırma
- `/pey-ver [ilan_id] [teklif]` — Teklif ver
- `/tuket [esya]` veya `/kullan [esya]` — Gıda/Medikal tüket

### 🏛️ Siyaset & Yönetim
- `/secimi-baslat` — Yetkili Ekip (30 dk adaylık + 60 dk oylama)
- `/aday-ol [vaat]` — 500 akçe depozito
- `/yonetim` — Başkan paneli
- `/tayin-et [@üye] [unvan]` — 6 kadroluk atama (Yardımcı, Müfettiş, Komutan, Baş Simyacı, **Baş Doktor**, Rahip)
- `/maas-ode [@üye] [miktar]` — Tek sakin maaş
- `/meslek-maas-ode [grup] [miktar]` — Meslek grubuna toplu maaş
- `/toplu-maas [miktar]` — Tüm sakinlere maaş

### ⚖️ Yargı
- `/yargila [@sanık] [suç]` — Başkan mahkeme açar
- `/hucreye-at [@üye]` — Muhafız
- `/hucreden-cikar [@üye]` — Muhafız
- `/sokak-yasagi [durum]` — Başkan
- `/darbe` — İsyancıların başkanı devirme

### ⚔️ Savaş & Keşif
- `/duello [@rakip]` — %20 kalıcı ölüm riski (butonlu, tur tabanlı)
- `/kavga [@rakip]` — Ölümcül olmayan düello (RP kavgası, kimse ölmez)
- `/sefer` — Başkan, 10 kişilik manga
- `/zombi-baskini-baslat` — Sadece RP Owner (Surlar kanalına)
- `/gez [bolge]` — 6 saat CD, 25 RP bölgesi
- `/anit` — Şeref listesi ve şehitler

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
- `/laboratuvar-gelistir` — Başkan/Baş Simyacı, 500 akçe/seviye (max 3)

### 🛡️ Kolluk & Savunma
- `/muhafiz-paneli` — Panel
- `/karantina-al [@üye]` — Karantinaya al
- `/karantina-kaldir [@üye]` — Karantinadan çıkar
- `/savunmayi-guclendir` — Başkan, 500 akçe +15 tahkimat
- `/nobet` — Muhafız, 4 saat CD, ödül
- `/muhafiz-donanim [esya]` — Defans ekipmanı al (göğüslük, kalkan, zırh, plaka)

### 🌾 Üretim & Ambar
- `/ciftci-paneli` — Panel
- `/tarla-calis` — 30 dk CD
- `/maden-kaz` — 30 dk CD
- `/orman-kes` — 30 dk CD
- `/ambar` — Stok listesi
- `/ambara-bagis [esya] [adet]` — Bağış
- `/ambardan-al [esya] [adet]` — Max 5/adet

### 💰 Tüccar (Yeni!)
- `/tuccar-paneli` — Tüccar ticaret paneli
- `/tuccar-al [esya] [adet]` — Ambardan ucuz al (20h/15h/25h/50h)
- `/tuccar-sat [esya] [adet]` — Ambara pahalı sat (35h/25h/40h/80h) — **Kar!**

### 💰 Ekonomi & Çevre
- `/maliye-yonetim` — Vergi Memuru paneli
- `/hava-durumu-degis [mevsim]` — Yetkili Ekip
- `/sunucu-yonetimi` — Sadece RP Owner/Admin/Administrator
- `/haber [kanal]` — Yetkili Ekip, gazete kanalı

### 📖 Rehber
- `/destek` — Dropdown kategori menüsü
- `/rehber` — Detaylı dropdown rehber

## ⚙️ Otomatik Task'lar

| Sıklık | Task | İşlev |
|--------|------|-------|
| 1 saat | Yedekleme + Watching Güncelleme | YEDEK_KANAL_ID kanalına JSON yedek + bot durumu güncelle (aktif sakin sayısı) |
| 5 saat | Vergi Tahsilatı | Tüm canlı sakinlerden veba vergisi |
| 6 saat | Gazete | Haber kanalına son 6 saatlik olay bülteni |
| 24 saat | Açlık/Susuzluk | Su -10, su 0 ise sağlık -15, sağlık 0 ise ölüm |

## 🗄️ Veritabanı Sıfırlama

### Yöntem 1: Slash Komutu (Yetkili Ekip)
```
/db-sifirla onay: EVET
```

### Yöntem 2: Prefix Komutu (Yetkili Ekip)
```
v.db-sifirla EVET
```

### Yöntem 3: Render Shell (Manuel)
1. Render dashboard → servisin → **"Shell"** sekmesi
2. `rm -f siginak_temel_veri.json siginak_temel_veri.json.tmp`
3. Render'dan **"Manual Restart"** yap

⚠️ Yedekleme kanalındaki eski yedekleri de sil!

## 🛡️ Yetki Sistemi

### `admin_mi()` fonksiyonu (Yetkili Ekip):
- RP Owner
- Administrator
- Admin
- Yetkili Ekip
- Discord Administrator yetkisi olanlar

### `rp_owner_mi()` fonksiyonu:
- RP Owner
- Administrator
- Admin

### Yetkili Ekip komutları:
- `/db-sifirla`, `/xp_kazan_test`, `/secimi-baslat`, `/hava-durumu-degis`, `/haber`, `/kaynak-ekle`

### RP Owner komutları:
- `/owner-kayit`, `/kayit-sil`, `/sunucu-yonetimi`, `/zombi-baskini-baslat`

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

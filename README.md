# 🦠 Sığınak Veba RP Bot v5.9.1

**Discord RPG/RP botu** — 1349 Bavyera Veba teması. Cogs mimarisi, slash + v. prefix desteği.

> **v5.9.1 — Yetkili Ekip Yetki Düzeltmesi**
> v5.9 üzerine küçük bir düzeltme: `has_permissions(administrator=True)` decorator'ı kaldırıldı, böylece Yönetici Ekip rolü olanlar da admin komutlarını kullanabilir.

---

## 🆕 v5.9.1 Yenilikler

### 🔓 Yetki Düzeltmesi: Yönetici Ekip Artık Tüm Admin Komutlarını Kullanabilir
- ✅ **`/secimi-baslat`** — `@app_commands.checks.has_permissions(administrator=True)` decorator'ı kaldırıldı. Artık sadece `admin_mi()` ile kontrol ediliyor, yani **Yönetici Ekip rolü** olanlar da başlatbilir.
- ✅ **`v.db-sifirla`** — `@commands.has_permissions(administrator=True)` decorator'ı kaldırıldı. Artık Yönetici Ekip rolü olanlar da kullanabilir.
- ✅ `db_sifirla_error` handler güncellendi (MissingPermissions artık gelmez).

### 📋 `admin_mi()` Fonksiyonu Kapsamı (Hatırlatma)
Şu rollerden herhangi birine sahip olanlar tüm admin komutlarını kullanabilir:
- ♔ **RP Owner** (1470544130559049921)
- 👑 **Administrator** (1518268192395497544)
- 🛡️ **Admin** (1518268274687873145)
- 🎩 **Yetkili Ekip** (1518378716533882921) ← v5.9.1 ile tam erişim
- Discord Administrator yetkisi olanlar

### 🎯 Etkilenen Komutlar (Tümü Artık Yönetici Ekip Kullanabilir)
- `/db-sifirla` ve `v.db-sifirla`
- `/xp_kazan_test` ve `v.xp_kazan_test`
- `/secimi-baslat` ve `v.secimi-baslat` ← v5.9.1 düzeltmesi
- `/hava-durumu-degis` ve `v.hava-durumu-degis`
- `/haber` ve `v.haber`
- `/kaynak-ekle` ve `v.kaynak-ekle`
- `/owner-kayit` ve `v.owner-kayit`
- `/kayit-sil` ve `v.kayit-sil`
- `/sunucu-yonetimi` ve `v.sunucu-yonetimi`
- `/zombi-baskini-baslat` ve `v.zombi-baskini-baslat`

---

## 📜 v5.9 Yenilikler & Düzeltmeler (önceki sürüm)

### 🐛 Kritik Bug Fix'ler
- ✅ **`/tayin-et` Baş Doktor hatası düzeltildi** — Artık "Baş Doktor" atanabiliyor (TAYIN_KADROLARI'na eksik entry eklendi)
- ✅ **Gazete "0 Akçe" gösterimi düzeltildi** — `kasa_hurda` (eski) → `KASA_AKÇE_PLACEHOLDER` (yeni) migration tamamlandı
- ✅ **`/gez` XP seviye atlama çalışmıyordu** — `sakin.get("id","")` her zaman `""` döndürüyordu, artık `u_id` ile çağrılıyor
- ✅ **`/anit` şeref listesi yanlış sıralıyordu** — XP yerine `seviye*100+xp` ile sıralanıyor (gerçek deneyim)
- ✅ **Enfeksiyon barı yanıltıcıydı** — Yüksek enfeksiyon kırmızı/sarı, düşük yeşil gösteriliyor (`bar_olustur(negatif=True)`)
- ✅ **`/kedileri-yok-et` "Sağlıklı" sakinleri pas geçiyordu** — Artık hem "Canlı" hem "Sağlıklı" durumu enfekte oluyor
- ✅ **`/sunucu-yonetimi` mevsim seçimi Türkçe karakter hatası** — `Ilkbahar`/`Kis` → `İlkbahar`/`Kış` (orman_kes/tarla_calis ile uyumlu)
- ✅ **Açlık task'ında "Öldü" yazıyordu** — Türkçe karakter "Ölü" olarak düzeltildi

### 🎯 Yeni Özellik: Prefix = Slash Birebir Aynı Çıktı
- ✅ **TÜM prefix (`v.`) komutları slash (`/`) komutlarıyla AYNI embed'i, AYNI renk kodlarını, AYNI metinleri veriyor**
- ✅ Aynı footer, aynı başlık, aynı açıklama formatı
- ✅ Türkçe alias'lar korundu (`v.kayıt`, `v.anıt`, `v.yargıla`, vb.)
- ✅ `v.pazar` artık slash gibi dropdown menü gösteriyor (kategori verilmezse)
- ✅ `v.destek` ve `v.rehber` artık slash ile aynı dropdown menüyü kullanıyor
- ✅ Prefix komut hata yakalama eklendi (`on_command_error`)

### 📌 Sürüm Numaraları Güncellendi
- ✅ main.py docstring: `v5.7` → `v5.9`
- ✅ keep_alive.py `/health` endpoint: `5.7` → `5.9`
- ✅ README.md başlık: `v5.7` → `v5.9`
- ✅ Tüm footer'lar (`embed.set_footer`): `v5.7` → `v5.9`
- ✅ Bot durumu (watching): sürüm bilgisi eklendi
- ✅ Rehber dropdown menü içerikleri güncellendi

### 🔧 Teknik İyileştirmeler
- ✅ `veritabani.py`'a `asyncio.Lock` altyapısı eklendi (DB race condition koruması için)
- ✅ `kesif.py` `_bolge_kanal_bul` artık `kanallar.py`'deki importları kullanıyor (duplicate ID yok)
- ✅ `sakin_olustur_defaults`'a `son_kutsama` alanı eklendi (eksik olduğu için KeyError riski vardı)
- ✅ Rehber gazete bültenine enfekte sakin sayısı detayı eklendi

---

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

---

## 📦 Kurulum

### Gereksinimler
- Python 3.10+ (3.13+ için `audioop-lts` otomatik eklenir)
- Discord Bot Token
- Render hesabı (ücretsiz tier)

### Yerel Geliştirme

```bash
git clone <repo-url>
cd siginak-bot-v5.9
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
   - `YEDEK_KANAL_ID` = 1516177967288422400 (opsiyonel, default zaten)
5. Deploy!
6. UptimeRobot'a `https://your-app.onrender.com/health` URL'ini ekle, 5 dk'da bir ping atsın

---

## 📁 Proje Yapısı

```
siginak-bot-v5.9/
├── main.py                  # Bot giriş noktası (v5.9)
├── veritabani.py            # JSON DB + yardımcı fonksiyonlar + rol ID'leri
├── kanallar.py              # RP kanal ID'leri
├── keep_alive.py            # Flask keep-alive (v5.9)
├── requirements.txt
├── render.yaml
└── cogs/
    ├── kayit.py             # /kayit /profil /envanter /biyografi-yaz /akçe-gonder /kaynak-ekle /kullan
    ├── meslek.py            # /meslek-sec /meslek-yonetim
    ├── pazar.py             # /pazar /satinal /bota-sat /esya-sat /takas-teklif /acik-arttirma-baslat /pey-ver /tuket
    ├── savas.py             # /duello /kavga /sefer /zombi-baskini-baslat
    ├── kesif.py             # /gez (25 bölge) /anit (v5.9: XP fix, sıralama fix)
    ├── yonetim.py           # /secimi-baslat /aday-ol /yonetim /tayin-et /maas-ode /meslek-maas-ode /toplu-maas /yargila
    ├── simya.py             # /deney /laboratuvar-gelistir /doktor-paneli /asi-uret /tedavi-et
    ├── kilise.py            # /rahip-paneli /afaroz-et /buyuk-kilise-cani /kedileri-yok-et /kutsa
    ├── kolluk.py            # /muhafiz-paneli /hucreye-at /hucreden-cikar /karantina-al /karantina-kaldir /sokak-yasagi /savunmayi-guclendir /darbe /nobet
    ├── uretim.py            # /ciftci-paneli /tarla-calis /maden-kaz /orman-kes /tuket /kullan /tuccar-paneli /tuccar-al /tuccar-sat /muhafiz-donanim
    ├── ambar.py             # /ambar /ambara-bagis /ambardan-al
    ├── maliye.py            # /maliye-yonetim (+ 5h otomatik vergi)
    ├── cevre.py             # /hava-durumu-degis /sunucu-yonetimi (v5.9: Türkçe karakter fix)
    ├── rehber.py            # /destek /rehber /haber (+ 6h gazete) (v5.9: kasa_hurda fix)
    ├── sistem.py            # 1h yedekleme + 24h açlık (v5.9: "Ölü" durum fix)
    └── prefix.py            # v. prefix komutları (v5.9: slash ile BİREBİR AYNI çıktı)
```

---

## 🎮 Komut Listesi (71 slash + 35+ prefix = 106+ komut)

> **💡 v5.9 YENİ:** Tüm prefix komutları slash ile **birebir aynı çıktıyı** verir!

### 📝 Kayıt & Profil
| Slash | Prefix | Açıklama |
|-------|--------|----------|
| `/kayit` | `v.kayit` veya `v.kayıt` | Sicil kütüğüne kaydol (10-40 yaş) |
| `/profil` | `v.profil` | Karakter kartın + barlar + biyografi |
| `/envanter` | `v.envanter` | Sırt çantan |
| `/biyografi-yaz` | `v.biyografi-yaz` | Karakter hikayesi (max 1000 karakter, 3 günde 1) |
| `/akçe-gonder` | `v.akçe-gonder` veya `v.akce-gonder` | Oyuncuya akçe gönder |
| `/owner-kayit` | `v.owner-kayit` veya `v.owner-kayıt` | Yetkili Ekip: başkasını zorla kaydet |
| `/kayit-sil` | `v.kayit-sil` veya `v.kayıt-sil` | Yetkili Ekip: kaydı sil |
| `/db-sifirla` | `v.db-sifirla` | Yetkili Ekip: veritabanını sıfırla |
| `/kaynak-ekle` | `v.kaynak-ekle` | Yetkili Ekip: kaynak ekle |
| `/xp_kazan_test` | `v.xp_kazan_test` | Yetkili Ekip: test XP |

### 🛒 Pazar & Ticaret
| Slash | Prefix | Açıklama |
|-------|--------|----------|
| `/pazar` | `v.pazar` (dropdown!) | 7 kategori (Silah, Zırh, Medikal, Gıda, Hammadde, Teknoloji, Mistik) |
| `/satinal` | `v.satinal` | Mesleğe göre %20 indirim |
| `/bota-sat` | `v.bota-sat` | Kasaya sat |
| `/esya-sat` | `v.esya-sat` | Oyuncuya satış |
| `/takas-teklif` | `v.takas-teklif` | Eşya takası |
| `/acik-arttirma-baslat` | `v.acik-arttirma-baslat` | 2 dk açık artırma |
| `/pey-ver` | `v.pey-ver` | Teklif ver |
| `/tuket` veya `/kullan` | `v.tuket` veya `v.kullan` | Gıda/Medikal tüket |

### 🏛️ Siyaset & Yönetim
| Slash | Prefix | Açıklama |
|-------|--------|----------|
| `/secimi-baslat` | `v.secimi-baslat` | Yetkili Ekip (30 dk adaylık + 60 dk oylama = 1.5 saat) |
| `/aday-ol` | `v.aday-ol` | 500 akçe depozito |
| `/yonetim` | `v.yonetim` | Başkan paneli |
| `/tayin-et` | `v.tayin-et` | 6 kadroluk atama (v5.9: Baş Doktor dahil!) |
| `/maas-ode` | `v.maas-ode` | Tek sakin maaş |
| `/meslek-maas-ode` | `v.meslek-maas-ode` veya `v.meslek-maaş-öde` | Meslek grubuna toplu maaş |
| `/toplu-maas` | `v.toplu-maas` veya `v.toplu-maaş` | Tüm sakinlere maaş |

### ⚖️ Yargı
| Slash | Prefix | Açıklama |
|-------|--------|----------|
| `/yargila` | `v.yargila` veya `v.yargıla` | Başkan mahkeme açar |
| `/hucreye-at` | `v.hucreye-at` | Muhafız |
| `/hucreden-cikar` | `v.hucreden-cikar` veya `v.hucreden-çıkar` | Muhafız |
| `/sokak-yasagi` | `v.sokak-yasagi` | Başkan |
| `/darbe` | `v.darbe` | İsyancıların başkanı devirme |

### ⚔️ Savaş & Keşif
| Slash | Prefix | Açıklama |
|-------|--------|----------|
| `/duello` | `v.duello` | %20 kalıcı ölüm riski (butonlu, tur tabanlı) |
| `/kavga` | `v.kavga` | Ölümcül olmayan düello (RP kavgası) |
| `/sefer` | `v.sefer` | Başkan, 10 kişilik manga |
| `/zombi-baskini-baslat` | `v.zombi-baskini-baslat` veya `v.zombi-baskını-başlat` | Yetkili Ekip (Surlar kanalına) |
| `/gez` | `v.gez` | 6 saat CD, 25 RP bölgesi (v5.9: XP fix) |
| `/anit` | `v.anit` veya `v.anıt` | Şeref listesi ve şehitler (v5.9: sıralama fix) |

### ⛪ Kilise & Rahip
| Slash | Prefix | Açıklama |
|-------|--------|----------|
| `/rahip-paneli` | `v.rahip-paneli` | Panel |
| `/afaroz-et` | `v.afaroz-et` | Şans düşür |
| `/buyuk-kilise-cani` | `v.buyuk-kilise-cani` | 3 günde 1, +10 moral |
| `/kutsa` | `v.kutsa` | 3 saatte 1, enfeksiyon -20, sağlık +15 |
| `/kedileri-yok-et` | `v.kedileri-yok-et` | Tüm canlıları enfekte eder (v5.9: "Sağlıklı" dahil) |

### 💊 Sağlık & Simya
| Slash | Prefix | Açıklama |
|-------|--------|----------|
| `/doktor-paneli` | `v.doktor-paneli` | Panel |
| `/asi-uret` | `v.asi-uret` | 2 tıbbi malzeme → 1 aşı |
| `/tedavi-et` | `v.tedavi-et` | 1 aşı ile hasta iyileştir |
| `/deney` | `v.deney` | Simyacı, %10/%85/%5-15 |
| `/laboratuvar-gelistir` | `v.laboratuvar-gelistir` veya `v.laboratuvar-geliştir` | Başkan/Baş Simyacı, 500 akçe/seviye (max 3) |

### 🛡️ Kolluk & Savunma
| Slash | Prefix | Açıklama |
|-------|--------|----------|
| `/muhafiz-paneli` | `v.muhafiz-paneli` | Panel |
| `/karantina-al` | `v.karantina-al` | Karantinaya al |
| `/karantina-kaldir` | `v.karantina-kaldir` veya `v.karantina-kaldır` | Karantinadan çıkar |
| `/savunmayi-guclendir` | `v.savunmayi-guclendir` veya `v.savunmayı-güçlendir` | Başkan, 500 akçe +15 tahkimat |
| `/nobet` | `v.nobet` | Muhafız, 4 saat CD, ödül |
| `/muhafiz-donanim` | `v.muhafiz-donanim` | Defans ekipmanı al |

### 🌾 Üretim & Ambar
| Slash | Prefix | Açıklama |
|-------|--------|----------|
| `/ciftci-paneli` | `v.ciftci-paneli` | Panel |
| `/tarla-calis` | `v.tarla-calis` | 30 dk CD |
| `/maden-kaz` | `v.maden-kaz` | 30 dk CD |
| `/orman-kes` | `v.orman-kes` | 30 dk CD |
| `/ambar` | `v.ambar` | Stok listesi |
| `/ambara-bagis` | `v.ambara-bagis` veya `v.ambara-bağış` | Bağış |
| `/ambardan-al` | `v.ambardan-al` | Max 5/adet |
| `/tuccar-paneli` | `v.tuccar-paneli` | Tüccar ticaret paneli |
| `/tuccar-al` | `v.tuccar-al` | Ambardan ucuz al |
| `/tuccar-sat` | `v.tuccar-sat` | Ambara pahalı sat (kar!) |

### 💰 Ekonomi & Çevre
| Slash | Prefix | Açıklama |
|-------|--------|----------|
| `/maliye-yonetim` | `v.maliye-yonetim` veya `v.maliye-yönetim` | Vergi Memuru paneli |
| `/hava-durumu-degis` | `v.hava-durumu-degis` veya `v.hava-durumu-değiş` | Yetkili Ekip |
| `/sunucu-yonetimi` | `v.sunucu-yonetimi` veya `v.sunucu-yönetimi` | RP Owner/Admin |
| `/haber` | `v.haber` | Yetkili Ekip, gazete kanalı |

### 📖 Rehber
| Slash | Prefix | Açıklama |
|-------|--------|----------|
| `/yardim` | `v.yardim` veya `v.yardım` veya `v.destek` | Dropdown kategori menüsü |
| `/rehber` | `v.rehber` | Detaylı dropdown rehber |

---

## ⚙️ Otomatik Task'lar

| Sıklık | Task | İşlev |
|--------|------|-------|
| 1 saat | Yedekleme + Watching Güncelleme | YEDEK_KANAL_ID kanalına JSON yedek + bot durumu güncelle (aktif sakin sayısı) |
| 5 saat | Vergi Tahsilatı | Tüm canlı sakinlerden veba vergisi |
| 6 saat | Gazete | Haber kanalına son 6 saatlik olay bülteni (v5.9: kasa doğru gösteriliyor) |
| 24 saat | Açlık/Susuzluk | Su -10, su 0 ise sağlık -15, sağlık 0 ise ölüm (v5.9: "Ölü" durum) |

---

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

---

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

---

## 🚀 Deploy Adımları

1. Bu kodu GitHub'a pushla
2. Render'da "New → Web Service" oluştur, GitHub'ı bağla
3. Environment Variables:
   - `DISCORD_TOKEN` = bot token
   - `YEDEK_KANAL_ID` = 1516177967288422400 (opsiyonel, default zaten)
4. Deploy!
5. UptimeRobot'a `https://your-app.onrender.com/health` URL'ini ekle, 5 dk'da bir ping atsın

---

## 📊 Sistem Özellikleri

- **Para Birimi:** Akçe (v5.6'dan beri, eski adı Hurda)
- **Prefix:** `v.` (örn: `v.kayit`, `v.profil`)
- **Bot Rolü:** 🤖 Veba 1320
- **Slash + Prefix:** Birebir aynı çıktı (v5.9)
- **Cog Sayısı:** 16 (prefix dahil)
- **Toplam Komut:** 71 slash + 35+ prefix = 106+ komut
- **Pazar Kataloğu:** 85 eşya (7 kategori)
- **Meslek Sayısı:** 27 (8 atanabilir, 19 serbest)
- **Keşif Bölgesi:** 25 RP bölgesi
- **Keşif Olay Havuzu:** 30 olay (10 olumlu / 10 olumsuz / 10 gizemli)

---

## 📞 İletişim

Sahip: HarunAE55
Repo: https://github.com/HarunAE55/siginak-bot

---

## 📜 Sürüm Geçmişi

- **v5.9** (Haziran 2026) — Büyük bakım: Kritik bug fix'ler, prefix-slash aynı çıktı, sürüm bump
- **v5.8** — Tüccar ticaret sistemi, muhafız donanım, akçe-gonder, kayit-sil, kaynak-ekle
- **v5.7** — Yeni roller (Administrator, Admin, Yetkili Ekip), /kavga komutu, akçe para birimi
- **v5.6** — Para birimi Hurda → Akçe olarak değiştirildi
- **v5.5** — Rehber dropdown düzeltmeleri
- **v5.4** — /kutsa KeyError fix, /kullan fix
- **v5.2** — Slash sync güvenli hale getirildi
- **v5.1** — /biyografi-yaz description kısaltma, /gez 25 bölgeye düşürüldü
- **v5.0** — İlk cogs mimarisi, slash komutları, Türkçe karakter → ASCII

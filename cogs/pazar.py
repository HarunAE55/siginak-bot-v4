"""
Cog: Pazar & Ticaret
===================
Komutlar:
- /pazar (kategori seçerek eşya listele)
- /satinal (kod ile eşya al)
- /bota-sat (envantere kasaya sat - TAM_PAZAR fix ile)
- /esya-sat (başka sakinle doğrudan satış)
- /takas-teklif (eşya-eşya takası)
- /acik-arttirma-baslat (2 dk açık arttırma)
- /pey-ver (aktif ilana teklif)

Kataloğumuz 85 eşyadan oluşur (Bölüm 1: 01-45, Bölüm 2: 46-85).
TAM_PAZAR her ikisini birleştirir.
"""

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random

from veritabani import (
    db, verileri_kaydet, olu_kontrolu,
    sokak_ve_karantina_kontrolu, haber_ekle
)


# ====================================================
# PAZAR KATALOĞU - BÖLÜM 1 (01-45): Silah, Zırh, Medikal
# ====================================================
KATALOG_BOLUM_1 = {
    # == 01-20 SİLAHLAR ==
    "01": {"isim": "Paslı Demir Kama", "fiyat": 150, "tip": "Silah", "bonus_turu": "Atak Gücü", "bonus_degeri": 5, "aciklama": "Sığınak dehlizlerinden çıkarılmış, pas tutmuş ama hala keskin kısa demir kama."},
    "02": {"isim": "Acemi Süvari Kısa Kılıcı", "fiyat": 300, "tip": "Silah", "bonus_turu": "Atak Gücü", "bonus_degeri": 10, "aciklama": "Hafif alaşımdan üretilmiş, sallaması kolay standart muhafız yan silahı."},
    "03": {"isim": "Ağır Demirci Baltası", "fiyat": 450, "tip": "Silah", "bonus_turu": "Atak Gücü", "bonus_degeri": 15, "aciklama": "Odun kesmek için tasarlanmış olsa da zırhları tek darbede yarabilen ağır balta."},
    "04": {"isim": "Piyade Savaş Teberi", "fiyat": 600, "tip": "Silah", "bonus_turu": "Atak Gücü", "bonus_degeri": 20, "aciklama": "Uzun menzilli darbeler vurabilen, çelik uçlu nizam teberi."},
    "05": {"isim": "Gezgin Kompozit Yayı", "fiyat": 750, "tip": "Silah", "bonus_turu": "Atak Gücü", "bonus_degeri": 25, "aciklama": "Esnek meşe ağacından ve gergin misinadan imal edilmiş avcı yayı."},
    "06": {"isim": "Şövalye Geniş Kılıcı", "fiyat": 900, "tip": "Silah", "bonus_turu": "Atak Gücü", "bonus_degeri": 30, "aciklama": "Çift elle kavranan, üzerinde rün işlemeleri bulunan ağır şövalye kılıcı."},
    "07": {"isim": "Hafif Kundaklı Yay", "fiyat": 1050, "tip": "Silah", "bonus_turu": "Atak Gücü", "bonus_degeri": 35, "aciklama": "Mekanik tetik tertibatı sayesinde çelik okları yüksek hızla fırlatan arbalet."},
    "08": {"isim": "Akasya Saplı Mızrak", "fiyat": 1200, "tip": "Silah", "bonus_turu": "Atak Gücü", "bonus_degeri": 40, "aciklama": "Ucu kırılmaz çelikle güçlendirilmiş, nizam savunmasında kritik uzun mızrak."},
    "09": {"isim": "Dikenli Çivili Gürz", "fiyat": 1350, "tip": "Silah", "bonus_turu": "Atak Gücü", "bonus_degeri": 45, "aciklama": "Ağır zırhlı düşmanların kemiklerini kırmak için dövülmüş çivili gürz."},
    "10": {"isim": "Şafak Muhafızı Çift Bıçağı", "fiyat": 1500, "tip": "Silah", "bonus_turu": "Atak Gücü", "bonus_degeri": 50, "aciklama": "Gizlilik odaklı izcilerin kullandığı, dengesi kusursuz ikiz hançer seti."},
    "11": {"isim": "Sığınak Engerek Palası", "fiyat": 1650, "tip": "Silah", "bonus_turu": "Atak Gücü", "bonus_degeri": 55, "aciklama": "Eğri namlulu, sığınak haydutlarının korkulu rüyası olan ağır pala."},
    "12": {"isim": "Gürz-i Kebir", "fiyat": 1800, "tip": "Silah", "bonus_turu": "Atak Gücü", "bonus_degeri": 60, "aciklama": "Sadece yüksek güce sahip savaşçıların savurabileceği devasa kuşatma gürzü."},
    "13": {"isim": "Süvari Savaş Çekici", "fiyat": 1950, "tip": "Silah", "bonus_turu": "Atak Gücü", "bonus_degeri": 65, "aciklama": "Bir yüzü düz çekiç, diğer yüzü ise zırh delen kargı ucuna sahip teçhizat."},
    "14": {"isim": "Gölge Suikastçı Kaması", "fiyat": 2100, "tip": "Silah", "bonus_turu": "Atak Gücü", "bonus_degeri": 70, "aciklama": "Işığı yansıtmayan özel siyah metalden dövülmüş suikast hançeri."},
    "15": {"isim": "Kraliyet Nişancı Arbaleti", "fiyat": 2250, "tip": "Silah", "bonus_turu": "Atak Gücü", "bonus_degeri": 75, "aciklama": "Dürbün niyetine kullanılan ince nişangahlı, yüksek mekanik güçlü ağır arbalet."},
    "16": {"isim": "Klan Şefi Savaş Baltası", "fiyat": 2400, "tip": "Silah", "bonus_turu": "Atak Gücü", "bonus_degeri": 80, "aciklama": "Çift taraflı devasa ağza sahip, vurduğu yeri parçalayan vahşi savaş baltası."},
    "17": {"isim": "Efsanevi Çelik Katana", "fiyat": 2550, "tip": "Silah", "bonus_turu": "Atak Gücü", "bonus_degeri": 85, "aciklama": "Uzak diyarlardan kalma, kat kat katlanmış çelikten dövülmüş kusursuz kılıç."},
    "18": {"isim": "Rünlü Şövalye Kargısı", "fiyat": 2700, "tip": "Silah", "bonus_turu": "Atak Gücü", "bonus_degeri": 90, "aciklama": "Üzerinde antik tılsımlar kazılı, hücum anında ölümcül hasar veren kargı."},
    "19": {"isim": "Karanlık Dehliz Tırpanı", "fiyat": 2850, "tip": "Silah", "bonus_turu": "Atak Gücü", "bonus_degeri": 95, "aciklama": "Sığınak infazcılarının kullandığı, geniş açılı ölümcül kesikler atan tırpan."},
    "20": {"isim": "Nizam-ı Kebir Kılıcı", "fiyat": 3000, "tip": "Silah", "bonus_turu": "Atak Gücü", "bonus_degeri": 100, "aciklama": "Yüce idarenin elit komutanlarına layık, sığınağın en güçlü çelik kılıcı."},
    # == 21-40 ZIRHLAR ==
    "21": {"isim": "Eski Kenevir Kıyafet", "fiyat": 180, "tip": "Zırh", "bonus_turu": "Defans Gücü", "bonus_degeri": 6, "aciklama": "Sadece rüzgardan ve tozdan koruyan, koruması çok zayıf kenevir hırka."},
    "22": {"isim": "Kalınlaştırılmış Deri Yelek", "fiyat": 360, "tip": "Zırh", "bonus_turu": "Defans Gücü", "bonus_degeri": 12, "aciklama": "Birkaç kat sığır derisinin üst üste dikilmesiyle yapılmış temel yelek."},
    "23": {"isim": "Gezgin Perçinli Deri Zırh", "fiyat": 540, "tip": "Zırh", "bonus_turu": "Defans Gücü", "bonus_degeri": 18, "aciklama": "Deri tabakanın üzerine demir pullar perçinlenerek direnci artırılmış zırh."},
    "24": {"isim": "Avcı Kamuflaj Pelerini", "fiyat": 720, "tip": "Zırh", "bonus_turu": "Defans Gücü", "bonus_degeri": 24, "aciklama": "Hem hafif darbe emilimi sağlayan hem de çalılıklarda gizleyen yeşil pelerin."},
    "25": {"isim": "Hafif Örme Zincir Zırh", "fiyat": 900, "tip": "Zırh", "bonus_turu": "Defans Gücü", "bonus_degeri": 30, "aciklama": "Demir halkaların birbirine geçirilmesiyle yapılan, kesici silahlara karşı etkili zırh."},
    "26": {"isim": "Takviyeli Muhafız Göğüslüğü", "fiyat": 1080, "tip": "Zırh", "bonus_turu": "Defans Gücü", "bonus_degeri": 36, "aciklama": "Nizam muhafızlarının giydiği, göğüs kafesini koruyan çelik plaka."},
    "27": {"isim": "Ağır Zincir Hauberk", "fiyat": 1260, "tip": "Zırh", "bonus_turu": "Defans Gücü", "bonus_degeri": 42, "aciklama": "Diz kapaklarına kadar uzanan, tüm vücudu saran yoğun örme demir zırh."},
    "28": {"isim": "Süvari Yarım Plaka Zırh", "fiyat": 1440, "tip": "Zırh", "bonus_turu": "Defans Gücü", "bonus_degeri": 48, "aciklama": "Omuz ve hayati organları koruyan, hareket kabiliyetini engellemeyen parlak zırh."},
    "29": {"isim": "Demirci Ustası Koruma Önlüğü", "fiyat": 1620, "tip": "Zırh", "bonus_turu": "Defans Gücü", "bonus_degeri": 54, "aciklama": "Isıya ve sert darbelere dayanıklı, kalınlaştırılmış ağır kösele zırh."},
    "30": {"isim": "Şövalye Çelik Zırhı", "fiyat": 1800, "tip": "Zırh", "bonus_turu": "Defans Gücü", "bonus_degeri": 60, "aciklama": "Ağır çelik plakaların birleşiminden oluşan, tam koruma sağlayan şövalye zırhı."},
    "31": {"isim": "Gölge Süvari Hafif Zırhı", "fiyat": 1980, "tip": "Zırh", "bonus_turu": "Defans Gücü", "bonus_degeri": 66, "aciklama": "Ses çıkarmayan özel eklemlerle donanmış, karartılmış çelik plaka zırh."},
    "32": {"isim": "Gelişmiş Alaşım Göğüslük", "fiyat": 2160, "tip": "Zırh", "bonus_turu": "Defans Gücü", "bonus_degeri": 72, "aciklama": "Farklı metallerin eritilerek birleştirilmesiyle yapılmış yüksek mukavemetli koruma."},
    "33": {"isim": "Klan Muhafızı Ağır Lamelları", "fiyat": 2340, "tip": "Zırh", "bonus_turu": "Defans Gücü", "bonus_degeri": 78, "aciklama": "Küçük çelik plakaların deri iplerle birbirine bağlanmasıyla üretilen koruma."},
    "34": {"isim": "Aslan Logolu Saray Zırhı", "fiyat": 2520, "tip": "Zırh", "bonus_turu": "Defans Gücü", "bonus_degeri": 84, "aciklama": "Sığınak yönetim binasını koruyan elit korumalara tahsis edilen işlemeli zırh."},
    "35": {"isim": "Ağır Kuşatma Levha Zırhı", "fiyat": 2700, "tip": "Zırh", "bonus_turu": "Defans Gücü", "bonus_degeri": 90, "aciklama": "Doğrudan cephe hücumları için tasarlanmış, neredeyse delinemez devasa zırh takımı."},
    "36": {"isim": "Efsanevi Göksel Çelik Zırh", "fiyat": 2880, "tip": "Zırh", "bonus_turu": "Defans Gücü", "bonus_degeri": 96, "aciklama": "Çok nadir bulunan göktaşı minerallerinden dövülmüş, hafif ama aşırı dayanıklı zırh."},
    "37": {"isim": "Rünlü Muhafız Plakası", "fiyat": 3060, "tip": "Zırh", "bonus_turu": "Defans Gücü", "bonus_degeri": 102, "aciklama": "Darbenin kinetik enerjisini emen rünlerle kaplanmış büyüleyici ağır zırh."},
    "38": {"isim": "Kraliyet Elçisi Kadife Zırhı", "fiyat": 3240, "tip": "Zırh", "bonus_turu": "Defans Gücü", "bonus_degeri": 108, "aciklama": "İç kısmı ince çelik plakalarla döşenmiş, dışı ise asalet göstergesi kadife kaplı koruma."},
    "39": {"isim": "Kadim Ejder Pullu Zırh", "fiyat": 3420, "tip": "Zırh", "bonus_turu": "Defans Gücü", "bonus_degeri": 114, "aciklama": "Sığınak efsanelerinde geçen, ateşe ve kılıç darbelerine mutlak bağışıklık veren zırh."},
    "40": {"isim": "Yüce Nizam Zırh-ı Hümayun", "fiyat": 3600, "tip": "Zırh", "bonus_turu": "Defans Gücü", "bonus_degeri": 120, "aciklama": "Yalnızca sığınak liderinin giyebileceği, en üst düzey savunma ve direnç zırhı."},
    # == 41-45 MEDİKAL ÜRÜNLER ==
    "41": {"isim": "Steril Sığınak Bandajı", "fiyat": 220, "tip": "Medikal", "bonus_turu": "Sağlık Takviyesi", "bonus_degeri": 15, "aciklama": "Açık yaraları sararak enfeksiyon kapmasını engelleyen temiz tıbbi bez."},
    "42": {"isim": "Radyasyon Önleyici Kimyasal Hap", "fiyat": 440, "tip": "Medikal", "bonus_turu": "Sağlık Takviyesi", "bonus_degeri": 30, "aciklama": "Vücudu ağır metal ve sığınak sızıntı toksinlerinden temizleyen kimyasal hap."},
    "43": {"isim": "Veba Antivirüs Serumu", "fiyat": 660, "tip": "Medikal", "bonus_turu": "Sağlık Takviyesi", "bonus_degeri": 45, "aciklama": "Simyacılar tarafından geliştirilen, ölümcül salgın mikroplarını kıran özel serum."},
    "44": {"isim": "Hücre Yenileyici Yoğun İksir", "fiyat": 880, "tip": "Medikal", "bonus_turu": "Sağlık Takviyesi", "bonus_degeri": 60, "aciklama": "İçeriğindeki tıbbi özler sayesinde derin yaraları hızla kapatan şifalı iksir."},
    "45": {"isim": "Kraliyet Bitkisel Yara Tentürü", "fiyat": 1100, "tip": "Medikal", "bonus_turu": "Sağlık Takviyesi", "bonus_degeri": 75, "aciklama": "Baş doktorun gizli formülüyle hazırlanan, canı anında tazeleyen en üst düzey merhem."},
}


# ====================================================
# PAZAR KATALOĞU - BÖLÜM 2 (46-85): Gıda, Hammadde, Teknoloji, Mistik
# ====================================================
PAZAR_KATALOGU_TAM = {
    # == 46-55 GIDALAR ==
    "46": {"isim": "Kuru Taş Ekmeği", "fiyat": 30, "tip": "Gıda", "bonus_turu": "Su Seviyesi", "bonus_degeri": 15, "aciklama": "Uzun süre dayanması için fırınlanmış sert sığınak ekmeği."},
    "47": {"isim": "Sıcak Arpa Çorbası", "fiyat": 60, "tip": "Gıda", "bonus_turu": "Su Seviyesi", "bonus_degeri": 25, "aciklama": "Değirmenden taze gelen arpa ile pişirilmiş sıcak çorba."},
    "48": {"isim": "Tuzlu Sığır Konservesi", "fiyat": 120, "tip": "Gıda", "bonus_turu": "Su Seviyesi", "bonus_degeri": 40, "aciklama": "Çobanların yetiştirdiği sığır etlerinden yapılan tuzlu ambar konservesi."},
    "49": {"isim": "Kuyudan Çekilmiş Temiz Su", "fiyat": 25, "tip": "Gıda", "bonus_turu": "Su Seviyesi", "bonus_degeri": 30, "aciklama": "Sığınağın derin su damarlarından arındırılarak çekilmiş içme suyu."},
    "50": {"isim": "Kurutulmuş Dağ Çileği", "fiyat": 80, "tip": "Gıda", "bonus_turu": "Akıl Sağlığı", "bonus_degeri": 15, "aciklama": "İzciler tarafından dış dünyadan toplanıp kurutulan lezzetli meyve."},
    "51": {"isim": "Fermante Han Birası", "fiyat": 90, "tip": "Gıda", "bonus_turu": "Akıl Sağlığı", "bonus_degeri": 20, "aciklama": "Hancının gizli mahzeninde dinlendirdiği sert sığınak birası."},
    "52": {"isim": "Kavrulmuş Yaban Domuzu Eti", "fiyat": 150, "tip": "Gıda", "bonus_turu": "Su Seviyesi", "bonus_degeri": 50, "aciklama": "Avcıların sığınak çevresindeki bataklıklardan avladığı dolgun et."},
    "53": {"isim": "Süzme Karakovan Balı", "fiyat": 200, "tip": "Gıda", "bonus_turu": "Sağlık Takviyesi", "bonus_degeri": 25, "aciklama": "Doğal mağaralardan toplanmış, bağışıklığı tavan yaptıran şifalı bal."},
    "54": {"isim": "Küflü Mağara Peyniri", "fiyat": 75, "tip": "Gıda", "bonus_turu": "Su Seviyesi", "bonus_degeri": 20, "aciklama": "Aylarca karanlık dehlizlerde bekletilerek olgunlaştırılmış peynir."},
    "55": {"isim": "Askeri Katık Tayın Rasyonu", "fiyat": 110, "tip": "Gıda", "bonus_turu": "Su Seviyesi", "bonus_degeri": 35, "aciklama": "Muhafızların operasyonlarda tükettiği yüksek kalorili hazır paket."},
    # == 56-65 HAMMADDELER ==
    "56": {"isim": "İşlenmemiş Demir Cevheri", "fiyat": 40, "tip": "Hammadde", "bonus_turu": "Üretim", "bonus_degeri": 5, "aciklama": "Madencilerin yerin yedi kat altından çıkardığı saf demir kaya parçası."},
    "57": {"isim": "Külçe Bakır Blok", "fiyat": 80, "tip": "Hammadde", "bonus_turu": "Üretim", "bonus_degeri": 10, "aciklama": "Yüksek ısıda eritilerek kalıplara dökülmüş, iletken ham bakır blok."},
    "58": {"isim": "Sert Meşe Kerestesi", "fiyat": 35, "tip": "Hammadde", "bonus_turu": "Üretim", "bonus_degeri": 4, "aciklama": "Oduncuların sığınak seralarında özenle kestiği dayanıklı yapı odunu."},
    "59": {"isim": "Kömür Torbası", "fiyat": 50, "tip": "Hammadde", "bonus_turu": "Üretim", "bonus_degeri": 6, "aciklama": "Demirci ocağını harlamak için gerekli, yüksek kalorili yer altı kömürü."},
    "60": {"isim": "Kaba Lif Dokuması", "fiyat": 45, "tip": "Hammadde", "bonus_turu": "Üretim", "bonus_degeri": 5, "aciklama": "Kıyafet ve zırh astarı yapımında kullanılan kenevir lifi örgüsü."},
    "61": {"isim": "Saf Gümüş Tozu", "fiyat": 160, "tip": "Hammadde", "bonus_turu": "Üretim", "bonus_degeri": 15, "aciklama": "Simyacıların iksir tescilinde ve tılsım yapımında kullandığı değerli toz."},
    "62": {"isim": "Ham Kösele Deri Parçası", "fiyat": 55, "tip": "Hammadde", "bonus_turu": "Üretim", "bonus_degeri": 7, "aciklama": "Zırh eklemlerini esnetmek ve kalkan kaplamak için ideal kalın deri."},
    "63": {"isim": "Sönmüş Kireç Taşı", "fiyat": 30, "tip": "Hammadde", "bonus_turu": "Üretim", "bonus_degeri": 3, "aciklama": "Sığınak duvarlarının harcında ve dezenfektan işlemlerinde kullanılan taş."},
    "64": {"isim": "Zift Varili", "fiyat": 180, "tip": "Hammadde", "bonus_turu": "Üretim", "bonus_degeri": 18, "aciklama": "Kuşatma silahlarında ve sığınak kapısı savunmasında yakılarak kullanılan siyah sıvı."},
    "65": {"isim": "Kükürt Kristalleri", "fiyat": 140, "tip": "Hammadde", "bonus_turu": "Üretim", "bonus_degeri": 12, "aciklama": "Barut imalatında ve laboratuvar deneylerinde kritik rol oynayan kükürt."},
    # == 66-75 TEKNOLOJİ ÖGELERİ ==
    "66": {"isim": "Paslı Bakır Dişli Çark", "fiyat": 250, "tip": "Teknoloji", "bonus_turu": "Atak Gücü", "bonus_degeri": 8, "aciklama": "Antik sığınak makinelerinden sökülmüş mekanik çark parçası."},
    "67": {"isim": "Yanmış Devre Kartı Kalıntısı", "fiyat": 400, "tip": "Teknoloji", "bonus_turu": "Üretim", "bonus_degeri": 15, "aciklama": "Eski dünyadan kalma, üzerinde hala bazı chipler barındıran elektronik kart."},
    "68": {"isim": "Mercekli Pirinç Teleskop", "fiyat": 600, "tip": "Teknoloji", "bonus_turu": "Defans Gücü", "bonus_degeri": 12, "aciklama": "İzcilerin gözetleme kulelerinde uzak tehlikeleri sezmesini sağlayan mercekli dürbün."},
    "69": {"isim": "Mekanik Kurmalı Saat", "fiyat": 550, "tip": "Teknoloji", "bonus_turu": "Akıl Sağlığı", "bonus_degeri": 18, "aciklama": "Zaman algısını kaybetmemek için sığınak sakinlerine dağıtılan kurmalı cep saati."},
    "70": {"isim": "Dinamit Lokumu", "fiyat": 800, "tip": "Teknoloji", "bonus_turu": "Atak Gücü", "bonus_degeri": 30, "aciklama": "Madencilerin kayaları patlatmak, muhafızların ise barikat yıkmak için kullandığı patlayıcı."},
    "71": {"isim": "Asit Bataryası Hücresi", "fiyat": 700, "tip": "Teknoloji", "bonus_turu": "Üretim", "bonus_degeri": 22, "aciklama": "İçerisinde sülfürik asit ve kurşun levhalar barındıran ilkel elektrik hücresi."},
    "72": {"isim": "Buharlı Basınç Vanası", "fiyat": 450, "tip": "Teknoloji", "bonus_turu": "Defans Gücü", "bonus_degeri": 10, "aciklama": "Sığınak havalandırma ve kazan dairelerinin patlamasını önleyen ağır döküm vana."},
    "73": {"isim": "Fosforlu Aydınlatma Feneri", "fiyat": 350, "tip": "Teknoloji", "bonus_turu": "Akıl Sağlığı", "bonus_degeri": 14, "aciklama": "Karanlık dehlizlerde pil gerektirmeden fosfor parlamasıyla ışık veren fener."},
    "74": {"isim": "Kripto El Telsizi Enkazı", "fiyat": 950, "tip": "Teknoloji", "bonus_turu": "Üretim", "bonus_degeri": 28, "aciklama": "Araştırmacıların tamir etmeye çalıştığı şifreli frekans alıcı-verici enkazı."},
    "75": {"isim": "Kuşatma Mancınık Dişlisi", "fiyat": 1200, "tip": "Teknoloji", "bonus_turu": "Atak Gücü", "bonus_degeri": 40, "aciklama": "Ağır savunma mekanizmalarını kurmakta kullanılan devasa döküm çelik dişli."},
    # == 76-85 MİSTİK ÖGELER ==
    "76": {"isim": "Veba Doktoru Gaga Maskesi", "fiyat": 500, "tip": "Mistik", "bonus_turu": "Enfeksiyon Direnci", "bonus_degeri": 20, "aciklama": "İç kısmı şifalı otlarla doldurulmuş, hastalıktan ve gazdan koruyan maske."},
    "77": {"isim": "Kadim Simya Taşı Parçası", "fiyat": 1000, "tip": "Mistik", "bonus_turu": "Akıl Sağlığı", "bonus_degeri": 35, "aciklama": "Baş simyacının potasında erittiği, dokunulduğunda zihni sakinleştiren gizemli taş."},
    "78": {"isim": "Rün Kazılı Tılsım Kemikleri", "fiyat": 400, "tip": "Mistik", "bonus_turu": "Enfeksiyon Direnci", "bonus_degeri": 15, "aciklama": "Rahibin kutsadığı, üzerine koruyucu sığınak rünleri kazınmış hayvan kemikleri."},
    "79": {"isim": "Karanlık Cevher Özü Suyu", "fiyat": 1200, "tip": "Mistik", "bonus_turu": "Atak Gücü", "bonus_degeri": 25, "aciklama": "Dehlizlerin en dibinden sızan, içene muazzam öfke ve kas gücü veren simsiyah sıvı."},
    "80": {"isim": "Lanetli Engizisyon Haçı", "fiyat": 850, "tip": "Mistik", "bonus_turu": "Akıl Sağlığı", "bonus_degeri": -10, "aciklama": "Akıl sağlığını kemiren ama defans gücünü anında fırlatan tekinsiz metal haç."},
    "81": {"isim": "Kutsanmış Mezar Toprağı", "fiyat": 300, "tip": "Mistik", "bonus_turu": "Enfeksiyon Direnci", "bonus_degeri": 12, "aciklama": "Mezarcının sığınak şehitliğinden topladığı, kötülükleri uzak tuttuğuna inanılan toprak."},
    "82": {"isim": "Göz Bebeksiz İdol Heykelciği", "fiyat": 1500, "tip": "Mistik", "bonus_turu": "Akıl Sağlığı", "bonus_degeri": 50, "aciklama": "Eski sığınak kültlerinden kalma, taştan oyulmuş antika totem."},
    "83": {"isim": "Simyacı Cıva Esansı", "fiyat": 900, "tip": "Mistik", "bonus_turu": "Atak Gücü", "bonus_degeri": 18, "aciklama": "Hava geçirmez cam tüplerde saklanan, kararsız yapıdaki tılsımlı saf cıva esansı."},
    "84": {"isim": "Kayıp Kıyamet Parşömeni", "fiyat": 2000, "tip": "Mistik", "bonus_turu": "Akıl Sağlığı", "bonus_degeri": 60, "aciklama": "Sığınak kurulmadan önceki son günleri ve kurtuluş rünlerini anlatan kadim deri parşömen."},
    "85": {"isim": "Yüce Nizam Kutsal Sancaığı", "fiyat": 5000, "tip": "Mistik", "bonus_turu": "Enfeksiyon Direnci", "bonus_degeri": 100, "aciklama": "Sığınağın ana salonunda asılı duran, tüm sakinlerin inancını ve direncini simgeleyen kutsal sancak."},
}


# BİRLEŞİK PAZAR KATALOĞU (85 eşya) - tüm komutlar bu kullanır
TAM_PAZAR = {**KATALOG_BOLUM_1, **PAZAR_KATALOGU_TAM}


def katalogdan_isim_bul(esya_ad: str):
    """Verilen isimden kataloğun tam ismini ve fiyatını bulur. Büyük/küçük harf duyarsız.
    Dönüş: (tam_isim, fiyat) veya (None, None)
    """
    for kod, veri in TAM_PAZAR.items():
        if veri["isim"].lower() == esya_ad.lower():
            return veri["isim"], veri["fiyat"]
    return None, None


# ====================================================
# COG SINIFI
# ====================================================
class PazarCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ====================================================
    # /pazar - Select Menu ile kategori seç
    # ====================================================
    @app_commands.command(name="pazar", description="[TİCARET] Sığınak pazarında kategori seçerek eşya satın al.")
    async def pazar_listele(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛒 SIĞINAK PAZAR TEZGAHI",
            color=0x2ECC71
        )
        embed.description = (
            "**Hoş geldin tüccar!** 🛒\n\n"
            "Aşağıdaki menüden bir kategori seçerek o kategorideki tüm eşyaları görebilirsin.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📋 **Kategoriler:**\n"
            "⚔️ • **Silahlar** — Kılıç, kama, yay, gürz vb.\n"
            "🛡️ • **Zırhlar** — Göğüslük, zincir, plaka vb.\n"
            "💊 • **Medikal** — Bandaj, serum, iksir vb.\n"
            "🍲 • **Gıda** — Ekmek, et, su, bira vb.\n"
            "🪵 • **Hammadde** — Demir, odun, kömür vb.\n"
            "⚙️ • **Teknoloji** — Dişli, teleskop, dinamit vb.\n"
            "🔮 • **Mistik** — Rün, tılsım, sançak vb.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 **Satın almak için:** `/satinal [kod] [adet]`\n"
            "💡 **Satmak için:** `/bota-sat [esya] [adet]`"
        )
        embed.set_footer(text="Sığınak Veba RP v5.5 | Kategori seçmek için aşağıdaki menüyü kullan")
        
        view = PazarView()
        await interaction.response.send_message(embed=embed, view=view)

    # ====================================================
    # /satinal - Kod ile eşya al
    # ====================================================
    @app_commands.command(name="satinal", description="[TİCARET] Belirtilen kodlu üründen girdiğiniz adette satın alım gerçekleştirir.")
    @app_commands.describe(esya_kodu="Pazar kataloğundaki ürün kodu (örn: 01, 46)", adet="Kaç adet alınacağı")
    async def satin_al(self, interaction: discord.Interaction, esya_kodu: str, adet: int):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Sicil kütüğünde kaydın yok!", ephemeral=True)
            return
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return
        if esya_kodu not in TAM_PAZAR:
            await interaction.response.send_message("❌ Girdiğiniz pazar kodu katalogda bulunmuyor!", ephemeral=True)
            return
        if adet <= 0:
            await interaction.response.send_message("❌ Alım adedi en az 1 olmalı!", ephemeral=True)
            return

        sakin = db["sakinler"][u_id]
        urun = TAM_PAZAR[esya_kodu]
        meslek = sakin.get("meslek_anahtar", "gezgin")

        # Mesleki indirim motoru
        indirim_uygula = False
        if meslek == "tuccar":
            indirim_uygula = True
        elif meslek == "demirci" and urun["tip"] == "Hammadde" and "Demir" in urun["isim"]:
            indirim_uygula = True
        elif meslek == "ciftci" and urun["tip"] == "Gıda" and ("Ekmek" in urun["isim"] or "Arpa" in urun["isim"]):
            indirim_uygula = True
        elif meslek in ["simyaci", "bas_simyaci", "doktor", "bas_doktor"] and urun["tip"] == "Mistik" and "Esansı" in urun["isim"]:
            indirim_uygula = True

        birim_fiyat = int(urun["fiyat"] * 0.8) if indirim_uygula else urun["fiyat"]
        toplam_maliyet = birim_fiyat * adet

        if sakin["cuzdan"] < toplam_maliyet:
            await interaction.response.send_message(
                f"❌ Bakiyeniz yetersiz! Gereken: `{toplam_maliyet}` Akçe, Cüzdanınızda: `{sakin['cuzdan']}`.",
                ephemeral=True
            )
            return

        # Hesap kesimi
        sakin["cuzdan"] -= toplam_maliyet
        sakin["envanter"][urun["isim"]] = sakin["envanter"].get(urun["isim"], 0) + adet

        # Bonusu karaktere yansıt
        b_turu = urun["bonus_turu"]
        b_degeri = urun["bonus_degeri"] * adet

        if b_turu == "Atak Gücü":
            sakin["atak"] += b_degeri
        elif b_turu == "Defans Gücü":
            sakin["defans"] = sakin.get("defans", 0) + b_degeri
        elif b_turu == "Sağlık Takviyesi":
            sakin["saglik"] = min(100, sakin.get("saglik", 100) + b_degeri)
        elif b_turu == "Su Seviyesi":
            sakin["su"] = min(100, sakin.get("su", 100) + b_degeri)
        elif b_turu == "Akıl Sağlığı":
            sakin["akil_sagligi"] = min(100, max(0, sakin.get("akil_sagligi", 100) + b_degeri))
        elif b_turu == "Enfeksiyon Direnci":
            sakin["enfeksiyon"] = max(0, sakin.get("enfeksiyon", 0) - b_degeri)

        verileri_kaydet()

        msg = f"🛒 Alım tamamlandı.\n• Alınan: `{adet} Adet {urun['isim']}`\n• Toplam Ödenen: `💰 {toplam_maliyet} Akçe`"
        if indirim_uygula:
            msg += " *(Mesleki %20 İndirim Uygulandı!)*"
        msg += f"\n• Karaktere Yansıyan Bonus: `+{b_degeri} {b_turu}`"

        await interaction.response.send_message(msg)

    # ====================================================
    # /bota-sat - Envanteri kasaya sat (TAM_PAZAR FIX'li)
    # ====================================================
    @app_commands.command(name="bota-sat", description="[TİCARET] Envanterinizdeki fazla ürünleri değer kaybı vergisiyle sığınak idaresine satar.")
    @app_commands.describe(esya_ad="Satmak istediğiniz eşyanın tam adı", adet="Satılacak miktar")
    async def bota_sat(self, interaction: discord.Interaction, esya_ad: str, adet: int):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Sicil kütüğünde kaydın yok!", ephemeral=True)
            return
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return
        if adet <= 0:
            await interaction.response.send_message("❌ Satış adedi en az 1 olmalıdır!", ephemeral=True)
            return

        sakin = db["sakinler"][u_id]
        envanter = sakin.get("envanter", {})

        mevcut_adet = envanter.get(esya_ad, 0)
        if mevcut_adet < adet:
            await interaction.response.send_message(
                f"❌ Envanterinizde yeterli miktarda `{esya_ad}` bulunamadı! Sizde olan: `{mevcut_adet}` Adet.",
                ephemeral=True
            )
            return

        # KATALOGDAN FİYAT BULMA - TAM_PAZAR kullanılır (eski sürümde PAZAR_KATALOGU_TAM idi, BUG)
        orijinal_fiyat = None
        tam_isim, fiyat = katalogdan_isim_bul(esya_ad)
        if tam_isim:
            orijinal_fiyat = fiyat
            esya_ad = tam_isim  # büyük/küçük harf düzeltmesi

        if orijinal_fiyat is None:
            await interaction.response.send_message(
                "❌ Bu eşya sığınak pazar kayıtlarında tanınmıyor! İsim hatası yapmadığınızdan emin olun.",
                ephemeral=True
            )
            return

        # Vergi hesaplama: tüccar ve vergi memuru %20, diğerleri %25
        meslek = sakin.get("meslek_anahtar", "gezgin")
        vergi_orani = 0.20 if meslek in ["tuccar", "vergi_mufettisi"] else 0.25

        brut_kazanc = orijinal_fiyat * adet
        vergi_kesintisi = int(brut_kazanc * vergi_orani)
        net_kazanc = brut_kazanc - vergi_kesintisi

        envanter[esya_ad] -= adet
        sakin["cuzdan"] += net_kazanc
        db["sistem_ayarlari"]["KASA_AKÇE_PLACEHOLDER"] += vergi_kesintisi

        if envanter[esya_ad] == 0:
            del envanter[esya_ad]

        verileri_kaydet()

        embed = discord.Embed(title="♻️ SIĞINAK İDARESİ GERİ DÖNÜŞÜM RAPORU", color=0xE67E22)
        embed.description = (
            f"**Satan Sakin:** {interaction.user.mention}\n"
            f"**Teslim Edilen:** `{adet} Adet {esya_ad}`\n\n"
            f"• Eşya Başı Orijinal Değer: `{orijinal_fiyat} Akçe`\n"
            f"• Toplam Brüt Tutar: `{brut_kazanc} Akçe`\n"
            f"• Değer Kaybı Vergisi (%{int(vergi_orani * 100)}): `-{vergi_kesintisi} Akçe`\n"
            f"--- \n"
            f"• **Cüzdana Aktarılan Net Kazanç:** `💰 {net_kazanc} Akçe`"
        )
        embed.set_footer(text="Borsa dengeleme protokolü uygulandı.")
        await interaction.response.send_message(embed=embed)

    @bota_sat.autocomplete("esya_ad")
    async def bota_sat_autocomplete(self, interaction: discord.Interaction, current: str):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            return []
        sakin_envanter = db["sakinler"][u_id].get("envanter", {})
        return [
            app_commands.Choice(name=f"{esya} ({adet} Adet Sahipsiniz)", value=esya)
            for esya, adet in sakin_envanter.items() if adet > 0 and current.lower() in esya.lower()
        ][:25]

    # ====================================================
    # /esya-sat - Doğrudan oyuncuya satış
    # ====================================================
    @app_commands.command(name="esya-sat", description="[TİCARET] Bir sığınak sakinine akçe karşılığı eşya satma teklifi sunar.")
    @app_commands.describe(kullanici="Alıcı sakin", esya_ad="Satılacak eşya", fiyat="Talep edilen akçe")
    async def esya_sat(self, interaction: discord.Interaction, kullanici: discord.User, esya_ad: str, fiyat: int):
        if kullanici.id == interaction.user.id:
            await interaction.response.send_message("❌ Kendi kendine bir şey satamazsın!", ephemeral=True)
            return
        if fiyat < 0:
            await interaction.response.send_message("❌ Fiyat negatif olamaz!", ephemeral=True)
            return

        s_id = str(interaction.user.id)
        a_id = str(kullanici.id)

        if s_id not in db["sakinler"] or a_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Oyuncu kayıtları sistemde bulunamadı!", ephemeral=True)
            return

        kontrol = sokak_ve_karantina_kontrolu(s_id)
        if kontrol:
            await interaction.response.send_message(kontrol, ephemeral=True)
            return

        satici_env = db["sakinler"][s_id].get("envanter", {})

        # TAM_PAZAR ile isim doğrulama (BUG FIX)
        gercek_esya_ad, _ = katalogdan_isim_bul(esya_ad)
        if not gercek_esya_ad:
            await interaction.response.send_message("❌ Girdiğiniz eşya ismi pazar kataloğunda kayıtlı değil!", ephemeral=True)
            return

        if satici_env.get(gercek_esya_ad, 0) < 1:
            await interaction.response.send_message(f"❌ Sırt çantanızda satılık `{gercek_esya_ad}` bulunmuyor!", ephemeral=True)
            return

        view = EsyaSatView(interaction.user, kullanici, gercek_esya_ad, fiyat)
        await interaction.response.send_message(
            f"💰 {interaction.user.mention}, {kullanici.mention} kullanıcısına doğrudan bir satış teklifi gönderdi!\n"
            f"• Satılacak Ürün: `1 Adet {gercek_esya_ad}`\n"
            f"• Talep Edilen Ücret: `🪙 {fiyat} Akçe`\n"
            f"**Alıcının onaylaması durumunda ticaret el altından tescillenecektir.**",
            view=view
        )

    @esya_sat.autocomplete("esya_ad")
    async def esya_sat_autocomplete(self, interaction: discord.Interaction, current: str):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            return []
        sakin_envanter = db["sakinler"][u_id].get("envanter", {})
        return [
            app_commands.Choice(name=f"{esya} ({adet} Adet)", value=esya)
            for esya, adet in sakin_envanter.items() if adet > 0 and current.lower() in esya.lower()
        ][:25]

    # ====================================================
    # /takas-teklif - Eşya-eşya takası
    # ====================================================
    @app_commands.command(name="takas-teklif", description="[TİCARET] Başka bir sakinle karşılıklı birebir eşya takası teklif arayüzü açar.")
    @app_commands.describe(
        kullanici="Takas yapılacak sakin",
        verilecek_esya="Sizin vereceğiniz eşya",
        istenen_esya="Karşı taraftan istediğiniz eşya"
    )
    async def takas_teklif(self, interaction: discord.Interaction, kullanici: discord.User, verilecek_esya: str, istenen_esya: str):
        if kullanici.id == interaction.user.id:
            await interaction.response.send_message("❌ Kendi kendine takas yapamazsın!", ephemeral=True)
            return

        eden_id = str(interaction.user.id)
        edilen_id = str(kullanici.id)

        if eden_id not in db["sakinler"] or edilen_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Taraflardan birinin sığınak kütük kaydı bulunamadı!", ephemeral=True)
            return

        kontrol = sokak_ve_karantina_kontrolu(eden_id)
        if kontrol:
            await interaction.response.send_message(kontrol, ephemeral=True)
            return

        eden_env = db["sakinler"][eden_id].get("envanter", {})
        edilen_env = db["sakinler"][edilen_id].get("envanter", {})

        # TAM_PAZAR ile isim eşleştirme (BUG FIX)
        v_esya_ad, _ = katalogdan_isim_bul(verilecek_esya)
        i_esya_ad, _ = katalogdan_isim_bul(istenen_esya)

        if not v_esya_ad or not i_esya_ad:
            await interaction.response.send_message("❌ Girdiğiniz eşya isimleri pazar kataloğunda eşleşmedi!", ephemeral=True)
            return

        if eden_env.get(v_esya_ad, 0) < 1:
            await interaction.response.send_message(f"❌ Envanterinizde satılık `{v_esya_ad}` bulunmuyor!", ephemeral=True)
            return
        if edilen_env.get(i_esya_ad, 0) < 1:
            await interaction.response.send_message(f"❌ Karşı tarafın envanterinde `{i_esya_ad}` bulunmuyor!", ephemeral=True)
            return

        view = TakasOnayView(interaction.user, kullanici, v_esya_ad, i_esya_ad)
        await interaction.response.send_message(
            f"🤝 {interaction.user.mention}, {kullanici.mention} kullanıcısına bir takas teklif etti!\n"
            f"• Verilecek Ürün: `1 Adet {v_esya_ad}`\n"
            f"• İstenen Ürün: `1 Adet {i_esya_ad}`\n"
            f"**İki tarafın da aşağıdaki onay butonuna basması gerekmektedir.**",
            view=view
        )

    @takas_teklif.autocomplete("verilecek_esya")
    async def takas_verilecek_autocomplete(self, interaction: discord.Interaction, current: str):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            return []
        sakin_envanter = db["sakinler"][u_id].get("envanter", {})
        return [
            app_commands.Choice(name=f"{esya} ({adet} Adet)", value=esya)
            for esya, adet in sakin_envanter.items() if adet > 0 and current.lower() in esya.lower()
        ][:25]

    @takas_teklif.autocomplete("istenen_esya")
    async def takas_istenen_autocomplete(self, interaction: discord.Interaction, current: str):
        # Karşı tarafın envanterini bilemeyiz, katalogdan öner
        return [
            app_commands.Choice(name=f"{v['isim']} ({v['tip']})", value=v["isim"])
            for v in TAM_PAZAR.values() if current.lower() in v["isim"].lower()
        ][:25]

    # ====================================================
    # /acik-arttirma-baslat - 2 dakikalık açık arttırma
    # ====================================================
    @app_commands.command(name="acik-arttirma-baslat", description="[TİCARET] Elinizdeki bir eşyayı 2 dakika sürecek bir açık arttırma pazarına çıkarır.")
    @app_commands.describe(esya_ad="Açık arttırmaya çıkacak eşyanın tam adı", baslangic_fiyati="Açılış akçe değeri")
    async def ihale_baslat(self, interaction: discord.Interaction, esya_ad: str, baslangic_fiyati: int):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Önce sığınağa kaydolmalısın!", ephemeral=True)
            return
        kontrol = sokak_ve_karantina_kontrolu(u_id)
        if kontrol:
            await interaction.response.send_message(kontrol, ephemeral=True)
            return
        if baslangic_fiyati < 1:
            await interaction.response.send_message("❌ Başlangıç fiyatı en az 1 Akçe olmalıdır!", ephemeral=True)
            return

        sakin = db["sakinler"][u_id]
        envanter = sakin.get("envanter", {})

        # TAM_PAZAR ile isim doğrulama (BUG FIX)
        gercek_esya_ad, _ = katalogdan_isim_bul(esya_ad)
        if not gercek_esya_ad:
            await interaction.response.send_message("❌ Bu eşya pazar kataloğunda bulunamadı!", ephemeral=True)
            return

        if envanter.get(gercek_esya_ad, 0) < 1:
            await interaction.response.send_message(f"❌ Sırt çantanızda açık arttırmaya çıkaracak `{gercek_esya_ad}` yok!", ephemeral=True)
            return

        # Eşyayı açık arttırma süresince envanterden düşüyoruz (güvenlik kilidi)
        envanter[gercek_esya_ad] -= 1
        if envanter[gercek_esya_ad] == 0:
            del envanter[gercek_esya_ad]
        verileri_kaydet()

        ilan_id = str(random.randint(1000, 9999))
        while ilan_id in db["acik_arttirmalar"]:
            ilan_id = str(random.randint(1000, 9999))

        db["acik_arttirmalar"][ilan_id] = {
            "satici_id": u_id,
            "satici_isim": sakin["isim"],
            "esya": gercek_esya_ad,
            "en_yuksek_pey": baslangic_fiyati,
            "en_son_peyleyen": None,
            "aktif": True,
            "kanal_id": interaction.channel_id
        }
        verileri_kaydet()

        embed = discord.Embed(title="📢 YENİ AÇIK ARTTIRMA İLANI", color=0x9B59B6)
        embed.description = (
            f"🏛️ **İlan Kodu:** `{ilan_id}`\n"
            f"👤 **Satıcı Sakin:** {interaction.user.mention}\n"
            f"📦 **Açık Arttırmadaki Eşya:** `{gercek_esya_ad}`\n"
            f"🪙 **Taban Açılış Fiyatı:** `{baslangic_fiyati} Akçe`\n\n"
            f"⏳ **Kalan Süre:** `2 Dakika (120 Saniye)`\n"
            f"ℹ️ Pey vermek için `/pey-ver ilan_id: {ilan_id} teklif_edilen_akçe: [Miktar]` komutunu kullanın!"
        )
        embed.set_footer(text="Süre dolduğunda en yüksek teklif sahibine otomatik teslim edilecektir.")
        await interaction.response.send_message(embed=embed)

        # 2 dakika bekle
        await asyncio.sleep(120)

        # İhale bitiş protokolü
        ihale = db["acik_arttirmalar"].get(ilan_id)
        if ihale and ihale["aktif"]:
            ihale["aktif"] = False
            bitis_embed = discord.Embed(title="🏁 AÇIK ARTTIRMA SÜRESİ DOLDU", color=0x34495E)

            if ihale["en_son_peyleyen"] is None:
                s_id = ihale["satici_id"]
                db["sakinler"][s_id]["envanter"][ihale["esya"]] = db["sakinler"][s_id].get("envanter", {}).get(ihale["esya"], 0) + 1
                bitis_embed.description = f"❌ `{ilan_id}` kodlu ilandaki `{ihale['esya']}` ürününe kimse teklif vermedi. Eşya sahibine iade edildi."
            else:
                alici_id = ihale["en_son_peyleyen"]
                satici_id = ihale["satici_id"]
                final_teklif = ihale["en_yuksek_pey"]

                idare_kesintisi = int(final_teklif * 0.05)
                satici_net_kazanc = final_teklif - idare_kesintisi

                db["sakinler"][satici_id]["cuzdan"] += satici_net_kazanc
                db["sistem_ayarlari"]["KASA_AKÇE_PLACEHOLDER"] += idare_kesintisi

                alici_env = db["sakinler"][alici_id].get("envanter", {})
                alici_env[ihale["esya"]] = alici_env.get(ihale["esya"], 0) + 1

                bitis_embed.description = (
                    f"🎉 **İhale Sonuçlandı!**\n\n"
                    f"📦 **Satılan Ürün:** `{ihale['esya']}`\n"
                    f"🏆 **Yeni Sahibi:** <@{alici_id}>\n"
                    f"💰 **Final Teklif Değeri:** `{final_teklif} Akçe`\n"
                    f"💸 **Satıcıya Aktarılan (%5 Vergisiz):** `{satici_net_kazanc} Akçe`"
                )
                bitis_embed.color = 0x2ECC71

            del db["acik_arttirmalar"][ilan_id]
            verileri_kaydet()

            kanal = self.bot.get_channel(ihale.get("kanal_id") or interaction.channel_id)
            if kanal:
                await kanal.send(embed=bitis_embed)
            else:
                await interaction.channel.send(embed=bitis_embed)

    @ihale_baslat.autocomplete("esya_ad")
    async def ihale_autocomplete(self, interaction: discord.Interaction, current: str):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            return []
        sakin_envanter = db["sakinler"][u_id].get("envanter", {})
        return [
            app_commands.Choice(name=f"{esya} ({adet} Adet)", value=esya)
            for esya, adet in sakin_envanter.items() if adet > 0 and current.lower() in esya.lower()
        ][:25]

    # ====================================================
    # /pey-ver - Aktif ilana teklif
    # ====================================================
    @app_commands.command(name="pey-ver", description="[TİCARET] Aktif bir açık arttırma ilanına mevcut tekliften daha yüksek akçe teklif eder.")
    @app_commands.describe(ilan_id="Teklif vereceğiniz 4 haneli ilan kodu", teklif_edilen_akçe="Gözden çıkardığınız yeni teklif tutarı")
    async def pey_ver(self, interaction: discord.Interaction, ilan_id: str, teklif_edilen_akçe: int):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Sığınak sicil kütüğünde kaydınız yok!", ephemeral=True)
            return
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return

        ihale = db["acik_arttirmalar"].get(ilan_id)
        if not ihale or not ihale["aktif"]:
            await interaction.response.send_message("❌ Bu kodda aktif bir açık arttırma ilanı bulunamadı!", ephemeral=True)
            return

        if ihale["satici_id"] == u_id:
            await interaction.response.send_message("❌ Kendi ilanına pey veremezsin!", ephemeral=True)
            return

        sakin = db["sakinler"][u_id]
        cuzdan = sakin.get("cuzdan", 0)

        if teklif_edilen_akçe <= ihale["en_yuksek_pey"]:
            await interaction.response.send_message(
                f"❌ Geçersiz teklif! Şu anki en yüksek teklif `{ihale['en_yuksek_pey']} Akçe`. Daha üstünü vermelisiniz!",
                ephemeral=True
            )
            return

        if cuzdan < teklif_edilen_akçe:
            await interaction.response.send_message(
                f"❌ Cüzdanınızda teklif ettiğiniz kadar `{teklif_edilen_akçe}` Akçe bulunmuyor!",
                ephemeral=True
            )
            return

        # Eski pey sahibine iade
        if ihale["en_son_peyleyen"] is not None:
            eski_alici_id = ihale["en_son_peyleyen"]
            db["sakinler"][eski_alici_id]["cuzdan"] += ihale["en_yuksek_pey"]

        # Yeni pey sahibinin parasını bloke et
        sakin["cuzdan"] -= teklif_edilen_akçe

        ihale["en_yuksek_pey"] = teklif_edilen_akçe
        ihale["en_son_peyleyen"] = u_id
        verileri_kaydet()

        pey_embed = discord.Embed(title="🔥 AÇIK ARTTIRMADA REKABET KIZIŞTI!", color=0xE17055)
        pey_embed.description = (
            f"🏛️ **İlan Kodu:** `{ilan_id}`\n"
            f"📦 **Eşya:** `{ihale['esya']}`\n"
            f"🚀 **Yeni En Yüksek Teklif:** `🪙 {teklif_edilen_akçe} Akçe`\n"
            f"👤 **Teklif Sahibi:** {interaction.user.mention}"
        )
        await interaction.response.send_message(embed=pey_embed)


# ====================================================
# VIEW SINIFLARI
# ====================================================
class EsyaSatView(discord.ui.View):
    def __init__(self, satici, alici, esya, fiyat):
        super().__init__(timeout=120)
        self.satici = satici
        self.alici = alici
        self.esya = esya
        self.fiyat = fiyat

    @discord.ui.button(label="💰 Satın Alımı Onayla", style=discord.ButtonStyle.success)
    async def onayla_sat(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.alici.id:
            await interaction.response.send_message("❌ Bu teklif senin adına yapılmamış!", ephemeral=True)
            return

        s_id = str(self.satici.id)
        a_id = str(self.alici.id)

        satici_env = db["sakinler"][s_id].get("envanter", {})
        alici_env = db["sakinler"][a_id].get("envanter", {})
        alici_cuzdan = db["sakinler"][a_id].get("cuzdan", 0)

        if satici_env.get(self.esya, 0) < 1:
            self.clear_items()
            await interaction.response.edit_message(content="❌ Satış iptal! Satıcının elinde o eşya kalmamış.", view=self)
            return
        if alici_cuzdan < self.fiyat:
            self.clear_items()
            await interaction.response.edit_message(content=f"❌ Satış iptal! Alıcının cüzdanında yeterli akçe yok. Gereken: `{self.fiyat}`", view=self)
            return

        db["sakinler"][a_id]["cuzdan"] -= self.fiyat
        db["sakinler"][s_id]["cuzdan"] += self.fiyat
        satici_env[self.esya] -= 1
        alici_env[self.esya] = alici_env.get(self.esya, 0) + 1
        if satici_env[self.esya] == 0:
            del satici_env[self.esya]
        verileri_kaydet()

        self.clear_items()
        await interaction.response.edit_message(
            content=f"💸 **DOĞRUDAN SATIŞ TAMAMLANDI!** {self.satici.mention}, {self.alici.mention} kullanıcısına `1 Adet {self.esya}` ürününü `{self.fiyat} Akçe` karşılığında el altından sattı!",
            view=self
        )

    @discord.ui.button(label="❌ Reddet", style=discord.ButtonStyle.danger)
    async def reddet_sat(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.alici.id:
            await interaction.response.send_message("❌ Bu teklifi reddetme yetkin yok!", ephemeral=True)
            return
        self.clear_items()
        await interaction.response.edit_message(content=f"❌ {self.alici.mention} doğrudan satış teklifini reddetti.", view=self)


class TakasOnayView(discord.ui.View):
    def __init__(self, davet_eden, davet_edilen, v_esya, i_esya):
        super().__init__(timeout=120)
        self.davet_eden = davet_eden
        self.davet_edilen = davet_edilen
        self.v_esya = v_esya
        self.i_esya = i_esya
        self.eden_onay = False
        self.edilen_onay = False

    @discord.ui.button(label="✅ Takası Onayla", style=discord.ButtonStyle.success)
    async def onayla(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.davet_eden.id:
            self.eden_onay = True
        elif interaction.user.id == self.davet_edilen.id:
            self.edilen_onay = True
        else:
            await interaction.response.send_message("❌ Bu takas teklifine dahil değilsin!", ephemeral=True)
            return

        if self.eden_onay and self.edilen_onay:
            eden_id = str(self.davet_eden.id)
            edilen_id = str(self.davet_edilen.id)

            eden_env = db["sakinler"][eden_id].get("envanter", {})
            edilen_env = db["sakinler"][edilen_id].get("envanter", {})

            # Son kontrol
            if eden_env.get(self.v_esya, 0) < 1 or edilen_env.get(self.i_esya, 0) < 1:
                self.clear_items()
                await interaction.response.edit_message(content="❌ Takas iptal! Taraflardan birinin envanteri yetersiz.", view=self)
                return

            eden_env[self.v_esya] -= 1
            edilen_env[self.i_esya] -= 1
            eden_env[self.i_esya] = eden_env.get(self.i_esya, 0) + 1
            edilen_env[self.v_esya] = edilen_env.get(self.v_esya, 0) + 1

            if eden_env[self.v_esya] == 0:
                del eden_env[self.v_esya]
            if edilen_env[self.i_esya] == 0:
                del edilen_env[self.i_esya]

            verileri_kaydet()
            self.clear_items()
            await interaction.response.edit_message(
                content=f"🤝 **TAKAS TAMAMLANDI!** {self.davet_eden.mention} ↔️ {self.davet_edilen.mention}\n• `{self.v_esya}` ⇄ `{self.i_esya}`",
                view=self
            )
        else:
            bekleyen = []
            if not self.eden_onay:
                bekleyen.append(self.davet_eden.mention)
            if not self.edilen_onay:
                bekleyen.append(self.davet_edilen.mention)
            await interaction.response.send_message(
                f"✅ Onayın alındı! Şu kişilerin onayı bekleniyor: {', '.join(bekleyen)}",
                ephemeral=True
            )


# ====================================================
# VIEW - PAZAR DROPDOWN (kategori seçim menüsü)
# ====================================================
class PazarView(discord.ui.View):
    """Pazar kategori seçim menüsü. /pazar komutunda kullanılır."""
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(PazarDropdown())


class PazarDropdown(discord.ui.Select):
    """Pazar kategorilerini içeren dropdown. Kullanıcı kategori seçince o kategorinin eşyalarını gösterir."""
    def __init__(self):
        options = [
            discord.SelectOption(label="Silahlar", description="Kılıç, kama, yay, gürz, mızrak", value="Silah", emoji="⚔️"),
            discord.SelectOption(label="Zırhlar", description="Göğüslük, zincir, plaka zırh", value="Zırh", emoji="🛡️"),
            discord.SelectOption(label="Medikal Ürünler", description="Bandaj, serum, iksir, tentür", value="Medikal", emoji="💊"),
            discord.SelectOption(label="Gıda Ürünleri", description="Ekmek, et, su, bira, bal", value="Gıda", emoji="🍲"),
            discord.SelectOption(label="Hammaddeler", description="Demir, odun, kömür, deri", value="Hammadde", emoji="🪵"),
            discord.SelectOption(label="Teknoloji Ögeleri", description="Dişli, teleskop, dinamit", value="Teknoloji", emoji="⚙️"),
            discord.SelectOption(label="Mistik Nesneler", description="Rün, tılsım, sancak, idol", value="Mistik", emoji="🔮"),
        ]
        super().__init__(placeholder="📂 Pazar kategorisi seç...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        kategori = self.values[0]
        kategori_emoji = {
            "Silah": "⚔️", "Zırh": "🛡️", "Medikal": "💊", "Gıda": "🍲",
            "Hammadde": "🪵", "Teknoloji": "⚙️", "Mistik": "🔮"
        }

        embed = discord.Embed(
            title=f"{kategori_emoji.get(kategori, '🛒')} SIĞINAK PAZAR TEZGAHI — {kategori.upper()}",
            color=0x2ECC71
        )
        embed.description = "*Satın almak için `/satinal` komutunu kullan: `/satinal esya_kodu: adet:`*\n\n"

        sayac = 0
        for kod, veri in TAM_PAZAR.items():
            if veri["tip"] != kategori:
                continue
            sayac += 1
            if sayac > 24:
                embed.description += "\n*... ve daha fazla eşya.*"
                break
            embed.add_field(
                name=f"📦 `{kod}` — {veri['isim']}",
                value=f"💰 `{veri['fiyat']}` Akçe | Etki: `+{veri['bonus_degeri']} {veri['bonus_turu']}`\n*{veri['aciklama']}*",
                inline=False
            )

        if sayac == 0:
            embed.description = "❌ Bu kategoride şu an eşya yok."

        embed.set_footer(text="Sığınak Veba RP v5.5 | Başka kategori için tekrar seçim yap")
        
        yeni_view = PazarView()
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, view=yeni_view, ephemeral=True)
        else:
            await interaction.response.edit_message(embed=embed, view=yeni_view)


async def setup(bot):
    await bot.add_cog(PazarCog(bot))

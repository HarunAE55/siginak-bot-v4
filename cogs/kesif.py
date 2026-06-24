"""
Cog: Keşif & Anıt (v5.9)
=========================
Komutlar:
- /gez (6 saat cooldown, %50 olumlu / %30 olumsuz / %20 gizemli, 30+ olay, büyük ödül/ceza)
- /anit (sığınak şeref listesi ve şehitler)

Önemli: /gez sonucu hem komutun kullanıldığı kanala, hem de ilgili RP bölge kanalına gönderilir.

v5.9 Değişiklikler:
- BUG FIX: xp_ekle çağrısında sakin.get("id","") yerine u_id kullanılıyor (önceden boş string dönüyordu)
- BUG FIX: Anıt sıralama XP yerine seviye*100+xp ile yapılıyor
- Temizlik: _bolge_kanal_bul artık kanallar.py'deki importları kullanıyor (duplicate ID yok)
- Bar görsellerinde enfeksiyon kırmızı/sarı gösteriliyor
"""

import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import datetime

from veritabani import (
    db, verileri_kaydet, olu_kontrolu, bar_olustur,
    sokak_ve_karantina_kontrolu, xp_ekle, haber_ekle
)
from kanallar import (
    ZAYIF_SURLAR, TOPRAK_YOL, BOS_EV_1, TARLA, SURLARIN_CEVRESI,
    MEYDAN_AGACI, PAZAR_YERI, BELEDIYE_BINASI, BASKAN_SALONU,
    KARANTINA_KAMPI, MEZARLIK, YESIL_KISLA, HASTANE, SIMYACININ_KULESI,
    KULENIN_TEPESI, KARANLIK_ORMAN_YOLU_BATI, KUZEY_PAZAR, HAN,
    SU_KUYUSU, IHTISAMLI_HANE, MADEN_OCAGI, ONDERIN_KOSKU,
    ODUNCUNUN_YERI, SIRLAR_MAGARASI, GIZEMLI_BATAKLIK
)


# ====================================================
# KEŞİF OLAY HAVUZU - BÜYÜK ÖDÜL/CEZA, 30 OLAY
# ====================================================
# Format: ("Açıklama metni", "etki_kodu")
# Etki kodları: akçe+/-N, saglik+/-N, su+/-N, akil+/-N, moral+/-N, enfeksiyon+/-N,
#               xp+N, odun+N, komur+N, erzak+N, enfeksiyon_temizle (kısmi)

# 10 OLUMLU OLAY - Büyük ödüller
OLUMLU_OLAYLAR = [
    ("🎒 Terkedilmiş bir kulübede eski bir tüccarın deri kesesi buldun! İçinden `+150 Akçe` çıktı.", "akçe+150"),
    ("🍎 Yabani bir elma bahçesine rastladın, taze meyvelerle karnını doyurdun. Su seviyen `+25` arttı, sağlığın `+15` iyileşti.", "su_saglik+25+15"),
    ("🪓 Yere düşmüş karaçam kütükleri buldun, köy ambarına `+25 Odun` taşıdın ve `+40 XP` kazandın.", "odun_xp+25+40"),
    ("🕯️ Yıkık bir şapelde yanan bir mum buldun, kısa dua ile aklın `+20` dinginleşti ve `+80 Akçe` bağışı buldun.", "akil_akçe+20+80"),
    ("🧴 Ölü bir gezginin çantasından sızdırmaz bir su tulumu ve kesesi çıktı. `+120 Akçe` edecek değerde ganimet!", "akçe+120"),
    ("🏹 Gölgede unutulmuş bir ok çantası buldun, içinde birkaç ok hâlâ kullanılabilir. `+50 XP` ve `+60 Akçe` kazandın.", "xp_akçe+50+60"),
    ("💰 Yıkık bir hanenin temelinde gömülü bir çömlek buldun! İçinde `+250 Akçe`lik eski bir servet!", "akçe+250"),
    ("🍷 Mahzende unutulmuş bir şarap fıçısı keşfettin. Bir yudum aldın, moralin `+30` yükseldi ve aklın `+15` berraklaştı.", "moral_akil+30+15"),
    ("📜 Bir rahibin cesedinden kutsal bir parşömen düştü. Üzerindeki dua seni `+20 Sağlık` iyileştirdi.", "saglik+20"),
    ("⛏️ Sığ bir maden ocağında terk edilmiş `+15 Kömür` ve `+10 Demir Cevheri` buldun, köy ambarına taşıdın!", "komur+15"),
]

# 10 OLUMSUZ OLAY - Büyük cezalar
OLUMSUZ_OLAYLAR = [
    ("🐀 Lağım fareleri sürü halinde saldırdı! Kaçtın ama ısırıklardan `+25 Enfeksiyon` yükü aldın ve `+10 Sağlık` kaybettin.", "enfeksiyon_saglik+25-10"),
    ("🧟 Putrefakt bir cesetle karşılaştın! Dehşet içinde kaçarken cüzdanından `-80 Akçe` düştü.", "akçe-80"),
    ("🌫️ Mezarlığın üzerinden veba bulutu geçti, soluğun kesildi. Moralin `-25` düştü, enfeksiyonun `+15` arttı.", "moral_enfeksiyon-25+15"),
    ("🕷️ Dehlizde devasa bir örümcek ağına yakalandın! Kurtulurken cildin yaralandı, sağlığın `-25` azaldı.", "saglik-25"),
    ("💨 Çürümüş ceset kokusu her yere sinmiş, miden bulandı. Su seviyen `-25` düştü, sağlığın `-10` azaldı.", "su_saglik-25-10"),
    ("🦇 Mağaradan yarasalar sürü halinde üzerine saldırdı! Panikle aklın `-20` karaldı ve `+10 Enfeksiyon` kaptın.", "akil_enfeksiyon-20+10"),
    ("💀 Bataklıkta gizli bir çukura düştün! Kurtuldun ama `+30 Enfeksiyon` ve `-30 Akçe` kaybettin.", "enfeksiyon_akçe+30-30"),
    ("🗡️ Haydutlar pusuya düşürdü seni! `+20 Sağlık` hasarı aldın ve `-100 Akçe` soyuldun.", "saglik_akçe-20-100"),
    ("☠️ Zombi sürüsü seni kıstırdı! Zar zor kurtuldun ama `+35 Enfeksiyon` kaptın ve `+20 Sağlık` kaybettin.", "enfeksiyon_saglik+35-20"),
    ("🔥 Bir kulübede çıkan yangında `+15 Sağlık` hasarı aldın, kurtardığın tek şey olduğun `+10 Akıl Sağlığı` kaybı oldu.", "saglik_akil-15-10"),
]

# 10 GİZEMLİ OLAY - Rünler, kutsamalar, paranormal
GIZEMLI_OLAYLAR = [
    ("🌀 Yıkık kilisenin sunağında parlayan garip bir rün buldun... Rün kayboldu ama vücudundaki tüm yaralar `+25 Sağlık` ile kapandı!", "saglik+25"),
    ("🔮 Bir mezar taşının altında kadim bir parşömen parçası buldun, üzerindeki rünler zihnini açtı! `+60 XP` kazandın.", "xp+60"),
    ("⚰️ Gece mezarlıkta bir rahibin hayaletiyle karşılaştın! Seni kutsadı ve enfeksiyon yükünü `-30` azalttı.", "enfeksiyon-30"),
    ("👁️ Göz bebeksiz bir idol heykelciği buldun, sana bakıyor gibi. Heyecanla `+100 Akçe`lik bir hazine keşfettin ama aklın `-15` karaldı.", "akçe_akil+100-15"),
    ("🌟 Gökyüzünden düşen parlak bir taş buldun, dokunduğunda sağlığın `+30` iyileşti ve `+40 XP` kazandın.", "saglik_xp+30+40"),
    ("🪞 Eski bir aynaya baktın, yansıtan yüzün değil başka biri! Şok oldu aklın `-20` ama o sırada `+150 Akçe` buldun.", "akil_akçe-20+150"),
    ("🕯️ Yanan mumlar senden ayrı yürümeye başladı, korktun ama onlar seni bir hazineye götürdü: `+200 Akçe`.", "akçe+200"),
    ("🦉 Bir baykuş konuşarak sana bir kehanet verdi. Kehanet kafa karıştırıcıydı (`-10 Akıl`) ama `+50 XP` kazandın.", "akil_xp-10+50"),
    ("🌊 Gizli bir yer altı nehrinde yıkandın, tüm yorgunluğun gitti! Sağlık `+15`, su `+30`, akıl `+10`.", "hepsi+15+30+10"),
    ("💫 Yere düşen bir yıldız taşını buldun, mucizevi! Enfeksiyon `-20`, sağlık `+20`, moral `+20`.", "ferahlat-20+20+20"),
]


# ====================================================
# OLAY ETKİ UYGULAMA FONKSİYONU
# ====================================================
def olay_ekisini_uygula(sakin_id: str, sakin: dict, etki: str) -> str:
    """v5.9 FIX: sakin_id parametre olarak alınır (önceden sakin.get('id','') kullanılıyordu ve hep '' dönüyordu).
    Etki kodunu sakine uygular. Ek rapor metni döner.
    """
    ek_metin = ""

    # Tekli etkiler (akçe+N, saglik-N, vb.)
    if "+" in etki and "_" not in etki:
        parca = etki.split("+")
        tur = parca[0]
        miktar = int(parca[1]) if len(parca) > 1 else 0
        _tekli_etki(sakin_id, sakin, tur, miktar, +1)
    elif "-" in etki and "_" not in etki and not etki.startswith("-"):
        parca = etki.split("-")
        tur = parca[0]
        miktar = int(parca[1]) if len(parca) > 1 else 0
        _tekli_etki(sakin_id, sakin, tur, miktar, -1)
    elif etki == "enfeksiyon_temizle":
        sakin["enfeksiyon"] = 0
        ek_metin = " (Enfeksiyon tamamen temizlendi!)"

    # İkili/üçlü etkiler (su_saglik+25+15, akil_akçe-20+150, ferahlat-20+20+20 vb.)
    elif "_" in etki:
        parcalar = etki.replace("_", " ").replace("+", " +").replace("-", " -").split()
        turler = []
        sayilar = []
        for p in parcalar:
            if p.startswith("+") or p.startswith("-"):
                sayilar.append(int(p))
            else:
                turler.append(p)

        for i, tur in enumerate(turler):
            if i < len(sayilar):
                miktar = sayilar[i]
                yon = +1 if miktar >= 0 else -1
                _tekli_etki(sakin_id, sakin, tur, abs(miktar), yon)

    return ek_metin


def _tekli_etki(sakin_id: str, sakin: dict, tur: str, miktar: int, yon: int):
    """Tek bir stat'a etki uygular. yon: +1 artış, -1 azalış.
    v5.9 FIX: xp artık doğru sakin_id ile xp_ekle'ye gidiyor (seviye atlama tetikleniyor)."""
    if tur == "akçe":
        if yon > 0:
            sakin["cuzdan"] = sakin.get("cuzdan", 0) + miktar
        else:
            sakin["cuzdan"] = max(0, sakin.get("cuzdan", 0) - miktar)
    elif tur == "saglik":
        if yon > 0:
            sakin["saglik"] = min(100, sakin.get("saglik", 100) + miktar)
        else:
            sakin["saglik"] = max(0, sakin.get("saglik", 100) - miktar)
    elif tur == "su":
        if yon > 0:
            sakin["su"] = min(100, sakin.get("su", 100) + miktar)
        else:
            sakin["su"] = max(0, sakin.get("su", 100) - miktar)
    elif tur == "akil":
        if yon > 0:
            sakin["akil_sagligi"] = min(100, sakin.get("akil_sagligi", 100) + miktar)
        else:
            sakin["akil_sagligi"] = max(0, sakin.get("akil_sagligi", 100) - miktar)
    elif tur == "moral":
        if yon > 0:
            sakin["moral"] = min(100, sakin.get("moral", 50) + miktar)
        else:
            sakin["moral"] = max(0, sakin.get("moral", 50) - miktar)
    elif tur == "enfeksiyon":
        if yon > 0:
            sakin["enfeksiyon"] = min(100, sakin.get("enfeksiyon", 0) + miktar)
        else:
            sakin["enfeksiyon"] = max(0, sakin.get("enfeksiyon", 0) - miktar)
    elif tur == "xp":
        if yon > 0:
            # v5.9 FIX: sakin_id artık doğru geliyor, seviye atlama çalışıyor
            xp_ekle(sakin_id, miktar)
            # xp_ekle zaten sakin["xp"]'i güncelliyor, tekrar ekleme yapma
    elif tur == "odun":
        if yon > 0:
            db["koy_ambari"]["stoklar"]["odun"] = db["koy_ambari"]["stoklar"].get("odun", 0) + miktar
    elif tur == "komur":
        if yon > 0:
            db["koy_ambari"]["stoklar"]["komur"] = db["koy_ambari"]["stoklar"].get("komur", 0) + miktar
    elif tur == "erzak":
        if yon > 0:
            db["koy_ambari"]["stoklar"]["erzak"] = db["koy_ambari"]["stoklar"].get("erzak", 0) + miktar
    elif tur == "ferahlat":
        # Özel: enfeksiyon -, sağlık +, moral +
        if yon > 0:
            sakin["enfeksiyon"] = max(0, sakin.get("enfeksiyon", 0) - miktar)
            sakin["saglik"] = min(100, sakin.get("saglik", 100) + miktar)
            sakin["moral"] = min(100, sakin.get("moral", 50) + miktar)


# ====================================================
# COG SINIFI
# ====================================================
class KesifCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ====================================================
    # /gez - 6 saat CD, %50 olumlu / %30 olumsuz / %20 gizemli
    # ====================================================
    @app_commands.command(name="gez", description="[KEŞİF] Sığınak sınırlarından çıkıp riskli dış bölgelere seyahat eder (6 saat cooldown).")
    @app_commands.choices(bolge=[
        app_commands.Choice(name="🛡️ Zayıf Surlar", value="Zayıf Surlar"),
        app_commands.Choice(name="🍂 Toprak Yol", value="Toprak Yol"),
        app_commands.Choice(name="🏠 Boş Ev", value="Boş Ev"),
        app_commands.Choice(name="🌾 Tarla", value="Tarla"),
        app_commands.Choice(name="🛡️ Surların Çevresi", value="Surların Çevresi"),
        app_commands.Choice(name="🌳 Meydan Ağacı", value="Meydan Ağacı"),
        app_commands.Choice(name="🪙 Pazar Yeri", value="Pazar Yeri"),
        app_commands.Choice(name="🏛️ Belediye Binası", value="Belediye Binası"),
        app_commands.Choice(name="⚖️ Başkan Salonu", value="Başkan Salonu"),
        app_commands.Choice(name="⛺ Karantina Kampı", value="Karantina Kampı"),
        app_commands.Choice(name="🪦 Mezarlık", value="Mezarlık"),
        app_commands.Choice(name="⚔️ Yeşil Kışla", value="Yeşil Kışla"),
        app_commands.Choice(name="🌿 Hastane", value="Hastane"),
        app_commands.Choice(name="🧪 Simyacının Kulesi", value="Simyacının Kulesi"),
        app_commands.Choice(name="🪜 Kulenin Tepesi", value="Kulenin Tepesi"),
        app_commands.Choice(name="🍂 Karanlık Orman Yolu", value="Karanlık Orman Yolu"),
        app_commands.Choice(name="🪙 Kuzey Pazar", value="Kuzey Pazar"),
        app_commands.Choice(name="🍺 Han", value="Han"),
        app_commands.Choice(name="💧 Su Kuyusu", value="Su Kuyusu"),
        app_commands.Choice(name="⛪ İhtişamlı Hane", value="İhtişamlı Hane"),
        app_commands.Choice(name="⛏️ Maden Ocağı", value="Maden Ocağı"),
        app_commands.Choice(name="🏰 Önderin Köşkü", value="Önderin Köşkü"),
        app_commands.Choice(name="🪵 Oduncunun Yeri", value="Oduncunun Yeri"),
        app_commands.Choice(name="🪨 Sırlar Mağarası", value="Sırlar Mağarası"),
        app_commands.Choice(name="🌿 Gizemli Bataklık", value="Gizemli Bataklık"),
    ])
    async def cografi_gez(self, interaction: discord.Interaction, bolge: str):
        u_id = str(interaction.user.id)

        if u_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Sicil kaydın yok!", ephemeral=True)
            return

        kontrol = sokak_ve_karantina_kontrolu(u_id)
        if kontrol:
            await interaction.response.send_message(kontrol, ephemeral=True)
            return

        sakin = db["sakinler"][u_id]

        # 6 SAAT COOLDOWN
        son_gezi = sakin.get("son_gezi")
        if son_gezi:
            fark = datetime.datetime.now() - datetime.datetime.fromisoformat(son_gezi)
            if fark.total_seconds() < 21600:  # 6 saat = 21600 sn
                kalan_saat = int((21600 - fark.total_seconds()) / 3600)
                kalan_dk = int(((21600 - fark.total_seconds()) % 3600) / 60)
                await interaction.response.send_message(
                    f"❌ Yorgunsun, dinlenmen gerekiyor! **{bolge}** bölgesine tekrar gitmek için `{kalan_saat} saat {kalan_dk} dakika` beklemelisin.",
                    ephemeral=True
                )
                return

        # Yola çıktı mesajı
        await interaction.response.send_message(
            f"🥾 {interaction.user.mention}, çantanı hazırladın ve `{bolge}` bölgesine doğru yola çıktın... Kader zarın atılıyor!",
            ephemeral=False
        )

        # RP kanalına kısa bildiri
        try:
            rp_kanal_id = self._bolge_kanal_bul(bolge)
            if rp_kanal_id:
                rp_kanal = self.bot.get_channel(rp_kanal_id)
                if rp_kanal:
                    await rp_kanal.send(f"🥾 **{sakin.get('isim', interaction.user.display_name)}** yola çıktı, bu bölgeden geçiyor...")
        except Exception:
            pass

        # 3 saniye bekle (dramatik etki)
        await asyncio.sleep(3)

        # ZAR AT - %50 olumlu / %30 olumsuz / %20 gizemli
        zar = random.randint(1, 10)
        if zar <= 5:  # 1-5: %50 olumlu
            secilen_olay, etki = random.choice(OLUMLU_OLAYLAR)
            embed_renk = 0x2ECC71
            kategori = "OLUMLU"
        elif zar <= 8:  # 6-8: %30 olumsuz
            secilen_olay, etki = random.choice(OLUMSUZ_OLAYLAR)
            embed_renk = 0xC0392B
            kategori = "OLUMSUZ"
        else:  # 9-10: %20 gizemli
            secilen_olay, etki = random.choice(GIZEMLI_OLAYLAR)
            embed_renk = 0x9B59B6
            kategori = "GİZEMLİ"

        # Etkiyi uygula - v5.9 FIX: sakin_id parametre olarak veriliyor
        ek_metin = olay_ekisini_uygula(u_id, sakin, etki)

        # Cooldown kaydı
        sakin["son_gezi"] = datetime.datetime.now().isoformat()
        verileri_kaydet()

        # Embed oluştur
        embed = discord.Embed(title=f"🗺️ SEFARET RAPORU: {bolge}", color=embed_renk)
        if ek_metin:
            embed.description = (
                f"👣 {interaction.user.mention}, seyahatin sırasında:\n\n"
                f"**{secilen_olay}**\n\n"
                f"_{ek_metin}_"
            )
        else:
            embed.description = (
                f"👣 {interaction.user.mention}, seyahatin sırasında:\n\n"
                f"**{secilen_olay}**"
            )
        embed.set_footer(text=f"Kategori: {kategori} | Zar: {zar}/10 | Cooldown: 6 saat | Sığınak Veba RP v5.9.1")

        await interaction.channel.send(embed=embed)

        # Gazeteye haber ekle
        haber_ekle(f"🥾 {sakin.get('isim', interaction.user.name)} {bolge} bölgesine gezi düzenledi. ({kategori})")

        # RP kanalına sonucu da gönder
        try:
            rp_kanal_id = self._bolge_kanal_bul(bolge)
            if rp_kanal_id:
                rp_kanal = self.bot.get_channel(rp_kanal_id)
                if rp_kanal:
                    rp_embed = discord.Embed(
                        title=f"🗺️ {bolge} - Gezi Raporu",
                        color=embed_renk,
                        description=f"👣 **{sakin.get('isim', interaction.user.display_name)}** bölgeden geçti:\n\n{secilen_olay}"
                    )
                    await rp_kanal.send(embed=rp_embed)
        except Exception:
            pass


    def _bolge_kanal_bul(self, bolge: str):
        """Bölge adından RP kanal ID'sini bul.
        v5.9: Artık kanallar.py'deki importları kullanıyor (duplicate yok)."""
        eslesme = {
            "Zayıf Surlar": ZAYIF_SURLAR,
            "Toprak Yol": TOPRAK_YOL,
            "Boş Ev": BOS_EV_1,
            "Tarla": TARLA,
            "Surların Çevresi": SURLARIN_CEVRESI,
            "Meydan Ağacı": MEYDAN_AGACI,
            "Pazar Yeri": PAZAR_YERI,
            "Belediye Binası": BELEDIYE_BINASI,
            "Başkan Salonu": BASKAN_SALONU,
            "Karantina Kampı": KARANTINA_KAMPI,
            "Mezarlık": MEZARLIK,
            "Yeşil Kışla": YESIL_KISLA,
            "Hastane": HASTANE,
            "Simyacının Kulesi": SIMYACININ_KULESI,
            "Kulenin Tepesi": KULENIN_TEPESI,
            "Karanlık Orman Yolu": KARANLIK_ORMAN_YOLU_BATI,
            "Kuzey Pazar": KUZEY_PAZAR,
            "Han": HAN,
            "Su Kuyusu": SU_KUYUSU,
            "İhtişamlı Hane": IHTISAMLI_HANE,
            "Maden Ocağı": MADEN_OCAGI,
            "Önderin Köşkü": ONDERIN_KOSKU,
            "Oduncunun Yeri": ODUNCUNUN_YERI,
            "Sırlar Mağarası": SIRLAR_MAGARASI,
            "Gizemli Bataklık": GIZEMLI_BATAKLIK,
        }
        return eslesme.get(bolge)

    # ====================================================
    # /anit - Şeref listesi ve şehitler
    # ====================================================
    @app_commands.command(name="anit", description="Sığınak meydanındaki kadim anitı, kuralları ve şeref listesini görüntüler.")
    async def anit_goruntule(self, interaction: discord.Interaction):
        # v5.9 FIX: XP yerine seviye*100+xp ile sırala (gerçek deneyim puanı)
        sirali_sakinler = sorted(
            db["sakinler"].items(),
            key=lambda x: (x[1].get("seviye", 1) * 100) + x[1].get("xp", 0),
            reverse=True
        )[:3]

        seref_kursusu = ""
        madalyalar = ["🥇", "🥈", "🥉"]
        for i, (s_id, veri) in enumerate(sirali_sakinler):
            seviye = veri.get("seviye", 1)
            xp = veri.get("xp", 0)
            seref_kursusu += f"{madalyalar[i]} **{veri.get('isim', 'Bilinmeyen Kahraman')}** - `Seviye {seviye} ({xp} XP)`\n"

        # Şehitler listesi
        olu_sakinler = [(s_id, v) for s_id, v in db["sakinler"].items() if v.get("durum") == "Ölü"]
        sehit_listesi = ""
        if olu_sakinler:
            for s_id, veri in olu_sakinler[:20]:  # İlk 20
                isim = veri.get("isim", "Bilinmeyen")
                soyisim = veri.get("soyisim", "")
                meslek = veri.get("meslek_isim", "Gezgin")
                sehit_listesi += f"⚰️ **{isim} {soyisim}** — *{meslek}*\n"
            if len(olu_sakinler) > 20:
                sehit_listesi += f"*... ve {len(olu_sakinler) - 20} şehit daha.*\n"
        else:
            sehit_listesi = "*Henüz sığınak için can veren olmamış.*\n"

        embed = discord.Embed(title="🏛️ SIĞINAK MEYDANI KADİM BAŞARI ANITI", color=0xF1C40F)
        embed.description = (
            "📜 **SIĞINAK TEMEL KANUNLARI:**\n"
            "1. Belediye başkanının sözü emirdir, aksini iddia etmek isyandır.\n"
            "2. Mahkeme kararlarına ve hücre cezalarına karşı gelmek darbe sebebi sayılır.\n"
            "3. Kilise kurallarına uymayanlar engizisyon tarafından afaroz edilir.\n"
            "4. Ölü bir karakter tüm eşyalarını kaybeder, yeniden `/kayit` olmak zorundadır.\n"
            "5. 6 saatten az sürede tekrar gezi yapılamaz.\n\n"
            "✨ **SIĞINAK KAHRAMANLARI ŞEREF KÜRSÜSÜ:**\n" + (seref_kursusu or "*Henüz anita adı kazınan bir kahraman yok.*\n") + "\n"
            "💀 **ŞEHİTLER DUVARI — Sığınak İçin Can Verenler:**\n" + sehit_listesi + "\n"
            f"📅 **Kuruluş Tarihi:** Sığınak kapıları `03.01.2026` tarihinde mühürlenerek hayata başlamıştır."
        )
        embed.set_footer(text="Sığınak Veba RP v5.9.1")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(KesifCog(bot))

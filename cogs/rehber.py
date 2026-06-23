"""
Cog: Yardim & Rehber & Gazete
=============================
Komutlar:
- /yardim (dropdown ile kategori secimli tum komutlar)
- /rehber (dropdown ile kategori secimli detayli yardim)
- /haber (admin, gazete kanali ayarlar)
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks
import datetime

from veritabani import db, verileri_kaydet, haber_ekle, admin_mi
from kanallar import GAZETE_KANAL_ID


class RehberCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.alti_saatlik_gazete_task.start()

    def cog_unload(self):
        self.alti_saatlik_gazete_task.cancel()

    @tasks.loop(hours=6)
    async def alti_saatlik_gazete_task(self):
        kanal_id = db["gazete_sistemi"].get("haber_kanali_id") or GAZETE_KANAL_ID
        if not kanal_id:
            return
        kanal = self.bot.get_channel(kanal_id)
        if not kanal:
            return
        olaylar = db["gazete_sistemi"].get("olay_gunlugu", [])
        embed = discord.Embed(title="ŞEHIR GAZETESI & SIGINAK BULTENI", color=0x7F8C8D)
        if self.bot.user and self.bot.user.avatar:
            embed.set_author(name="Siginak Resmi Matbaasi", icon_url=self.bot.user.avatar.url)
        bulten = "\n".join(olaylar[-30:]) if olaylar else "*Bu 6 saatlik donemde siginak sokaklari oldukca sessizdi...*"
        sur_can = db["sefer_sistemi"].get("sur_cani", 500)
        maks_sur = db["sefer_sistemi"].get("maks_sur_cani", 500)
        sur_yuzde = int((sur_can / maks_sur) * 100) if maks_sur > 0 else 0
        embed.description = (
            f"**Donem:** Son 6 Saatin Ozeti\n"
            f"**Salgin Durumu:** Taramalar devam ediyor.\n"
            f"**Sur Saglamligi:** %{sur_yuzde}\n"
            f"**Aktif Sakin:** {len([s for s in db['sakinler'].values() if s.get('durum') != 'Olu'])}\n"
            f"**Ortak Kasa:** {db['sistem_ayarlari'].get('kasa_hurda', 0)} Akce\n\n"
            f"**MANSITLER:**\n{bulten}"
        )
        try:
            await kanal.send(embed=embed)
        except Exception as e:
            print(f"Gazete hatasi: {e}")
        db["gazete_sistemi"]["olay_gunlugu"] = []
        db["gazete_sistemi"]["son_gazete_timestamp"] = datetime.datetime.now().isoformat()
        verileri_kaydet()

    @alti_saatlik_gazete_task.before_loop
    async def before_gazete_task(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="yardim", description="Siginak botunun tum komutlarini kategori secerek ogren.")
    async def yardim_komutu(self, interaction: discord.Interaction):
        embed = discord.Embed(title="SIGINAK VEBEA RP - KOMUT MERKEZI", color=0x2C3E50)
        if self.bot.user and self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.description = (
            "**Hos geldin sakin!**\n\n"
            "Asagidaki menuden bir kategori secerek o kategoriye ait tum komutlari gorebilirsin.\n\n"
            "**Kategoriler:**\n"
            "Kayit & Profil | Pazar & Ticaret | Siyaset & Yonetim\n"
            "Yargi & Ceza | Engizisyon & Rahip | Saglik & Simya\n"
            "Kolluk & Savunma | Uretim & Ambar | Savas & Kesif\n"
            "Ekonomi & Cevre | Yonetim & Admin\n\n"
            "Ipucu: Komutlar hem /slash hem v.prefix ile calisir."
        )
        embed.set_footer(text="Siginak Veba RP v5.7 | Kategori secmek icin asagidaki menuyu kullan")
        view = YardimView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="rehber", description="Detayli rehber. Kategori secerek her sistemi ogren.")
    async def rehber_komutu(self, interaction: discord.Interaction):
        embed = discord.Embed(title="SIGINAK REHBERI - Detayli Bilgi", color=0x9B59B6)
        embed.description = (
            "**Detayli Rehber Sistemi**\n\n"
            "Asagidaki menuden bir kategori sec. Sectigin kategoride:\n"
            "Komutlarin nasil kullanilacagini, ne ise yaradigini,\n"
            "ornek kullanimlari ve ipuclarini gorebilirsin.\n\n"
            "Yeni baslayanlar icin: Kayit & Profil kategorisinden basla!"
        )
        embed.set_footer(text="Siginak Veba RP v5.7 | Detayli rehber")
        view = YardimView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="haber", description="[YETKILI] Otomatik 6 saatlik gazetenin yazilacagi kanali belirler.")
    @app_commands.describe(kanal="Haber bultenlerinin akacagi kanal")
    async def haber_kanali_ayarla(self, interaction: discord.Interaction, kanal: discord.TextChannel):
        if not admin_mi(interaction):
            await interaction.response.send_message("Bu komut sadece yonetici ekibine ozeldir!", ephemeral=True)
            return
        db["gazete_sistemi"]["haber_kanali_id"] = kanal.id
        verileri_kaydet()
        await interaction.response.send_message(f"Basin Ofisi Kuruldu! Haberler artik {kanal.mention} kanalina yazilacak!")
        haber_ekle(f"Basin Ofisi {kanal.name} kanalinda faaliyetlerine basladi.")


class YardimView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(YardimDropdown())


class YardimDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Kayit & Profil", description="Karakter olusturma, profil, envanter, biyografi", value="kayit", emoji="📝"),
            discord.SelectOption(label="Pazar & Ticaret", description="Alim satim, acik arttirma, takas, tuketim", value="pazar", emoji="🛒"),
            discord.SelectOption(label="Siyaset & Yonetim", description="Secim, baskanlik, atama, maas", value="yonetim", emoji="🏛️"),
            discord.SelectOption(label="Yargi & Ceza", description="Mahkeme, hucre, darbe, sokak yasagi", value="yargi", emoji="⚖️"),
            discord.SelectOption(label="Engizisyon & Rahip", description="Afaroz, kutsama, kilise cani", value="kilise", emoji="⛪"),
            discord.SelectOption(label="Saglik & Simya", description="Asi, tedavi, deney, laboratuvar", value="simya", emoji="💊"),
            discord.SelectOption(label="Kolluk & Savunma", description="Muhafiz, karantina, nobet, savunma", value="kolluk", emoji="🛡️"),
            discord.SelectOption(label="Uretim & Ambar", description="Tarla, maden, orman, ambar bagisi", value="uretim", emoji="🌾"),
            discord.SelectOption(label="Savas & Kesif", description="Duello, kavga, sefer, gezi, baskin", value="savas", emoji="⚔️"),
            discord.SelectOption(label="Ekonomi & Cevre", description="Vergi, hava durumu, RP Owner paneli", value="ekonomi", emoji="💰"),
            discord.SelectOption(label="Yonetim & Admin", description="Owner araclari, db-sifirla, xp test", value="admin", emoji="🔧"),
        ]
        super().__init__(placeholder="Komut kategorisi sec...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        kategori = self.values[0]
        embed = kategori_embed_olustur(kategori)
        yeni_view = YardimView()
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, view=yeni_view, ephemeral=True)
        else:
            await interaction.response.edit_message(embed=embed, view=yeni_view)


def kategori_embed_olustur(kategori: str) -> discord.Embed:
    kategoriler = {
        "kayit": {
            "title": "📝 KAYIT & PROFIL",
            "color": 0x3498DB,
            "content": (
                "**Karakter Olusturma:**\n"
                "`/kayit` veya `v.kayit isim soyisim yas memleket`\n"
                "Ornek: `v.kayit Johann Bauer 25 Bavyera`\n"
                "Yas: 10-40 arasi\n"
                "Baslangic: 500 Akce + 20 XP + rastgele 10-20 Atak\n\n"
                "**Profil Komutlari:**\n"
                "/profil - Karakter kartin, barlar, biyografi\n"
                "/envanter - Sirt cantan\n"
                "/biyografi-yaz [metin] - Hikayeni yaz (max 1000 karakter, 3 gunde 1)\n\n"
                "**Meslek:**\n"
                "/meslek-sec [meslek] - Meslek sec (3 gunde 1)\n"
                "/meslek-yonetim - Meslegin paneli\n\n"
                "**Statu Sistemi:**\n"
                "Saglik (0-100) - 0 olursa olursun\n"
                "Su/Besin (0-100) - 24 saatte -10 duser\n"
                "Akil Sagligi (0-100)\n"
                "Enfeksiyon (0-100) - Yuksek olunca tehlikeli\n"
                "Seviye/XP - 100 XP = 1 seviye, her seviye x25 Akce"
            )
        },
        "pazar": {
            "title": "🛒 PAZAR & TICARET",
            "color": 0x2ECC71,
            "content": (
                "**Pazar (85 esya, 7 kategori):**\n"
                "/pazar - Kategori secim menusu (dropdown)\n"
                "Silah | Zirh | Medikal | Gida | Hammadde | Teknoloji | Mistik\n\n"
                "**Alim Satim:**\n"
                "/satinal [kod] [adet] - Esya al (meslek indirimleri var)\n"
                "/bota-sat [esya] [adet] - Kasaya sat (%20-25 vergi)\n"
                "/esya-sat [@uye] [esya] [fiyat] - Oyuncuya sat\n\n"
                "**Takas & Acik Arttirma:**\n"
                "/takas-teklif [@uye] [verilen] [istenen] - Esya takasi\n"
                "/acik-arttirma-baslat [esya] [acilis] - 2 dk acik arttirma\n"
                "/pey-ver [ilan_id] [teklif] - Acik arttirmaya teklif\n\n"
                "**Tuketim:**\n"
                "/tuket [esya] veya /kullan [esya] - Gida/Medikal tuket\n\n"
                "**Tuccar Paneli:**\n"
                "/tuccar-paneli - Tuccar ticaret paneli\n"
                "/tuccar-al [esya] [adet] - Ambardan ucuz al\n"
                "/tuccar-sat [esya] [adet] - Ambara pahali sat (kar!)\n\n"
                "**Meslek Indirimleri (%20):**\n"
                "Tuccar (tum pazar), Demirci (demir), Ciftci (ekmek/arpa)"
            )
        },
        "yonetim": {
            "title": "🏛️ SIYASET & YONETIM",
            "color": 0xF1C40F,
            "content": (
                "**Baskan Secimi:**\n"
                "/secimi-baslat (Yetkili Ekip) - 30 dk adaylik + 60 dk oylama\n"
                "/aday-ol [vaat] - Aday ol (500 Akce depozito)\n\n"
                "**Baskan Yetkileri:**\n"
                "/yonetim - Sur ve koy gelistirme paneli\n"
                "Sur: 250a, +1 seviye | Koy: 300a, +1 seviye\n"
                "/tayin-et [@uye] [unvan] - 6 kadroya atama\n"
                "Unvanlar: Baskan Yardimcisi, Vergi Memuru, Muhafiz Komutani, Bas Simyaci, Bas Doktor, Rahip\n\n"
                "**Maas Sistemi:**\n"
                "/maas-ode [@uye] [miktar] - Tek sakin maas\n"
                "/meslek-maas-ode [grup] [miktar] - Meslek grubuna toplu\n"
                "/toplu-maas [miktar] - Tum sakinlere maas\n\n"
                "**Gruplar:** muhafiz, saglik, ureticiler, idari"
            )
        },
        "yargi": {
            "title": "⚖️ YARGI & CEZA",
            "color": 0x9E9E9E,
            "content": (
                "**Mahkeme (Baskan):**\n"
                "/yargila [@sanik] [suc] - 3 secenek:\n"
                "Halk Oylamasi - 2 dk, halk karar verir\n"
                "Idam - Sanik olur, -300 Akce itibar kaybi (TIRANLIK)\n"
                "Surgun - Sanik surgun, -150 Akce kaybi\n\n"
                "**Hucre (Muhafiz):**\n"
                "/hucreye-at [@uye] - Zindana at\n"
                "/hucreden-cikar [@uye] - Tahliye et\n\n"
                "**Sokaga Cikma Yasagi (Baskan):**\n"
                "/sokak-yasagi [durum] - Ac/kapat\n"
                "Aktifken: gezi, pazar, takas, duello yasak\n\n"
                "**Darbe:**\n"
                "/darbe - Baskan varsa isyan baslat\n"
                "Basari sansi: 5-90% (itibar ve savunmaya gore)"
            )
        },
        "kilise": {
            "title": "⛪ ENGIZISYON & RAHIP",
            "color": 0x9B59B6,
            "content": (
                "**Rahip Yetkileri (sadece Rahip rolu):**\n\n"
                "/rahip-paneli - Panel gosterir\n\n"
                "/afaroz-et [@uye] [neden]\n"
                "Sapkini dinden cikar, sans -0.5\n\n"
                "/buyuk-kilise-cani\n"
                "3 gunde 1, tum sakinlere +10 moral\n\n"
                "/kutsa [@uye]\n"
                "3 saatte 1, enfeksiyon -20, saglik +15, moral +5\n\n"
                "/kedileri-yok-et TEHLIKELI\n"
                "Sadece 1 kez, tum Canli sakinleri Enfekte yapar!"
            )
        },
        "simya": {
            "title": "💊 SAGLIK & SIMYA",
            "color": 0x1ABC9C,
            "content": (
                "**Doktor (Bas Doktor/Doktor/Karantinaci):**\n\n"
                "/doktor-paneli - Panel\n"
                "/asi-uret - 2 tibbi malzeme -> 1 asi (+10 XP)\n"
                "/tedavi-et [@uye] - 1 asi ile hastayi iyilestir (+25 XP)\n\n"
                "**Simyaci (Bas Simyaci/Simyaci):**\n\n"
                "/deney - 3 senaryo:\n"
                "%10 basarili (virüs +5, +30 XP)\n"
                "%85 basarisiz\n"
                "%5-15 olum (simyaci olur, virüs sifirlanir!)\n"
                "Lab seviyesi 2: +%25 basari, seviye 3: +%45\n\n"
                "/laboratuvar-gelistir (Baskan/Bas Simyaci)\n"
                "500 Akce/seviye, max seviye 3"
            )
        },
        "kolluk": {
            "title": "🛡️ KOLLUK & SAVUNMA",
            "color": 0x2980B9,
            "content": (
                "**Muhafiz Sinifi:**\n\n"
                "/muhafiz-paneli - Panel\n"
                "/hucreye-at [@uye] - Zindana at\n"
                "/hucreden-cikar [@uye] - Tahliye\n\n"
                "/nobet - 4 saatte 1, 40-80 Akce + 20 XP\n"
                "Komutan +%50, muhafiz +%20 bonus\n\n"
                "**Karantina:**\n"
                "/karantina-al [@uye] - Enfekte sakini karantinaya\n"
                "/karantina-kaldir [@uye] - Karantinadan cikar\n\n"
                "**Baskan Savunma:**\n"
                "/savunmayi-guclendir - 500 Akce, +15 tahkimat (max 100)\n\n"
                "**Muhafiz Donanim:**\n"
                "/muhafiz-donanim [esya] - Defans ekipmani al\n"
                "Deri Gogusluk (+5, 200a) | Demir Kalkan (+10, 500a)\n"
                "Celik Zirh (+20, 1200a) | Komutan Plakasi (+30, 2500a)"
            )
        },
        "uretim": {
            "title": "🌾 URETIM & AMBAR",
            "color": 0xF39C12,
            "content": (
                "**Calisma Komutlari (30 dk CD):**\n\n"
                "/tarla-calis - Ciftci/Coban/Degirmenci/Hanci\n"
                "Hava: Yaz x2.0 | Ilkbahar x1.5 | Yagmurlu x0.7 | Kis x0.3\n"
                "+15 XP\n\n"
                "/maden-kaz - Madenci/Demirci\n"
                "Kis x0.6, Yagmurlu x0.8 | +20 XP\n\n"
                "/orman-kes - Oduncu/Hanci\n"
                "Yaz x1.3, Yagmurlu x0.5, Kis x0.2 | +15 XP\n\n"
                "**Ambar:**\n"
                "/ambar - Stoklari gor\n"
                "/ambara-bagis [esya] [adet] - Bagis, +2a/adet + itibar\n"
                "/ambardan-al [esya] [adet] - Max 5/adet, fakirlere ucretsiz\n\n"
                "Seviye atlama otomatik!"
            )
        },
        "savas": {
            "title": "⚔️ SAVAS & KESIF",
            "color": 0xC0392B,
            "content": (
                "**Duello (Olumcul):**\n"
                "/duello [@rakip] - Tur tabanli, butonlu, kabul/red\n"
                "Saldir, Defans, Yetenek (%50 kritik)\n"
                "Kaybedenin %20 ihtimalle kalici olum!\n\n"
                "**Kavga (Olumcul Degil):**\n"
                "/kavga [@rakip] - Kabul/red butonlu\n"
                "Kimse olmez, sadece yaralanma\n"
                "Saglik min 5'e duser, RP kavgalari icin ideal\n\n"
                "**Sefer (Baskan):**\n"
                "/sefer - 10 kisilik manga, 60 sn lobi\n"
                "150+ hasar = kalici olum\n"
                "Zafer: zorluk +1, ganimet, +50 XP\n\n"
                "**Zombi Baskini (Yetkili Ekip):**\n"
                "/zombi-baskini-baslat - Manuel baskin\n"
                "Surlar kanalina alarm, 2 dk savunma\n\n"
                "**Kesif:**\n"
                "/gez [bolge] - 6 saat CD, 25 RP bolgesi\n"
                "%50 olumlu / %30 olumsuz / %20 gizemli\n\n"
                "**Anit:** /anit - Seref listesi ve sehitle r"
            )
        },
        "ekonomi": {
            "title": "💰 EKONOMI & CEVRE",
            "color": 0xE67E22,
            "content": (
                "**Vergi (Vergi Memuru/Mufettisi):**\n"
                "/maliye-yonetim - Panel + oran ayarlama\n"
                "Veba Vergisi: 5 saatte bir (default 20a)\n"
                "Ticaret Kesintisi: %10-50\n\n"
                "**Hava Durumu:**\n"
                "/hava-durumu-degis [mevsim] - Yetkili Ekip\n"
                "4 mevsim: Ilkbahar, Yaz, Yagmurlu, Kis\n\n"
                "**Sunucu Yonetimi (/sunucu-yonetimi):**\n"
                "Kraliyet Destegi - +2000 odun, +1000 komur, +500a, +1 sur\n"
                "Toplu Enfeksiyon - Tum canlilari enfekte et\n"
                "Hava Menusu - Mevsim degistir\n"
                "Salgin Kuvveti - Dusuk/Orta/Kiyamet\n\n"
                "**Otomatik Task'lar:**\n"
                "1h: Yedekleme | 5h: Vergi | 6h: Gazete | 24h: Aclik"
            )
        },
        "admin": {
            "title": "🔧 YONETIM & ADMIN",
            "color": 0x7F8C8D,
            "content": (
                "**Yetkili Ekip Komutlari:**\n\n"
                "/owner-kayit [@uye] [isim] [soyisim] [yas] [memleket]\n"
                "Bir uyeyi zorla kaydet\n\n"
                "/kayit-sil [@uye] EVET\n"
                "Uyenin sicil kaydini sil\n\n"
                "/sunucu-yonetimi\n"
                "Tansal kontrol paneli (Kraliyet, Enfeksiyon, Hava)\n\n"
                "/zombi-baskini-baslat\n"
                "Manuel zombi baskini baslat\n\n"
                "/db-sifirla EVET - Tum veritabanini sifirla\n"
                "/kaynak-ekle [kaynak] [miktar] - Odun/komur/erzak/Akce ekle\n"
                "/xp_kazan_test [miktar] [@uye] - Test XP ekle\n"
                "/secimi-baslat - Secim sureci baslat\n"
                "/hava-durumu-degis [mevsim] - Mevsim degistir\n"
                "/haber [kanal] - Gazete kanali ayarla\n\n"
                "**Para Birimi:** Akce\n"
                "**Prefix:** v. (orn: v.kayit, v.profil)"
            )
        },
    }
    veri = kategoriler.get(kategori, {"title": "Bilinmeyen", "color": 0x7F8C8D, "content": "Kategori bulunamadi."})
    embed = discord.Embed(title=veri["title"], color=veri["color"])
    embed.description = veri["content"]
    embed.set_footer(text="Siginak Veba RP v5.7 | Baska kategori icin tekrar secim yap")
    return embed


async def setup(bot):
    await bot.add_cog(RehberCog(bot))

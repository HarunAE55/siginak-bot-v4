"""
Cog: Rehber & Gazete
===================
Komutlar:
- /destek (tüm komutların özet listesi)
- /rehber (dropdown ile kategori seçimli detaylı yardım)
- /haber (admin, gazete kanalı ayarlar)

Otomatik Task: 6 saatte bir gazete bülteni (haber kanalına olay günlüğü yazılır)
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks
import datetime

from veritabani import db, verileri_kaydet, haber_ekle
from kanallar import GAZETE_KANAL_ID


class RehberCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 6 saatlik gazete task'ını başlat
        self.alti_saatlik_gazete_task.start()

    def cog_unload(self):
        self.alti_saatlik_gazete_task.cancel()

    # ====================================================
    # 6 SAATLİK OTOMATİK GAZETE TASK
    # ====================================================
    @tasks.loop(hours=6)
    async def alti_saatlik_gazete_task(self):
        # Önce ayarlanmış kanal var mı kontrol et, yoksa default kanal
        kanal_id = db["gazete_sistemi"].get("haber_kanali_id") or GAZETE_KANAL_ID
        if not kanal_id:
            return

        kanal = self.bot.get_channel(kanal_id)
        if not kanal:
            return

        olaylar = db["gazete_sistemi"].get("olay_gunlugu", [])

        embed = discord.Embed(title="📰 ŞEHİR GAZETESİ & SIĞINAK BÜLTENİ 📰", color=0x7F8C8D)
        if self.bot.user and self.bot.user.avatar:
            embed.set_author(name="Sığınak Resmi Matbaası", icon_url=self.bot.user.avatar.url)

        bülten_metni = ""
        if olaylar:
            bülten_metni = "\n".join(olaylar[-30:])  # Son 30 olay
        else:
            bülten_metni = "*Bu 6 saatlik dönemde sığınak sokakları oldukça sessiz ve sakindi...*"

        sur_can = db["sefer_sistemi"].get("sur_canı", 500)
        maks_sur = db["sefer_sistemi"].get("maks_sur_canı", 500)
        sur_yuzde = int((sur_can / maks_sur) * 100) if maks_sur > 0 else 0

        embed.description = (
            f"⏳ **Dönem:** Son 6 Saatin Siyasi, Teokratik ve Ekonomik Özeti\n"
            f"📊 **Salgın Durumu:** Köy genelinde taramalar devam ediyor.\n"
            f"🏰 **Sur Sağlamlığı:** %{sur_yuzde}\n"
            f"👥 **Aktif Sakin Sayısı:** `{len([s for s in db['sakinler'].values() if s.get('durum') != 'Ölü'])}`\n"
            f"💰 **Ortak Kasa:** `{db['sistem_ayarlari'].get('KASA_AKÇE_PLACEHOLDER', 0)} Akçe`\n\n"
            f"📋 **MANŞETLER VE KAYITLAR:**\n{bülten_metni}"
        )

        try:
            await kanal.send(embed=embed)
        except Exception as e:
            print(f"❌ Gazete gönderilemedi: {e}")

        # Olay günlüğünü sıfırla
        db["gazete_sistemi"]["olay_gunlugu"] = []
        db["gazete_sistemi"]["son_gazete_timestamp"] = datetime.datetime.now().isoformat()
        verileri_kaydet()

    @alti_saatlik_gazete_task.before_loop
    async def before_gazete_task(self):
        await self.bot.wait_until_ready()

    # ====================================================
    # /destek - Tüm komutların özet listesi
    # ====================================================
    @app_commands.command(name="destek", description="Sığınak botunun tüm komutlarını kategori bazında listeler.")
    async def destek_rehberi(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📚 SIĞINAK RPG SİSTEMİ - KOMUT KILAVUZU", color=0x34495E)
        embed.description = (
            "Tüm komutların özeti aşağıdadır. Daha detaylı bilgi için `/rehber` komutunu kullanarak kategori seçebilirsin.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

        embed.add_field(
            name="📝 1. Kayıt & Profil",
            value="`/kayit` `/profil` `/envanter` `/biyografi-yaz` `/meslek-sec` `/meslek-yonetim`",
            inline=False
        )
        embed.add_field(
            name="🛒 2. Pazar & Ticaret",
            value="`/pazar` `/satinal` `/bota-sat` `/esya-sat` `/takas-teklif` `/acik-arttirma-baslat` `/pey-ver` `/tuket`",
            inline=False
        )
        embed.add_field(
            name="🏛️ 3. Siyaset & Yönetim",
            value="`/secimi-baslat` `/aday-ol` `/yonetim` `/tayin-et` `/maas-ode` `/meslek-maas-ode` `/toplu-maas`",
            inline=False
        )
        embed.add_field(
            name="⚖️ 4. Yargı & Ceza",
            value="`/yargila` `/hucreye-at` `/hucreden-cikar` `/sokak-yasagi` `/darbe`",
            inline=False
        )
        embed.add_field(
            name="⛪ 5. Engizisyon & Rahip",
            value="`/rahip-paneli` `/afaroz-et` `/buyuk-kilise-cani` `/kedileri-yok-et` `/kutsa`",
            inline=False
        )
        embed.add_field(
            name="💊 6. Sağlık & Simya",
            value="`/doktor-paneli` `/asi-uret` `/tedavi-et` `/deney` `/laboratuvar-gelistir`",
            inline=False
        )
        embed.add_field(
            name="🛡️ 7. Kolluk & Savunma",
            value="`/muhafiz-paneli` `/karantina-al` `/karantina-kaldir` `/savunmayi-guclendir` `/nobet`",
            inline=False
        )
        embed.add_field(
            name="🌾 8. Üretim & Ambar",
            value="`/ciftci-paneli` `/tarla-calis` `/maden-kaz` `/orman-kes` `/ambar` `/ambara-bagis` `/ambardan-al`",
            inline=False
        )
        embed.add_field(
            name="⚔️ 9. Savaş & Keşif",
            value="`/duello` `/sefer` `/zombi-baskini-baslat` `/gez` `/anit`",
            inline=False
        )
        embed.add_field(
            name="💰 10. Ekonomi & Maliye",
            value="`/maliye-yonetim` `/hava-durumu-degis` `/haber`",
            inline=False
        )
        embed.add_field(
            name="🔧 11. Yönetim Paneli",
            value="`/sunucu-yonetimi` (RP Owner) `/owner-kayit` (RP Owner) `/kayit-sil` (RP Owner) `/xp_kazan_test` (Admin)",
            inline=False
        )
        embed.add_field(
            name="📖 12. Rehber",
            value="`/destek` `/rehber`",
            inline=False
        )

        embed.set_footer(text="Sığınak Veba RP v5.5 | Detaylı yardım için: /rehber")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ====================================================
    # /rehber - Detaylı dropdown rehber
    # ====================================================
    @app_commands.command(name="rehber", description="Detaylı rehber. Kategori seçerek her sistemi öğren.")
    async def rehber_dropdown(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📖 SIĞINAK REHBERİ", color=0x9B59B6)
        embed.description = (
            "Aşağıdaki menüden bir kategori seçerek detaylı bilgi alabilirsin.\n\n"
            "🆕 **Yeni başlayanlar için:** `📝 Kayıt & Profil` kategorisinden başla!"
        )
        view = RehberView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # ====================================================
    # /haber - Admin gazete kanalı ayarlar
    # ====================================================
    @app_commands.command(name="haber", description="[ADMİN] Otomatik 6 saatlik gazetenin yazılacağı kanalı belirler.")
    @app_commands.describe(kanal="Haber bültenlerinin akacağı kanal")
    async def haber_kanali_ayarla(self, interaction: discord.Interaction, kanal: discord.TextChannel):
        from veritabani import admin_mi
        if not admin_mi(interaction):
            await interaction.response.send_message(
                "❌ Bu komut sadece yetkili ekibe özeldir!",
                ephemeral=True
            )
            return

        db["gazete_sistemi"]["haber_kanali_id"] = kanal.id
        verileri_kaydet()

        await interaction.response.send_message(
            f"📰 **Basın Ofisi Kuruldu!** Sığınak haberleri artık {kanal.mention} kanalına yazılacak!"
        )
        haber_ekle(f"📰 Belediye Basın Ofisi {kanal.name} kanalında resmi faaliyetlerine başladı.")


# ====================================================
# VIEW - REHBER DROPDOWN
# ====================================================
class RehberView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(RehberDropdown())


class RehberDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="📝 Kayıt & Profil", description="Nasıl kayıt olunur, biyografi, profil detayları", value="kayit", emoji="📝"),
            discord.SelectOption(label="🛒 Pazar & Ticaret", description="Alım satım, açık arttırma, takas, tüketim", value="pazar", emoji="🛒"),
            discord.SelectOption(label="🏛️ Siyaset & Yönetim", description="Seçim, başkanlık, atama, maaş", value="yonetim", emoji="🏛️"),
            discord.SelectOption(label="⚖️ Yargı & Ceza", description="Mahkeme, hücre, darbe, sokak yasağı", value="yargi", emoji="⚖️"),
            discord.SelectOption(label="⛪ Kilise & Rahip", description="Afaroz, kutsama, kilise çanı", value="kilise", emoji="⛪"),
            discord.SelectOption(label="💊 Sağlık & Simya", description="Aşı, tedavi, deney, laboratuvar", value="simya", emoji="💊"),
            discord.SelectOption(label="🛡️ Kolluk & Savunma", description="Muhafız, karantina, nöbet", value="kolluk", emoji="🛡️"),
            discord.SelectOption(label="🌾 Üretim & Ambar", description="Tarla, maden, orman, ambar bağışı", value="uretim", emoji="🌾"),
            discord.SelectOption(label="⚔️ Savaş & Keşif", description="Düello, sefer, gezi, baskın", value="savas", emoji="⚔️"),
            discord.SelectOption(label="💰 Ekonomi & Çevre", description="Vergi, hava durumu, RP Owner paneli", value="ekonomi", emoji="💰"),
        ]
        super().__init__(placeholder="📚 Bilgi almak istediğin kategoriyi seç...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        kategori = self.values[0]
        embed = self.kategori_embed(kategori)
        await interaction.response.edit_message(embed=embed, view=self)

    def kategori_embed(self, kategori: str) -> discord.Embed:
        kategoriler = {
            "kayit": {
                "title": "📝 KAYIT & PROFİL REHBERİ",
                "color": 0x3498DB,
                "content": (
                    "**Nasıl Kayıt Olunur?**\n"
                    "`/kayit isim: soyisim: yaş: memleket:` komutuyla sicil kütüğüne kaydolursun.\n"
                    "• Yaş sınırı: **10-40** arası\n"
                    "• Başlangıç: **500 Akçe** + **20 XP** + rastgele **10-20 Atak Gücü**\n\n"
                    "**Karakter Kartın:**\n"
                    "• `/profil` — Tüm istatistiklerin, barların ve biyografin\n"
                    "• `/envanter` — Sırt çantandaki eşyalar\n"
                    "• `/biyografi-yaz [metin]` — Karakterinin hikayesi (max 1000 karakter, 3 günde 1 değiştirilebilir)\n\n"
                    "**Statü Sistemi:**\n"
                    "❤️ Sağlık (0-100) — 0 olursa ölürsün\n"
                    "💧 Su/Besin (0-100) — 24 saatte -10 düşer (24h task)\n"
                    "🧠 Akıl Sağlığı (0-100)\n"
                    "☣️ Enfeksiyon (0-100) — 100 olunca ölüm riski\n"
                    "😊 Moral (0-100)\n"
                    "⚔️ Atak / 🛡️ Defans — Savaşlarda kullanılır\n"
                    "⭐ Seviye/XP — 100 XP = 1 seviye, her seviye ×25 akçe ödülü\n\n"
                    "**Önemli:** Öldüğünde tüm eşyaların kaybolur, `/kayit` ile sıfırdan başlarsın."
                )
            },
            "pazar": {
                "title": "🛒 PAZAR & TİCARET REHBERİ",
                "color": 0x2ECC71,
                "content": (
                    "**Pazar Sistemi (85 eşya, 7 kategori):**\n"
                    "• `/pazar [kategori]` — Kategorideki eşyaları listele\n"
                    "• `/satinal [kod] [adet]` — Katalogdaki kodla eşya al\n"
                    "  - Kategoriler: ⚔️ Silah, 🛡️ Zırh, 💊 Medikal, 🍲 Gıda, 🪵 Hammadde, ⚙️ Teknoloji, 🔮 Mistik\n\n"
                    "**Meslek İndirimleri (%20):**\n"
                    "• Tüccar → Tüm pazarda %20 indirim\n"
                    "• Demirci → Demir hammaddelerinde\n"
                    "• Çiftçi → Ekmek/Arpa gıdalarında\n"
                    "• Simyacı/Doktor → Cıva Esansı mistik eşyalarında\n\n"
                    "**Satış Yolları:**\n"
                    "• `/bota-sat [esya] [adet]` — Kısaya sat (tüccar/müfettiş %20, diğerleri %25 vergi)\n"
                    "• `/esya-sat [@üye] [esya] [fiyat]` — Oyuncuya doğrudan satış teklifi\n"
                    "• `/takas-teklif [@üye] [verilen] [istenen]` — Eşya takası\n"
                    "• `/acik-arttirma-baslat [esya] [açılış]` — 2 dk açık arttırma (%5 idare kesintisi)\n"
                    "• `/pey-ver [ilan_id] [teklif]` — Açık arttırmaya teklif ver\n\n"
                    "**Tüketim:**\n"
                    "• `/tuket [esya]` — Gıda/Medikal tüket, su/sağlık yenilenir"
                )
            },
            "yonetim": {
                "title": "🏛️ SİYASET & YÖNETİM REHBERİ",
                "color": 0xF1C40F,
                "content": (
                    "**Belediye Başkanı Seçimi:**\n"
                    "• Admin `/secimi-baslat` yapar → 15 dk adaylık + 45 dk oylama = 1 saat\n"
                    "• Aday olmak için: `/aday-ol [vaat]` — 500 akçe depozito gerekir\n"
                    "• Her sakin 1 oy kullanır, en çok oyu olan başkan olur\n"
                    "• Beraberlikte seçim iptal\n\n"
                    "**Başkan Yetkileri:**\n"
                    "• `/yonetim` — Sur ve köy geliştirme paneli\n"
                    "  - 🧱 Sur Geliştir: 250 akçe, +1 sur seviyesi\n"
                    "  - 🏡 Köy Geliştir: 300 akçe, +1 köy seviyesi\n"
                    "• `/tayin-et [@üye] [unvan]` — 5 kadroya atama (Yardımcı, Müfettiş, Komutan, Baş Simyacı, Rahip)\n"
                    "• `/maas-ode [@üye] [miktar]` — Tek sakin maaş\n"
                    "• `/meslek-maas-ode [grup] [miktar]` — Meslek grubuna toplu maaş\n"
                    "• `/toplu-maas [miktar]` — Tüm halka maaş\n\n"
                    "**Kayıt Yönetimi (RP Owner only):**\n"
                    "• `/owner-kayit [@üye] ...` — Bir üyeyi zorla kaydet\n"
                    "• `/kayit-sil [@üye] EVET` — Bir üyenin kaydını sil"
                )
            },
            "yargi": {
                "title": "⚖️ YARGI & CEZA REHBERİ",
                "color": 0x9E9E9E,
                "content": (
                    "**Mahkeme Sistemi (Başkan açar):**\n"
                    "• `/yargila [@sanık] [suç]` — 3 seçenek:\n"
                    "  1. 📢 **Halk Oylaması** — 2 dk, halk suçlu/suçsuuz oylar\n"
                    "  2. 💀 **Yargısız İdam** — Sanık ölür, başkan -300 akçe itibar kaybı (TİRANLIK)\n"
                    "  3. 🧳 **Mutlak Sürgün** — Sanık sürgün, başkan -150 akçe kaybı\n\n"
                    "**Hücre Sistemi (Kolluk):**\n"
                    "• `/hucreye-at [@sakin]` — Muhafız sınıfı, kuralları bozanı zindana atar\n"
                    "• `/hucreden-cikar [@sakin]` — Tahliye\n"
                    "• Hücrede olan hiçbir komutu kullanamaz\n\n"
                    "**Sokağa Çıkma Yasağı:**\n"
                    "• `/sokak-yasagi [durum]` — Başkan açar/kapatır\n"
                    "• Aktifken idari kadro hariç herkes donar (gezi, pazar, takas, düello yasak)\n\n"
                    "**Darbe:**\n"
                    "• `/darbe` — Başkan varsa isyan başlat\n"
                    "• Başarı şansı: 5% ile 90% arası (itibar ve savunmaya göre)\n"
                    "• Başarılıysa kasanın yarısı yağmalanır, isyancı yeni başkan olur"
                )
            },
            "kilise": {
                "title": "⛪ KİLİSE & RAHİP REHBERİ",
                "color": 0x9B59B6,
                "content": (
                    "**Rahip Yetkileri (sadece Rahip rolü):**\n\n"
                    "• `/rahip-paneli` — Panel gösterir\n\n"
                    "• `/afaroz-et [@sakin] [neden]`\n"
                    "  - Sapkını dinden çıkar\n"
                    "  - Şans çarpanını -0.5 düşürür\n\n"
                    "• `/buyuk-kilise-cani`\n"
                    "  - 3 günde 1 çalınabilir\n"
                    "  - Tüm sakinlere +10 moral\n\n"
                    "• `/kutsa [@sakin]`\n"
                    "  - 3 saatte 1\n"
                    "  - Enfeksiyon -20, Sağlık +15, Moral +5\n\n"
                    "• `/kedileri-yok-et` ⚠️ TEHLİKELİ\n"
                    "  - Sadece 1 kez yapılabilir\n"
                    "  - Fare nüfusu 10x artar\n"
                    "  - Tüm Canlı sakinler Enfekte olur\n"
                    "  - Rahibin itibarı -30 düşer"
                )
            },
            "simya": {
                "title": "💊 SAĞLIK & SİMYA REHBERİ",
                "color": 0x1ABC9C,
                "content": (
                    "**Doktor Sistemi (Bas Doktor/Doktor/Karantinacı):**\n\n"
                    "• `/doktor-paneli` — Panel gösterir\n\n"
                    "• `/asi-uret`\n"
                    "  - 2 tıbbi malzeme → 1 aşı üretir\n"
                    "  - +10 XP kazanır\n\n"
                    "• `/tedavi-et [@sakin]`\n"
                    "  - 1 aşı kullanır\n"
                    "  - Enfekte/Karantinadaki sakini iyileştirir\n"
                    "  - +25 XP kazanır\n\n"
                    "**Simyaci Sistemi (Baş Simyacı/Simyacı):**\n\n"
                    "• `/deney`\n"
                    "  - 3 senaryo: %10 başarılı, %85 başarısız, %5-15 ölüm\n"
                    "  - Başarı: virüs ilerlemesi +5, +30 XP\n"
                    "  - Ölüm: simyacı ölür, virüs verisi sıfırlanır!\n"
                    "  - Lab seviyesi 2: +%25 başarı, seviye 3: +%45 başarı\n\n"
                    "• `/laboratuvar-gelistir` (Başkan veya Baş Simyacı)\n"
                    "  - 500 akçe/seviye\n"
                    "  - Max seviye 3"
                )
            },
            "kolluk": {
                "title": "🛡️ KOLLUK & SAVUNMA REHBERİ",
                "color": 0x2980B9,
                "content": (
                    "**Muhafız Sınıfı (Komutan/Muhafız/Nişancı/İzci):**\n\n"
                    "• `/muhafiz-paneli` — Panel gösterir\n"
                    "• `/hucreye-at [@sakin]` — Zindana at\n"
                    "• `/hucreden-cikar [@sakin]` — Tahliye et\n\n"
                    "• `/nobet` ⭐ YENİ\n"
                    "  - 4 saatte 1\n"
                    "  - 40-80 akçe + 20 XP kazandırır\n"
                    "  - Komutanlar +%50 bonus, muhafızlar +%20 bonus\n"
                    "  - %20 ihtimal hırsız yakalama bonusu\n"
                    "  - %10 ihtimal sıkıcı nöbet (az ödül)\n\n"
                    "**Karantina Sistemi:**\n"
                    "• `/karantina-al [@sakin]` — Enfekte sakini karantinaya at\n"
                    "  - Yetkililer: Başkan, Yardımcı, Komutan, Muhafız, Karantinacı rolü\n"
                    "• `/karantina-kaldir [@sakin]` — Karantinayı kaldır\n"
                    "  - Yetkililer: Başkan, Komutan, Baş Simyacı, Simyacı, Karantinacı rolü\n\n"
                    "**Başkan Savunma:**\n"
                    "• `/savunmayi-guclendir` — 500 akçe, +15 muhafız tahkimatı (max 100)"
                )
            },
            "uretim": {
                "title": "🌾 ÜRETİM & AMBAR REHBERİ",
                "color": 0xF39C12,
                "content": (
                    "**Çalışma Komutları (30 dk CD):**\n\n"
                    "• `/tarla-calis` — Çiftçi/Çoban/Değirmenci/Hancı\n"
                    "  - 10-20 erzak üretir\n"
                    "  - Hava durumuna göre çarpan:\n"
                    "    ☀️ Yaz: x2.0 | 🌱 İlkbahar: x1.5 | 🌧️ Yağmurlu: x0.7 | ❄️ Kış: x0.3\n"
                    "  - +15 XP\n\n"
                    "• `/maden-kaz` — Madenci/Demirci\n"
                    "  - 8-15 kömür üretir\n"
                    "  - Kış x0.6, Yağmurlu x0.8\n"
                    "  - +20 XP\n\n"
                    "• `/orman-kes` — Oduncu/Hancı\n"
                    "  - 12-22 odun üretir\n"
                    "  - Yaz x1.3, Yağmurlu x0.5, Kış x0.2\n"
                    "  - +15 XP\n\n"
                    "**Ambar Sistemi:**\n"
                    "• `/ambar` — Stokları gör\n"
                    "• `/ambara-bagis [esya] [adet]` — Bağış yap, +2 akçe/adet + itibar\n"
                    "• `/ambardan-al [esya] [adet]` — Ücretsiz al (max 5, cüzdanı 400+ olan alamaz)\n\n"
                    "**Tüketim:**\n"
                    "• `/tuket [esya]` — Gıda/Medikal tüket, su/sağlık yenile\n\n"
                    "⭐ Seviye atlama otomatiktir!"
                )
            },
            "savas": {
                "title": "⚔️ SAVAŞ & KEŞİF REHBERİ",
                "color": 0xC0392B,
                "content": (
                    "**Düello (herkese açık):**\n"
                    "• `/duello [@rakip]` — Tur tabanlı, butonlu\n"
                    "• 3 hamle: ⚔️ Saldır, 🛡️ Defans, ⚡ Yetenek (%50 kritik)\n"
                    "• Kaybedenin **%20 ihtimalle kalıcı ölüm**!\n"
                    "• Ölümse ganimet kazanan rakibe gider\n\n"
                    "**Sefer (Başkan):**\n"
                    "• `/sefer` — 10 kişilik manga, 60 sn lobi\n"
                    "• Tur tabanlı savaş simülasyonu\n"
                    "• 150+ hasar yiyen kalıcı ölür\n"
                    "• Zafer: zorluk +1, ganimet, +50 XP\n\n"
                    "**Zombi Baskını (RP Owner):**\n"
                    "• `/zombi-baskini-baslat` — Manuel baskın tetikler\n"
                    "• 2 dk savunma penceresi\n"
                    "• Savunma < baskın ise sur hasar alır\n"
                    "• Muhafız sınıfı +%20 savunma, diğerleri -15%\n\n"
                    "**Keşif (`/gez`):**\n"
                    "• 6 saat cooldown\n"
                    "• 6 bölge: Terkedilmiş Köy, Veba Mezarlığı, Karanlık Koruluk, Yıkık Kilise, Dehliz Labirenti, Zombi Tarlası\n"
                    "• %50 olumlu / %30 olumsuz / %20 gizemli\n"
                    "• Sonuç ilgili RP kanalına da gönderilir\n\n"
                    "**Anıt:** `/anit` — Şeref listesi ve şehitler"
                )
            },
            "ekonomi": {
                "title": "💰 EKONOMİ & ÇEVRE REHBERİ",
                "color": 0xE67E22,
                "content": (
                    "**Vergi Sistemi (Vergi Memuru/Müfettişi):**\n"
                    "• `/maliye-yonetim` — Panel + oran ayarlama\n"
                    "• Veba Vergisi: 5 saatte bir tüm canlılardan kesilir (default 20 akçe)\n"
                    "• Ticaret Kesintisi: Bot satışlarından alınır (default %10, max %50)\n\n"
                    "**Hava Durumu:**\n"
                    "• `/hava-durumu-degis [mevsim]` — Admin komutu\n"
                    "• 4 mevsim: İlkbahar, Yaz, Yağmurlu, Kış\n"
                    "• Üretim komutlarını etkiler\n\n"
                    "**RP Owner Paneli (`/sunucu-yonetimi`):**\n"
                    "• 👑 **Kraliyet Acil Desteği** — +2000 odun, +1000 kömür, +500 akçe, +1 sur\n"
                    "• ☣️ **Tüm Sığınağa Enfeksiyon** — Tüm canlıları enfekte et, virüs +15\n"
                    "• 🌍 **Hava Durumu Menüsü** — Mevsim değiştir\n"
                    "• ☣️ **Salgın Kuvveti** — Düşük(1) / Orta(2) / Kıyamet(3)\n\n"
                    "**Otomatik Task'lar:**\n"
                    "• 1 saat: Yedekleme (Discord kanalına JSON)\n"
                    "• 5 saat: Vergi tahsilatı\n"
                    "• 6 saat: Gazete bülteni\n"
                    "• 24 saat: Açlık/susuzluk -10 (su 0 olursa -15 sağlık)"
                )
            },
        }

        veri = kategoriler.get(kategori, {"title": "❓ Bilinmeyen", "color": 0x7F8C8D, "content": "Kategori bulunamadı."})
        embed = discord.Embed(title=veri["title"], color=veri["color"])
        embed.description = veri["content"]
        embed.set_footer(text="Sığınak Veba RP v5.5 | Başka kategori için tekrar seçim yap")
        return embed


async def setup(bot):
    await bot.add_cog(RehberCog(bot))

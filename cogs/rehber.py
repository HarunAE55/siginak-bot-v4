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
            f"💰 **Ortak Kasa:** `{db['sistem_ayarlari'].get('kasa_hurda', 0)} Hurda`\n\n"
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
    # /destek - Dropdown ile kategori seçimli yardım menüsü
    # ====================================================
    @app_commands.command(name="destek", description="Sığınak botunun tüm komutlarını kategori seçerek öğren.")
    async def destek_rehberi(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🦠 SIĞINAK VEBEA RP - KOMUT MERKEZİ",
            color=0x2C3E50
        )
        if self.bot.user and self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.description = (
            "**Hoş geldin sakin!** 👋\n\n"
            "Aşağıdaki menüden bir kategori seçerek o kategoriye ait tüm komutları görebilirsin.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📜 **Kategoriler:**\n"
            "📝 • **Kayıt & Profil** — Karakter oluşturma, profil, biyografi\n"
            "🛒 • **Pazar & Ticaret** — Alım satım, açık arttırma, takas\n"
            "🏛️ • **Siyaset & Yönetim** — Seçim, başkan, atama, maaş\n"
            "⚖️ • **Yargı & Ceza** — Mahkeme, hücre, darbe, yasak\n"
            "⛪ • **Engizisyon & Rahip** — Afaroz, kutsama, kilise\n"
            "💊 • **Sağlık & Simya** — Aşı, tedavi, deney, laboratuvar\n"
            "🛡️ • **Kolluk & Savunma** — Muhafız, karantina, nöbet\n"
            "🌾 • **Üretim & Ambar** — Tarla, maden, odun, ambar\n"
            "⚔️ • **Savaş & Keşif** — Düello, sefer, gezi, baskın\n"
            "💰 • **Ekonomi & Çevre** — Vergi, hava durumu, RP Owner\n"
            "🔧 • **Yönetim & Admin** — Owner araçları, db-sifirla\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 **İpucu:** Komutlar hem `/slash` hem `v.prefix` ile çalışır.\n"
            "Örnek: `/kayit` veya `v.kayit Johann Bauer 25 Bavyera`"
        )
        embed.set_footer(text="Sığınak Veba RP v5.4 | Kategori seçmek için aşağıdaki menüyü kullan")
        
        view = DestekView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # ====================================================
    # /rehber - Detaylı dropdown rehber (aynı view, farklı mesaj)
    # ====================================================
    @app_commands.command(name="rehber", description="Detaylı rehber. Kategori seçerek her sistemi öğren.")
    async def rehber_dropdown(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📖 SIĞINAK REHBERİ - Detaylı Bilgi",
            color=0x9B59B6
        )
        embed.description = (
            "**Detaylı Rehber Sistemi** 🎓\n\n"
            "Aşağıdaki menüden bir kategori seç. Seçtiğin kategoride:\n"
            "• Komutların **nasıl kullanılacağını**\n"
            "• Komutların **ne işe yaradığını**\n"
            "• **Örnek kullanımları**\n"
            "• **İpuçlarını**\n\ngörebilirsin.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🆕 **Yeni başlayanlar için:** `📝 Kayıt & Profil` kategorisinden başla!\n"
            "💡 **Hızlı yardım:** `/destek` komutu da aynı kategori menüsünü açar."
        )
        embed.set_footer(text="Sığınak Veba RP v5.4 | Detaylı rehber")
        
        view = DestekView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # ====================================================
    # /haber - Admin gazete kanalı ayarlar
    # ====================================================
    @app_commands.command(name="haber", description="[ADMİN] Otomatik 6 saatlik gazetenin yazılacağı kanalı belirler.")
    @app_commands.describe(kanal="Haber bültenlerinin akacağı kanal")
    async def haber_kanali_ayarla(self, interaction: discord.Interaction, kanal: discord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Sığınak resmi basın kanalını sadece kurucular ayarlayabilir!",
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
# VIEW - DESTEK/REHBER DROPDOWN (kategori seçim menüsü)
# ====================================================
class DestekView(discord.ui.View):
    """Kategori seçim menüsü içeren view. /destek ve /rehber komutlarında kullanılır."""
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(DestekDropdown())


class DestekDropdown(discord.ui.Select):
    """11 kategori içeren dropdown. Kullanıcı kategori seçince o kategorinin komutlarını gösterir."""
    def __init__(self):
        options = [
            discord.SelectOption(label="Kayıt & Profil", description="Karakter oluşturma, profil, envanter, biyografi", value="kayit", emoji="📝"),
            discord.SelectOption(label="Pazar & Ticaret", description="Alım satım, açık arttırma, takas, tüketim", value="pazar", emoji="🛒"),
            discord.SelectOption(label="Siyaset & Yönetim", description="Seçim, başkanlık, atama, maaş", value="yonetim", emoji="🏛️"),
            discord.SelectOption(label="Yargı & Ceza", description="Mahkeme, hücre, darbe, sokak yasağı", value="yargi", emoji="⚖️"),
            discord.SelectOption(label="Engizisyon & Rahip", description="Afaroz, kutsama, kilise çanı", value="kilise", emoji="⛪"),
            discord.SelectOption(label="Sağlık & Simya", description="Aşı, tedavi, deney, laboratuvar", value="simya", emoji="💊"),
            discord.SelectOption(label="Kolluk & Savunma", description="Muhafız, karantina, nöbet, savunma", value="kolluk", emoji="🛡️"),
            discord.SelectOption(label="Üretim & Ambar", description="Tarla, maden, orman, ambar bağışı", value="uretim", emoji="🌾"),
            discord.SelectOption(label="Savaş & Keşif", description="Düello, sefer, gezi, baskın, anıt", value="savas", emoji="⚔️"),
            discord.SelectOption(label="Ekonomi & Çevre", description="Vergi, hava durumu, RP Owner paneli", value="ekonomi", emoji="💰"),
            discord.SelectOption(label="Yönetim & Admin", description="Owner araçları, db-sifirla, xp test", value="admin", emoji="🔧"),
        ]
        super().__init__(placeholder="📂 Komut kategorisi seç...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        kategori = self.values[0]
        embed = kategori_embed_olustur(kategori)
        # Yeni bir view oluştur (dropdown tekrar seçilebilsin diye)
        yeni_view = DestekView()
        # Eğer interaction zaten yanıtlandıysa followup kullan, yoksa edit
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, view=yeni_view, ephemeral=True)
        else:
            await interaction.response.edit_message(embed=embed, view=yeni_view)


def kategori_embed_olustur(kategori: str) -> discord.Embed:
    """Kategori adına göre detaylı embed döndürür (modül seviyesinde fonksiyon)."""
    kategoriler = {
        "kayit": {
            "title": "📝 KAYIT & PROFİL",
            "color": 0x3498DB,
            "content": (
                "**Karakter Oluşturma:**\n"
                "`/kayit` veya `v.kayit isim soyisim yaş memleket`\n"
                "Örnek: `v.kayit Johann Bauer 25 Bavyera`\n"
                "• Yaş: **10-40** arası\n"
                "• Başlangıç: 500 Hurda + 20 XP + rastgele 10-20 Atak\n\n"
                "**Profil Komutları:**\n"
                "• `/profil` — Karakter kartın, barlar, biyografi\n"
                "• `/envanter` — Sırt çantan\n"
                "• `/biyografi-yaz [metin]` — Hikayeni yaz (max 1000 karakter, 3 günde 1)\n\n"
                "**Meslek:**\n"
                "• `/meslek-sec [meslek]` — Meslek seç (3 günde 1 değiştirilebilir)\n"
                "• `/meslek-yonetim` — Mesleğinin paneli\n\n"
                "**Statü Sistemi:**\n"
                "❤️ Sağlık (0-100) — 0 olursa ölürsün\n"
                "💧 Su/Besin (0-100) — 24 saatte -10 düşer\n"
                "🧠 Akıl Sağlığı (0-100)\n"
                "☣️ Enfeksiyon (0-100) — Yüksek olunca tehlikeli\n"
                "⭐ Seviye/XP — 100 XP = 1 seviye, her seviye ×25 hurda"
            )
        },
        "pazar": {
            "title": "🛒 PAZAR & TİCARET",
            "color": 0x2ECC71,
            "content": (
                "**Pazar (85 eşya, 7 kategori):**\n"
                "• `/pazar [kategori]` — Kategorideki eşyalar\n"
                "  ⚔️ Silah | 🛡️ Zırh | 💊 Medikal | 🍲 Gıda | 🪵 Hammadde | ⚙️ Teknoloji | 🔮 Mistik\n\n"
                "**Alım Satım:**\n"
                "• `/satinal [kod] [adet]` — Eşya al (meslek indirimleri var)\n"
                "• `/bota-sat [esya] [adet]` — Kasaya sat (%20-25 vergi)\n"
                "• `/esya-sat [@üye] [esya] [fiyat]` — Oyuncuya sat\n\n"
                "**Takas & Açık Arttırma:**\n"
                "• `/takas-teklif [@üye] [verilen] [istenen]` — Eşya takası\n"
                "• `/acik-arttirma-baslat [esya] [açılış]` — 2 dk açık arttırma\n"
                "• `/pey-ver [ilan_id] [teklif]` — Açık arttırmaya teklif\n\n"
                "**Tüketim:**\n"
                "• `/tuket [esya]` veya `/kullan [esya]` — Gıda/Medikal tüket, su/sağlık yenile\n\n"
                "**Meslek İndirimleri (%20):**\n"
                "Tüccar (tüm pazar), Demirci (demir), Çiftçi (ekmek/arpa), Simyacı/Doktor (cıva esansı)"
            )
        },
        "yonetim": {
            "title": "🏛️ SİYASET & YÖNETİM",
            "color": 0xF1C40F,
            "content": (
                "**Başkan Seçimi:**\n"
                "• `/secimi-baslat` (Admin) — 15 dk adaylık + 45 dk oylama\n"
                "• `/aday-ol [vaat]` — Aday ol (500 hurda depozito)\n\n"
                "**Başkan Yetkileri:**\n"
                "• `/yonetim` — Sur ve köy geliştirme paneli\n"
                "  🧱 Sur: 250h, +1 seviye | 🏡 Köy: 300h, +1 seviye\n"
                "• `/tayin-et [@üye] [unvan]` — 5 kadroya atama\n"
                "  Unvanlar: Başkan Yardımcısı, Vergi Müfettişi, Muhafız Komutanı, Baş Simyacı, Rahip\n\n"
                "**Maaş Sistemi:**\n"
                "• `/maas-ode [@üye] [miktar]` — Tek sakin maaş\n"
                "• `/meslek-maas-ode [grup] [miktar]` — Meslek grubuna toplu\n"
                "• `/toplu-maas [miktar]` — Tüm sakinlere maaş\n\n"
                "**Gruplar:** muhafiz, saglik, ureticiler, idari"
            )
        },
        "yargi": {
            "title": "⚖️ YARGI & CEZA",
            "color": 0x9E9E9E,
            "content": (
                "**Mahkeme (Başkan):**\n"
                "• `/yargila [@sanık] [suç]` — 3 seçenek:\n"
                "  📢 Halk Oylaması — 2 dk, halk karar verir\n"
                "  💀 İdam — Sanık ölür, -300 hurda itibar kaybı (TİRNANLIK)\n"
                "  🧳 Sürgün — Sanık sürgün, -150 hurda kaybı\n\n"
                "**Hücre (Muhafız):**\n"
                "• `/hucreye-at [@üye]` — Zindana at\n"
                "• `/hucreden-cikar [@üye]` — Tahliye et\n\n"
                "**Sokağa Çıkma Yasağı (Başkan):**\n"
                "• `/sokak-yasagi [durum]` — Aç/kapat\n"
                "Aktifken: gezi, pazar, takas, düello yasak (idari kadro hariç)\n\n"
                "**Darbe:**\n"
                "• `/darbe` — Başkan varsa isyan başlat\n"
                "Başarı şansı: 5-90% (itibar ve savunmaya göre)"
            )
        },
        "kilise": {
            "title": "⛪ ENGİZİSYON & RAHİP",
            "color": 0x9B59B6,
            "content": (
                "**Rahip Yetkileri (sadece Rahip rolü):**\n\n"
                "• `/rahip-paneli` — Panel gösterir\n\n"
                "• `/afaroz-et [@üye] [neden]`\n"
                "  Sapkını dinden çıkar, şans -0.5\n\n"
                "• `/buyuk-kilise-cani`\n"
                "  3 günde 1, tüm sakinlere +10 moral\n\n"
                "• `/kutsa [@üye]`\n"
                "  3 saatte 1, enfeksiyon -20, sağlık +15, moral +5\n\n"
                "• `/kedileri-yok-et` ⚠️ TEHLİKELİ\n"
                "  Sadece 1 kez, tüm Canlı sakinleri Enfekte yapar!"
            )
        },
        "simya": {
            "title": "💊 SAĞLIK & SİMYA",
            "color": 0x1ABC9C,
            "content": (
                "**Doktor (Baş Doktor/Doktor/Karantinacı):**\n\n"
                "• `/doktor-paneli` — Panel\n"
                "• `/asi-uret` — 2 tıbbi malzeme → 1 aşı (+10 XP)\n"
                "• `/tedavi-et [@üye]` — 1 aşı ile hastayı iyileştir (+25 XP)\n\n"
                "**Simyacı (Baş Simyacı/Simyacı):**\n\n"
                "• `/deney` — 3 senaryo:\n"
                "  %10 başarılı (virüs +5, +30 XP)\n"
                "  %85 başarısız\n"
                "  %5-15 ölüm (simyacı ölür, virüs sıfırlanır!)\n"
                "  Lab seviyesi 2: +%25 başarı, seviye 3: +%45\n\n"
                "• `/laboratuvar-gelistir` (Başkan/Baş Simyacı)\n"
                "  500 hurda/seviye, max seviye 3"
            )
        },
        "kolluk": {
            "title": "🛡️ KOLLUK & SAVUNMA",
            "color": 0x2980B9,
            "content": (
                "**Muhafız Sınıfı:**\n\n"
                "• `/muhafiz-paneli` — Panel\n"
                "• `/hucreye-at [@üye]` — Zindana at\n"
                "• `/hucreden-cikar [@üye]` — Tahliye\n\n"
                "• `/nobet` ⭐\n"
                "  4 saatte 1, 40-80 hurda + 20 XP\n"
                "  Komutan +%50, muhafız +%20 bonus\n"
                "  %20 hırsız yakalama, %10 sıkıcı nöbet\n\n"
                "**Karantina:**\n"
                "• `/karantina-al [@üye]` — Enfekte sakini karantinaya\n"
                "  Yetkililer: Başkan, Yardımcı, Komutan, Muhafız, Karantinacı\n"
                "• `/karantina-kaldir [@üye]` — Karantinadan çıkar\n\n"
                "**Başkan Savunma:**\n"
                "• `/savunmayi-guclendir` — 500 hurda, +15 tahkimat (max 100)"
            )
        },
        "uretim": {
            "title": "🌾 ÜRETİM & AMBAR",
            "color": 0xF39C12,
            "content": (
                "**Çalışma Komutları (30 dk CD):**\n\n"
                "• `/tarla-calis` — Çiftçi/Çoban/Değirmenci/Hancı\n"
                "  Hava: ☀️ Yaz x2.0 | 🌱 İlkbahar x1.5 | 🌧️ Yağmurlu x0.7 | ❄️ Kış x0.3\n"
                "  +15 XP\n\n"
                "• `/maden-kaz` — Madenci/Demirci\n"
                "  Kış x0.6, Yağmurlu x0.8 | +20 XP\n\n"
                "• `/orman-kes` — Oduncu/Hancı\n"
                "  Yaz x1.3, Yağmurlu x0.5, Kış x0.2 | +15 XP\n\n"
                "**Ambar:**\n"
                "• `/ambar` — Stokları gör\n"
                "• `/ambara-bagis [esya] [adet]` — Bağış, +2h/adet + itibar\n"
                "• `/ambardan-al [esya] [adet]` — Max 5/adet, fakirlere ücretsiz\n\n"
                "⭐ Seviye atlama otomatik!"
            )
        },
        "savas": {
            "title": "⚔️ SAVAŞ & KEŞİF",
            "color": 0xC0392B,
            "content": (
                "**Düello:**\n"
                "• `/duello [@rakip]` — Tur tabanlı, butonlu\n"
                "  ⚔️ Saldır, 🛡️ Defans, ⚡ Yetenek (%50 kritik)\n"
                "  Kaybedenin %20 ihtimalle kalıcı ölüm!\n\n"
                "**Sefer (Başkan):**\n"
                "• `/sefer` — 10 kişilik manga, 60 sn lobi\n"
                "  150+ hasar = kalıcı ölüm\n"
                "  Zafer: zorluk +1, ganimet, +50 XP\n\n"
                "**Zombi Baskını (RP Owner):**\n"
                "• `/zombi-baskini-baslat` — Manuel baskın\n"
                "  Surlar kanalına alarm, 2 dk savunma\n\n"
                "**Keşif:**\n"
                "• `/gez [bolge]` — 6 saat CD\n"
                "  Tüm RP kanalları mevcut\n"
                "  %50 olumlu / %30 olumsuz / %20 gizemli\n\n"
                "**Anıt:** `/anit` — Şeref listesi ve şehitler"
            )
        },
        "ekonomi": {
            "title": "💰 EKONOMİ & ÇEVRE",
            "color": 0xE67E22,
            "content": (
                "**Vergi (Vergi Memuru/Müfettişi):**\n"
                "• `/maliye-yonetim` — Panel + oran ayarlama\n"
                "  Veba Vergisi: 5 saatte bir (default 20h)\n"
                "  Ticaret Kesintisi: %10-50\n\n"
                "**Hava Durumu:**\n"
                "• `/hava-durumu-degis [mevsim]` — Admin\n"
                "  4 mevsim: İlkbahar, Yaz, Yağmurlu, Kış\n\n"
                "**RP Owner Paneli (`/sunucu-yonetimi`):**\n"
                "• 👑 Kraliyet Desteği — +2000 odun, +1000 kömür, +500h, +1 sur\n"
                "• ☣️ Toplu Enfeksiyon — Tüm canlıları enfekte et\n"
                "• 🌍 Hava Menüsü — Mevsim değiştir\n"
                "• ☣️ Salgın Kuvveti — Düşük/Orta/Kıyamet\n\n"
                "**Otomatik Task'lar:**\n"
                "1h: Yedekleme | 5h: Vergi | 6h: Gazete | 24h: Açlık"
            )
        },
        "admin": {
            "title": "🔧 YÖNETİM & ADMİN",
            "color": 0x7F8C8D,
            "content": (
                "**RP Owner Komutları:**\n\n"
                "• `/owner-kayit [@üye] [isim] [soyisim] [yas] [memleket]`\n"
                "  Bir üyeyi zorla kaydet\n\n"
                "• `/kayit-sil [@üye] EVET`\n"
                "  Üyenin sicil kaydını sil\n\n"
                "• `/sunucu-yonetimi`\n"
                "  Tanrısal kontrol paneli (Kraliyet, Enfeksiyon, Hava)\n\n"
                "• `/zombi-baskini-baslat`\n"
                "  Manuel zombi baskını başlat\n\n"
                "**Admin Komutları:**\n\n"
                "• `/db-sifirla EVET` — Tüm veritabanını sıfırla\n"
                "• `/xp_kazan_test [miktar] [@üye]` — Test XP ekle\n"
                "• `/secimi-baslat` — Seçim süreci başlat\n"
                "• `/hava-durumu-degis [mevsim]` — Mevsim değiştir\n"
                "• `/haber [kanal]` — Gazete kanalı ayarla\n\n"
                "**Prefix versiyonları:**\n"
                "• `v.owner-kayit`, `v.kayit-sil`, `v.sunucu-yonetimi`\n"
                "• `v.db-sifirla EVET`, `v.xp_kazan_test`, `v.secimi-baslat`"
            )
        },
    }
    veri = kategoriler.get(kategori, {"title": "❓ Bilinmeyen", "color": 0x7F8C8D, "content": "Kategori bulunamadı."})
    embed = discord.Embed(title=veri["title"], color=veri["color"])
    embed.description = veri["content"]
    embed.set_footer(text="Sığınak Veba RP v5.4 | Başka kategori için tekrar seçim yap")
    return embed


async def setup(bot):
    await bot.add_cog(RehberCog(bot))

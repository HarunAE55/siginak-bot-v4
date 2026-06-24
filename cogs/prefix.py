"""
Cog: Prefix Komutları (v.) - v5.9
=================================
Tüm ana komutlar için v. prefix desteği.
Slash komutlar hâlâ çalışır, bu ek olarak v. prefix de sağlar.

v5.9 YENİDEN YAZIM:
- TÜM prefix komutları slash komutlarıyla BİREBİR AYNI çıktıyı verir.
- Aynı embed yapıları, aynı renk kodları, aynı metinler, aynı footer'lar.
- Türkçe alias'lar korundu (v.kayıt = v.kayit, vb.)
- Tüm sürüm numaraları v5.9 olarak gösteriliyor.

Örnek kullanımlar:
  v.kayit Johann Bauer 25 Bavyera
  v.profil
  v.destek
  v.rehber
  v.pazar Silah
  v.satinal 01 1
  v.gez "Terkedilmiş Köy"
  v.anit
  v.envanter
  v.biyografi-yaz Bavaryalı bir köylü, veba salgınında hayatta kalmaya çalışan bir gezgin.
  v.meslek-sec ciftci
  v.meslek-yonetim
  v.ambar
  v.ciftci-paneli
  v.tarla-calis
  v.maden-kaz
  v.orman-kes
  v.tuket "Kuru Taş Ekmeği"
  v.db-sifirla EVET  (sadece admin)

Türkçe Alias'lar:
  v.kayıt          = v.kayit
  v.anıt           = v.anit
  v.yargıla        = v.yargila
  v.meslek-seç     = v.meslek-sec
  v.ambara-bağış   = v.ambara-bagis
  v.karantina-kaldır = v.karantina-kaldir
  v.savunmayı-güçlendir = v.savunmayi-guclendir
  v.hucreden-çıkar = v.hucreden-cikar
  v.laboratuvar-geliştir = v.laboratuvar-gelistir
  v.hava-durumu-değiş = v.hava-durumu-degis
  v.sunucu-yönetimi = v.sunucu-yonetimi
  v.maliye-yönetim = v.maliye-yonetim
  v.meslek-maaş-öde = v.meslek-maas-ode
  v.toplu-maaş     = v.toplu-maas
  v.owner-kayıt    = v.owner-kayit
  v.kayıt-sil      = v.kayit-sil
  v.zombi-baskını-başlat = v.zombi-baskini-baslat
  v.yardım         = v.destek
"""

import discord
from discord.ext import commands
import random
import asyncio
import datetime

from veritabani import (
    db, verileri_kaydet, olu_kontrolu, bar_olustur,
    sakin_olustur_defaults, sakin_sil, xp_ekle, haber_ekle,
    sokak_ve_karantina_kontrolu, olum_protokolu,
    admin_mi, rp_owner_mi,
    RP_OWNER_ROL_ID,
)
from kanallar import KAYIT_LOG
from cogs.pazar import TAM_PAZAR, katalogdan_isim_bul, PazarView
from cogs.meslek import MESLEK_VERILERI
from cogs.simya import MESLEK_GRUPLARI
from cogs.ambar import ESYA_HARITASI, ESYA_ETIKET


PREFIX = "v."
SURUM = "5.9.1"


class PrefixCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ============================================================
    # YARDIMCI: Context'ten sakin ID al
    # ============================================================
    def _uid(self, ctx):
        return str(ctx.author.id)

    def _sakin_kontrol(self, ctx):
        """Sakin kayıtlı mı ve hayatta mı kontrol et. Hata mesajı veya None döner.
        v5.9: Slash komutlarıyla AYNI hata mesajları."""
        u_id = self._uid(ctx)
        if u_id not in db["sakinler"]:
            return "❌ Önce sığınağa kayıt olmalısın! `v.kayit isim soyisim yaş memleket`"
        kontrol = olu_kontrolu(u_id)
        if kontrol:
            return kontrol
        return None

    # ============================================================
    # v.kayit / v.kayıt - SLASH İLE AYNI ÇIKTI
    # ============================================================
    @commands.command(name="kayit", aliases=["kayıt"])
    async def prefix_kayit(self, ctx, isim: str = None, soyisim: str = None, yas: int = None, memleket: str = None):
        """Kayıt olmak için: v.kayit Johann Bauer 25 Bavyera"""
        if not isim or not soyisim or yas is None or not memleket:
            await ctx.send("❌ Kullanım: `v.kayit isim soyisim yaş memleket`\nÖrnek: `v.kayit Johann Bauer 25 Bavyera`")
            return

        u_id = self._uid(ctx)

        if yas > 40 or yas < 10:
            await ctx.send("❌ Sığınak kuralları gereği 10-40 yaş arasında olmalısınız!")
            return

        if u_id in db["sakinler"]:
            if db["sakinler"][u_id].get("durum") != "Ölü":
                await ctx.send("❌ Sığınak sicil kütüğünde zaten aktif bir kaydınız mevcut!")
                return

        # Yeni sakin oluşturma (xp_ekle ile seviye atlamayı otomatik işler)
        baslangic_atak = random.randint(10, 20)
        sakin_olustur_defaults(u_id, isim, soyisim, yas, memleket, baslangic_atak)
        verileri_kaydet()

        # SLASH İLE AYNI EMBED
        embed = discord.Embed(title="📝 SIĞINAK SİCİL DEFTERİ — RESMİ SAKİN KAYDI", color=0x34495E)
        embed.description = (
            f"Sığınak nüfus kütüğüne kaydınız işlendi!\n\n"
            f"**Kimlik Kartı Detayları:**\n"
            f"• **Ad Soyad:** `{isim} {soyisim}`\n"
            f"• **Yaş / Memleket:** `{yas} / {memleket}`\n\n"
            f"**Mühürlenen Başlangıç Statüleri:**\n"
            f"• **Rastgele Atak Gücü:** `⚔️ {baslangic_atak}`\n"
            f"• **Sığınak Yardımı:** `500 Akçe` ve `20 XP`\n\n"
            f"💡 *Karakterinin hikayesini yazmak için `/biyografi-yaz` komutunu kullanabilirsin.*"
        )
        await ctx.send(embed=embed)

        # Kayıt log kanalına da yaz (slash ile aynı)
        try:
            kanal = self.bot.get_channel(KAYIT_LOG)
            if kanal:
                log_embed = discord.Embed(title="📝 Yeni Sakin Kaydı", color=0x2ECC71)
                log_embed.description = (
                    f"👤 **Kullanıcı:** {ctx.author.mention}\n"
                    f"🎭 **Karakter:** `{isim} {soyisim}`\n"
                    f"🎂 **Yaş:** `{yas}`\n"
                    f"📍 **Memleket:** `{memleket}`\n"
                    f"⚔️ **Başlangıç Atak:** `{baslangic_atak}`"
                )
                await kanal.send(embed=log_embed)
        except Exception:
            pass

    # ============================================================
    # v.profil - SLASH İLE AYNI ÇIKTI
    # ============================================================
    @commands.command(name="profil")
    async def prefix_profil(self, ctx):
        u_id = self._uid(ctx)
        if u_id not in db["sakinler"]:
            await ctx.send("❌ Sığınak sicil kütüğünde kaydınız bulunmuyor!")
            return
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await ctx.send(olu_kontrol)
            return

        sakin = db["sakinler"][u_id]

        # Durum emojisi (slash ile aynı)
        durum = sakin.get("durum", "Canlı")
        durum_emoji = {
            "Canlı": "🟢",
            "Sağlıklı": "🟢",
            "Enfekte": "🟡",
            "Karantinada": "🟠",
            "Hücrede": "🔴",
            "Ölü": "💀",
            "Sürgün": "🔵"
        }.get(durum, "⚪")

        embed = discord.Embed(
            title=f"👤 {sakin['isim'].upper()} {sakin['soyisim'].upper()} — SİCİL KARTI",
            color=0x3498DB
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)

        # Kimlik bilgileri (slash ile birebir aynı)
        embed.add_field(name=f"{durum_emoji} Durum", value=f"`{durum}`", inline=True)
        embed.add_field(name="💼 Aktif Meslek", value=f"`{sakin.get('meslek_isim', 'Gezgin')}`", inline=True)
        embed.add_field(name="🏅 Seviye / XP", value=f"`Seviye {sakin.get('seviye', 1)}` / `{sakin.get('xp', 0)} XP`", inline=True)

        embed.add_field(name="💰 Cüzdan", value=f"`{sakin.get('cuzdan', 0)} Akçe`", inline=True)
        embed.add_field(name="⚔️ Atak Gücü", value=f"`{sakin.get('atak', 10)}`", inline=True)
        embed.add_field(name="🛡️ Defans Gücü", value=f"`{sakin.get('defans', 0)}`", inline=True)

        embed.add_field(name="🎂 Yaş", value=f"`{sakin.get('yas', '?')}`", inline=True)
        embed.add_field(name="📍 Memleket", value=f"`{sakin.get('memleket', 'Bilinmiyor')}`", inline=True)
        embed.add_field(name="🎯 İtibar", value=f"`{sakin.get('itibar', 50)}`", inline=True)

        # Barlar - v5.9: enfeksiyon negatif stat
        embed.add_field(name="❤️ Sağlık", value=bar_olustur(sakin.get("saglik", 100)), inline=False)
        embed.add_field(name="💧 Su ve Besin", value=bar_olustur(sakin.get("su", 100)), inline=False)
        embed.add_field(name="🧠 Akıl Sağlığı", value=bar_olustur(sakin.get("akil_sagligi", 100)), inline=False)
        embed.add_field(name="☣️ Enfeksiyon Yükü", value=bar_olustur(sakin.get("enfeksiyon", 0), negatif=True), inline=False)
        embed.add_field(name="😊 Moral", value=bar_olustur(sakin.get("moral", 50)), inline=False)

        # Biyografi (slash ile aynı)
        biyografi = sakin.get("biyografi", "").strip()
        if biyografi:
            embed.add_field(
                name="📖 Biyografi",
                value=f"*{biyografi[:1000]}*" if len(biyografi) <= 1000 else f"*{biyografi[:1000]}...*",
                inline=False
            )
        else:
            embed.add_field(
                name="📖 Biyografi",
                value="*Karakterinin hikayesi henüz yazılmadı. `/biyografi-yaz` komutuyla ekleyebilirsin.*",
                inline=False
            )

        await ctx.send(embed=embed)

    # ============================================================
    # v.envanter - SLASH İLE AYNI ÇIKTI
    # ============================================================
    @commands.command(name="envanter")
    async def prefix_envanter(self, ctx):
        u_id = self._uid(ctx)
        if u_id not in db["sakinler"]:
            await ctx.send("❌ Önce sığınağa kayıt olmalısınız!")
            return
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await ctx.send(olu_kontrol)
            return

        sakin = db["sakinler"][u_id]
        envanter_verisi = sakin.get("envanter", {})

        embed = discord.Embed(title=f"🎒 {sakin['isim'].upper()} SIRT ÇANTASI", color=0xF39C12)

        icerik = ""
        for esya, adet in envanter_verisi.items():
            if adet > 0:
                icerik += f"• 📦 **{esya}**: `{adet} Adet`\n"

        embed.description = icerik if icerik else "*Sırt çantan bomboş, pazardan alışveriş yapmalısın!*"
        await ctx.send(embed=embed)

    # ============================================================
    # v.biyografi-yaz - SLASH İLE AYNI ÇIKTI
    # ============================================================
    @commands.command(name="biyografi-yaz")
    async def prefix_biyografi(self, ctx, *, metin: str = None):
        if not metin:
            await ctx.send("❌ Kullanım: `v.biyografi-yaz [metin]`\nÖrnek: `v.biyografi-yaz Bavaryalı bir köylü, ailesini vebada kaybetti.`")
            return

        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return

        if len(metin) > 1000:
            await ctx.send(f"❌ Biyografi çok uzun! Max 1000 karakter, sizin yazdığınız: `{len(metin)}`")
            return

        if len(metin.strip()) < 10:
            await ctx.send("❌ Biyografi en az 10 karakter olmalı!")
            return

        u_id = self._uid(ctx)
        son_degisim = db["sakinler"][u_id].get("son_biyografi_degisimi")
        if son_degisim:
            fark = datetime.datetime.now() - datetime.datetime.fromisoformat(son_degisim)
            if fark.total_seconds() < 259200:  # 3 gün
                kalan_saat = int((259200 - fark.total_seconds()) / 3600)
                await ctx.send(f"❌ Biyografini kısa süre önce değiştirdin! {kalan_saat} saat beklemelisin.")
                return

        db["sakinler"][u_id]["biyografi"] = metin.strip()
        db["sakinler"][u_id]["son_biyografi_degisimi"] = datetime.datetime.now().isoformat()
        verileri_kaydet()

        # SLASH İLE AYNI EMBED
        embed = discord.Embed(title="📖 BİYOGRAFİ GÜNCELLENDİ", color=0x9B59B6)
        embed.description = (
            f"Karakterinin hikayesi sicil kütüğüne işlendi!\n\n"
            f"**Yeni Biyografi:**\n*{metin.strip()}*\n\n"
            f"⏱️ *Bir sonraki değişiklik 3 gün sonra yapılabilir.*"
        )
        await ctx.send(embed=embed)

    # ============================================================
    # v.destek / v.yardım - SLASH /yardim İLE AYNI MENÜ
    # ============================================================
    @commands.command(name="destek", aliases=["yardım", "yardim"])
    async def prefix_destek(self, ctx):
        # Slash /yardim ile aynı dropdown menüyü kullan
        embed = discord.Embed(title="📖 SIĞINAK VEBEA RP - KOMUT MERKEZİ", color=0x2C3E50)
        if self.bot.user and self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.description = (
            "**Hoş geldin sakin!**\n\n"
            "Aşağıdaki menüden bir kategori seçerek o kategoriye ait tüm komutları görebilirsin.\n\n"
            "**Kategoriler:**\n"
            "Kayıt & Profil | Pazar & Ticaret | Siyaset & Yönetim\n"
            "Yargı & Ceza | Engizisyon & Rahip | Sağlık & Simya\n"
            "Kolluk & Savunma | Üretim & Ambar | Savaş & Keşif\n"
            "Ekonomi & Çevre | Yönetim & Admin\n\n"
            "İpucu: Komutlar hem /slash hem v.prefix ile çalışır ve **aynı çıktıyı** verir."
        )
        embed.set_footer(text=f"Sığınak Veba RP v{SURUM} | Kategori seçmek için aşağıdaki menüyü kullan")
        # cogs.rehber'den YardimView'i import et
        from cogs.rehber import YardimView
        await ctx.send(embed=embed, view=YardimView())

    # ============================================================
    # v.rehber - SLASH /rehber İLE AYNI
    # ============================================================
    @commands.command(name="rehber")
    async def prefix_rehber(self, ctx):
        embed = discord.Embed(title="📖 SIĞINAK REHBERİ - Detaylı Bilgi", color=0x9B59B6)
        embed.description = (
            "**Detaylı Rehber Sistemi**\n\n"
            "Aşağıdaki menüden bir kategori seç. Seçtiğin kategoride:\n"
            "Komutların nasıl kullanılacağını, ne işe yaradığını,\n"
            "örnek kullanımları ve ipuçlarını görebilirsin.\n\n"
            "Yeni başlayanlar için: Kayıt & Profil kategorisinden başla!\n\n"
            "💡 İpucu: `/slash` ve `v.prefix` komutları **birebir aynı çıktıyı** verir."
        )
        embed.set_footer(text=f"Sığınak Veba RP v{SURUM} | Detaylı rehber")
        from cogs.rehber import YardimView
        await ctx.send(embed=embed, view=YardimView())

    # ============================================================
    # v.pazar - SLASH İLE AYNI DROPDOWN MENÜ
    # ============================================================
    @commands.command(name="pazar")
    async def prefix_pazar(self, ctx, *, kategori: str = None):
        # Kategori verilmediyse slash gibi dropdown menü göster
        if not kategori:
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
                "💡 **Satın almak için:** `/satinal [kod] [adet]` veya `v.satinal [kod] [adet]`\n"
                "💡 **Satmak için:** `/bota-sat [esya] [adet]` veya `v.bota-sat [esya] [adet]`"
            )
            embed.set_footer(text=f"Sığınak Veba RP v{SURUM} | Kategori seçmek için aşağıdaki menüyü kullan")
            await ctx.send(embed=embed, view=PazarView())
            return

        # Kategori verilmişse direkt listele (slash dropdown callback ile aynı format)
        kategori_emoji = {
            "Silah": "⚔️", "Zırh": "🛡️", "Medikal": "💊", "Gıda": "🍲",
            "Hammadde": "🪵", "Teknoloji": "⚙️", "Mistik": "🔮"
        }

        # Kategori eşleştirme (büyük/küçük harf duyarsız)
        kategori_kapitale = None
        for k in kategori_emoji:
            if k.lower() == kategori.lower():
                kategori_kapitale = k
                break

        if not kategori_kapitale:
            await ctx.send(f"❌ Geçersiz kategori! Seçenekler: {', '.join(kategori_emoji.keys())}")
            return

        embed = discord.Embed(
            title=f"{kategori_emoji[kategori_kapitale]} SIĞINAK PAZAR TEZGAHI — {kategori_kapitale.upper()}",
            color=0x2ECC71
        )
        embed.description = "*Satın almak için `v.satinal esya_kodu adet` komutunu kullan*\n\n"

        sayac = 0
        for kod, veri in TAM_PAZAR.items():
            if veri["tip"] != kategori_kapitale:
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

        embed.set_footer(text=f"Sığınak Veba RP v{SURUM} | Başka kategori için: v.pazar")
        await ctx.send(embed=embed)

    # ============================================================
    # v.satinal - SLASH İLE AYNI ÇIKTI
    # ============================================================
    @commands.command(name="satinal")
    async def prefix_satinal(self, ctx, esya_kodu: str = None, adet: int = 1):
        if not esya_kodu:
            await ctx.send("❌ Kullanım: `v.satinal <esya_kodu> <adet>`\nÖrnek: `v.satinal 01 1`")
            return

        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return

        u_id = self._uid(ctx)
        if esya_kodu not in TAM_PAZAR:
            await ctx.send("❌ Girdiğiniz pazar kodu katalogda bulunmuyor!")
            return
        if adet <= 0:
            await ctx.send("❌ Alım adedi en az 1 olmalı!")
            return

        sakin = db["sakinler"][u_id]
        urun = TAM_PAZAR[esya_kodu]
        meslek = sakin.get("meslek_anahtar", "gezgin")

        # Mesleki indirim motoru (slash ile birebir aynı)
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
            await ctx.send(
                f"❌ Bakiyeniz yetersiz! Gereken: `{toplam_maliyet}` Akçe, Cüzdanınızda: `{sakin['cuzdan']}`."
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

        # SLASH İLE AYNI mesaj formatı
        msg = f"🛒 Alım tamamlandı.\n• Alınan: `{adet} Adet {urun['isim']}`\n• Toplam Ödenen: `💰 {toplam_maliyet} Akçe`"
        if indirim_uygula:
            msg += " *(Mesleki %20 İndirim Uygulandı!)*"
        msg += f"\n• Karaktere Yansıyan Bonus: `+{b_degeri} {b_turu}`"
        await ctx.send(msg)

    # ============================================================
    # v.bota-sat - SLASH İLE AYNI EMBED
    # ============================================================
    @commands.command(name="bota-sat")
    async def prefix_bota_sat(self, ctx, esya_ad: str = None, adet: int = 1):
        if not esya_ad:
            await ctx.send('❌ Kullanım: `v.bota-sat <esya_adı> <adet>`\nÖrnek: `v.bota-sat "Paslı Demir Kama" 1`')
            return

        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return

        u_id = self._uid(ctx)
        sakin = db["sakinler"][u_id]
        envanter = sakin.get("envanter", {})

        mevcut_adet = envanter.get(esya_ad, 0)
        if mevcut_adet < adet:
            await ctx.send(f"❌ Envanterinizde yeterli miktarda `{esya_ad}` bulunamadı! Sizde olan: `{mevcut_adet}` Adet.")
            return

        # KATALOGDAN FİYAT BULMA - TAM_PAZAR kullanılır
        orijinal_fiyat = None
        tam_isim, fiyat = katalogdan_isim_bul(esya_ad)
        if tam_isim:
            orijinal_fiyat = fiyat
            esya_ad = tam_isim  # büyük/küçük harf düzeltmesi

        if orijinal_fiyat is None:
            await ctx.send("❌ Bu eşya sığınak pazar kayıtlarında tanınmıyor! İsim hatası yapmadığınızdan emin olun.")
            return

        # Vergi hesaplama (slash ile aynı)
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

        # SLASH İLE AYNI EMBED
        embed = discord.Embed(title="♻️ SIĞINAK İDARESİ GERİ DÖNÜŞÜM RAPORU", color=0xE67E22)
        embed.description = (
            f"**Satan Sakin:** {ctx.author.mention}\n"
            f"**Teslim Edilen:** `{adet} Adet {esya_ad}`\n\n"
            f"• Eşya Başı Orijinal Değer: `{orijinal_fiyat} Akçe`\n"
            f"• Toplam Brüt Tutar: `{brut_kazanc} Akçe`\n"
            f"• Değer Kaybı Vergisi (%{int(vergi_orani * 100)}): `-{vergi_kesintisi} Akçe`\n"
            f"--- \n"
            f"• **Cüzdana Aktarılan Net Kazanç:** `💰 {net_kazanc} Akçe`"
        )
        embed.set_footer(text="Borsa dengeleme protokolü uygulandı.")
        await ctx.send(embed=embed)

    # ============================================================
    # v.esya-sat - SLASH İLE AYNI (oyuncuya satış)
    # ============================================================
    @commands.command(name="esya-sat")
    async def prefix_esya_sat(self, ctx, kullanici: discord.User = None, *, args: str = None):
        """v.esya-sat @üye <esya> <fiyat>"""
        if kullanici is None or args is None:
            await ctx.send("❌ Kullanım: `v.esya-sat @üye <esya_adı> <fiyat>`\nÖrnek: `v.esya-sat @John \"Paslı Demir Kama\" 200`")
            return

        if kullanici.id == ctx.author.id:
            await ctx.send("❌ Kendi kendine bir şey satamazsın!")
            return

        # Args: "esya adı" fiyat
        parcalar = args.rsplit(None, 1)
        if len(parcalar) != 2:
            await ctx.send("❌ Kullanım: `v.esya-sat @üye <esya_adı> <fiyat>`")
            return

        esya_ad, fiyat_str = parcalar
        try:
            fiyat = int(fiyat_str)
        except ValueError:
            await ctx.send("❌ Fiyat sayı olmalı!")
            return

        if fiyat < 0:
            await ctx.send("❌ Fiyat negatif olamaz!")
            return

        s_id = str(ctx.author.id)
        a_id = str(kullanici.id)

        if s_id not in db["sakinler"] or a_id not in db["sakinler"]:
            await ctx.send("❌ Oyuncu kayıtları sistemde bulunamadı!")
            return

        kontrol = sokak_ve_karantina_kontrolu(s_id)
        if kontrol:
            await ctx.send(kontrol)
            return

        satici_env = db["sakinler"][s_id].get("envanter", {})

        # TAM_PAZAR ile isim doğrulama
        gercek_esya_ad, _ = katalogdan_isim_bul(esya_ad)
        if not gercek_esya_ad:
            await ctx.send("❌ Girdiğiniz eşya ismi pazar kataloğunda kayıtlı değil!")
            return

        if satici_env.get(gercek_esya_ad, 0) < 1:
            await ctx.send(f"❌ Sırt çantanızda satılık `{gercek_esya_ad}` bulunmuyor!")
            return

        # Aynı view'i kullan (cogs.pazar'dan import)
        from cogs.pazar import EsyaSatView
        view = EsyaSatView(ctx.author, kullanici, gercek_esya_ad, fiyat)
        await ctx.send(
            f"💰 {ctx.author.mention}, {kullanici.mention} kullanıcısına doğrudan bir satış teklifi gönderdi!\n"
            f"• Satılacak Ürün: `1 Adet {gercek_esya_ad}`\n"
            f"• Talep Edilen Ücret: `🪙 {fiyat} Akçe`\n"
            f"**Alıcının onaylaması durumunda ticaret el altından tescillenecektir.**",
            view=view
        )

    # ============================================================
    # v.takas-teklif - SLASH İLE AYNI
    # ============================================================
    @commands.command(name="takas-teklif")
    async def prefix_takas_teklif(self, ctx, kullanici: discord.User = None, *, args: str = None):
        """v.takas-teklif @üye <verilecek_esya> | <istenen_esya>"""
        if kullanici is None or args is None:
            await ctx.send('❌ Kullanım: `v.takas-teklif @üye <verilecek_esya> | <istenen_esya>`\nÖrnek: `v.takas-teklif @John "Demir Kılıç" | "Çelik Zırh"`')
            return

        if kullanici.id == ctx.author.id:
            await ctx.send("❌ Kendi kendine takas yapamazsın!")
            return

        if "|" not in args:
            await ctx.send('❌ Kullanım: `v.takas-teklif @üye <verilecek_esya> | <istenen_esya>`')
            return

        parcalar = args.split("|", 1)
        verilecek = parcalar[0].strip().strip('"').strip("'")
        istenen = parcalar[1].strip().strip('"').strip("'")

        eden_id = str(ctx.author.id)
        edilen_id = str(kullanici.id)

        if eden_id not in db["sakinler"] or edilen_id not in db["sakinler"]:
            await ctx.send("❌ Taraflardan birinin sığınak kütük kaydı bulunamadı!")
            return

        kontrol = sokak_ve_karantina_kontrolu(eden_id)
        if kontrol:
            await ctx.send(kontrol)
            return

        eden_env = db["sakinler"][eden_id].get("envanter", {})
        edilen_env = db["sakinler"][edilen_id].get("envanter", {})

        v_esya_ad, _ = katalogdan_isim_bul(verilecek)
        i_esya_ad, _ = katalogdan_isim_bul(istenen)

        if not v_esya_ad or not i_esya_ad:
            await ctx.send("❌ Girdiğiniz eşya isimleri pazar kataloğunda eşleşmedi!")
            return

        if eden_env.get(v_esya_ad, 0) < 1:
            await ctx.send(f"❌ Envanterinizde satılık `{v_esya_ad}` bulunmuyor!")
            return
        if edilen_env.get(i_esya_ad, 0) < 1:
            await ctx.send(f"❌ Karşı tarafın envanterinde `{i_esya_ad}` bulunmuyor!")
            return

        from cogs.pazar import TakasOnayView
        view = TakasOnayView(ctx.author, kullanici, v_esya_ad, i_esya_ad)
        await ctx.send(
            f"🤝 {ctx.author.mention}, {kullanici.mention} kullanıcısına bir takas teklif etti!\n"
            f"• Verilecek Ürün: `1 Adet {v_esya_ad}`\n"
            f"• İstenen Ürün: `1 Adet {i_esya_ad}`\n"
            f"**İki tarafın da aşağıdaki onay butonuna basması gerekmektedir.**",
            view=view
        )

    # ============================================================
    # v.acik-arttirma-baslat - SLASH İLE AYNI
    # ============================================================
    @commands.command(name="acik-arttirma-baslat")
    async def prefix_ihale_baslat(self, ctx, *, args: str = None):
        """v.acik-arttirma-baslat <esya> <baslangic_fiyati>"""
        if not args:
            await ctx.send('❌ Kullanım: `v.acik-arttirma-baslat <esya_adı> <açılış_fiyatı>`\nÖrnek: `v.acik-arttirma-baslat "Paslı Demir Kama" 100`')
            return

        parcalar = args.rsplit(None, 1)
        if len(parcalar) != 2:
            await ctx.send('❌ Kullanım: `v.acik-arttirma-baslat <esya_adı> <açılış_fiyatı>`')
            return

        esya_ad, fiyat_str = parcalar
        esya_ad = esya_ad.strip('"').strip("'")
        try:
            baslangic_fiyati = int(fiyat_str)
        except ValueError:
            await ctx.send("❌ Fiyat sayı olmalı!")
            return

        u_id = self._uid(ctx)
        if u_id not in db["sakinler"]:
            await ctx.send("❌ Önce sığınağa kaydolmalısın!")
            return

        kontrol = sokak_ve_karantina_kontrolu(u_id)
        if kontrol:
            await ctx.send(kontrol)
            return

        if baslangic_fiyati < 1:
            await ctx.send("❌ Başlangıç fiyatı en az 1 Akçe olmalıdır!")
            return

        sakin = db["sakinler"][u_id]
        envanter = sakin.get("envanter", {})

        gercek_esya_ad, _ = katalogdan_isim_bul(esya_ad)
        if not gercek_esya_ad:
            await ctx.send("❌ Bu eşya pazar kataloğunda bulunamadı!")
            return

        if envanter.get(gercek_esya_ad, 0) < 1:
            await ctx.send(f"❌ Sırt çantanızda açık arttırmaya çıkaracak `{gercek_esya_ad}` yok!")
            return

        # Eşyayı açık arttırma süresince envanterden düş
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
            "kanal_id": ctx.channel.id
        }
        verileri_kaydet()

        # SLASH İLE AYNI EMBED
        embed = discord.Embed(title="📢 YENİ AÇIK ARTTIRMA İLANI", color=0x9B59B6)
        embed.description = (
            f"🏛️ **İlan Kodu:** `{ilan_id}`\n"
            f"👤 **Satıcı Sakin:** {ctx.author.mention}\n"
            f"📦 **Açık Arttırmadaki Eşya:** `{gercek_esya_ad}`\n"
            f"🪙 **Taban Açılış Fiyatı:** `{baslangic_fiyati} Akçe`\n\n"
            f"⏳ **Kalan Süre:** `2 Dakika (120 Saniye)`\n"
            f"ℹ️ Pey vermek için `v.pey-ver {ilan_id} [Miktar]` komutunu kullanın!"
        )
        embed.set_footer(text="Süre dolduğunda en yüksek teklif sahibine otomatik teslim edilecektir.")
        await ctx.send(embed=embed)

        # 2 dakika bekle
        await asyncio.sleep(120)

        # İhale bitiş protokolü (slash ile birebir aynı)
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

            kanal = self.bot.get_channel(ihale.get("kanal_id") or ctx.channel.id)
            if kanal:
                await kanal.send(embed=bitis_embed)
            else:
                await ctx.send(embed=bitis_embed)

    # ============================================================
    # v.pey-ver - SLASH İLE AYNI EMBED
    # ============================================================
    @commands.command(name="pey-ver")
    async def prefix_pey_ver(self, ctx, ilan_id: str = None, teklif: int = None):
        if not ilan_id or teklif is None:
            await ctx.send("❌ Kullanım: `v.pey-ver <ilan_id> <teklif>`\nÖrnek: `v.pey-ver 1234 250`")
            return

        u_id = self._uid(ctx)
        if u_id not in db["sakinler"]:
            await ctx.send("❌ Sığınak sicil kütüğünde kaydınız yok!")
            return
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await ctx.send(olu_kontrol)
            return

        ihale = db["acik_arttirmalar"].get(ilan_id)
        if not ihale or not ihale["aktif"]:
            await ctx.send("❌ Bu kodda aktif bir açık arttırma ilanı bulunamadı!")
            return

        if ihale["satici_id"] == u_id:
            await ctx.send("❌ Kendi ilanına pey veremezsin!")
            return

        sakin = db["sakinler"][u_id]
        cuzdan = sakin.get("cuzdan", 0)

        if teklif <= ihale["en_yuksek_pey"]:
            await ctx.send(f"❌ Geçersiz teklif! Şu anki en yüksek teklif `{ihale['en_yuksek_pey']} Akçe`. Daha üstünü vermelisiniz!")
            return

        if cuzdan < teklif:
            await ctx.send(f"❌ Cüzdanınızda teklif ettiğiniz kadar `{teklif}` Akçe bulunmuyor!")
            return

        # Eski pey sahibine iade
        if ihale["en_son_peyleyen"] is not None:
            eski_alici_id = ihale["en_son_peyleyen"]
            db["sakinler"][eski_alici_id]["cuzdan"] += ihale["en_yuksek_pey"]

        sakin["cuzdan"] -= teklif
        ihale["en_yuksek_pey"] = teklif
        ihale["en_son_peyleyen"] = u_id
        verileri_kaydet()

        # SLASH İLE AYNI EMBED
        pey_embed = discord.Embed(title="🔥 AÇIK ARTTIRMADA REKABET KIZIŞTI!", color=0xE17055)
        pey_embed.description = (
            f"🏛️ **İlan Kodu:** `{ilan_id}`\n"
            f"📦 **Eşya:** `{ihale['esya']}`\n"
            f"🚀 **Yeni En Yüksek Teklif:** `🪙 {teklif} Akçe`\n"
            f"👤 **Teklif Sahibi:** {ctx.author.mention}"
        )
        await ctx.send(embed=pey_embed)

    # ============================================================
    # v.tuket / v.kullan - SLASH İLE AYNI EMBED
    # ============================================================
    @commands.command(name="tuket", aliases=["kullan"])
    async def prefix_tuket(self, ctx, *, esya_ad: str = None):
        if not esya_ad:
            await ctx.send("❌ Kullanım: `v.tuket <esya_adı>`\nÖrnek: `v.tuket Kuru Taş Ekmeği`")
            return

        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return

        u_id = self._uid(ctx)
        sakin = db["sakinler"][u_id]
        envanter = sakin.get("envanter", {})

        mevcut = envanter.get(esya_ad, 0)
        if mevcut < 1:
            await ctx.send(f"❌ Envanterinizde `{esya_ad}` bulunmuyor!")
            return

        # Eşyanın tipini ve bonusunu katalogdan bul
        urun = None
        for kod, veri in TAM_PAZAR.items():
            if veri["isim"].lower() == esya_ad.lower():
                urun = veri
                esya_ad = veri["isim"]
                break

        if not urun:
            await ctx.send("❌ Bu eşya katalogda tanınmıyor, tüketilemez!")
            return

        if urun["tip"] not in ["Gıda", "Medikal"]:
            await ctx.send(f"❌ `{esya_ad}` tüketilebilir bir gıda/medikal değil! (Tip: {urun['tip']})")
            return

        # Tüket ve etki uygula (slash ile birebir aynı)
        envanter[esya_ad] -= 1
        if envanter[esya_ad] == 0:
            del envanter[esya_ad]

        b_turu = urun["bonus_turu"]
        b_degeri = urun["bonus_degeri"]
        etkiler = []

        if b_turu == "Su Seviyesi":
            sakin["su"] = min(100, sakin.get("su", 100) + b_degeri)
            etkiler.append(f"💧 Su +{b_degeri}")
        elif b_turu == "Sağlık Takviyesi":
            sakin["saglik"] = min(100, sakin.get("saglik", 100) + b_degeri)
            etkiler.append(f"❤️ Sağlık +{b_degeri}")
        elif b_turu == "Akıl Sağlığı":
            sakin["akil_sagligi"] = min(100, max(0, sakin.get("akil_sagligi", 100) + b_degeri))
            etkiler.append(f"🧠 Akıl +{b_degeri}")
        elif b_turu == "Enfeksiyon Direnci":
            sakin["enfeksiyon"] = max(0, sakin.get("enfeksiyon", 0) - b_degeri)
            etkiler.append(f"☣️ Enfeksiyon -{b_degeri}")

        verileri_kaydet()

        # SLASH İLE AYNI EMBED
        embed = discord.Embed(title="🍽️ TÜKETİLDİ", color=0xF39C12)
        embed.description = (
            f"👤 **Tüketen:** {ctx.author.mention}\n"
            f"📦 **Tüketilen:** `1 Adet {esya_ad}`\n\n"
            f"**Etkiler:**\n" + "\n".join([f"• {e}" for e in etkiler])
        )
        await ctx.send(embed=embed)

    # ============================================================
    # v.meslek-sec / v.meslek-seç - SLASH İLE AYNI
    # ============================================================
    @commands.command(name="meslek-sec", aliases=["meslek-seç"])
    async def prefix_meslek_sec(self, ctx, *, secim: str = None):
        if not secim:
            liste = ", ".join([f"`{k}`" for k, v in MESLEK_VERILERI.items() if not v["atama"]])
            await ctx.send(f"❌ Kullanım: `v.meslek-sec <meslek_anahtarı>`\nSeçenekler: {liste}")
            return

        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return

        u_id = self._uid(ctx)
        secim_temiz = secim.lower().strip()

        if secim_temiz not in MESLEK_VERILERI:
            await ctx.send("❌ Sığınak tüzüğünde böyle bir iş kolu bulunamadı!")
            return

        meslek_veri = MESLEK_VERILERI[secim_temiz]
        if meslek_veri["atama"]:
            await ctx.send(f"❌ `{meslek_veri['isim']}` mesleği sadece Belediye Başkanı tarafından atanabilir!")
            return

        mevcut_meslek = db["sakinler"][u_id].get("meslek_anahtar", "gezgin")
        if secim_temiz == mevcut_meslek:
            await ctx.send("❌ Zaten bu mesleği icra ediyorsun!")
            return

        # 3 gün cooldown
        son_degisim = db["sakinler"][u_id].get("son_meslek_degisimi")
        if son_degisim:
            fark = datetime.datetime.now() - datetime.datetime.fromisoformat(son_degisim)
            if fark.total_seconds() < 259200:
                kalan_saat = int((259200 - fark.total_seconds()) / 3600)
                await ctx.send(f"❌ Meslek değiştirebilmek için {kalan_saat} saat beklemelisin!")
                return

        db["sakinler"][u_id]["meslek_anahtar"] = secim_temiz
        db["sakinler"][u_id]["meslek_isim"] = meslek_veri["isim"]
        db["sakinler"][u_id]["son_meslek_degisimi"] = datetime.datetime.now().isoformat()
        verileri_kaydet()

        # SLASH İLE AYNI mesaj
        await ctx.send(f"💼 **MESLEK DEĞİŞİKLİĞİ:** Yeni mesleğin resmen **{meslek_veri['isim']}** olarak tescillendi.")

    # ============================================================
    # v.meslek-yonetim - SLASH İLE AYNI EMBED (panel dict)
    # ============================================================
    @commands.command(name="meslek-yonetim")
    async def prefix_meslek_yonetim(self, ctx):
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return

        u_id = self._uid(ctx)
        sakin = db["sakinler"][u_id]
        meslek = sakin.get("meslek_anahtar", "gezgin")
        m_isim = sakin.get("meslek_isim", "Gezgin")

        # cogs.meslek'teki paneller dict'ini import et
        from cogs.meslek import MeslekCog
        # Paneller slash ile aynı olmalı - doğrudan kopyala
        paneller = {
            "belediye_baskani": "👑 **SIĞINAK YÜCE KABİNE PANELİ**\n• Vergi Oranları Koridoru: Sabit %20\n• Sığınak Güvenlik Defansı: `[🟩🟩🟩🟩🟩🟩🟩🟩🟩⬛] %90`\n• Ambar Ödenek Durumu: `45.000 Akçe`",
            "baskan_yardimcisi": "📜 **BAŞKAN YARDIMCILIĞI BÜROSU**\n• Onay Bekleyen Sakin Dilekçeleri: `0`\n• İç Düzen Koruma Kararnameleri: Aktif.",
            "vergi_mufettisi": "⚖️ **MERKEZİ MALİYE DENETİM MASASI**\n• Sığınak Enflasyon Katsayısı: `1.0`\n• Karapara ve Kaçak Akçe İncelemesi: Temiz.",
            "bas_simyaci": "🔮 **KADİM SİMYA LABORATUVARI**\n• İksir Kazanı Sıcaklığı: `180°C`\n• Mevcut Simya Karışım Formülü: *Cıva Esansı Birleşimi*",
            "simyaci": "🔮 **KADİM SİMYA LABORATUVARI**\n• İksir Kazanı Sıcaklığı: `180°C`\n• Mevcut Simya Karışım Formülü: *Cıva Esansı Birleşimi*",
            "bas_doktor": "🩺 **SIĞINAK REVİR BAŞHEKİMLİĞİ**\n• Yatak Doluluk Oranı: `2 / 10`\n• Karantina Altındaki Sakin Sayısı: `0`.",
            "doktor": "🩺 **SIĞINAK REVİR BAŞHEKİMLİĞİ**\n• Yatak Doluluk Oranı: `2 / 10`\n• Karantina Altındaki Sakin Sayısı: `0`.",
            "karantinaci": "☣️ **SALGIN TECRİT VE DEZENFEKSİYON BİRİMİ**\n• Sığınak Hava Filtre Kalitesi: `%94`\n• Atık Radyasyon İzolasyonu: Güvenli.",
            "muhafiz_komutani": "⚔️ **MUHAFIZ ALAY KOMUTANLIĞI STRATEJİ ODASI**\n• Nöbetçi Muhafız Hattı: Tam Kadro\n• Cephanelik Ok ve Barut Rezervi: Tam Dolu.",
            "muhafiz": "🛡️ **NİZAM MUHAFIZ DEVRİYE RAPORU**\n• Bölge Güvenlik Durumu: Sakin ve Tehdit Yok.\n• Emir Komuta Hattı: Komutana Bağlı.",
            "nisanci": "🏹 **SUR ÜSTÜ NİŞANCI MEVZİSİ**\n• Arbalet Gerginlik Ayarı: Tam Performans\n• Görüş Mesafesi: Açık ve Net.",
            "izci": "🧭 **KAYIP DEHLİZLER KEŞİF DEFTERİ**\n• Haritalandırılan Mağara Tüneli: `12 / 50`\n• Dış Dünya Radyasyon Sızıntı Raporu: Stabil.",
            "ciftci": "🌾 **SERA VE TARIM ARAZİSİ ANALİZİ**\n• Toprak Nem Oranı: `🟩🟩🟩🟩🟩🟩⬛⬛⬛⬛ %60`\n• Hasada Kalan Gün: `2 Tur`.",
            "coban": "🐏 **SIĞINAK MANDIRA VE SÜRÜ SAYIMI**\n• Sürüdeki Küçükbaş Sayısı: `24 Baş`\n• Günlük Süt ve Yün Verimliliği: Yüksek.",
            "demirci": "🔥 **ÖRSLÜ DEMİRCİ OCAĞI KÖRÜĞÜ**\n• Ocak Sıcaklığı: Yüksek Kor Derecesi\n• Üretim Sırası: Ağır Çelik Plaka Göğüslük.",
            "oduncu": "🪵 **HİDROLİK KERESTE BİÇME ATÖLYESİ**\n• Tomruk Stok Seviyesi: `120 Adet Meşe`\n• Testere Diş Kalınlığı: Keskin.",
            "madenci": "⛏️ **DERİN MADEN OCAĞI ŞAFTI**\n• Kazılan Derinlik: `-340 Metre`\n• Tespit Edilen Damar: Yoğun Demir Cevheri.",
            "tuccar": "💰 **TİCARET ODASI VE BAKİYE SİCİLİ**\n• Kredi Skoru: Kusursuz\n• Pazar Tezgah Vergisi Muafiyeti: Aktif (%20 İndirimli).",
            "degirmenci": "⚙️ **HİDROLİK TAŞ DEĞİRMEN ÇARKALARI**\n• Öğütülen Buğday Miktarı: `450 Kg`\n• Çark Dönüş Devri: Dengeli.",
            "hanci": "🍺 **SIĞINAK HAN MAHMUR RAPORU**\n• Masalardaki Sakin Sayısı: `14 Sakin`\n• Boş Oda Durumu: `4 / 12 Oda Boş`.",
            "gezgin": "👣 **AVARE GEZGİN YOL HARİTASI**\n• Adımlanan Koridor Sayısı: Bilinmiyor\n• Günlük Serbest Keşif İzni: Sınırsız.",
            "avci": "🎯 **YABAN AV PARSEL TAKİP DEFTERİ**\n• Kurulan Tuzak Sayısı: `3 Adet`\n• Avlanan Son Canlı: Yaban Domuzu.",
            "arastirmaci": "🔬 **KAYIP TEKNOLOJİ TEZGAHI ANALİZİ**\n• Çözülen Şifreli Devre Kartı: `%45`\n• Eski Dünya Arşiv Kaydı: Okunuyor.",
            "kraliyet_elcisi": "👑 **DİPLOMATİK ELÇİLİK MÜHÜR ODASI**\n• Gelen Dış Mektuplar: `Yolsuzluk Yok`\n• Diplomatik Dokunulmazlık Durumu: Geçerli.",
            "rahip": "⛪ **KUTSAL MANASTIR DUA KÜRSÜSÜ**\n• İbadete Gelen Cemaat Huzuru: Sakin\n• Bağış Kutusu Akçe Seviyesi: `230 Akçe`.",
            "mezarci": "🪦 **SIĞINAK ŞEHİTLİK VE MEZARLIK SİCİLİ**\n• Boş Mezar Hazırlığı: `5 Adet`\n• Defin İşlemi Bekleyen Kadavra: Yok.",
        }

        embed = discord.Embed(title=f"🛠️ {m_isim.upper()} FAALİYET VE YÖNETİM PANELİ", color=0x9B59B6)
        embed.description = paneller.get(meslek, "🧭 Serbest meslek alanı, özel bir panel tetiklenmedi.")
        await ctx.send(embed=embed)

    # ============================================================
    # v.gez - SLASH İLE AYNI EMBED (olay havuzu slash ile aynı)
    # ============================================================
    @commands.command(name="gez")
    async def prefix_gez(self, ctx, *, bolge: str = None):
        # Bölge listesi - slash ile aynı 25 bölge
        gecerli_bolgeler = [
            "Zayıf Surlar", "Toprak Yol", "Boş Ev", "Tarla", "Surların Çevresi",
            "Meydan Ağacı", "Pazar Yeri", "Belediye Binası", "Başkan Salonu",
            "Karantina Kampı", "Mezarlık", "Yeşil Kışla", "Hastane",
            "Simyacının Kulesi", "Kulenin Tepesi", "Karanlık Orman Yolu",
            "Kuzey Pazar", "Han", "Su Kuyusu", "İhtişamlı Hane", "Maden Ocağı",
            "Önderin Köşkü", "Oduncunun Yeri", "Sırlar Mağarası", "Gizemli Bataklık"
        ]
        if not bolge:
            await ctx.send(
                "❌ Kullanım: `v.gez <bolge>`\n"
                "Bölgeler: " + ", ".join(gecerli_bolgeler)
            )
            return

        # Bölge eşleştirme
        bolge_eslesen = None
        for g in gecerli_bolgeler:
            if g.lower() == bolge.lower():
                bolge_eslesen = g
                break

        if not bolge_eslesen:
            await ctx.send(f"❌ Geçersiz bölge! Seçenekler: {', '.join(gecerli_bolgeler)}")
            return

        bolge = bolge_eslesen
        u_id = self._uid(ctx)

        if u_id not in db["sakinler"]:
            await ctx.send("❌ Sicil kaydın yok! `v.kayit` ol.")
            return

        kontrol = sokak_ve_karantina_kontrolu(u_id)
        if kontrol:
            await ctx.send(kontrol)
            return

        sakin = db["sakinler"][u_id]

        # 6 saat cooldown
        son_gezi = sakin.get("son_gezi")
        if son_gezi:
            fark = datetime.datetime.now() - datetime.datetime.fromisoformat(son_gezi)
            if fark.total_seconds() < 21600:
                kalan_saat = int((21600 - fark.total_seconds()) / 3600)
                kalan_dk = int(((21600 - fark.total_seconds()) % 3600) / 60)
                await ctx.send(f"❌ Yorgunsun, dinlenmen gerekiyor! **{bolge}** bölgesine tekrar gitmek için `{kalan_saat} saat {kalan_dk} dakika` beklemelisin.")
                return

        await ctx.send(f"🥾 {ctx.author.mention}, çantanı hazırladın ve `{bolge}` bölgesine doğru yola çıktın... Kader zarın atılıyor!")

        await asyncio.sleep(3)

        # Olay havuzunu import et (cogs.kesif'ten)
        from cogs.kesif import OLUMLU_OLAYLAR, OLUMSUZ_OLAYLAR, GIZEMLI_OLAYLAR, olay_ekisini_uygula

        zar = random.randint(1, 10)
        if zar <= 5:
            secilen_olay, etki = random.choice(OLUMLU_OLAYLAR)
            embed_renk = 0x2ECC71
            kategori = "OLUMLU"
        elif zar <= 8:
            secilen_olay, etki = random.choice(OLUMSUZ_OLAYLAR)
            embed_renk = 0xC0392B
            kategori = "OLUMSUZ"
        else:
            secilen_olay, etki = random.choice(GIZEMLI_OLAYLAR)
            embed_renk = 0x9B59B6
            kategori = "GİZEMLİ"

        # v5.9: sakin_id parametresi ile çağır (xp seviye atlama fix)
        ek_metin = olay_ekisini_uygula(u_id, sakin, etki)

        sakin["son_gezi"] = datetime.datetime.now().isoformat()
        verileri_kaydet()

        # SLASH İLE AYNI EMBED
        embed = discord.Embed(title=f"🗺️ SEFARET RAPORU: {bolge}", color=embed_renk)
        if ek_metin:
            embed.description = (
                f"👣 {ctx.author.mention}, seyahatin sırasında:\n\n"
                f"**{secilen_olay}**\n\n"
                f"_{ek_metin}_"
            )
        else:
            embed.description = (
                f"👣 {ctx.author.mention}, seyahatin sırasında:\n\n"
                f"**{secilen_olay}**"
            )
        embed.set_footer(text=f"Kategori: {kategori} | Zar: {zar}/10 | Cooldown: 6 saat | Sığınak Veba RP v{SURUM}")
        await ctx.send(embed=embed)

        haber_ekle(f"🥾 {sakin.get('isim', ctx.author.name)} {bolge} bölgesine gezi düzenledi. ({kategori})")

    # ============================================================
    # v.anit / v.anıt - SLASH İLE AYNI EMBED (v5.9 sıralama fix)
    # ============================================================
    @commands.command(name="anit", aliases=["anıt"])
    async def prefix_anit(self, ctx):
        # v5.9: seviye*100+xp ile sırala
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

        olu_sakinler = [(s_id, v) for s_id, v in db["sakinler"].items() if v.get("durum") == "Ölü"]
        sehit = ""
        if olu_sakinler:
            for s_id, veri in olu_sakinler[:20]:
                isim = veri.get("isim", "Bilinmeyen")
                soyisim = veri.get("soyisim", "")
                meslek = veri.get("meslek_isim", "Gezgin")
                sehit += f"⚰️ **{isim} {soyisim}** — *{meslek}*\n"
            if len(olu_sakinler) > 20:
                sehit += f"*... ve {len(olu_sakinler) - 20} şehit daha.*\n"
        else:
            sehit = "*Henüz sığınak için can veren olmamış.*\n"

        embed = discord.Embed(title="🏛️ SIĞINAK MEYDANI KADİM BAŞARI ANITI", color=0xF1C40F)
        embed.description = (
            "📜 **SIĞINAK TEMEL KANUNLARI:**\n"
            "1. Belediye başkanının sözü emirdir, aksini iddia etmek isyandır.\n"
            "2. Mahkeme kararlarına ve hücre cezalarına karşı gelmek darbe sebebi sayılır.\n"
            "3. Kilise kurallarına uymayanlar engizisyon tarafından afaroz edilir.\n"
            "4. Ölü bir karakter tüm eşyalarını kaybeder, yeniden `/kayit` olmak zorundadır.\n"
            "5. 6 saatten az sürede tekrar gezi yapılamaz.\n\n"
            "✨ **SIĞINAK KAHRAMANLARI ŞEREF KÜRSÜSÜ:**\n" + (seref_kursusu or "*Henüz anita adı kazınan bir kahraman yok.*\n") + "\n"
            "💀 **ŞEHİTLER DUVARI — Sığınak İçin Can Verenler:**\n" + sehit + "\n"
            f"📅 **Kuruluş Tarihi:** Sığınak kapıları `03.01.2026` tarihinde mühürlenerek hayata başlamıştır."
        )
        embed.set_footer(text=f"Sığınak Veba RP v{SURUM}")
        await ctx.send(embed=embed)

    # ============================================================
    # v.ambar - SLASH İLE AYNI EMBED
    # ============================================================
    @commands.command(name="ambar")
    async def prefix_ambar(self, ctx):
        stoklar = db["koy_ambari"]["stoklar"]
        embed = discord.Embed(title="🏡 SIĞINAK KOLEKTİF KÖY AMBARI STOK RAPORU", color=0x34495E)
        ambar_text = "📋 **Mevcut Ortak Stok Bilgileri:**\n\n"
        for anahtar, etiket in ESYA_ETIKET.items():
            miktar = stoklar.get(anahtar, 0)
            ambar_text += f"{etiket}: `{miktar} Adet`\n"
        embed.description = ambar_text
        embed.set_footer(text=f"Sığınak Seviyesi: {db['sistem_ayarlari'].get('koy_seviyesi', 1)} | Toplam Yapılan Bağış: {db['koy_ambari'].get('toplam_bagis_sayisi', 0)}")
        await ctx.send(embed=embed)

    # ============================================================
    # v.ambara-bagis / v.ambara-bağış - SLASH İLE AYNI
    # ============================================================
    @commands.command(name="ambara-bagis", aliases=["ambara-bağış"])
    async def prefix_ambara_bagis(self, ctx, esya_ad: str = None, adet: int = None):
        if not esya_ad or adet is None:
            await ctx.send("❌ Kullanım: `v.ambara-bagis <esya_adı> <adet>`\nÖrnek: `v.ambara-bagis erzak 5`")
            return

        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return

        u_id = self._uid(ctx)
        sakin = db["sakinler"][u_id]

        if adet <= 0:
            await ctx.send("❌ Bağış miktarı pozitif bir sayı olmalıdır!")
            return

        temiz_ad = ESYA_HARITASI.get(esya_ad.lower().strip())
        if not temiz_ad:
            await ctx.send("❌ Geçersiz eşya adı! Bağışlanabilir malzemeler: `erzak`, `ilaç`, `odun`, `kömür`")
            return

        if "envanter" not in sakin:
            sakin["envanter"] = {}

        mevcut_stok = sakin["envanter"].get(temiz_ad, 0)
        if mevcut_stok < adet:
            await ctx.send(f"❌ Envanterinizde yeterli malzeme yok! Mevcut: `{mevcut_stok}` adet {esya_ad}.")
            return

        # Transfer (slash ile aynı)
        sakin["envanter"][temiz_ad] -= adet
        if sakin["envanter"][temiz_ad] == 0:
            del sakin["envanter"][temiz_ad]
        db["koy_ambari"]["stoklar"][temiz_ad] = db["koy_ambari"]["stoklar"].get(temiz_ad, 0) + adet
        db["koy_ambari"]["toplam_bagis_sayisi"] += 1

        # İtibar ödülü
        itibar_bonusu = adet * 2
        sakin["cuzdan"] = sakin.get("cuzdan", 0) + itibar_bonusu
        sakin["itibar"] = min(100, sakin.get("itibar", 50) + adet)
        verileri_kaydet()

        embed = discord.Embed(title="🤝 AMBARA YÜCE BAĞIŞ PROTOKOLÜ", color=0x2ECC71)
        embed.description = (
            f"👤 **Hayırsever Sakin:** {ctx.author.mention}\n"
            f"📦 **Köy Ambarına Teslim Edilen:** `{adet} Adet {ESYA_ETIKET[temiz_ad]}`\n\n"
            f"📈 **Toplumsal İtibar Ödülü:** `+{itibar_bonusu} Akçe` ve `+{adet} İtibar Puanı`"
        )
        await ctx.send(embed=embed)
        haber_ekle(f"🤝 {sakin['isim']} köy ambarına {adet} adet {ESYA_ETIKET[temiz_ad]} bağışladı.")

    # ============================================================
    # v.ambardan-al - SLASH İLE AYNI
    # ============================================================
    @commands.command(name="ambardan-al")
    async def prefix_ambardan_al(self, ctx, esya_ad: str = None, adet: int = None):
        if not esya_ad or adet is None:
            await ctx.send("❌ Kullanım: `v.ambardan-al <esya_adı> <adet>`\nÖrnek: `v.ambardan-al erzak 3`")
            return

        u_id = self._uid(ctx)
        if u_id not in db["sakinler"]:
            await ctx.send("❌ Sığınak siciliniz bulunamadı!")
            return
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await ctx.send(olu_kontrol)
            return

        sakin = db["sakinler"][u_id]
        if sakin.get("durum") == "Sürgün":
            await ctx.send("❌ Sürgün edilmiş bir suçlu olarak köy ambarına yaklaşamazsınız!")
            return
        if adet <= 0:
            await ctx.send("❌ Geçersiz adet miktarı!")
            return
        if adet > 5:
            await ctx.send("❌ Suistimali önlemek adına tek seferde ambardan en fazla `5` adet malzeme çekebilirsiniz!")
            return

        temiz_ad = ESYA_HARITASI.get(esya_ad.lower().strip())
        if not temiz_ad:
            await ctx.send("❌ Geçersiz eşya adı! İstenebilecek malzemeler: `erzak`, `ilaç`, `odun`, `kömür`")
            return

        cuzdan_durumu = sakin.get("cuzdan", 0)
        saglik_durumu = sakin.get("durum", "Canlı")
        if cuzdan_durumu > 400 and saglik_durumu in ["Sağlıklı", "Canlı"]:
            await ctx.send("❌ Durumunuz gayet iyi! Ambar havuzu sadece ihtiyaç sahipleri içindir. Lütfen pazarı kullanın.")
            return

        stoklar = db["koy_ambari"]["stoklar"]
        if stoklar.get(temiz_ad, 0) < adet:
            await ctx.send(f"❌ Köy ambarında yeterli stok kalmamış! Mevcut {ESYA_ETIKET[temiz_ad]} stoku: `{stoklar.get(temiz_ad, 0)}`")
            return

        stoklar[temiz_ad] -= adet
        if "envanter" not in sakin:
            sakin["envanter"] = {}
        sakin["envanter"][temiz_ad] = sakin["envanter"].get(temiz_ad, 0) + adet
        verileri_kaydet()

        embed = discord.Embed(title="📦 SOSYAL YARDIM VE AMBAR TEDARİĞİ", color=0x3498DB)
        embed.description = (
            f"📢 Sığınak Sosyal Yardımlaşma Fonu devrede!\n\n"
            f"👤 **Teslim Alan Sakin:** {ctx.author.mention}\n"
            f"📦 **Tedarik Edilen Malzeme:** `{adet} Adet {ESYA_ETIKET[temiz_ad]}`\n\n"
            f"ℹ️ *Malzemeler envanterinize eklenmiştir.*"
        )
        await ctx.send(embed=embed)

    # ============================================================
    # v.ciftci-paneli - SLASH İLE AYNI EMBED
    # ============================================================
    @commands.command(name="ciftci-paneli")
    async def prefix_ciftci_paneli(self, ctx):
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return

        u_id = self._uid(ctx)
        meslek = db["sakinler"][u_id].get("meslek_anahtar", "")
        if meslek not in MESLEK_GRUPLARI["uretici"]:
            await ctx.send("❌ Sığınakta kayıtlı tescilli bir üretici değilsiniz!")
            return

        hava = db["cevre_durumu"].get("hava_durumu", "İlkbahar")
        embed = discord.Embed(title="🌾 SIĞINAK ÜRETİM MERKEZİ", color=0xF1C40F)
        embed.description = (
            f"👋 Merhaba **{db['sakinler'][u_id].get('isim', 'Üretici')}**!\n\n"
            f"🌤️ **Mevcut Hava Durumu:** `{hava}`\n\n"
            f"📋 **Yapabileceğin İşler:**\n"
            f"• `/tarla-calis` veya `v.tarla-calis` — Tarlada çalış, erzak üret (Çiftçi/Çoban/Değirmenci/Hancı)\n"
            f"• `/maden-kaz` veya `v.maden-kaz` — Madende kömür çıkar (Madenci/Demirci)\n"
            f"• `/orman-kes` veya `v.orman-kes` — Ormanda odun kes (Oduncu/Hancı)\n"
            f"• `/tuket [esya]` veya `v.tuket [esya]` — Envanterinden gıda tüket, su ve sağlığını yenile\n\n"
            f"⏱️ *Her çalışma komutu 30 dakika cooldown'a sahiptir.*"
        )
        await ctx.send(embed=embed)

    # ============================================================
    # v.tarla-calis - SLASH İLE AYNI EMBED
    # ============================================================
    @commands.command(name="tarla-calis")
    async def prefix_tarla_calis(self, ctx):
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return

        u_id = self._uid(ctx)
        sakin = db["sakinler"][u_id]
        if sakin.get("durum") == "Hücrede":
            await ctx.send("❌ Hücrede olan biri tarlada çalışamaz!")
            return
        if sakin.get("meslek_anahtar") not in ["ciftci", "coban", "degirmenci", "hanci"]:
            await ctx.send("❌ Toprakla uğraşacak ekipmanınız veya tarım izniniz yok!")
            return

        son = sakin.get("son_calisma")
        if son:
            fark = datetime.datetime.now() - datetime.datetime.fromisoformat(son)
            if fark.total_seconds() < 1800:
                kalan_dk = int((1800 - fark.total_seconds()) / 60)
                await ctx.send(f"❌ Dinlenmeniz gerekiyor! Tarlada tekrar çalışmak için `{kalan_dk} dakika` bekleyin.")
                return

        hava = db["cevre_durumu"]["hava_durumu"]
        taban_erzak = random.randint(10, 20)
        carpan = 1.0
        if hava == "İlkbahar": carpan = 1.5
        elif hava == "Yaz": carpan = 2.0
        elif hava == "Yağmurlu": carpan = 0.7
        elif hava == "Kış": carpan = 0.3

        nihai_erzak = int(taban_erzak * carpan)
        kazanilan_akçe = nihai_erzak * 3
        kazanilan_xp = 15

        db["koy_ambari"]["stoklar"]["erzak"] = db["koy_ambari"]["stoklar"].get("erzak", 0) + nihai_erzak
        sakin["cuzdan"] = sakin.get("cuzdan", 0) + kazanilan_akçe
        atlamalar = xp_ekle(u_id, kazanilan_xp)
        sakin["son_calisma"] = datetime.datetime.now().isoformat()
        verileri_kaydet()

        # SLASH İLE AYNI EMBED
        embed = discord.Embed(title="🌾 HASAT TAMAMLANDI!", color=0x2ECC71)
        embed.description = (
            f"🌤️ **Mevsim/Hava:** `{hava}` (Çarpan: x{carpan})\n"
            f"📦 **Köy Ambarına Eklenen Erzak:** `+{nihai_erzak} Adet`\n"
            f"💰 **Kişisel Kazancınız:** `+{kazanilan_akçe} Akçe` | `+{kazanilan_xp} XP`"
        )
        if atlamalar:
            embed.add_field(
                name="🎉 Seviye Atlamaları",
                value="\n".join([f"• Seviye {a['seviye']}! +{a['odul']} Akçe" for a in atlamalar]),
                inline=False
            )
        await ctx.send(embed=embed)

    # ============================================================
    # v.maden-kaz - SLASH İLE AYNI EMBED
    # ============================================================
    @commands.command(name="maden-kaz")
    async def prefix_maden_kaz(self, ctx):
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return

        u_id = self._uid(ctx)
        sakin = db["sakinler"][u_id]
        if sakin.get("durum") == "Hücrede":
            await ctx.send("❌ Hücrede olan biri madene inemez!")
            return
        if sakin.get("meslek_anahtar") not in ["madenci", "demirci"]:
            await ctx.send("❌ Kazmanız yok, madene inemezsiniz!")
            return

        son = sakin.get("son_calisma")
        if son:
            fark = datetime.datetime.now() - datetime.datetime.fromisoformat(son)
            if fark.total_seconds() < 1800:
                kalan_dk = int((1800 - fark.total_seconds()) / 60)
                await ctx.send(f"❌ Dinlenmeniz gerekiyor! Madene tekrar inmek için `{kalan_dk} dakika` bekleyin.")
                return

        hava = db["cevre_durumu"]["hava_durumu"]
        taban_komur = random.randint(8, 15)
        carpan = 1.0
        if hava == "Kış": carpan = 0.6
        elif hava == "Yağmurlu": carpan = 0.8

        nihai_komur = int(taban_komur * carpan)
        kazanilan_akçe = nihai_komur * 4
        kazanilan_xp = 20

        db["koy_ambari"]["stoklar"]["komur"] = db["koy_ambari"]["stoklar"].get("komur", 0) + nihai_komur
        sakin["cuzdan"] = sakin.get("cuzdan", 0) + kazanilan_akçe
        atlamalar = xp_ekle(u_id, kazanilan_xp)
        sakin["son_calisma"] = datetime.datetime.now().isoformat()
        verileri_kaydet()

        embed = discord.Embed(title="⛏️ MADEN KAZISI BAŞARILI!", color=0x95A5A6)
        embed.description = (
            f"🪨 **Köy Ambarına Eklenen Kömür:** `+{nihai_komur} Adet`\n"
            f"💰 **Kişisel Kazancınız:** `+{kazanilan_akçe} Akçe` | `+{kazanilan_xp} XP`"
        )
        if atlamalar:
            embed.add_field(
                name="🎉 Seviye Atlamaları",
                value="\n".join([f"• Seviye {a['seviye']}! +{a['odul']} Akçe" for a in atlamalar]),
                inline=False
            )
        await ctx.send(embed=embed)

    # ============================================================
    # v.orman-kes - SLASH İLE AYNI EMBED
    # ============================================================
    @commands.command(name="orman-kes")
    async def prefix_orman_kes(self, ctx):
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return

        u_id = self._uid(ctx)
        sakin = db["sakinler"][u_id]
        if sakin.get("durum") == "Hücrede":
            await ctx.send("❌ Hücrede olan biri odun kesemez!")
            return
        if sakin.get("meslek_anahtar") not in ["oduncu", "hanci"]:
            await ctx.send("❌ Baltanız yok, odun kesemezsiniz!")
            return

        son = sakin.get("son_calisma")
        if son:
            fark = datetime.datetime.now() - datetime.datetime.fromisoformat(son)
            if fark.total_seconds() < 1800:
                kalan_dk = int((1800 - fark.total_seconds()) / 60)
                await ctx.send(f"❌ Dinlenmeniz gerekiyor! Ormanda tekrar çalışmak için `{kalan_dk} dakika` bekleyin.")
                return

        hava = db["cevre_durumu"]["hava_durumu"]
        taban_odun = random.randint(12, 22)
        carpan = 1.0
        if hava == "Kış": carpan = 0.2
        elif hava == "Yağmurlu": carpan = 0.5
        elif hava == "Yaz": carpan = 1.3

        nihai_odun = int(taban_odun * carpan)
        kazanilan_akçe = nihai_odun * 2
        kazanilan_xp = 15

        db["koy_ambari"]["stoklar"]["odun"] = db["koy_ambari"]["stoklar"].get("odun", 0) + nihai_odun
        sakin["cuzdan"] = sakin.get("cuzdan", 0) + kazanilan_akçe
        atlamalar = xp_ekle(u_id, kazanilan_xp)
        sakin["son_calisma"] = datetime.datetime.now().isoformat()
        verileri_kaydet()

        embed = discord.Embed(title="🪵 ODUN KESİMİ TAMAMLANDI!", color=0x27AE60)
        embed.description = (
            f"🪓 **Köy Ambarına Eklenen Odun:** `+{nihai_odun} Adet`\n"
            f"💰 **Kişisel Kazancınız:** `+{kazanilan_akçe} Akçe` | `+{kazanilan_xp} XP`"
        )
        if atlamalar:
            embed.add_field(
                name="🎉 Seviye Atlamaları",
                value="\n".join([f"• Seviye {a['seviye']}! +{a['odul']} Akçe" for a in atlamalar]),
                inline=False
            )
        await ctx.send(embed=embed)

    # ============================================================
    # v.tuccar-paneli - SLASH İLE AYNI EMBED
    # ============================================================
    @commands.command(name="tuccar-paneli")
    async def prefix_tuccar_paneli(self, ctx):
        u_id = self._uid(ctx)
        if u_id not in db["sakinler"]:
            await ctx.send("❌ Sicil kaydın yok!")
            return
        if db["sakinler"][u_id].get("meslek_anahtar") != "tuccar":
            await ctx.send("❌ Bu panel sadece Tüccar mesleğine ait!")
            return

        stoklar = db["koy_ambari"]["stoklar"]
        embed = discord.Embed(title="💰 TÜCCAR TİCARET PANELİ", color=0xF1C40F)
        embed.description = (
            f"📊 **Ambar Stokları:**\n"
            f"• 🌾 Erzak: `{stoklar.get('erzak', 0)}` (Alış: 20h / Satış: 35h)\n"
            f"• 🪵 Odun: `{stoklar.get('odun', 0)}` (Alış: 15h / Satış: 25h)\n"
            f"• 🪨 Kömür: `{stoklar.get('komur', 0)}` (Alış: 25h / Satış: 40h)\n"
            f"• ⚕️ Tıbbi: `{stoklar.get('tibbi_malzeme', 0)}` (Alış: 50h / Satış: 80h)\n\n"
            f"💡 **Komutlar:**\n"
            f"• `v.tuccar-al <esya> <adet>` — Ambardan ucuz al\n"
            f"• `v.tuccar-sat <esya> <adet>` — Ambara pahalı sat (kar!)\n\n"
            f"💰 **Cüzdan:** `{db['sakinler'][u_id].get('cuzdan', 0)} Akçe`"
        )
        await ctx.send(embed=embed)

    # ============================================================
    # v.tuccar-al / v.tuccar-sat - SLASH İLE AYNI
    # ============================================================
    @commands.command(name="tuccar-al")
    async def prefix_tuccar_al(self, ctx, esya: str = None, adet: int = None):
        if not esya or adet is None:
            await ctx.send("❌ Kullanım: `v.tuccar-al <esya> <adet>`\nEşyalar: erzak, odun, komur, tibbi_malzeme")
            return

        u_id = self._uid(ctx)
        if u_id not in db["sakinler"]:
            await ctx.send("❌ Sicil kaydın yok!")
            return
        if db["sakinler"][u_id].get("meslek_anahtar") != "tuccar":
            await ctx.send("❌ Sadece Tüccar!")
            return
        if adet <= 0 or adet > 20:
            await ctx.send("❌ 1-20 adet!")
            return

        fiyatlar = {"erzak": 20, "odun": 15, "komur": 25, "tibbi_malzeme": 50}
        birim = fiyatlar.get(esya, 20)
        toplam = birim * adet
        sakin = db["sakinler"][u_id]
        if sakin["cuzdan"] < toplam:
            await ctx.send(f"❌ Yetersiz! Gereken: `{toplam}`")
            return
        stoklar = db["koy_ambari"]["stoklar"]
        if stoklar.get(esya, 0) < adet:
            await ctx.send(f"❌ Stok yok! Mevcut: `{stoklar.get(esya, 0)}`")
            return
        sakin["cuzdan"] -= toplam
        stoklar[esya] -= adet
        if "envanter" not in sakin:
            sakin["envanter"] = {}
        sakin["envanter"][esya] = sakin["envanter"].get(esya, 0) + adet
        verileri_kaydet()
        await ctx.send(f"✅ `{adet} Adet {esya}` ambardan `{toplam} Akçe`'ya alındı!")

    @commands.command(name="tuccar-sat")
    async def prefix_tuccar_sat(self, ctx, esya: str = None, adet: int = None):
        if not esya or adet is None:
            await ctx.send("❌ Kullanım: `v.tuccar-sat <esya> <adet>`")
            return

        u_id = self._uid(ctx)
        if u_id not in db["sakinler"]:
            await ctx.send("❌ Sicil kaydın yok!")
            return
        if db["sakinler"][u_id].get("meslek_anahtar") != "tuccar":
            await ctx.send("❌ Sadece Tüccar!")
            return
        if adet <= 0:
            await ctx.send("❌ Geçersiz adet!")
            return

        sakin = db["sakinler"][u_id]
        envanter = sakin.get("envanter", {})
        if envanter.get(esya, 0) < adet:
            await ctx.send(f"❌ Envanterinde yeterli yok! Mevcut: `{envanter.get(esya, 0)}`")
            return
        fiyatlar = {"erzak": 35, "odun": 25, "komur": 40, "tibbi_malzeme": 80}
        birim = fiyatlar.get(esya, 35)
        toplam = birim * adet
        envanter[esya] -= adet
        if envanter[esya] == 0:
            del envanter[esya]
        sakin["cuzdan"] += toplam
        db["koy_ambari"]["stoklar"][esya] = db["koy_ambari"]["stoklar"].get(esya, 0) + adet
        verileri_kaydet()
        await ctx.send(f"✅ `{adet} Adet {esya}` ambara `{toplam} Akçe`'ya satıldı!")

    # ============================================================
    # v.muhafiz-donanim - SLASH İLE AYNI EMBED
    # ============================================================
    @commands.command(name="muhafiz-donanim")
    async def prefix_muhafiz_donanim(self, ctx, esya: str = None):
        if not esya:
            await ctx.send("❌ Kullanım: `v.muhafiz-donanim <esya>`\nSeçenekler: gogusluk, kalkan, zirh, plaka")
            return

        u_id = self._uid(ctx)
        if u_id not in db["sakinler"]:
            await ctx.send("❌ Sicil kaydın yok!")
            return

        meslek = db["sakinler"][u_id].get("meslek_anahtar", "")
        if meslek not in ["muhafiz_komutani", "muhafiz", "nisanci", "izci"]:
            await ctx.send("❌ Sadece muhafız sınıfı!")
            return

        donanim = {
            "gogusluk": {"isim": "Deri Göğüslük", "defans": 5, "fiyat": 200},
            "kalkan": {"isim": "Demir Kalkan", "defans": 10, "fiyat": 500},
            "zirh": {"isim": "Çelik Zırh", "defans": 20, "fiyat": 1200},
            "plaka": {"isim": "Komutan Plakası", "defans": 30, "fiyat": 2500},
        }
        item = donanim.get(esya)
        if not item:
            await ctx.send("❌ Geçersiz! Seçenekler: gogusluk, kalkan, zirh, plaka")
            return

        sakin = db["sakinler"][u_id]
        if sakin["cuzdan"] < item["fiyat"]:
            await ctx.send(f"❌ Yetersiz! Gereken: `{item['fiyat']}`")
            return
        sakin["cuzdan"] -= item["fiyat"]
        sakin["defans"] = sakin.get("defans", 0) + item["defans"]
        verileri_kaydet()

        # SLASH İLE AYNI EMBED
        embed = discord.Embed(title="🛡️ EKİPMAN ALINDI!", color=0x2980B9)
        embed.description = f"🛡️ **Ekipman:** `{item['isim']}`\n⚡ **Defans:** `+{item['defans']}`\n💰 **Ödenen:** `{item['fiyat']} Akçe`\n🛡️ **Toplam Defans:** `{sakin['defans']}`"
        await ctx.send(embed=embed)

    # ============================================================
    # v.duello - SLASH İLE AYNI
    # ============================================================
    @commands.command(name="duello")
    async def prefix_duello(self, ctx, kullanici: discord.User = None):
        if kullanici is None:
            await ctx.send("❌ Kullanım: `v.duello @rakip`")
            return
        if kullanici.id == ctx.author.id:
            await ctx.send("❌ Kendi kendine meydan okuyamazsın!")
            return

        u_id = str(ctx.author.id)
        r_id = str(kullanici.id)
        if u_id not in db["sakinler"] or r_id not in db["sakinler"]:
            await ctx.send("❌ Taraflardan birinin sığınak kütüğünde kaydı yok!")
            return

        kontrol = sokak_ve_karantina_kontrolu(u_id)
        if kontrol:
            await ctx.send(kontrol)
            return

        if db["sakinler"][u_id].get("durum") == "Ölü" or db["sakinler"][r_id].get("durum") == "Ölü":
            await ctx.send("❌ Ölü karakterler düello yapamaz!")
            return

        veri_eden = db["sakinler"][u_id]
        veri_edilen = db["sakinler"][r_id]

        embed = discord.Embed(title="⚔️ DÜELLO DAVETİ!", color=0xC0392B)
        embed.description = (
            f"🗡️ **{ctx.author.mention}**, **{kullanici.mention}** kullanıcısına meydan okudu!\n\n"
            f"🔺 **Davet Eden:** {veri_eden['isim']} | ⚔️ Atak: `{veri_eden.get('atak', 10)}` | 🛡️ Defans: `{veri_eden.get('defans', 0)}`\n"
            f"🔻 **Davet Edilen:** {veri_edilen['isim']} | ⚔️ Atak: `{veri_edilen.get('atak', 10)}` | 🛡️ Defans: `{veri_edilen.get('defans', 0)}`\n\n"
            f"⚠️ *Kabul edersen ölümcül bir düelloya gireceksin! Kaybedenin %20 ihtimalle karakteri kalıcı olarak ÖLÜR!*\n\n"
            f"⏱️ *Davet 60 saniye sonra otomatik olarak sona erer.*"
        )

        from cogs.savas import DuelloDavetView
        view = DuelloDavetView(ctx.author, kullanici, veri_eden, veri_edilen)
        await ctx.send(
            f"⚔️ {kullanici.mention}, {ctx.author.mention} sana meydan okudu! Kabul ediyor musun?",
            embed=embed,
            view=view
        )

    # ============================================================
    # v.kavga - SLASH İLE AYNI
    # ============================================================
    @commands.command(name="kavga")
    async def prefix_kavga(self, ctx, kullanici: discord.User = None):
        if kullanici is None:
            await ctx.send("❌ Kullanım: `v.kavga @rakip`")
            return
        if kullanici.id == ctx.author.id:
            await ctx.send("❌ Kendinle kavga edemezsin!")
            return

        u_id = str(ctx.author.id)
        r_id = str(kullanici.id)
        if u_id not in db["sakinler"] or r_id not in db["sakinler"]:
            await ctx.send("❌ Taraflardan birinin kaydı yok!")
            return

        if db["sakinler"][u_id].get("durum") == "Ölü" or db["sakinler"][r_id].get("durum") == "Ölü":
            await ctx.send("❌ Ölü karakterler kavga edemez!")
            return

        veri_eden = db["sakinler"][u_id]
        veri_edilen = db["sakinler"][r_id]

        embed = discord.Embed(title="🥊 KAVGA DAVETİ!", color=0xE67E22)
        embed.description = (
            f"🥊 **{ctx.author.mention}**, **{kullanici.mention}** kullanıcısına kavga teklif etti!\n\n"
            f"🔺 **Teklif Eden:** {veri_eden['isim']} | ⚔️ Atak: `{veri_eden.get('atak', 10)}` | 🛡️ Defans: `{veri_eden.get('defans', 0)}`\n"
            f"🔻 **Teklif Edilen:** {veri_edilen['isim']} | ⚔️ Atak: `{veri_edilen.get('atak', 10)}` | 🛡️ Defans: `{veri_edilen.get('defans', 0)}`\n\n"
            f"⚠️ *Bu kavgada kimse ÖLMEZ! Sadece yaralanma olur (sağlık min 5'e düşer).*\n\n"
            f"⏱️ *Davet 60 saniye sonra otomatik olarak sona erer.*"
        )

        from cogs.savas import KavgaDavetView
        view = KavgaDavetView(ctx.author, kullanici, veri_eden, veri_edilen)
        await ctx.send(
            f"🥊 {kullanici.mention}, {ctx.author.mention} sana kavga teklif etti! Kabul ediyor musun?",
            embed=embed,
            view=view
        )

    # ============================================================
    # v.akçe-gonder - SLASH İLE AYNI EMBED
    # ============================================================
    @commands.command(name="akçe-gonder", aliases=["akce-gonder"])
    async def prefix_akce_gonder(self, ctx, hedef: discord.Member = None, miktar: int = None):
        if hedef is None or miktar is None:
            await ctx.send("❌ Kullanım: `v.akçe-gonder @üye <miktar>`")
            return

        u_id = self._uid(ctx)
        if u_id not in db["sakinler"]:
            await ctx.send("❌ Sicil kaydın yok!")
            return
        if str(hedef.id) == u_id:
            await ctx.send("❌ Kendine akçe gönderemezsin!")
            return
        if miktar <= 0:
            await ctx.send("❌ Miktar pozitif olmalı!")
            return
        h_id = str(hedef.id)
        if h_id not in db["sakinler"]:
            await ctx.send("❌ Hedef sakin kayıtlı değil!")
            return

        sakin = db["sakinler"][u_id]
        if sakin["cuzdan"] < miktar:
            await ctx.send(f"❌ Yetersiz! Cüzdan: `{sakin['cuzdan']}`")
            return

        sakin["cuzdan"] -= miktar
        db["sakinler"][h_id]["cuzdan"] += miktar
        verileri_kaydet()

        embed = discord.Embed(title="💸 AKÇE TRANSFERİ", color=0x2ECC71)
        embed.description = f"👤 **Gönderen:** {ctx.author.mention}\n👤 **Alan:** {hedef.mention}\n🪙 **Miktar:** `{miktar} Akçe`"
        await ctx.send(embed=embed)

    # ============================================================
    # v.owner-kayit / v.owner-kayıt - SLASH İLE AYNI EMBED
    # ============================================================
    @commands.command(name="owner-kayit", aliases=["owner-kayıt"])
    async def prefix_owner_kayit(self, ctx, uye: discord.Member = None, isim: str = None, soyisim: str = None, yas: int = None, memleket: str = None, baslangic_akce: int = 500):
        if uye is None or not isim or not soyisim or yas is None or not memleket:
            await ctx.send("❌ Kullanım: `v.owner-kayit @üye <isim> <soyisim> <yas> <memleket> [baslangic_akçe]`")
            return

        if not admin_mi(ctx):
            await ctx.send("❌ Bu komut sadece yönetici ekibine özeldir!")
            return

        if yas > 40 or yas < 10:
            await ctx.send("❌ Yaş 10-40 arası olmalı!")
            return

        u_id = str(uye.id)
        if u_id in db["sakinler"] and db["sakinler"][u_id].get("durum") != "Ölü":
            await ctx.send(f"❌ {uye.mention} zaten aktif bir sicile sahip! Önce `v.kayit-sil` ile mevcut kaydı silin.")
            return

        baslangic_atak = random.randint(10, 20)
        sakin_olustur_defaults(u_id, isim, soyisim, yas, memleket, baslangic_atak)
        db["sakinler"][u_id]["cuzdan"] = baslangic_akce
        verileri_kaydet()

        embed = discord.Embed(title="👑 OWNER KAYDI", color=0xF1C40F)
        embed.description = (
            f"**RP Owner** {ctx.author.mention} tarafından zorla kayıt işlemi gerçekleştirildi!\n\n"
            f"👤 **Kaydedilen Üye:** {uye.mention}\n"
            f"🎭 **Karakter:** `{isim} {soyisim}`\n"
            f"🎂 **Yaş:** `{yas}`\n"
            f"📍 **Memleket:** `{memleket}`\n"
            f"⚔️ **Başlangıç Atak:** `{baslangic_atak}`\n"
            f"💰 **Başlangıç Akçe:** `{baslangic_akce}`"
        )
        await ctx.send(embed=embed)

    # ============================================================
    # v.kayit-sil / v.kayıt-sil - SLASH İLE AYNI EMBED
    # ============================================================
    @commands.command(name="kayit-sil", aliases=["kayıt-sil"])
    async def prefix_kayit_sil(self, ctx, uye: discord.Member = None, onay: str = None):
        if uye is None or onay is None:
            await ctx.send("❌ Kullanım: `v.kayit-sil @üye EVET`")
            return

        if not admin_mi(ctx):
            await ctx.send("❌ Bu komut sadece yönetici ekibine özeldir!")
            return

        if onay.upper() != "EVET":
            await ctx.send("❌ Onaylamak için `EVET` yazmalısınız. Bu işlem geri alınamaz!")
            return

        u_id = str(uye.id)
        if u_id not in db["sakinler"]:
            await ctx.send(f"❌ {uye.mention} zaten sicil kütüğünde kayıtlı değil!")
            return

        silinen_isim = db["sakinler"][u_id].get("isim", "?")
        silinen_soyisim = db["sakinler"][u_id].get("soyisim", "?")
        sakin_sil(u_id)

        embed = discord.Embed(title="🗑️ SİCİL KAYDI SİLİNDİ", color=0xE74C3C)
        embed.description = (
            f"**RP Owner** {ctx.author.mention} tarafından sicil kaydı silindi!\n\n"
            f"👤 **Etkilenen Üye:** {uye.mention}\n"
            f"🎭 **Silinen Karakter:** `{silinen_isim} {silinen_soyisim}`\n\n"
            f"⚠️ *Bu işlem geri alınamaz. Üye yeniden `/kayit` olmak zorundadır.*"
        )
        await ctx.send(embed=embed)

    # ============================================================
    # v.db-sifirla - SLASH İLE AYNI EMBED
    # ============================================================
    @commands.command(name="db-sifirla")
    async def prefix_db_sifirla(self, ctx, onay: str = None):
        """Veritabanını tamamen sıfırlar. Sadece Yetkili Ekip. Örnek: v.db-sifirla EVET"""
        # v5.9.1: has_permissions(administrator=True) kaldırıldı
        # Artık sadece admin_mi() ile kontrol ediliyor - Yönetici Ekip rolü olanlar da kullanabilir
        if not admin_mi(ctx):
            await ctx.send("❌ Bu komut sadece yetkili ekibe özeldir!")
            return

        if onay != "EVET":
            await ctx.send("⚠️ **DİKKAT!** Bu işlem tüm kayıtları siler!\nOnaylamak için: `v.db-sifirla EVET`")
            return

        eski_sayi = len(db.get("sakinler", {}))

        db.clear()
        db["sakinler"] = {}
        db["sistem_ayarlari"] = {
            "KASA_AKÇE_PLACEHOLDER": 50000,
            "toplam_kayitli_sakin": 0,
            "sur_seviyesi": 1,
            "koy_seviyesi": 1
        }

        from veritabani import db_ilkle
        db_ilkle()
        verileri_kaydet()

        # SLASH İLE AYNI EMBED
        embed = discord.Embed(title="🗑️ VERİTABANI SIFIRLANDI", color=0xE74C3C)
        embed.description = (
            f"✅ Tüm veritabanı sıfırlandı!\n\n"
            f"📊 **Silinen Sakin Sayısı:** `{eski_sayi}`\n"
            f"💰 **Kasa:** `50000 Akçe` (default)\n"
            f"🧱 **Sur Seviyesi:** `1`\n"
            f"🏡 **Köy Seviyesi:** `1`\n\n"
            f"⚠️ *Tüm oyuncular yeniden `/kayit` olmak zorundadır.*\n"
            f"💡 *Yedekleme kanalındaki eski yedekleri de silin (yoksa bot açılışta geri yükleyebilir).*"
        )
        await ctx.send(embed=embed)

    @prefix_db_sifirla.error
    async def db_sifirla_error(self, ctx, error):
        # v5.9.1: has_permissions kaldırıldığı için MissingPermissions gelmez, ama yine de genel hata yakalama kalsın
        await ctx.send(f"❌ Hata: {error}")

    # ============================================================
    # v.kaynak-ekle - SLASH İLE AYNI
    # ============================================================
    @commands.command(name="kaynak-ekle")
    async def prefix_kaynak_ekle(self, ctx, kaynak: str = None, miktar: int = None):
        if not kaynak or miktar is None:
            await ctx.send("❌ Kullanım: `v.kaynak-ekle <kaynak> <miktar>`\nKaynaklar: odun, komur, erzak, tibbi_malzeme, KASA_AKÇE_PLACEHOLDER")
            return

        if not admin_mi(ctx):
            await ctx.send("❌ Bu komut sadece yetkili ekibe özeldir!")
            return
        if miktar <= 0 or miktar > 100000:
            await ctx.send("❌ Miktar 1-100000 arası!")
            return

        if kaynak == "KASA_AKÇE_PLACEHOLDER":
            db["sistem_ayarlari"]["KASA_AKÇE_PLACEHOLDER"] = db["sistem_ayarlari"].get("KASA_AKÇE_PLACEHOLDER", 0) + miktar
            verileri_kaydet()
            await ctx.send(f"✅ Kasaya `{miktar} Akçe` eklendi! Yeni: `{db['sistem_ayarlari']['KASA_AKÇE_PLACEHOLDER']}`")
        else:
            db["koy_ambari"]["stoklar"][kaynak] = db["koy_ambari"]["stoklar"].get(kaynak, 0) + miktar
            verileri_kaydet()
            await ctx.send(f"✅ `{kaynak}` stokuna `{miktar}` eklendi! Yeni: `{db['koy_ambari']['stoklar'][kaynak]}`")

    # ============================================================
    # v.xp_kazan_test - SLASH İLE AYNI EMBED
    # ============================================================
    @commands.command(name="xp_kazan_test")
    async def prefix_xp_test(self, ctx, miktar: int = None, hedef: discord.Member = None):
        if miktar is None:
            await ctx.send("❌ Kullanım: `v.xp_kazan_test <miktar> [@üye]`")
            return

        if not admin_mi(ctx):
            await ctx.send("❌ Bu komut sadece yetkili ekibe özeldir!")
            return

        if miktar <= 0 or miktar > 10000:
            await ctx.send("❌ Miktar 1-10000 arası!")
            return

        hedef_user = hedef if hedef else ctx.author
        h_id = str(hedef_user.id)

        if h_id not in db["sakinler"]:
            await ctx.send("❌ Hedef sakin kayıtlı değil!")
            return

        atlamalar = xp_ekle(h_id, miktar)
        verileri_kaydet()

        # SLASH İLE AYNI EMBED
        embed = discord.Embed(title="🧪 TEST: XP Eklendi", color=0xE67E22)
        embed.description = f"👤 **Hedef:** {hedef_user.mention}\n📈 **Eklenen XP:** `{miktar}`"
        if atlamalar:
            embed.description += "\n\n🎉 **SEVİYE ATLAMALAR:**\n"
            for a in atlamalar:
                embed.description += f"• Seviye {a['seviye']}! +{a['odul']} Akçe ödülü\n"
        embed.set_footer(text="Bu komut sadece yöneticilere açıktır.")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(PrefixCog(bot))

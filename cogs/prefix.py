"""
Cog: Prefix Komutları (v.)
==========================
Tüm ana komutlar için v. prefix desteği.
Slash komutlar hala çalışır, bu ek olarak v. prefix de sağlar.

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
    RP_OWNER_ROL_ID,
)
from cogs.pazar import TAM_PAZAR, katalogdan_isim_bul
from cogs.meslek import MESLEK_VERILERI
from cogs.simya import MESLEK_GRUPLARI
from cogs.ambar import ESYA_HARITASI, ESYA_ETIKET


PREFIX = "v."


class PrefixCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ============================================================
    # YARDIMCI: Context'ten sakin ID al
    # ============================================================
    def _uid(self, ctx):
        return str(ctx.author.id)

    def _sakin_kontrol(self, ctx):
        """Sakin kayıtlı mı ve hayatta mı kontrol et. Hata mesajı veya None döner."""
        u_id = self._uid(ctx)
        if u_id not in db["sakinler"]:
            return "❌ Önce sığınağa kayıt olmalısın! `v.kayit isim soyisim yaş memleket`"
        kontrol = olu_kontrolu(u_id)
        if kontrol:
            return kontrol
        return None

    # ============================================================
    # v.kayit
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

        baslangic_atak = random.randint(10, 20)
        sakin_olustur_defaults(u_id, isim, soyisim, yas, memleket, baslangic_atak)
        verileri_kaydet()

        embed = discord.Embed(title="📝 SIĞINAK SİCİL DEFTERİ — RESMİ SAKİN KAYDI", color=0x34495E)
        embed.description = (
            f"Sığınak nüfus kütüğüne kaydınız işlendi!\n\n"
            f"**Kimlik Kartı:**\n"
            f"• **Ad Soyad:** `{isim} {soyisim}`\n"
            f"• **Yaş / Memleket:** `{yas} / {memleket}`\n"
            f"• **Rastgele Atak Gücü:** `⚔️ {baslangic_atak}`\n"
            f"• **Sığınak Yardımı:** `500 Hurda` ve `20 XP`\n\n"
            f"💡 *Biyografini yazmak için `v.biyografi-yaz` komutunu kullanabilirsin.*"
        )
        await ctx.send(embed=embed)

    # ============================================================
    # v.profil
    # ============================================================
    @commands.command(name="profil")
    async def prefix_profil(self, ctx):
        u_id = self._uid(ctx)
        if u_id not in db["sakinler"]:
            await ctx.send("❌ Sığınak sicil kütüğünde kaydınız bulunmuyor! `v.kayit` olun.")
            return

        sakin = db["sakinler"][u_id]
        durum = sakin.get("durum", "Canlı")
        durum_emoji = {
            "Canlı": "🟢", "Sağlıklı": "🟢", "Enfekte": "🟡", "Karantinada": "🟠",
            "Hücrede": "🔴", "Ölü": "💀", "Sürgün": "🔵"
        }.get(durum, "⚪")

        embed = discord.Embed(
            title=f"👤 {sakin['isim'].upper()} {sakin['soyisim'].upper()} — SİCİL KARTI",
            color=0x3498DB
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)

        embed.add_field(name=f"{durum_emoji} Durum", value=f"`{durum}`", inline=True)
        embed.add_field(name="💼 Meslek", value=f"`{sakin.get('meslek_isim', 'Gezgin')}`", inline=True)
        embed.add_field(name="🏅 Seviye / XP", value=f"`Seviye {sakin.get('seviye', 1)}` / `{sakin.get('xp', 0)} XP`", inline=True)
        embed.add_field(name="💰 Cüzdan", value=f"`{sakin.get('cuzdan', 0)} Hurda`", inline=True)
        embed.add_field(name="⚔️ Atak", value=f"`{sakin.get('atak', 10)}`", inline=True)
        embed.add_field(name="🛡️ Defans", value=f"`{sakin.get('defans', 0)}`", inline=True)
        embed.add_field(name="🎂 Yaş", value=f"`{sakin.get('yas', '?')}`", inline=True)
        embed.add_field(name="📍 Memleket", value=f"`{sakin.get('memleket', 'Bilinmiyor')}`", inline=True)
        embed.add_field(name="🎯 İtibar", value=f"`{sakin.get('itibar', 50)}`", inline=True)

        embed.add_field(name="❤️ Sağlık", value=bar_olustur(sakin.get("saglik", 100)), inline=False)
        embed.add_field(name="💧 Su ve Besin", value=bar_olustur(sakin.get("su", 100)), inline=False)
        embed.add_field(name="🧠 Akıl Sağlığı", value=bar_olustur(sakin.get("akil_sagligi", 100)), inline=False)
        embed.add_field(name="☣️ Enfeksiyon Yükü", value=bar_olustur(sakin.get("enfeksiyon", 0)), inline=False)
        embed.add_field(name="😊 Moral", value=bar_olustur(sakin.get("moral", 50)), inline=False)

        biyografi = sakin.get("biyografi", "").strip()
        if biyografi:
            embed.add_field(name="📖 Biyografi", value=f"*{biyografi[:1000]}*" if len(biyografi) <= 1000 else f"*{biyografi[:1000]}...*", inline=False)
        else:
            embed.add_field(name="📖 Biyografi", value="*Karakterinin hikayesi henüz yazılmadı. `v.biyografi-yaz` komutuyla ekleyebilirsin.*", inline=False)

        await ctx.send(embed=embed)

    # ============================================================
    # v.envanter
    # ============================================================
    @commands.command(name="envanter")
    async def prefix_envanter(self, ctx):
        u_id = self._uid(ctx)
        if u_id not in db["sakinler"]:
            await ctx.send("❌ Önce sığınağa kayıt olmalısınız!")
            return

        sakin = db["sakinler"][u_id]
        envanter = sakin.get("envanter", {})

        embed = discord.Embed(title=f"🎒 {sakin['isim'].upper()} SIRT ÇANTASI", color=0xF39C12)
        icerik = ""
        for esya, adet in envanter.items():
            if adet > 0:
                icerik += f"• 📦 **{esya}**: `{adet} Adet`\n"
        embed.description = icerik if icerik else "*Sırt çantan bomboş, pazardan alışveriş yapmalısın!*"
        await ctx.send(embed=embed)

    # ============================================================
    # v.biyografi-yaz
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
            if fark.total_seconds() < 259200:
                kalan_saat = int((259200 - fark.total_seconds()) / 3600)
                await ctx.send(f"❌ Biyografini kısa süre önce değiştirdin! {kalan_saat} saat beklemelisin.")
                return

        db["sakinler"][u_id]["biyografi"] = metin.strip()
        db["sakinler"][u_id]["son_biyografi_degisimi"] = datetime.datetime.now().isoformat()
        verileri_kaydet()

        embed = discord.Embed(title="📖 BİYOGRAFİ GÜNCELLENDİ", color=0x9B59B6)
        embed.description = f"**Yeni Biyografi:**\n*{metin.strip()}*\n\n⏱️ *Bir sonraki değişiklik 3 gün sonra yapılabilir.*"
        await ctx.send(embed=embed)

    # ============================================================
    # v.destek
    # ============================================================
    @commands.command(name="destek")
    async def prefix_destek(self, ctx):
        embed = discord.Embed(title="📚 SIĞINAK RPG SİSTEMİ - KOMUT KILAVUZU", color=0x34495E)
        embed.description = (
            "Tüm komutların özeti. Hem slash (`/`) hem prefix (`v.`) çalışır.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        embed.add_field(name="📝 1. Kayıt & Profil", value="`/kayit` `/profil` `/envanter` `/biyografi-yaz` `/meslek-sec` `/meslek-yonetim`", inline=False)
        embed.add_field(name="🛒 2. Pazar & Ticaret", value="`/pazar` `/satinal` `/bota-sat` `/esya-sat` `/takas-teklif` `/acik-arttirma-baslat` `/pey-ver` `/tuket`", inline=False)
        embed.add_field(name="🏛️ 3. Siyaset & Yönetim", value="`/secimi-baslat` `/aday-ol` `/yonetim` `/tayin-et` `/maas-ode` `/meslek-maas-ode` `/toplu-maas`", inline=False)
        embed.add_field(name="⚖️ 4. Yargı & Ceza", value="`/yargila` `/hucreye-at` `/hucreden-cikar` `/sokak-yasagi` `/darbe`", inline=False)
        embed.add_field(name="⛪ 5. Engizisyon & Rahip", value="`/rahip-paneli` `/afaroz-et` `/buyuk-kilise-cani` `/kedileri-yok-et` `/kutsa`", inline=False)
        embed.add_field(name="💊 6. Sağlık & Simya", value="`/doktor-paneli` `/asi-uret` `/tedavi-et` `/deney` `/laboratuvar-gelistir`", inline=False)
        embed.add_field(name="🛡️ 7. Kolluk & Savunma", value="`/muhafiz-paneli` `/karantina-al` `/karantina-kaldir` `/savunmayi-guclendir` `/nobet`", inline=False)
        embed.add_field(name="🌾 8. Üretim & Ambar", value="`/ciftci-paneli` `/tarla-calis` `/maden-kaz` `/orman-kes` `/ambar` `/ambara-bagis` `/ambardan-al`", inline=False)
        embed.add_field(name="⚔️ 9. Savaş & Keşif", value="`/duello` `/sefer` `/zombi-baskini-baslat` `/gez` `/anit`", inline=False)
        embed.add_field(name="💰 10. Ekonomi & Çevre", value="`/maliye-yonetim` `/hava-durumu-degis` `/haber`", inline=False)
        embed.add_field(name="🔧 11. Yönetim", value="`/sunucu-yonetimi` `/owner-kayit` `/kayit-sil` `/db-sifirla` `/xp_kazan_test`", inline=False)
        embed.add_field(name="📖 12. Rehber", value="`/destek` `/rehber`", inline=False)
        embed.set_footer(text="Sığınak Veba RP v5.1 | Slash ve v. prefix desteği")
        await ctx.send(embed=embed)

    # ============================================================
    # v.rehber
    # ============================================================
    @commands.command(name="rehber")
    async def prefix_rehber(self, ctx):
        embed = discord.Embed(title="📖 SIĞINAK REHBERİ", color=0x9B59B6)
        embed.description = (
            "Detaylı rehber için `/rehber` slash komutunu kullan (dropdown menü ile).\n\n"
            "Hızlı yardım:\n"
            "• `v.destek` — Tüm komutların özeti\n"
            "• `v.kayit isim soyisim yaş memleket` — Kayıt ol\n"
            "• `v.profil` — Karakter kartın\n"
            "• `v.pazar <kategori>` — Pazar gez (Silah, Zırh, Medikal, Gıda, Hammadde, Teknoloji, Mistik)\n"
            "• `v.satinal <kod> <adet>` — Eşya al\n"
            "• `v.gez <bolge>` — Dış dünyaya keşfe çık\n\n"
            "**Bölge seçenekleri:** Terkedilmiş Köy, Veba Mezarlığı, Karanlık Koruluk, Yıkık Kilise, Dehliz Labirenti, Zombi Tarlası"
        )
        await ctx.send(embed=embed)

    # ============================================================
    # v.pazar
    # ============================================================
    @commands.command(name="pazar")
    async def prefix_pazar(self, ctx, *, kategori: str = None):
        if not kategori:
            await ctx.send("❌ Kullanım: `v.pazar <kategori>`\nKategoriler: Silah, Zırh, Medikal, Gıda, Hammadde, Teknoloji, Mistik")
            return

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
                value=f"💰 `{veri['fiyat']}` Hurda | Etki: `+{veri['bonus_degeri']} {veri['bonus_turu']}`\n*{veri['aciklama']}*",
                inline=False
            )

        if sayac == 0:
            embed.description = "❌ Bu kategoride şu an eşya yok."

        await ctx.send(embed=embed)

    # ============================================================
    # v.satinal
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
            await ctx.send(f"❌ Bakiyeniz yetersiz! Gereken: `{toplam_maliyet}` Hurda, Cüzdanınızda: `{sakin['cuzdan']}`.")
            return

        sakin["cuzdan"] -= toplam_maliyet
        sakin["envanter"][urun["isim"]] = sakin["envanter"].get(urun["isim"], 0) + adet

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

        msg = f"🛒 Alım tamamlandı.\n• Alınan: `{adet} Adet {urun['isim']}`\n• Toplam Ödenen: `💰 {toplam_maliyet} Hurda`"
        if indirim_uygula:
            msg += " *(Mesleki %20 İndirim Uygulandı!)*"
        msg += f"\n• Karaktere Yansıyan Bonus: `+{b_degeri} {b_turu}`"
        await ctx.send(msg)

    # ============================================================
    # v.bota-sat
    # ============================================================
    @commands.command(name="bota-sat")
    async def prefix_bota_sat(self, ctx, esya_ad: str = None, adet: int = 1):
        if not esya_ad:
            await ctx.send("❌ Kullanım: `v.bota-sat <esya_adı> <adet>`\nÖrnek: `v.bota-sat \"Paslı Demir Kama\" 1`")
            return

        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return

        u_id = self._uid(ctx)
        sakin = db["sakinler"][u_id]
        envanter = sakin.get("envanter", {})

        tam_isim, fiyat = katalogdan_isim_bul(esya_ad)
        if not tam_isim:
            await ctx.send("❌ Bu eşya pazar kayıtlarında tanınmıyor!")
            return

        esya_ad = tam_isim
        orijinal_fiyat = fiyat

        mevcut = envanter.get(esya_ad, 0)
        if mevcut < adet:
            await ctx.send(f"❌ Envanterinizde yeterli `{esya_ad}` yok! Mevcut: `{mevcut}`")
            return

        meslek = sakin.get("meslek_anahtar", "gezgin")
        vergi_orani = 0.20 if meslek in ["tuccar", "vergi_mufettisi"] else 0.25

        brut = orijinal_fiyat * adet
        vergi = int(brut * vergi_orani)
        net = brut - vergi

        envanter[esya_ad] -= adet
        sakin["cuzdan"] += net
        db["sistem_ayarlari"]["kasa_hurda"] += vergi

        if envanter[esya_ad] == 0:
            del envanter[esya_ad]

        verileri_kaydet()

        embed = discord.Embed(title="♻️ SIĞINAK İDARESİ GERİ DÖNÜŞÜM RAPORU", color=0xE67E22)
        embed.description = (
            f"**Satan:** {ctx.author.mention}\n"
            f"**Teslim Edilen:** `{adet} Adet {esya_ad}`\n\n"
            f"• Brüt Tutar: `{brut} Hurda`\n"
            f"• Vergi (%{int(vergi_orani*100)}): `-{vergi} Hurda`\n"
            f"• **Net Kazanç:** `💰 {net} Hurda`"
        )
        await ctx.send(embed=embed)

    # ============================================================
    # v.tuket / v.kullan
    # ============================================================
    @commands.command(name="tuket", aliases=["kullan", "ye", "ic"])
    async def prefix_tuket(self, ctx, *, esya_ad: str = None):
        if not esya_ad:
            await ctx.send("❌ Kullanım: `v.tuket <esya_adı>` veya `v.kullan <esya_adı>`\nÖrnek: `v.tuket Kuru Taş Ekmeği`")
            return

        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return

        u_id = self._uid(ctx)
        sakin = db["sakinler"][u_id]
        envanter = sakin.get("envanter", {})

        tam_isim, _ = katalogdan_isim_bul(esya_ad)
        if not tam_isim:
            await ctx.send("❌ Bu eşya katalogda tanınmıyor!")
            return

        esya_ad = tam_isim
        if envanter.get(esya_ad, 0) < 1:
            await ctx.send(f"❌ Envanterinizde `{esya_ad}` yok!")
            return

        urun = None
        for kod, veri in TAM_PAZAR.items():
            if veri["isim"] == esya_ad:
                urun = veri
                break

        if urun["tip"] not in ["Gıda", "Medikal"]:
            await ctx.send(f"❌ `{esya_ad}` tüketilebilir bir gıda/medikal değil!")
            return

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

        embed = discord.Embed(title="🍽️ TÜKETİLDİ", color=0xF39C12)
        embed.description = f"📦 **Tüketilen:** `1 Adet {esya_ad}`\n\n**Etkiler:**\n" + "\n".join([f"• {e}" for e in etkiler])
        await ctx.send(embed=embed)

    # ============================================================
    # v.meslek-sec
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

        mevcut = db["sakinler"][u_id].get("meslek_anahtar", "gezgin")
        if secim_temiz == mevcut:
            await ctx.send("❌ Zaten bu mesleği icra ediyorsun!")
            return

        son = db["sakinler"][u_id].get("son_meslek_degisimi")
        if son:
            fark = datetime.datetime.now() - datetime.datetime.fromisoformat(son)
            if fark.total_seconds() < 259200:
                kalan = int((259200 - fark.total_seconds()) / 3600)
                await ctx.send(f"❌ Meslek değiştirmek için {kalan} saat beklemelisin!")
                return

        db["sakinler"][u_id]["meslek_anahtar"] = secim_temiz
        db["sakinler"][u_id]["meslek_isim"] = meslek_veri["isim"]
        db["sakinler"][u_id]["son_meslek_degisimi"] = datetime.datetime.now().isoformat()
        verileri_kaydet()

        await ctx.send(f"💼 **MESLEK DEĞİŞİKLİĞİ:** Yeni mesleğin resmen **{meslek_veri['isim']}** olarak tescillendi.")

    # ============================================================
    # v.meslek-yonetim
    # ============================================================
    @commands.command(name="meslek-yonetim", aliases=["meslek-yönetim"])
    async def prefix_meslek_yonetim(self, ctx):
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return

        u_id = self._uid(ctx)
        sakin = db["sakinler"][u_id]
        meslek = sakin.get("meslek_anahtar", "gezgin")
        m_isim = sakin.get("meslek_isim", "Gezgin")

        embed = discord.Embed(title=f"🛠️ {m_isim.upper()} FAALİYET VE YÖNETİM PANELİ", color=0x9B59B6)
        embed.description = f"📊 Mesleğin: `{m_isim}`\n💼 Meslek Anahtarı: `{meslek}`\n\nDetaylı panel için `/meslek-yonetim` slash komutunu kullanın."
        await ctx.send(embed=embed)

    # ============================================================
    # v.gez
    # ============================================================
    @commands.command(name="gez")
    async def prefix_gez(self, ctx, *, bolge: str = None):
        if not bolge:
            await ctx.send(
                "❌ Kullanım: `v.gez <bolge>`\n"
                "Bölgeler: Terkedilmiş Köy, Veba Mezarlığı, Karanlık Koruluk, Yıkık Kilise, Dehliz Labirenti, Zombi Tarlası"
            )
            return

        # Bölge eşleştirme
        gecerli_bolgeler = ["Terkedilmiş Köy", "Veba Mezarlığı", "Karanlık Koruluk", "Yıkık Kilise", "Dehliz Labirenti", "Zombi Tarlası"]
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
                await ctx.send(f"❌ Yorgunsun! `{kalan_saat} saat {kalan_dk} dk` beklemelisin.")
                return

        await ctx.send(f"🥾 {ctx.author.mention}, çantanı hazırladın ve `{bolge}` bölgesine doğru yola çıktın... Kader zarın atılıyor!")

        await asyncio.sleep(3)

        # Olay havuzunu import et
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

        olay_ekisini_uygula(sakin, etki)
        sakin["son_gezi"] = datetime.datetime.now().isoformat()
        verileri_kaydet()

        embed = discord.Embed(title=f"🗺️ SEFARET RAPORU: {bolge}", color=embed_renk)
        embed.description = f"👣 {ctx.author.mention}, seyahatin sırasında:\n\n**{secilen_olay}**"
        embed.set_footer(text=f"Kategori: {kategori} | Zar: {zar}/10 | Cooldown: 6 saat")
        await ctx.send(embed=embed)

        haber_ekle(f"🥾 {sakin.get('isim', ctx.author.name)} {bolge} bölgesine gezi düzenledi. ({kategori})")

    # ============================================================
    # v.anit
    # ============================================================
    @commands.command(name="anit", aliases=["anıt"])
    async def prefix_anit(self, ctx):
        sirali = sorted(db["sakinler"].items(), key=lambda x: x[1].get("xp", 0), reverse=True)[:3]
        seref = ""
        madalyalar = ["🥇", "🥈", "🥉"]
        for i, (s_id, veri) in enumerate(sirali):
            seref += f"{madalyalar[i]} **{veri.get('isim', 'Bilinmeyen')}** - `{veri.get('xp', 0)} XP`\n"

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
            "1. Belediye başkanının sözü emirdir.\n"
            "2. Mahkeme kararlarına karşı gelmek darbe sebebidir.\n"
            "3. Kilise kurallarına uymayanlar afaroz edilir.\n"
            "4. Ölü karakter tüm eşyalarını kaybeder, yeniden `v.kayit` olur.\n"
            "5. 6 saatten az sürede tekrar gezi yapılamaz.\n\n"
            "✨ **KAHRAMANLAR ŞEREF KÜRSÜSÜ:**\n" + (seref or "*Henüz kahraman yok.*\n") + "\n"
            "💀 **ŞEHİTLER DUVARI:**\n" + sehit + "\n"
            "📅 **Kuruluş Tarihi:** `03.01.2026`"
        )
        await ctx.send(embed=embed)

    # ============================================================
    # v.ambar
    # ============================================================
    @commands.command(name="ambar")
    async def prefix_ambar(self, ctx):
        stoklar = db["koy_ambari"]["stoklar"]
        embed = discord.Embed(title="🏡 SIĞINAK KOLEKTİF KÖY AMBARI STOK RAPORU", color=0x34495E)
        text = "📋 **Mevcut Ortak Stok:**\n\n"
        for anahtar, etiket in ESYA_ETIKET.items():
            miktar = stoklar.get(anahtar, 0)
            text += f"{etiket}: `{miktar} Adet`\n"
        embed.description = text
        embed.set_footer(text=f"Toplam Bağış: {db['koy_ambari'].get('toplam_bagis_sayisi', 0)}")
        await ctx.send(embed=embed)

    # ============================================================
    # v.ciftci-paneli
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
            await ctx.send("❌ Tescilli bir üretici değilsiniz!")
            return

        hava = db["cevre_durumu"].get("hava_durumu", "İlkbahar")
        embed = discord.Embed(title="🌾 SIĞINAK ÜRETİM MERKEZİ", color=0xF1C40F)
        embed.description = (
            f"🌤️ **Hava:** `{hava}`\n\n"
            "📋 **Komutlar:**\n"
            "• `v.tarla-calis` — Tarlada çalış (Çiftçi/Çoban/Değirmenci/Hancı)\n"
            "• `v.maden-kaz` — Madende kaz (Madenci/Demirci)\n"
            "• `v.orman-kes` — Ormanda odun kes (Oduncu/Hancı)\n"
            "• `v.tuket <esya>` — Gıda tüket\n\n"
            "⏱️ Her çalışma 30 dk cooldown'a sahiptir."
        )
        await ctx.send(embed=embed)

    # ============================================================
    # v.tarla-calis
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
                kalan = int((1800 - fark.total_seconds()) / 60)
                await ctx.send(f"❌ Dinlenmeniz gerekiyor! `{kalan} dakika` bekleyin.")
                return

        hava = db["cevre_durumu"]["hava_durumu"]
        taban = random.randint(10, 20)
        carpan = 1.0
        if hava == "İlkbahar": carpan = 1.5
        elif hava == "Yaz": carpan = 2.0
        elif hava == "Yağmurlu": carpan = 0.7
        elif hava == "Kış": carpan = 0.3

        nihai = int(taban * carpan)
        hurda = nihai * 3
        atlamalar = xp_ekle(u_id, 15)
        sakin["cuzdan"] = sakin.get("cuzdan", 0) + hurda
        db["koy_ambari"]["stoklar"]["erzak"] = db["koy_ambari"]["stoklar"].get("erzak", 0) + nihai
        sakin["son_calisma"] = datetime.datetime.now().isoformat()
        verileri_kaydet()

        embed = discord.Embed(title="🌾 HASAT TAMAMLANDI!", color=0x2ECC71)
        embed.description = (
            f"🌤️ **Hava:** `{hava}` (x{carpan})\n"
            f"📦 **Ambara Eklenen Erzak:** `+{nihai} Adet`\n"
            f"💰 **Kazanç:** `+{hurda} Hurda` | `+15 XP`"
        )
        if atlamalar:
            embed.add_field(name="🎉 Seviye Atlamaları", value="\n".join([f"• Seviye {a['seviye']}! +{a['odul']} Hurda" for a in atlamalar]), inline=False)
        await ctx.send(embed=embed)

    # ============================================================
    # v.maden-kaz
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
                kalan = int((1800 - fark.total_seconds()) / 60)
                await ctx.send(f"❌ Dinlenmeniz gerekiyor! `{kalan} dakika` bekleyin.")
                return

        hava = db["cevre_durumu"]["hava_durumu"]
        taban = random.randint(8, 15)
        carpan = 1.0
        if hava == "Kış": carpan = 0.6
        elif hava == "Yağmurlu": carpan = 0.8

        nihai = int(taban * carpan)
        hurda = nihai * 4
        atlamalar = xp_ekle(u_id, 20)
        sakin["cuzdan"] = sakin.get("cuzdan", 0) + hurda
        db["koy_ambari"]["stoklar"]["komur"] = db["koy_ambari"]["stoklar"].get("komur", 0) + nihai
        sakin["son_calisma"] = datetime.datetime.now().isoformat()
        verileri_kaydet()

        embed = discord.Embed(title="⛏️ MADEN KAZISI BAŞARILI!", color=0x95A5A6)
        embed.description = f"🪨 **Ambara Eklenen Kömür:** `+{nihai} Adet`\n💰 **Kazanç:** `+{hurda} Hurda` | `+20 XP`"
        if atlamalar:
            embed.add_field(name="🎉 Seviye Atlamaları", value="\n".join([f"• Seviye {a['seviye']}! +{a['odul']} Hurda" for a in atlamalar]), inline=False)
        await ctx.send(embed=embed)

    # ============================================================
    # v.orman-kes
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
                kalan = int((1800 - fark.total_seconds()) / 60)
                await ctx.send(f"❌ Dinlenmeniz gerekiyor! `{kalan} dakika` bekleyin.")
                return

        hava = db["cevre_durumu"]["hava_durumu"]
        taban = random.randint(12, 22)
        carpan = 1.0
        if hava == "Kış": carpan = 0.2
        elif hava == "Yağmurlu": carpan = 0.5
        elif hava == "Yaz": carpan = 1.3

        nihai = int(taban * carpan)
        hurda = nihai * 2
        atlamalar = xp_ekle(u_id, 15)
        sakin["cuzdan"] = sakin.get("cuzdan", 0) + hurda
        db["koy_ambari"]["stoklar"]["odun"] = db["koy_ambari"]["stoklar"].get("odun", 0) + nihai
        sakin["son_calisma"] = datetime.datetime.now().isoformat()
        verileri_kaydet()

        embed = discord.Embed(title="🪵 ODUN KESİMİ TAMAMLANDI!", color=0x27AE60)
        embed.description = f"🪓 **Ambara Eklenen Odun:** `+{nihai} Adet`\n💰 **Kazanç:** `+{hurda} Hurda` | `+15 XP`"
        if atlamalar:
            embed.add_field(name="🎉 Seviye Atlamaları", value="\n".join([f"• Seviye {a['seviye']}! +{a['odul']} Hurda" for a in atlamalar]), inline=False)
        await ctx.send(embed=embed)

    # ============================================================
    # v.db-sifirla — SADECE ADMIN (Veritabanı tam sıfırlama)
    # ============================================================
    @commands.command(name="db-sifirla")
    @commands.has_permissions(administrator=True)
    async def prefix_db_sifirla(self, ctx, onay: str = None):
        """Veritabanını tamamen sıfırlar. Sadece admin. Örnek: v.db-sifirla EVET"""
        if onay != "EVET":
            await ctx.send("⚠️ **DİKKAT!** Bu işlem tüm kayıtları siler (sakinler, meslekler, kasa, vb.)!\nOnaylamak için: `v.db-sifirla EVET`")
            return

        eski_sayi = len(db.get("sakinler", {}))

        # Veritabanını sıfırla
        db.clear()
        db["sakinler"] = {}
        db["sistem_ayarlari"] = {
            "kasa_hurda": 50000,
            "toplam_kayitli_sakin": 0,
            "sur_seviyesi": 1,
            "koy_seviyesi": 1
        }

        # Tüm tabloları default ile yeniden oluştur
        from veritabani import db_ilkle
        db_ilkle()
        verileri_kaydet()

        embed = discord.Embed(title="🗑️ VERİTABANI SIFIRLANDI", color=0xE74C3C)
        embed.description = (
            f"✅ Tüm veritabanı sıfırlandı!\n\n"
            f"📊 **Silinen Sakin Sayısı:** `{eski_sayi}`\n"
            f"💰 **Kasa:** `50000 Hurda` (default)\n"
            f"🧱 **Sur Seviyesi:** `1`\n"
            f"🏡 **Köy Seviyesi:** `1`\n\n"
            f"⚠️ *Tüm oyuncular yeniden `v.kayit` olmak zorundadır.*\n"
            f"💡 *Yedekleme kanalındaki eski yedekleri de silmeniz önerilir (yoksa bot açılışta geri yükleyebilir).*"
        )
        await ctx.send(embed=embed)

    @prefix_db_sifirla.error
    async def db_sifirla_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Bu komut sadece sunucu yöneticileri tarafından kullanılabilir!")
        else:
            await ctx.send(f"❌ Hata: {error}")

    # ============================================================
    # v.ambara-bagis
    # ============================================================
    @commands.command(name="ambara-bagis", aliases=["ambara-bağış"])
    async def prefix_ambara_bagis(self, ctx, esya_ad: str = None, adet: int = 1):
        if not esya_ad:
            await ctx.send("❌ Kullanım: `v.ambara-bagis <esya> <adet>`\nÖrnek: `v.ambara-bagis erzak 5`")
            return
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return
        u_id = self._uid(ctx)
        sakin = db["sakinler"][u_id]
        if adet <= 0:
            await ctx.send("❌ Bağış miktarı pozitif olmalı!")
            return
        temiz_ad = ESYA_HARITASI.get(esya_ad.lower().strip())
        if not temiz_ad:
            await ctx.send("❌ Geçersiz eşya! Bağışlanabilir: `erzak`, `ilaç`, `odun`, `kömür`")
            return
        if "envanter" not in sakin:
            sakin["envanter"] = {}
        mevcut = sakin["envanter"].get(temiz_ad, 0)
        if mevcut < adet:
            await ctx.send(f"❌ Envanterinizde yeterli yok! Mevcut: `{mevcut}`")
            return
        sakin["envanter"][temiz_ad] -= adet
        if sakin["envanter"][temiz_ad] == 0:
            del sakin["envanter"][temiz_ad]
        db["koy_ambari"]["stoklar"][temiz_ad] = db["koy_ambari"]["stoklar"].get(temiz_ad, 0) + adet
        db["koy_ambari"]["toplam_bagis_sayisi"] += 1
        itibar_bonusu = adet * 2
        sakin["cuzdan"] = sakin.get("cuzdan", 0) + itibar_bonusu
        sakin["itibar"] = min(100, sakin.get("itibar", 50) + adet)
        verileri_kaydet()
        embed = discord.Embed(title="🤝 AMBARA BAĞIŞ", color=0x2ECC71)
        embed.description = f"📦 **Bağışlanan:** `{adet} Adet {ESYA_ETIKET[temiz_ad]}`\n📈 **Ödül:** `+{itibar_bonusu} Hurda` ve `+{adet} İtibar`"
        await ctx.send(embed=embed)

    # ============================================================
    # v.ambardan-al
    # ============================================================
    @commands.command(name="ambardan-al")
    async def prefix_ambardan_al(self, ctx, esya_ad: str = None, adet: int = 1):
        if not esya_ad:
            await ctx.send("❌ Kullanım: `v.ambardan-al <esya> <adet>`\nÖrnek: `v.ambardan-al erzak 5`")
            return
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return
        u_id = self._uid(ctx)
        sakin = db["sakinler"][u_id]
        if sakin.get("durum") == "Sürgün":
            await ctx.send("❌ Sürgün edildiğiniz için ambara yaklaşamazsınız!")
            return
        if adet <= 0 or adet > 5:
            await ctx.send("❌ Tek seferde max 5 adet çekebilirsiniz!")
            return
        temiz_ad = ESYA_HARITASI.get(esya_ad.lower().strip())
        if not temiz_ad:
            await ctx.send("❌ Geçersiz eşya! İstenebilir: `erzak`, `ilaç`, `odun`, `kömür`")
            return
        cuzdan = sakin.get("cuzdan", 0)
        durum = sakin.get("durum", "Canlı")
        if cuzdan > 400 and durum in ["Sağlıklı", "Canlı"]:
            await ctx.send("❌ Durumunuz iyi! Ambar sadece ihtiyaç sahipleri içindir.")
            return
        stoklar = db["koy_ambari"]["stoklar"]
        if stoklar.get(temiz_ad, 0) < adet:
            await ctx.send(f"❌ Ambarda yeterli stok yok! Mevcut: `{stoklar.get(temiz_ad, 0)}`")
            return
        stoklar[temiz_ad] -= adet
        if "envanter" not in sakin:
            sakin["envanter"] = {}
        sakin["envanter"][temiz_ad] = sakin["envanter"].get(temiz_ad, 0) + adet
        verileri_kaydet()
        embed = discord.Embed(title="📦 AMBARDAN MALZEME", color=0x3498DB)
        embed.description = f"📦 **Tedarik Edilen:** `{adet} Adet {ESYA_ETIKET[temiz_ad]}`"
        await ctx.send(embed=embed)

    # ============================================================
    # v.duello
    # ============================================================
    @commands.command(name="duello")
    async def prefix_duello(self, ctx, kullanici: discord.Member = None):
        if not kullanici:
            await ctx.send("❌ Kullanım: `v.duello @kullanıcı`")
            return
        if kullanici.id == ctx.author.id:
            await ctx.send("❌ Kendi kendine meydan okuyamazsın!")
            return
        u_id = self._uid(ctx)
        r_id = str(kullanici.id)
        if u_id not in db["sakinler"] or r_id not in db["sakinler"]:
            await ctx.send("❌ Taraflardan birinin kaydı yok!")
            return
        if db["sakinler"][u_id].get("durum") == "Ölü" or db["sakinler"][r_id].get("durum") == "Ölü":
            await ctx.send("❌ Ölü karakterler düello yapamaz!")
            return
        await ctx.send(f"⚔️ {ctx.author.mention}, {kullanici.mention} kullanıcısına meydan okudu!\n\n⚠️ Düello slash komutu daha iyi çalışır: `/duello @kullanıcı` (butonlu tur tabanlı)\n\n💡 Bu prefix versiyonu sadece duyuru yapar. Tam düello için `/duello` kullanın.")

    # ============================================================
    # v.sefer
    # ============================================================
    @commands.command(name="sefer")
    async def prefix_sefer(self, ctx):
        u_id = self._uid(ctx)
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return
        if db["sakinler"][u_id].get("meslek_anahtar") != "belediye_baskani":
            await ctx.send("❌ Sefere çıkma emrini yalnızca Belediye Başkanı verebilir!")
            return
        await ctx.send("⚔️ **DIŞ DÜNYA SEFERİ!** Belediye Başkanı sefer düzenliyor!\n\n💡 Sefer lobisi slash komutu ile açılır: `/sefer` (butonlu katılım sistemi)")

    # ============================================================
    # v.zombi-baskini-baslat
    # ============================================================
    @commands.command(name="zombi-baskini-baslat", aliases=["zombi-baskını-başlat"])
    async def prefix_zombi_baskini(self, ctx):
        if not any(rol.id == RP_OWNER_ROL_ID for rol in ctx.author.roles):
            await ctx.send("❌ Bu komut sadece RP Owner tarafından kullanılabilir!")
            return
        await ctx.send("🚨 **ZOMBİ BASKINI!** RP Owner baskın başlattı!\n\n💡 Tam baskın sistemi slash komutu ile çalışır: `/zombi-baskini-baslat` (butonlu savunma, 2 dk süre)")

    # ============================================================
    # v.takas-teklif
    # ============================================================
    @commands.command(name="takas-teklif")
    async def prefix_takas(self, ctx, kullanici: discord.Member = None, *, esyalar: str = None):
        if not kullanici or not esyalar:
            await ctx.send("❌ Kullanım: `v.takas-teklif @kullanıcı \"verilecek|istenen\"`\nÖrnek: `v.takas-teklif @ali \"Paslı Demir Kama|Kuru Taş Ekmeği\"`")
            return
        await ctx.send(f"🤝 {ctx.author.mention}, {kullanici.mention} ile takas teklif etmek istiyor!\n\n💡 Tam takas sistemi slash komutu ile çalışır: `/takas-teklif` (butonlu onay sistemi)")

    # ============================================================
    # v.esya-sat
    # ============================================================
    @commands.command(name="esya-sat")
    async def prefix_esya_sat(self, ctx, kullanici: discord.Member = None, *, esya_fiyat: str = None):
        if not kullanici or not esya_fiyat:
            await ctx.send("❌ Kullanım: `v.esya-sat @kullanıcı \"esya|fiyat\"`\nÖrnek: `v.esya-sat @ali \"Paslı Demir Kama|150\"`")
            return
        await ctx.send(f"💰 {ctx.author.mention}, {kullanici.mention} kullanıcısına satış teklif ediyor!\n\n💡 Tam satış sistemi slash komutu ile çalışır: `/esya-sat` (butonlu onay)")

    # ============================================================
    # v.acik-arttirma-baslat
    # ============================================================
    @commands.command(name="acik-arttirma-baslat")
    async def prefix_acik_arttirma(self, ctx, esya_ad: str = None, baslangic_fiyati: int = None):
        if not esya_ad or baslangic_fiyati is None:
            await ctx.send("❌ Kullanım: `v.acik-arttirma-baslat <esya> <açılış_fiyatı>`\nÖrnek: `v.acik-arttirma-baslat \"Paslı Demir Kama\" 100`")
            return
        await ctx.send(f"📢 **AÇIK ARTTIRMA!** {ctx.author.mention} açık arttırma başlatıyor!\n\n💡 Tam açık arttırma sistemi slash komutu ile çalışır: `/acik-arttirma-baslat` (2 dk süre, `/pey-ver` ile teklif)")

    # ============================================================
    # v.pey-ver
    # ============================================================
    @commands.command(name="pey-ver")
    async def prefix_pey_ver(self, ctx, ilan_id: str = None, teklif: int = None):
        if not ilan_id or teklif is None:
            await ctx.send("❌ Kullanım: `v.pey-ver <ilan_id> <teklif>`\nÖrnek: `v.pey-ver 1234 150`")
            return
        await ctx.send("💡 Açık arttırmaya teklif vermek için slash komutunu kullanın: `/pey-ver ilan_id: 1234 teklif_edilen_hurda: 150`")

    # ============================================================
    # v.aday-ol
    # ============================================================
    @commands.command(name="aday-ol")
    async def prefix_aday_ol(self, ctx, *, vaat: str = None):
        if not vaat:
            await ctx.send("❌ Kullanım: `v.aday-ol <vaat>`\nÖrnek: `v.aday-ol Herkese ücretsiz ekmek!`")
            return
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return
        u_id = self._uid(ctx)
        sakin = db["sakinler"][u_id]
        if sakin.get("cuzdan", 0) < 500:
            await ctx.send("❌ Adaylık için en az `500 Hurda` gerekir!")
            return
        if db["aktif_secim"]["durum"] != "adaylik_acik":
            await ctx.send("❌ Şu anda adaylık süreci açık değil!")
            return
        if u_id in db["aktif_secim"]["adaylar"]:
            await ctx.send("❌ Zaten adaysın!")
            return
        sakin["cuzdan"] -= 500
        db["aktif_secim"]["adaylar"][u_id] = {"isim": sakin["isim"], "vaat": vaat, "oy_sayisi": 0}
        verileri_kaydet()
        embed = discord.Embed(title="👑 YENİ BAŞKAN ADAYI!", color=0xF1C40F)
        embed.description = f"👤 **Aday:** {ctx.author.mention}\n📜 **Vaadi:** *{vaat}*"
        await ctx.send(embed=embed)

    # ============================================================
    # v.secimi-baslat
    # ============================================================
    @commands.command(name="secimi-baslat")
    @commands.has_permissions(administrator=True)
    async def prefix_secimi_baslat(self, ctx):
        await ctx.send("🗳️ **SEÇİM SÜRECİ!** Admin seçim başlatıyor!\n\n💡 Tam seçim sistemi (15 dk adaylık + 45 dk oylama) slash komutu ile çalışır: `/secimi-baslat`")

    # ============================================================
    # v.yonetim
    # ============================================================
    @commands.command(name="yonetim")
    async def prefix_yonetim(self, ctx):
        u_id = self._uid(ctx)
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return
        if db["sakinler"][u_id].get("meslek_anahtar") != "belediye_baskani":
            await ctx.send("❌ Bu panel sadece Belediye Başkanına ait!")
            return
        embed = discord.Embed(title="👑 SIĞINAK YÖNETİM MERKEZİ", color=0xF1C40F)
        embed.description = (
            f"💰 **Kasa:** `{db['sistem_ayarlari']['kasa_hurda']} Hurda`\n"
            f"🧱 **Sur Seviyesi:** `{db['sistem_ayarlari']['sur_seviyesi']}`\n"
            f"🏡 **Köy Seviyesi:** `{db['sistem_ayarlari']['koy_seviyesi']}`\n\n"
            "💡 Tam yönetim paneli (butonlu) slash komutu ile: `/yonetim`"
        )
        await ctx.send(embed=embed)

    # ============================================================
    # v.tayin-et
    # ============================================================
    @commands.command(name="tayin-et")
    async def prefix_tayin_et(self, ctx, kullanici: discord.Member = None, *, unvan: str = None):
        if not kullanici or not unvan:
            await ctx.send("❌ Kullanım: `v.tayin-et @kullanıcı <unvan>`\nUnvanlar: baskan_yardimcisi, vergi_mufettisi, muhafiz_komutani, bas_simyaci, rahip")
            return
        await ctx.send(f"📜 {ctx.author.mention}, {kullanici.mention} kullanıcısını `{unvan}` olarak atamak istiyor!\n\n💡 Tam atama sistemi slash komutu ile: `/tayin-et`")

    # ============================================================
    # v.maas-ode
    # ============================================================
    @commands.command(name="maas-ode")
    async def prefix_maas_ode(self, ctx, kullanici: discord.Member = None, miktar: int = None):
        if not kullanici or miktar is None:
            await ctx.send("❌ Kullanım: `v.maas-ode @kullanıcı <miktar>`\nÖrnek: `v.maas-ode @ali 100`")
            return
        u_id = self._uid(ctx)
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return
        if db["sakinler"][u_id].get("meslek_anahtar") != "belediye_baskani":
            await ctx.send("❌ Bu komut sadece Belediye Başkanına ait!")
            return
        if miktar <= 0:
            await ctx.send("❌ Miktar pozitif olmalı!")
            return
        h_id = str(kullanici.id)
        if h_id not in db["sakinler"]:
            await ctx.send("❌ Hedef sakin kayıtlı değil!")
            return
        if db["sistem_ayarlari"]["kasa_hurda"] < miktar:
            await ctx.send(f"❌ Kasada yeterli hurda yok! Mevcut: `{db['sistem_ayarlari']['kasa_hurda']}`")
            return
        db["sistem_ayarlari"]["kasa_hurda"] -= miktar
        db["sakinler"][h_id]["cuzdan"] += miktar
        verileri_kaydet()
        embed = discord.Embed(title="💸 MAAŞ ÖDENDİ", color=0x2ECC71)
        embed.description = f"👤 **Ödeme Yapılan:** {kullanici.mention}\n🪙 **Tutar:** `{miktar} Hurda`\n📉 **Kalan Kasa:** `{db['sistem_ayarlari']['kasa_hurda']}`"
        await ctx.send(embed=embed)

    # ============================================================
    # v.meslek-maas-ode
    # ============================================================
    @commands.command(name="meslek-maas-ode", aliases=["meslek-maaş-öde"])
    async def prefix_meslek_maas(self, ctx, grup: str = None, miktar: int = None):
        if not grup or miktar is None:
            await ctx.send("❌ Kullanım: `v.meslek-maas-ode <grup> <miktar>`\nGruplar: muhafiz, saglik, ureticiler, idari")
            return
        await ctx.send(f"📊 {ctx.author.mention} `{grup}` grubuna `{miktar}` hurda maaş ödemek istiyor!\n\n💡 Tam toplu maaş sistemi slash komutu ile: `/meslek-maas-ode`")

    # ============================================================
    # v.toplu-maas
    # ============================================================
    @commands.command(name="toplu-maas", aliases=["toplu-maaş"])
    async def prefix_toplu_maas(self, ctx, miktar: int = None):
        if miktar is None:
            await ctx.send("❌ Kullanım: `v.toplu-maas <miktar>`\nÖrnek: `v.toplu-maas 50`")
            return
        u_id = self._uid(ctx)
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return
        if db["sakinler"][u_id].get("meslek_anahtar") != "belediye_baskani":
            await ctx.send("❌ Bu komut sadece Belediye Başkanına ait!")
            return
        if miktar <= 0:
            await ctx.send("❌ Miktar pozitif olmalı!")
            return
        hayatta = [s_id for s_id, v in db["sakinler"].items() if v.get("durum") != "Ölü"]
        if not hayatta:
            await ctx.send("❌ Hayatta kimse yok!")
            return
        toplam = miktar * len(hayatta)
        if db["sistem_ayarlari"]["kasa_hurda"] < toplam:
            await ctx.send(f"❌ Kasada yeterli yok! Gereken: `{toplam}`, Mevcut: `{db['sistem_ayarlari']['kasa_hurda']}`")
            return
        db["sistem_ayarlari"]["kasa_hurda"] -= toplam
        for s_id in hayatta:
            db["sakinler"][s_id]["cuzdan"] += miktar
        verileri_kaydet()
        embed = discord.Embed(title="🏛️ TOPLU MAAŞ", color=0x9B59B6)
        embed.description = f"👥 **Nüfus:** `{len(hayatta)} sakin`\n🪙 **Kişi Başı:** `{miktar} Hurda`\n🔥 **Toplam:** `{toplam} Hurda`"
        await ctx.send(embed=embed)

    # ============================================================
    # v.yargila
    # ============================================================
    @commands.command(name="yargila", aliases=["yargıla"])
    async def prefix_yargila(self, ctx, kullanici: discord.Member = None, *, suc: str = None):
        if not kullanici or not suc:
            await ctx.send("❌ Kullanım: `v.yargila @sanık <suç_nedeni>`\nÖrnek: `v.yargila @ali Hırsızlık yaptı`")
            return
        await ctx.send(f"⚖️ {ctx.author.mention}, {kullanici.mention} kullanıcısını yargılıyor!\nSuç: *{suc}*\n\n💡 Tam mahkeme sistemi slash komutu ile: `/yargila` (halk oylaması, idam, sürgün)")

    # ============================================================
    # v.hucreye-at
    # ============================================================
    @commands.command(name="hucreye-at")
    async def prefix_hucreye_at(self, ctx, kullanici: discord.Member = None):
        if not kullanici:
            await ctx.send("❌ Kullanım: `v.hucreye-at @kullanıcı`")
            return
        u_id = self._uid(ctx)
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return
        meslek = db["sakinler"][u_id].get("meslek_anahtar", "")
        if meslek not in MESLEK_GRUPLARI["kolluk"]:
            await ctx.send("❌ Tutuklama yetkiniz yok!")
            return
        h_id = str(kullanici.id)
        if h_id not in db["sakinler"]:
            await ctx.send("❌ Bu kişi sığınakta yaşamıyor!")
            return
        if db["sakinler"][h_id].get("durum") in ["Ölü", "Hücrede"]:
            await ctx.send("❌ Bu sakin zaten ölü veya hücrede!")
            return
        if db["sakinler"][h_id].get("meslek_anahtar") == "belediye_baskani":
            await ctx.send("❌ Belediye Başkanını hücreye atamazsın!")
            return
        db["sakinler"][h_id]["durum"] = "Hücrede"
        verileri_kaydet()
        await ctx.send(f"🔒 {kullanici.mention} zindana atıldı!")

    # ============================================================
    # v.hucreden-cikar
    # ============================================================
    @commands.command(name="hucreden-cikar", aliases=["hucreden-çıkar"])
    async def prefix_hucreden_cikar(self, ctx, kullanici: discord.Member = None):
        if not kullanici:
            await ctx.send("❌ Kullanım: `v.hucreden-cikar @kullanıcı`")
            return
        u_id = self._uid(ctx)
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return
        meslek = db["sakinler"][u_id].get("meslek_anahtar", "")
        if meslek not in MESLEK_GRUPLARI["kolluk"]:
            await ctx.send("❌ Tahliye yetkiniz yok!")
            return
        h_id = str(kullanici.id)
        if db["sakinler"].get(h_id, {}).get("durum") != "Hücrede":
            await ctx.send("❌ Bu sakin zaten hücrede değil!")
            return
        db["sakinler"][h_id]["durum"] = "Canlı"
        verileri_kaydet()
        await ctx.send(f"🔓 {kullanici.mention} hücreden çıkarıldı!")

    # ============================================================
    # v.karantina-al
    # ============================================================
    @commands.command(name="karantina-al")
    async def prefix_karantina_al(self, ctx, kullanici: discord.Member = None):
        if not kullanici:
            await ctx.send("❌ Kullanım: `v.karantina-al @kullanıcı`")
            return
        u_id = self._uid(ctx)
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return
        meslek = db["sakinler"][u_id].get("meslek_anahtar", "")
        KARANTINACI_ROL_ID = 1508540605259714700
        has_karantinaci = any(rol.id == KARANTINACI_ROL_ID for rol in ctx.author.roles)
        if meslek not in ["belediye_baskani", "baskan_yardimcisi", "muhafiz_komutani", "muhafiz"] and not has_karantinaci:
            await ctx.send("❌ Karantina yetkiniz yok!")
            return
        h_id = str(kullanici.id)
        if db["sakinler"].get(h_id, {}).get("durum") != "Enfekte":
            await ctx.send("❌ Bu sakin zaten sağlıklı!")
            return
        db["sakinler"][h_id]["durum"] = "Karantinada"
        if h_id not in db["idari_kisitlamalar"]["karantina_cadiri"]:
            db["idari_kisitlamalar"]["karantina_cadiri"].append(h_id)
        verileri_kaydet()
        await ctx.send(f"☣️ {kullanici.mention} karantinaya alındı!")

    # ============================================================
    # v.karantina-kaldir
    # ============================================================
    @commands.command(name="karantina-kaldir", aliases=["karantina-kaldır"])
    async def prefix_karantina_kaldir(self, ctx, kullanici: discord.Member = None):
        if not kullanici:
            await ctx.send("❌ Kullanım: `v.karantina-kaldir @kullanıcı`")
            return
        u_id = self._uid(ctx)
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return
        meslek = db["sakinler"][u_id].get("meslek_anahtar", "")
        KARANTINACI_ROL_ID = 1508540605259714700
        has_karantinaci = any(rol.id == KARANTINACI_ROL_ID for rol in ctx.author.roles)
        if meslek not in ["belediye_baskani", "muhafiz_komutani", "bas_simyaci", "simyaci"] and not has_karantinaci:
            await ctx.send("❌ Karantina kaldırma yetkiniz yok!")
            return
        h_id = str(kullanici.id)
        if db["sakinler"].get(h_id, {}).get("durum") != "Karantinada":
            await ctx.send("❌ Bu sakin karantinada değil!")
            return
        db["sakinler"][h_id]["durum"] = "Sağlıklı"
        if h_id in db["idari_kisitlamalar"]["karantina_cadiri"]:
            db["idari_kisitlamalar"]["karantina_cadiri"].remove(h_id)
        verileri_kaydet()
        await ctx.send(f"🟢 {kullanici.mention} karantinadan çıkarıldı!")

    # ============================================================
    # v.sokak-yasagi
    # ============================================================
    @commands.command(name="sokak-yasagi")
    async def prefix_sokak_yasagi(self, ctx, durum: str = None):
        if not durum:
            await ctx.send("❌ Kullanım: `v.sokak-yasagi <aç/kapat>`")
            return
        u_id = self._uid(ctx)
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return
        if db["sakinler"][u_id].get("meslek_anahtar") != "belediye_baskani":
            await ctx.send("❌ Bu komut sadece Belediye Başkanına ait!")
            return
        if durum.lower() in ["aç", "ac", "açık", "acik", "true", "evet"]:
            db["idari_kisitlamalar"]["sokaga_cikma_yasagi"] = True
            await ctx.send("🚨 **Sokağa çıkma yasağı ilan edildi!**")
        else:
            db["idari_kisitlamalar"]["sokaga_cikma_yasagi"] = False
            await ctx.send("🔓 Sokağa çıkma yasağı kaldırıldı!")
        verileri_kaydet()

    # ============================================================
    # v.savunmayi-guclendir
    # ============================================================
    @commands.command(name="savunmayi-guclendir", aliases=["savunmayı-güçlendir"])
    async def prefix_savunma(self, ctx):
        u_id = self._uid(ctx)
        if db["sakinler"].get(u_id, {}).get("meslek_anahtar") != "belediye_baskani":
            await ctx.send("❌ Sadece Belediye Başkanı!")
            return
        if db["sistem_ayarlari"]["kasa_hurda"] < 500:
            await ctx.send("❌ Kasada 500 Hurda yok!")
            return
        mevcut = db["savunma_sistemi"]["muhafiz_tahkimati"]
        if mevcut >= 100:
            await ctx.send("❌ Tahkimat zaten maksimum!")
            return
        db["sistem_ayarlari"]["kasa_hurda"] -= 500
        db["savunma_sistemi"]["muhafiz_tahkimati"] = min(100, mevcut + 15)
        verileri_kaydet()
        await ctx.send(f"🛡️ Muhafız tahkimatı güçlendirildi! Yeni: `{db['savunma_sistemi']['muhafiz_tahkimati']}/100`")

    # ============================================================
    # v.darbe
    # ============================================================
    @commands.command(name="darbe")
    async def prefix_darbe(self, ctx):
        u_id = self._uid(ctx)
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return
        baskan_id = None
        for s_id, v in db["sakinler"].items():
            if v.get("meslek_anahtar") == "belediye_baskani":
                baskan_id = s_id
                break
        if not baskan_id or baskan_id == u_id:
            await ctx.send("❌ Devrilecek başkan yok!")
            return
        itibar = db["sistem_ayarlari"].get("kasa_hurda", 0) / 10
        savunma = db["savunma_sistemi"]["muhafiz_tahkimati"]
        sans = 10 + (100 - min(itibar, 100)) + (50 - savunma)
        sans = max(5, min(sans, 90))
        zar = random.randint(1, 100)
        if zar <= sans:
            db["sakinler"][baskan_id]["meslek_anahtar"] = "gezgin"
            db["sakinler"][baskan_id]["meslek_isim"] = "Gezgin (Devrildi)"
            db["sakinler"][u_id]["meslek_anahtar"] = "belediye_baskani"
            db["sakinler"][u_id]["meslek_isim"] = "Belediye Başkanı"
            db["sistem_ayarlari"]["kasa_hurda"] = max(0, db["sistem_ayarlari"].get("kasa_hurda", 0) // 2)
            verileri_kaydet()
            await ctx.send(f"🔥 **DARBE BAŞARILI!** {ctx.author.mention} yeni başkan!")
        else:
            await ctx.send(f"🛡️ Darbe bastırıldı! (Şans: %{sans}, Zar: {zar})")

    # ============================================================
    # v.nobet
    # ============================================================
    @commands.command(name="nobet")
    async def prefix_nobet(self, ctx):
        u_id = self._uid(ctx)
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return
        sakin = db["sakinler"][u_id]
        meslek = sakin.get("meslek_anahtar", "")
        if meslek not in MESLEK_GRUPLARI["kolluk"]:
            await ctx.send("❌ Sadece muhafız sınıfı nöbet tutabilir!")
            return
        son = sakin.get("son_nobet")
        if son:
            fark = datetime.datetime.now() - datetime.datetime.fromisoformat(son)
            if fark.total_seconds() < 14400:
                kalan = int((14400 - fark.total_seconds()) / 3600)
                await ctx.send(f"❌ Nöbet yorgunluğu! `{kalan} saat` beklemelisin.")
                return
        taban = random.randint(40, 80)
        taban_xp = 20
        if meslek == "muhafiz_komutani":
            taban = int(taban * 1.5)
            taban_xp = 35
        elif meslek == "muhafiz":
            taban = int(taban * 1.2)
            taban_xp = 25
        olay = random.randint(1, 10)
        ek = ""
        if olay <= 2:
            bonus = random.randint(30, 60)
            taban += bonus
            ek = f"\n🚨 Hırsız yakaladın! +{bonus} Hurda bonus!"
        elif olay >= 9:
            taban = int(taban * 0.7)
            ek = "\n😴 Sıkıcı nöbet, ödül azaldı."
        sakin["cuzdan"] = sakin.get("cuzdan", 0) + taban
        atlamalar = xp_ekle(u_id, taban_xp)
        sakin["son_nobet"] = datetime.datetime.now().isoformat()
        verileri_kaydet()
        embed = discord.Embed(title="🛡️ NÖBET RAPORU", color=0x3498DB)
        embed.description = f"💰 **Kazanç:** `+{taban} Hurda`\n⭐ **XP:** `+{taban_xp}`{ek}"
        if atlamalar:
            embed.add_field(name="🎉 Seviye", value="\n".join([f"• Seviye {a['seviye']}! +{a['odul']} Hurda" for a in atlamalar]), inline=False)
        await ctx.send(embed=embed)

    # ============================================================
    # v.muhafiz-paneli
    # ============================================================
    @commands.command(name="muhafiz-paneli")
    async def prefix_muhafiz_paneli(self, ctx):
        u_id = self._uid(ctx)
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return
        meslek = db["sakinler"][u_id].get("meslek_anahtar", "")
        if meslek not in MESLEK_GRUPLARI["kolluk"]:
            await ctx.send("❌ Asayiş yetkiniz yok!")
            return
        embed = discord.Embed(title="🛡️ MUHAFIZ PANELİ", color=0x2980B9)
        embed.description = (
            f"🛡️ **Tahkimat:** `{db['savunma_sistemi'].get('muhafiz_tahkimati', 10)}/100`\n\n"
            "📋 **Komutlar:**\n"
            "• `v.hucreye-at @üye` — Zindana at\n"
            "• `v.hucreden-cikar @üye` — Tahliye\n"
            "• `v.karantina-al @üye` — Karantinaya al\n"
            "• `v.karantina-kaldir @üye` — Karantinadan çıkar\n"
            "• `v.nobet` — Nöbet tut, ödül al"
        )
        await ctx.send(embed=embed)

    # ============================================================
    # v.rahip-paneli
    # ============================================================
    @commands.command(name="rahip-paneli")
    async def prefix_rahip_paneli(self, ctx):
        RAHIP_ROL_ID = 1515026155969843401
        if not any(rol.id == RAHIP_ROL_ID for rol in ctx.author.roles):
            await ctx.send("❌ Sadece Rahip sınıfı!")
            return
        kilise = db["kilise_sistemi"]
        embed = discord.Embed(title="⛪ RAHİP PANELİ", color=0x9B59B6)
        embed.description = (
            f"📊 **Kilise Durumu:**\n"
            f"• Fare Nüfusu: `{kilise.get('fare_nufusu', 10)}`\n"
            f"• Kedi Katliamı: `{'Evet' if kilise.get('kedi_katliami_yapildi') else 'Hayır'}`\n\n"
            "📋 **Komutlar:**\n"
            "• `v.afaroz-et @üye <neden>` — Dinden çıkar\n"
            "• `v.buyuk-kilise-cani` — Herkese +10 moral\n"
            "• `v.kutsa @üye` — Enfeksiyon -20, sağlık +15\n"
            "• `v.kedileri-yok-et` — ⚠️ Tehlikeli!"
        )
        await ctx.send(embed=embed)

    # ============================================================
    # v.afaroz-et
    # ============================================================
    @commands.command(name="afaroz-et")
    async def prefix_afaroz_et(self, ctx, kullanici: discord.Member = None, *, neden: str = None):
        if not kullanici or not neden:
            await ctx.send("❌ Kullanım: `v.afaroz-et @üye <neden>`")
            return
        RAHIP_ROL_ID = 1515026155969843401
        if not any(rol.id == RAHIP_ROL_ID for rol in ctx.author.roles):
            await ctx.send("❌ Rahip değilsin!")
            return
        s_id = str(kullanici.id)
        if s_id not in db["sakinler"]:
            await ctx.send("❌ Bu kişi sığınakta yaşamıyor!")
            return
        mevcut = db["sakinler"][s_id].get("sans_carpani", 1.0)
        db["sakinler"][s_id]["sans_carpani"] = max(0.1, mevcut - 0.5)
        verileri_kaydet()
        await ctx.send(f"🚫 {kullanici.mention} afaroz edildi! Neden: *{neden}*. Şansı düştü.")

    # ============================================================
    # v.buyuk-kilise-cani
    # ============================================================
    @commands.command(name="buyuk-kilise-cani")
    async def prefix_kilise_cani(self, ctx):
        RAHIP_ROL_ID = 1515026155969843401
        if not any(rol.id == RAHIP_ROL_ID for rol in ctx.author.roles):
            await ctx.send("❌ Sadece rahip kilise çanını çalabilir!")
            return
        simdi = datetime.datetime.now()
        son = db["kilise_sistemi"]["son_can_calinma"]
        if son:
            fark = simdi - datetime.datetime.fromisoformat(son)
            if fark.days < 3:
                kalan = int((3 * 86400 - fark.total_seconds()) / 3600)
                await ctx.send(f"🔔 Çan soğumadı! `{kalan} saat` beklemelisin.")
                return
        sayac = 0
        for s_id, v in db["sakinler"].items():
            if v.get("durum") not in ("Ölü", "Hücrede"):
                v["moral"] = min(100, v.get("moral", 50) + 10)
                sayac += 1
        db["kilise_sistemi"]["son_can_calinma"] = simdi.isoformat()
        verileri_kaydet()
        await ctx.send(f"🔔 **BÜYÜK KİLİSE ÇANI!** {sayac} sakinin morali +10 arttı!")

    # ============================================================
    # v.kutsa
    # ============================================================
    @commands.command(name="kutsa", aliases=["kutsama"])
    async def prefix_kutsa(self, ctx, kullanici: discord.Member = None):
        if not kullanici:
            await ctx.send("❌ Kullanım: `v.kutsa @üye`")
            return
        RAHIP_ROL_ID = 1515026155969843401
        if not any(rol.id == RAHIP_ROL_ID for rol in ctx.author.roles):
            await ctx.send("❌ Kutsama yetkisi sadece Rahibe ait!")
            return
        rahip_id = self._uid(ctx)
        # RAHİP KAYITLI MI KONTROL ET (KeyError fix)
        if rahip_id not in db["sakinler"]:
            await ctx.send("❌ Rahip olarak kayıtlı değilsin! Önce `v.kayit` ol.")
            return
        if db["sakinler"][rahip_id].get("durum") == "Ölü":
            await ctx.send("❌ Ölü rahip kutsayamaz!")
            return
        son = db["sakinler"][rahip_id].get("son_kutsama")
        if son:
            fark = datetime.datetime.now() - datetime.datetime.fromisoformat(son)
            if fark.total_seconds() < 10800:
                kalan = int((10800 - fark.total_seconds()) / 60)
                await ctx.send(f"❌ Kutsama gücün toplanıyor! `{kalan} dk` beklemelisin.")
                return
        h_id = str(kullanici.id)
        if h_id not in db["sakinler"]:
            await ctx.send("❌ Bu kişi sığınakta yaşamıyor!")
            return
        hedef = db["sakinler"][h_id]
        if hedef.get("durum") == "Ölü":
            await ctx.send("❌ Ölüyü kutsayamazsın!")
            return
        eski_enf = hedef.get("enfeksiyon", 0)
        hedef["enfeksiyon"] = max(0, eski_enf - 20)
        hedef["saglik"] = min(100, hedef.get("saglik", 100) + 15)
        hedef["moral"] = min(100, hedef.get("moral", 50) + 5)
        if hedef["enfeksiyon"] == 0 and hedef.get("durum") == "Enfekte":
            hedef["durum"] = "Sağlıklı"
        db["sakinler"][rahip_id]["son_kutsama"] = datetime.datetime.now().isoformat()
        verileri_kaydet()
        await ctx.send(f"✨ {kullanici.mention} kutsandı! Enfeksiyon: `{eski_enf}→{hedef['enfeksiyon']}`, Sağlık: +15, Moral: +5")

    # ============================================================
    # v.kedileri-yok-et
    # ============================================================
    @commands.command(name="kedileri-yok-et")
    async def prefix_kedileri_yok_et(self, ctx):
        RAHIP_ROL_ID = 1515026155969843401
        if not any(rol.id == RAHIP_ROL_ID for rol in ctx.author.roles):
            await ctx.send("❌ Bu karar sadece rahip tarafından alınabilir!")
            return
        rahip_id = self._uid(ctx)
        if db["sakinler"].get(rahip_id, {}).get("durum") == "Ölü":
            await ctx.send("❌ Ölü biri kedi yakamaz!")
            return
        if db["kilise_sistemi"]["kedi_katliami_yapildi"]:
            await ctx.send("❌ Kediler zaten yakıldı!")
            return
        db["kilise_sistemi"]["kedi_katliami_yapildi"] = True
        db["kilise_sistemi"]["fare_nufusu"] *= 10
        sayac = 0
        for s_id, v in db["sakinler"].items():
            if v.get("durum") == "Canlı":
                v["durum"] = "Enfekte"
                sayac += 1
        db["sakinler"][rahip_id]["itibar"] = max(0, db["sakinler"][rahip_id].get("itibar", 50) - 30)
        verileri_kaydet()
        await ctx.send(f"🔥 **KEDİLER YAKILDI!** {sayac} sakin enfekte oldu! Fare nüfusu patladı!")

    # ============================================================
    # v.deney
    # ============================================================
    @commands.command(name="deney")
    async def prefix_deney(self, ctx):
        u_id = self._uid(ctx)
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return
        sakin = db["sakinler"][u_id]
        meslek = sakin.get("meslek_anahtar", "")
        if meslek not in ["bas_simyaci", "simyaci"]:
            await ctx.send("❌ Sadece Baş Simyacı/Simyacı deney yapabilir!")
            return
        lab = db["biyolaboratuvar"]
        ilerleme = lab["virus_ilerlemesi"]
        seviye = lab["lab_seviyesi"]
        temel_basari = 10
        basari_bonusu = (seviye - 1) * 25
        guncel_basari = min(temel_basari + basari_bonusu, 70)
        if ilerleme >= 50:
            guncel_olum = 15
        elif ilerleme >= 25:
            guncel_olum = 10
        else:
            guncel_olum = 5
        zar = random.randint(1, 100)
        lab["toplam_deney"] += 1
        if zar <= guncel_olum:
            ganimet = olum_protokolu(u_id, "diger")
            lab["virus_ilerlemesi"] = 0
            verileri_kaydet()
            await ctx.send(f"💥 **PATLAMA!** {ctx.author.mention} laboratuvarda öldü! Virüs verisi sıfırlandı!\n📦 {ganimet[:100] if ganimet else 'Aktarılacak bir şey kalmamıştı.'}")
        elif zar <= (guncel_olum + guncel_basari):
            lab["virus_ilerlemesi"] = min(ilerleme + 5, 100)
            atlamalar = xp_ekle(u_id, 30)
            verileri_kaydet()
            msg = f"✅ **Deney başarılı!** Virüs: `%{ilerleme}` → `%{lab['virus_ilerlemesi']}` (+5)\n⭐ +30 XP"
            if atlamalar:
                msg += "\n" + "\n".join([f"🎉 Seviye {a['seviye']}! +{a['odul']} Hurda" for a in atlamalar])
            await ctx.send(msg)
        else:
            verileri_kaydet()
            await ctx.send(f"❌ **Deney başarısız.** Mevcut ilerleme: `%{ilerleme}`")

    # ============================================================
    # v.laboratuvar-gelistir
    # ============================================================
    @commands.command(name="laboratuvar-gelistir", aliases=["laboratuvar-geliştir"])
    async def prefix_lab_gelistir(self, ctx):
        u_id = self._uid(ctx)
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return
        meslek = db["sakinler"][u_id].get("meslek_anahtar", "")
        if meslek not in ["belediye_baskani", "bas_simyaci"]:
            await ctx.send("❌ Sadece Başkan veya Baş Simyacı!")
            return
        lab = db["biyolaboratuvar"]
        if lab.get("lab_seviyesi", 1) >= 3:
            await ctx.send("❌ Laboratuvar zaten max seviye (3)!")
            return
        if db["sistem_ayarlari"]["kasa_hurda"] < 500:
            await ctx.send("❌ Kasada 500 Hurda yok!")
            return
        db["sistem_ayarlari"]["kasa_hurda"] -= 500
        lab["lab_seviyesi"] += 1
        verileri_kaydet()
        await ctx.send(f"🔬 **Laboratuvar yükseltildi!** Yeni seviye: `{lab['lab_seviyesi']}`")

    # ============================================================
    # v.doktor-paneli
    # ============================================================
    @commands.command(name="doktor-paneli")
    async def prefix_doktor_paneli(self, ctx):
        u_id = self._uid(ctx)
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return
        meslek = db["sakinler"][u_id].get("meslek_anahtar", "")
        if meslek not in MESLEK_GRUPLARI["tibbi"]:
            await ctx.send("❌ Tıbbi yetkiniz yok!")
            return
        embed = discord.Embed(title="🏥 DOKTOR PANELİ", color=0x1ABC9C)
        embed.description = (
            f"📦 **Aşı Stoku:** `{db['cevre_durumu'].get('karantina_asi_stoku', 0)}`\n"
            f"⚕️ **Tıbbi Malzeme:** `{db['koy_ambari']['stoklar'].get('tibbi_malzeme', 0)}`\n\n"
            "📋 **Komutlar:**\n"
            "• `v.asi-uret` — 2 tıbbi malzeme → 1 aşı\n"
            "• `v.tedavi-et @üye` — Hastayı iyileştir"
        )
        await ctx.send(embed=embed)

    # ============================================================
    # v.asi-uret
    # ============================================================
    @commands.command(name="asi-uret")
    async def prefix_asi_uret(self, ctx):
        u_id = self._uid(ctx)
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return
        meslek = db["sakinler"][u_id].get("meslek_anahtar", "")
        if meslek not in MESLEK_GRUPLARI["tibbi"]:
            await ctx.send("❌ Aşı üretme yetkiniz yok!")
            return
        stoklar = db["koy_ambari"]["stoklar"]
        if stoklar.get("tibbi_malzeme", 0) < 2:
            await ctx.send("❌ Ambarda 2 tıbbi malzeme yok!")
            return
        stoklar["tibbi_malzeme"] -= 2
        db["cevre_durumu"]["karantina_asi_stoku"] += 1
        atlamalar = xp_ekle(u_id, 10)
        verileri_kaydet()
        msg = f"🧪 1 aşı üretildi! Toplam: `{db['cevre_durumu']['karantina_asi_stoku']}` (+10 XP)"
        if atlamalar:
            msg += "\n" + "\n".join([f"🎉 Seviye {a['seviye']}! +{a['odul']} Hurda" for a in atlamalar])
        await ctx.send(msg)

    # ============================================================
    # v.tedavi-et
    # ============================================================
    @commands.command(name="tedavi-et")
    async def prefix_tedavi_et(self, ctx, kullanici: discord.Member = None):
        if not kullanici:
            await ctx.send("❌ Kullanım: `v.tedavi-et @üye`")
            return
        u_id = self._uid(ctx)
        hata = self._sakin_kontrol(ctx)
        if hata:
            await ctx.send(hata)
            return
        meslek = db["sakinler"][u_id].get("meslek_anahtar", "")
        if meslek not in MESLEK_GRUPLARI["tibbi"]:
            await ctx.send("❌ Tedavi yetkiniz yok!")
            return
        if db["cevre_durumu"]["karantina_asi_stoku"] <= 0:
            await ctx.send("❌ Aşı stoku yok! Önce `v.asi-uret`")
            return
        h_id = str(kullanici.id)
        if h_id not in db["sakinler"]:
            await ctx.send("❌ Bu kişi sığınakta yaşamıyor!")
            return
        if db["sakinler"][h_id].get("durum") not in ["Enfekte", "Karantinada"]:
            await ctx.send("❌ Bu sakin zaten sağlıklı!")
            return
        db["cevre_durumu"]["karantina_asi_stoku"] -= 1
        db["sakinler"][h_id]["durum"] = "Sağlıklı"
        db["sakinler"][h_id]["enfeksiyon"] = 0
        atlamalar = xp_ekle(u_id, 25)
        verileri_kaydet()
        msg = f"🟢 {kullanici.mention} tedavi edildi! Kalan aşı: `{db['cevre_durumu']['karantina_asi_stoku']}` (+25 XP)"
        if atlamalar:
            msg += "\n" + "\n".join([f"🎉 Seviye {a['seviye']}! +{a['odul']} Hurda" for a in atlamalar])
        await ctx.send(msg)

    # ============================================================
    # v.haber
    # ============================================================
    @commands.command(name="haber")
    @commands.has_permissions(administrator=True)
    async def prefix_haber(self, ctx, kanal: discord.TextChannel = None):
        if not kanal:
            await ctx.send("❌ Kullanım: `v.haber #kanal`")
            return
        db["gazete_sistemi"]["haber_kanali_id"] = kanal.id
        verileri_kaydet()
        await ctx.send(f"📰 **Basın Ofisi!** Haberler artık {kanal.mention} kanalına yazılacak!")

    # ============================================================
    # v.hava-durumu-degis
    # ============================================================
    @commands.command(name="hava-durumu-degis", aliases=["hava-durumu-değiş"])
    @commands.has_permissions(administrator=True)
    async def prefix_hava_degis(self, ctx, *, yeni_hava: str = None):
        if not yeni_hava:
            await ctx.send("❌ Kullanım: `v.hava-durumu-degis <mevsim>`\nSeçenekler: İlkbahar, Yaz, Yağmurlu, Kış")
            return
        temiz = yeni_hava.strip().capitalize()
        gecerli = ["İlkbahar", "Yaz", "Yağmurlu", "Kış"]
        if temiz not in gecerli:
            await ctx.send(f"❌ Geçersiz! Seçenekler: {', '.join(gecerli)}")
            return
        db["cevre_durumu"]["hava_durumu"] = temiz
        verileri_kaydet()
        await ctx.send(f"🌤️ Hava durumu **{temiz}** olarak değiştirildi!")

    # ============================================================
    # v.sunucu-yonetimi
    # ============================================================
    @commands.command(name="sunucu-yonetimi", aliases=["sunucu-yönetimi"])
    async def prefix_sunucu_yonetimi(self, ctx):
        if not any(rol.id == RP_OWNER_ROL_ID for rol in ctx.author.roles):
            await ctx.send("❌ Bu komut sadece RP Owner'a özel!")
            return
        embed = discord.Embed(title="⚡ SUNUCU YÖNETİMİ", color=0x1ABC9C)
        embed.description = (
            f"🌍 **Hava:** `{db['cevre_ayarlari'].get('hava_durumu', 'Güneşli')}`\n"
            f"🌤️ **Mevsim:** `{db['cevre_durumu'].get('hava_durumu', 'İlkbahar')}`\n"
            f"☣️ **Salgın Gücü:** `Seviye {db['cevre_ayarlari'].get('salgin_kuvveti', 1)}`\n"
            f"💰 **Kasa:** `{db['sistem_ayarlari'].get('kasa_hurda', 0)} Hurda`\n\n"
            "💡 Tam panel (butonlu) slash komutu ile: `/sunucu-yonetimi`\n"
            "Butonlar: Kraliyet Desteği, Toplu Enfeksiyon, Hava/Salgın menüleri"
        )
        await ctx.send(embed=embed)

    # ============================================================
    # v.maliye-yonetim
    # ============================================================
    @commands.command(name="maliye-yonetim", aliases=["maliye-yönetim"])
    async def prefix_maliye_yonetim(self, ctx):
        VERGI_MEMURU_ROL_ID = 1508536734709973032
        if not any(rol.id == VERGI_MEMURU_ROL_ID for rol in ctx.author.roles):
            await ctx.send("❌ Sadece Vergi Memuru/Müfettişi!")
            return
        maliye = db["maliye_ayarlari"]
        embed = discord.Embed(title="🏛️ MALİYE PANELİ", color=0xE67E22)
        embed.description = (
            f"🦠 **Veba Vergisi:** `{maliye['veba_vergisi']} Hurda / 5 saat`\n"
            f"⚖️ **Ticaret Kesintisi:** `%{maliye['ticaret_kesintisi']}`\n"
            f"💰 **Kasa:** `{db['sistem_ayarlari'].get('kasa_hurda', 0)} Hurda`\n"
            f"📊 **Toplam Tahsilat:** `{maliye['toplam_tahsilat']} Hurda`\n\n"
            "💡 Oranları değiştirmek için slash komutu: `/maliye-yonetim` (modal ile ayarlama)"
        )
        await ctx.send(embed=embed)

    # ============================================================
    # v.owner-kayit
    # ============================================================
    @commands.command(name="owner-kayit", aliases=["owner-kayıt"])
    async def prefix_owner_kayit(self, ctx, kullanici: discord.Member = None, isim: str = None, soyisim: str = None, yas: int = None, memleket: str = None):
        if not kullanici or not isim or not soyisim or yas is None or not memleket:
            await ctx.send("❌ Kullanım: `v.owner-kayit @üye <isim> <soyisim> <yas> <memleket>`\nÖrnek: `v.owner-kayit @ali Mehmet Yılmaz 25 Bavyera`")
            return
        if not any(rol.id == RP_OWNER_ROL_ID for rol in ctx.author.roles):
            await ctx.send("❌ Bu komut sadece RP Owner'a özel!")
            return
        if yas > 40 or yas < 10:
            await ctx.send("❌ Yaş 10-40 arası olmalı!")
            return
        u_id = str(kullanici.id)
        if u_id in db["sakinler"] and db["sakinler"][u_id].get("durum") != "Ölü":
            await ctx.send(f"❌ {kullanici.mention} zaten aktif sicile sahip!")
            return
        baslangic_atak = random.randint(10, 20)
        sakin_olustur_defaults(u_id, isim, soyisim, yas, memleket, baslangic_atak)
        verileri_kaydet()
        await ctx.send(f"👑 {kullanici.mention} RP Owner tarafından kaydedildi! Atak: `{baslangic_atak}`, Hurda: `500`")

    # ============================================================
    # v.kayit-sil
    # ============================================================
    @commands.command(name="kayit-sil", aliases=["kayıt-sil"])
    async def prefix_kayit_sil(self, ctx, kullanici: discord.Member = None, onay: str = None):
        if not kullanici or onay != "EVET":
            await ctx.send("❌ Kullanım: `v.kayit-sil @üye EVET`")
            return
        if not any(rol.id == RP_OWNER_ROL_ID for rol in ctx.author.roles):
            await ctx.send("❌ Bu komut sadece RP Owner'a özel!")
            return
        u_id = str(kullanici.id)
        if u_id not in db["sakinler"]:
            await ctx.send(f"❌ {kullanici.mention} zaten kayıtlı değil!")
            return
        silinen_isim = db["sakinler"][u_id].get("isim", "?")
        sakin_sil(u_id)
        await ctx.send(f"🗑️ {kullanici.mention} (`{silinen_isim}`) sicil kaydı silindi!")

    # ============================================================
    # v.xp_kazan_test
    # ============================================================
    @commands.command(name="xp_kazan_test")
    @commands.has_permissions(administrator=True)
    async def prefix_xp_test(self, ctx, miktar: int = None, hedef: discord.Member = None):
        if miktar is None:
            await ctx.send("❌ Kullanım: `v.xp_kazan_test <miktar> [@üye]`")
            return
        if miktar <= 0 or miktar > 10000:
            await ctx.send("❌ Miktar 1-10000 arası olmalı!")
            return
        hedef_user = hedef if hedef else ctx.author
        h_id = str(hedef_user.id)
        if h_id not in db["sakinler"]:
            await ctx.send("❌ Hedef sakin kayıtlı değil!")
            return
        atlamalar = xp_ekle(h_id, miktar)
        verileri_kaydet()
        msg = f"🧪 TEST: {hedef_user.mention} +{miktar} XP"
        if atlamalar:
            msg += "\n" + "\n".join([f"🎉 Seviye {a['seviye']}! +{a['odul']} Hurda" for a in atlamalar])
        await ctx.send(msg)

    @prefix_xp_test.error
    async def xp_test_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Bu komut sadece sunucu yöneticileri tarafından kullanılabilir!")


async def setup(bot):
    await bot.add_cog(PrefixCog(bot))

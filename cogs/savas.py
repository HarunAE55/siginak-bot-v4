"""
Cog: Savaş & Baskın
==================
Komutlar:
- /duello (butonlu, tur tabanlı düello, %20 kalıcı ölüm riski)
- /sefer (başkan başlatır, 10 kişilik manga, dış dünya seferi)
- /zombi-baskini-baslat (SADECE RP Owner - manuel baskın tetikler, otomatik döngü KALDIRILDI)
"""

import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio

from veritabani import (
    db, verileri_kaydet, olu_kontrolu, olum_protokolu,
    sokak_ve_karantina_kontrolu, xp_ekle, haber_ekle,
    RP_OWNER_ROL_ID
)
from kanallar import BASKIN_KANAL_ID


class SavasCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ====================================================
    # /duello - Butonlu, tur tabanlı düello
    # ====================================================
    @app_commands.command(name="duello", description="[SAVAŞ] Başka bir sığınak sakinini butonlu, tur tabanlı ölümcül bir düelloya davet eder.")
    @app_commands.describe(kullanici="Meydan okumak istediğiniz sakin")
    async def duello_davet(self, interaction: discord.Interaction, kullanici: discord.User):
        if kullanici.id == interaction.user.id:
            await interaction.response.send_message("❌ Kendi kendine meydan okuyamazsın!", ephemeral=True)
            return

        u_id = str(interaction.user.id)
        r_id = str(kullanici.id)

        if u_id not in db["sakinler"] or r_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Taraflardan birinin sığınak kütüğünde kaydı yok!", ephemeral=True)
            return

        kontrol = sokak_ve_karantina_kontrolu(u_id)
        if kontrol:
            await interaction.response.send_message(kontrol, ephemeral=True)
            return

        if db["sakinler"][u_id].get("durum") == "Ölü" or db["sakinler"][r_id].get("durum") == "Ölü":
            await interaction.response.send_message("❌ Ölü karakterler düello yapamaz!", ephemeral=True)
            return

        veri_eden = db["sakinler"][u_id]
        veri_edilen = db["sakinler"][r_id]

        embed = discord.Embed(title="⚔️ DÜELLO DAVETİ!", color=0xC0392B)
        embed.description = (
            f"🗡️ **{interaction.user.mention}**, **{kullanici.mention}** kullanıcısına meydan okudu!\n\n"
            f"🔺 **Davet Eden:** {veri_eden['isim']} | ⚔️ Atak: `{veri_eden.get('atak', 10)}` | 🛡️ Defans: `{veri_eden.get('defans', 0)}`\n"
            f"🔻 **Davet Edilen:** {veri_edilen['isim']} | ⚔️ Atak: `{veri_edilen.get('atak', 10)}` | 🛡️ Defans: `{veri_edilen.get('defans', 0)}`\n\n"
            f"⚠️ *Kabul edersen ölümcül bir düelloya gireceksin! Kaybedenin %20 ihtimalle karakteri kalıcı olarak ÖLÜR!*\n\n"
            f"⏱️ *Davet 60 saniye sonra otomatik olarak sona erer.*"
        )

        view = DuelloDavetView(interaction.user, kullanici, veri_eden, veri_edilen)
        await interaction.response.send_message(
            f"⚔️ {kullanici.mention}, {interaction.user.mention} sana meydan okudu! Kabul ediyor musun?",
            embed=embed,
            view=view
        )

    # ====================================================
    # /sefer - Başkan dış dünya seferi
    # ====================================================
    @app_commands.command(name="sefer", description="[BAŞKAN] Sığınak ordusunu toplayarak dış dünyaya ganimet ve keşif seferi düzenler.")
    async def sefer_duzenle(self, interaction: discord.Interaction):
        u_id = str(interaction.user.id)
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return
        meslek = db["sakinler"].get(u_id, {}).get("meslek_anahtar", "")

        if meslek != "belediye_baskani":
            await interaction.response.send_message("❌ Sefere çıkma emrini yalnızca Belediye Başkanı verebilir!", ephemeral=True)
            return

        zorluk = db["sefer_sistemi"]["sefer_zorlugu"]
        view = SeferLobisiView(u_id, zorluk)

        embed = discord.Embed(title=f"☠️ DIŞ DÜNYA SEFERİ ODASI (Zorluk: Seviye {zorluk})", color=0x962D2D)
        embed.description = (
            f"📢 **Belediye Başkanı {interaction.user.mention}** dış dünyadaki zombi yuvalarını temizlemek ve ganimet toplamak için ordu kaldırıyor!\n\n"
            "⚠️ **DİKKAT:** Bu seferde kalıcı ölüm riski mevcuttur! Başarılı olursanız sığınak zenginleşir, başarısız olursanız mangadakiler zombi yemi olur!\n\n"
            "👉 Katılmak için aşağıdaki butona basın. Başkan hazır olduğunda savaşı başlatacak!"
        )

        await interaction.response.send_message(embed=embed, view=view)

        # Lobinin dolmasını bekle
        await view.wait()

        if not view.katilimcilar:
            return  # Kimse katılmadıysa iptal

        # Savaş simülasyonu
        yaratik_cani = zorluk * 400
        toplam_ganimet_hurda = 0
        rapor_text = f"🪓 **SAVAŞ RAPORU** 🪓\n👾 **Düşman Gücü:** Seviye {zorluk} Zombi Sürüsü (Toplam Can: {yaratik_cani})\n\n"

        manga_raporu = {}
        for user in view.katilimcilar:
            manga_raporu[str(user.id)] = {"user": user, "hasar": 0, "yenen_hasar": 0, "kill": 0, "durum": "Sağ"}

        # Savaş turları
        while yaratik_cani > 0 and any(m["durum"] == "Sağ" for m in manga_raporu.values()):
            for p_id, veri in manga_raporu.items():
                if veri["durum"] == "Ölü":
                    continue

                p_hasar = random.randint(30, 80) + (db["sakinler"][p_id].get("xp", 0) // 10)
                yaratik_cani -= p_hasar
                veri["hasar"] += p_hasar

                if yaratik_cani <= 0:
                    veri["kill"] += 1
                    break

                z_hasar = random.randint(10, 40) + (zorluk * 5)
                veri["yenen_hasar"] += z_hasar

                if veri["yenen_hasar"] >= 150:
                    veri["durum"] = "Ölü"
                    ganimet = olum_protokolu(p_id, olum_sebebi="diger")
                    rapor_text += f"☠️ **{veri['user'].mention}** zombiler tarafından parçalanarak **KAYBEDİLDİ** (Kalıcı Ölüm)!\n"
                    if ganimet:
                        rapor_text += f"📦 *Miras kasaya aktarıldı.*\n"

        embed_sonuc = discord.Embed(title="📊 SEFER NETİCESİ VE GANİMET DAĞILIMI", color=0x2ECC71 if yaratik_cani <= 0 else 0xC0392B)

        if yaratik_cani <= 0:
            db["sefer_sistemi"]["sefer_zorlugu"] += 1
            toplam_ganimet_hurda = zorluk * random.randint(150, 300)
            db["sistem_ayarlari"]["kasa_hurda"] = db["sistem_ayarlari"].get("kasa_hurda", 0) + (toplam_ganimet_hurda // 2)
            embed_sonuc.description = f"🎉 **ZAFER!** Dış dünya temizlendi. Sefer Zorluğu Seviye `{db['sefer_sistemi']['sefer_zorlugu']}` oldu.\n💰 Sığınak Kasasına `{toplam_ganimet_hurda // 2} Hurda` aktarıldı!\n\n"
            haber_ekle(f"⚔️ Belediye Başkanı sefer düzenledi ve ZAFER kazanıldı. Ganimet: {toplam_ganimet_hurda // 2} Hurda.")
        else:
            embed_sonuc.description = "❌ **HEZİMET!** Sığınak ordusu geri çekilmek zorunda kaldı.\n\n"
            haber_ekle("💀 Sefer hezimetle sonuçlandı. Manga ağır kayıp verdi.")

        stat_text = ""
        for p_id, veri in manga_raporu.items():
            if veri["durum"] == "Sağ" and yaratik_cani <= 0:
                pay = (toplam_ganimet_hurda // 2) // len(view.katilimcilar) if view.katilimcilar else 0
                db["sakinler"][p_id]["cuzdan"] = db["sakinler"][p_id].get("cuzdan", 0) + pay
                atlamalar = xp_ekle(p_id, 50)
                stat_text += f"👤 {veri['user'].mention} -> Vurulan: `{veri['hasar']}` | Ganimet: `+{pay} Hurda` (+50 XP)\n"
                if atlamalar:
                    for a in atlamalar:
                        stat_text += f"   🎉 Seviye {a['seviye']} atladı! +{a['odul']} Hurda\n"
            else:
                stat_text += f"☠️ {veri['user'].mention} -> Savaşta elendi.\n"

        embed_sonuc.add_field(name="⚔️ Manga Performans Tablosu", value=stat_text or "Kimse hayatta kalamadı.", inline=False)
        if "☠️" in rapor_text:
            embed_sonuc.add_field(name="🚨 Önemli Olaylar", value=rapor_text, inline=False)

        verileri_kaydet()
        await interaction.channel.send(embed=embed_sonuc)

    # ====================================================
    # /zombi-baskini-baslat - SADECE RP OWNER
    # ====================================================
    @app_commands.command(name="zombi-baskini-baslat", description="[OWNER] Sadece RP Owner: Sığınak surlarına manuel zombi baskını başlatır.")
    async def zombi_baskini_baslat(self, interaction: discord.Interaction):
        # RP Owner kontrolü
        if not any(rol.id == RP_OWNER_ROL_ID for rol in interaction.user.roles):
            await interaction.response.send_message(
                "❌ Bu komut sadece RP Owner rolüne sahip yetkililer tarafından kullanılabilir!",
                ephemeral=True
            )
            return

        # Baskın gücü hesaplama
        sakin_sayisi = len(db["sakinler"])
        sur_sev = db["sefer_sistemi"]["sur_seviyesi"]
        baskin_gucu = (sakin_sayisi * 40) + (sur_sev * 100) + random.randint(50, 200)

        view = BaskinSavunmaView(baskin_gucu)

        # Baskın kanalı (öncelik: salgın kanalı, yoksa mevcut kanal)
        kanal = self.bot.get_channel(BASKIN_KANAL_ID) or interaction.channel

        embed = discord.Embed(title="🚨 ACİL ALARM! SIĞINAK SURLARINA ZOMBİ BASKINI!", color=0x990000)
        embed.description = (
            f"🧟‍♂️ **Zombi Sürüsü Geliyor!** Yaklaşan düşman gücü: `{baskin_gucu}`\n"
            f"🏰 **Mevcut Sur Durumu:** Seviye `{sur_sev}` | Dayanıklılık: `{db['sefer_sistemi']['sur_canı']}/{db['sefer_sistemi']['maks_sur_canı']}`\n\n"
            "🚨 **MUHAFIZLAR VE SAKİNLER GÖREVE!** Zombiler surları dövmeden önce savunma hattı kurun!\n"
            "⏱️ **Müdahale Süresi:** `2 Dakika`"
        )
        embed.set_footer(text=f"Baskını başlatan: {interaction.user.display_name} (RP Owner)")

        await interaction.response.send_message("🚨 Baskın başlatıldı! Savunma kanalına alarm gönderildi.", ephemeral=True)
        await kanal.send(embed=embed, view=view)

        haber_ekle(f"🚨 RP Owner tarafından zombi baskını başlatıldı! Güç: {baskin_gucu}")

        # 2 dakika bekle
        await asyncio.sleep(120)

        # Sonuç hesaplama
        if view.toplam_savunma_gucu >= baskin_gucu:
            embed_zafer = discord.Embed(title="🟢 BASKIN PÜSKÜRTÜLDÜ!", color=0x2ECC71)
            embed_zafer.description = (
                f"🛡️ Sığınak halkı ve muhafızlar etten duvar ördü!\n"
                f"🔥 **Gerekli Güç:** `{baskin_gucu}` | **Toplanan Savunma Gücü:** `{view.toplam_savunma_gucu}`\n"
                f"🎉 Surlar hasar almadı. Savunmaya katılan herkes kahraman ilan edildi!"
            )
            await kanal.send(embed=embed_zafer)
            haber_ekle("🛡️ Zombi baskını püskürtüldü! Sığınak halkı zafer kazandı.")
        else:
            alinan_hasar = baskin_gucu - view.toplam_savunma_gucu
            db["sefer_sistemi"]["sur_canı"] = max(0, db["sefer_sistemi"]["sur_canı"] - alinan_hasar)

            embed_yenilgi = discord.Embed(title="💥 SURLAR DARBE ALDI!", color=0xC0392B)
            embed_yenilgi.description = (
                f"❌ Savunma hattı zombileri durdurmaya yetmedi!\n"
                f"💔 **Surların Yediği Hasar:** `-{alinan_hasar}`\n"
                f"🏰 **Kalan Sur Canı:** `{db['sefer_sistemi']['sur_canı']}/{db['sefer_sistemi']['maks_sur_canı']}`"
            )

            if db["sefer_sistemi"]["sur_canı"] <= 0:
                db["sefer_sistemi"]["sur_seviyesi"] = max(1, db["sefer_sistemi"]["sur_seviyesi"] - 1)
                db["sefer_sistemi"]["sur_canı"] = db["sefer_sistemi"]["maks_sur_canı"]
                embed_yenilgi.description += "\n\n🚨 **SURLAR YIKILDI!** Zombiler savunma hattını yerle bir etti!"

            await kanal.send(embed=embed_yenilgi)
            haber_ekle(f"💀 Zombi baskını başarılı oldu! Surlar {alinan_hasar} hasar aldı.")

        verileri_kaydet()


# ====================================================
# VIEW SINIFLARI - DÜELLO
# ====================================================
class DuelloDavetView(discord.ui.View):
    def __init__(self, davet_eden, davet_edilen, veri_eden, veri_edilen):
        super().__init__(timeout=60)
        self.davet_eden = davet_eden
        self.davet_edilen = davet_edilen
        self.veri_eden = veri_eden
        self.veri_edilen = veri_edilen
        self.cevap_verildi = False

    @discord.ui.button(label="⚔️ Kabul Et", style=discord.ButtonStyle.danger)
    async def kabul_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.davet_edilen.id:
            await interaction.response.send_message("❌ Bu davet sana gelmedi!", ephemeral=True)
            return

        self.cevap_verildi = True
        self.clear_items()

        view = DuelloView(self.davet_eden, self.davet_edilen, self.veri_eden, self.veri_edilen)
        embed = await view.duello_durum_embed()
        embed.add_field(name="🔔 Düello Kabul Edildi!", value=f"**{self.davet_edilen.mention}** meydan okumayı kabul etti! Kılıçlar çekildi!", inline=False)

        await interaction.response.edit_message(
            content=f"⚔️ **DÜELLO BAŞLADI!** {self.davet_eden.mention} vs {self.davet_edilen.mention}",
            embed=embed,
            view=view
        )

    @discord.ui.button(label="❌ Reddet", style=discord.ButtonStyle.secondary)
    async def reddet_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.davet_edilen.id:
            await interaction.response.send_message("❌ Bu davet sana gelmedi!", ephemeral=True)
            return

        self.cevap_verildi = True
        self.clear_items()

        embed = discord.Embed(title="❌ DÜELLO REDDEDİLDİ", color=0x7F8C8D)
        embed.description = f"🛡️ **{self.davet_edilen.mention}** meydan okumayı reddetti. Düello iptal edildi."
        await interaction.response.edit_message(embed=embed, view=self)


class DuelloView(discord.ui.View):
    def __init__(self, davet_eden, davet_edilen, veri_eden, veri_edilen):
        super().__init__(timeout=300)  # 5 dk
        self.oyuncular = {
            "eden": {
                "id": str(davet_eden.id), "user": davet_eden,
                "isim": veri_eden["isim"],
                "hp": veri_eden.get("saglik", 100),
                "atak": veri_eden.get("atak", 10),
                "defans": veri_eden.get("defans", 10),
                "savunmada": False
            },
            "edilen": {
                "id": str(davet_edilen.id), "user": davet_edilen,
                "isim": veri_edilen["isim"],
                "hp": veri_edilen.get("saglik", 100),
                "atak": veri_edilen.get("atak", 10),
                "defans": veri_edilen.get("defans", 10),
                "savunmada": False
            }
        }
        self.sira = random.choice(["eden", "edilen"])
        self.tur = 1

    async def duello_durum_embed(self):
        embed = discord.Embed(title=f"⚔️ KANLI DÜELLO — TUR #{self.tur}", color=0xC0392B)
        o1 = self.oyuncular["eden"]
        o2 = self.oyuncular["edilen"]
        sira_kimde = o1['user'].mention if self.sira == "eden" else o2['user'].mention

        embed.description = (
            f"**Hamle Sırası:** {sira_kimde}\n\n"
            f"🔺 **{o1['isim']}** (Davet Eden)\n"
            f"❤️ Can: `{o1['hp']}/100` | ⚔️ Atak: `{o1['atak']}` | 🛡️ Defans: `{o1['defans']}`\n\n"
            f"🔻 **{o2['isim']}** (Davet Edilen)\n"
            f"❤️ Can: `{o2['hp']}/100` | ⚔️ Atak: `{o2['atak']}` | 🛡️ Defans: `{o2['defans']}`\n\n"
            f"⚠️ *Unutmayın: Canı 0'a düşen oyuncunun %20 ihtimalle karakteri kalıcı olarak ÖLÜR!*"
        )
        return embed

    async def hamle_yap(self, interaction: discord.Interaction, hamle_tipi):
        aktif = self.oyuncular[self.sira]
        pasif = self.oyuncular["edilen" if self.sira == "eden" else "eden"]

        if str(interaction.user.id) != aktif["id"]:
            await interaction.response.send_message("❌ Sıra sende değil, bekle!", ephemeral=True)
            return

        log_mesaj = ""

        if hamle_tipi == "saldir":
            ham_hasar = aktif["atak"] + random.randint(1, 6)
            emilen_hasar = pasif["defans"] if pasif["savunmada"] else int(pasif["defans"] / 2)
            net_hasar = max(3, ham_hasar - emilen_hasar)
            pasif["hp"] -= net_hasar
            log_mesaj = f"⚔️ **{aktif['isim']}**, rakibine sert bir darbe indirdi ve **{net_hasar}** hasar verdi!"
            pasif["savunmada"] = False

        elif hamle_tipi == "defans":
            aktif["savunmada"] = True
            log_mesaj = f"🛡️ **{aktif['isim']}**, defans pozisyonuna geçti! Bir sonraki el zırhı hasarı tam emecek."

        elif hamle_tipi == "yetenek":
            if random.random() < 0.50:
                kritik_hasar = int((aktif["atak"] * 1.8) + random.randint(5, 10))
                pasif["hp"] -= kritik_hasar
                log_mesaj = f"⚡ **{aktif['isim']}** ÖZEL YETENEK KULLANDI! Rakibin zırhını yararak **{kritik_hasar}** KRİTİK hasar vurdu!"
            else:
                log_mesaj = f"💨 **{aktif['isim']}** özel yetenek kullanmaya çalışırken ayağı kaydı ve ISKALADI!"
            pasif["savunmada"] = False

        if pasif["hp"] < 0:
            pasif["hp"] = 0

        # Düello bitti mi?
        if pasif["hp"] <= 0:
            self.clear_items()
            await interaction.response.edit_message(embed=await self.duello_durum_embed(), view=self)
            await self.bitti_protokolu(interaction.channel, aktif, pasif)
            return

        self.sira = "edilen" if self.sira == "eden" else "eden"
        self.tur += 1

        embed = await self.duello_durum_embed()
        embed.add_field(name="Son Hamle Raporu", value=log_mesaj, inline=False)
        await interaction.response.edit_message(embed=embed, view=self)

    async def bitti_protokolu(self, kanal, kazanan_bilesen, kaybeden_bilesen):
        k_id = kaybeden_bilesen["id"]
        w_id = kazanan_bilesen["id"]

        kaybeden_veri = db["sakinler"][k_id]
        kazanan_veri = db["sakinler"][w_id]
        kazanan_veri["saglik"] = kazanan_bilesen["hp"]

        # %20 ölüm riski
        zar = random.randint(1, 100)
        olum_gerceklesme_orani = 20

        sonuc_embed = discord.Embed(title="💀 DÜELLO SONUÇLANDI", color=0x2C3E50)

        if zar <= olum_gerceklesme_orani:
            # Kalıcı ölüm
            ganimet_metni = olum_protokolu(k_id, olum_sebebi="duello", kazanan_id=w_id)

            sonuc_embed.description = (
                f"🏆 **Kazanan:** <@{w_id}>\n"
                f"🩸 **Kaybeden:** <@{k_id}>\n\n"
                f"☠️ **KRİTİK DURUM:** Arka planda atılan ölüm zarı `{zar}` geldi! "
                f"**{kaybeden_bilesen['isim']}** aldığı ölümcül yaralardan dolayı sığınakta **RESMEN VEFAT ETTİ!**\n\n"
                f"💰 **YAĞMALANAN GANİMETLER:**\n"
                f"{ganimet_metni if ganimet_metni else 'Kayda değer bir eşyası yoktu.'}"
            )
            sonuc_embed.color = 0x7F8C8D

            # Ölüm ekranı
            olum_embed = discord.Embed(title="💀 HAYATIN SONA ERDİ", color=0x7F8C8D)
            olum_embed.description = (
                f"<@{k_id}> Sığınakta kanlı bir düelloda can verdin.\n\n"
                f"⚰️ Tüm eşyaların ve hurdaların rakibine yağmalandı.\n"
                f"🔄 Yeniden hayata dönmek için `/kayıt` komutunu kullan."
            )
            await kanal.send(embed=olum_embed)
            haber_ekle(f"☠️ {kaybeden_bilesen['isim']} düelloda öldü. Kazanan: {kazanan_bilesen['isim']}.")
        else:
            # Yaralı kurtuldu
            kaybeden_veri["saglik"] = 10
            tazminat = min(50, kaybeden_veri.get("cuzdan", 0))
            kaybeden_veri["cuzdan"] -= tazminat
            kazanan_veri["cuzdan"] += tazminat

            sonuc_embed.description = (
                f"🏆 **Kazanan:** <@{w_id}>\n"
                f"🩹 **Kaybeden:** <@{k_id}>\n\n"
                f"🍀 **DURUM:** Ölüm zarı `{zar}` geldi (%20'lik sınıra takılmadı). "
                f"**{kaybeden_bilesen['isim']}** ağır yaralı olarak revire kaldırıldı. Hayatta kaldı!\n"
                f"💸 **Savaş Tazminatı:** Kaybedenden `💰 {tazminat} Hurda` alındı."
            )

        verileri_kaydet()
        await kanal.send(embed=sonuc_embed)

    @discord.ui.button(label="⚔️ Saldır", style=discord.ButtonStyle.danger)
    async def saldir_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.hamle_yap(interaction, "saldir")

    @discord.ui.button(label="🛡️ Defans Yap", style=discord.ButtonStyle.primary)
    async def defans_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.hamle_yap(interaction, "defans")

    @discord.ui.button(label="⚡ Yetenek Kullan", style=discord.ButtonStyle.success)
    async def yetenek_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.hamle_yap(interaction, "yetenek")


# ====================================================
# VIEW - SEFER LOBİSİ
# ====================================================
class SeferLobisiView(discord.ui.View):
    def __init__(self, baskan_id, zorluk):
        super().__init__(timeout=60)
        self.baskan_id = baskan_id
        self.zorluk = zorluk
        self.katilimcilar = []

    @discord.ui.button(label="Sefere Katıl! ⚔️", style=discord.ButtonStyle.danger)
    async def katil_butonu(self, interaction: discord.Interaction, button: discord.ui.Button):
        u_id = str(interaction.user.id)

        if u_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Sicil kaydın yok!", ephemeral=True)
            return

        if db["sakinler"][u_id].get("durum") in ["Ölü", "Karantinada", "Hücrede"]:
            await interaction.response.send_message("❌ Mevcut durumun sefere çıkmaya müsait değil!", ephemeral=True)
            return

        if interaction.user in self.katilimcilar:
            await interaction.response.send_message("❌ Zaten lobiye katıldın!", ephemeral=True)
            return

        if len(self.katilimcilar) >= 10:
            await interaction.response.send_message("❌ Sefer mangası tamamen dolu! (Maks 10 Kişi)", ephemeral=True)
            return

        self.katilimcilar.append(interaction.user)
        await interaction.response.send_message(f"✅ Sefere katıldın! Mangadaki sıran: `{len(self.katilimcilar)}/10`")

    @discord.ui.button(label="Seferi Başlat! 🔥", style=discord.ButtonStyle.success)
    async def baslat_butonu(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.baskan_id:
            await interaction.response.send_message("❌ Orduyu sadece Belediye Başkanı dış dünyaya kaldırabilir!", ephemeral=True)
            return

        if len(self.katilimcilar) == 0:
            await interaction.response.send_message("❌ Tek başına gidemezsin, yanına en az bir asker al!", ephemeral=True)
            return

        self.stop()
        await interaction.response.send_message("⚔️ Manga toplandı! Sığınak kapıları açılıyor, dış dünyaya taarruz başladı...")


# ====================================================
# VIEW - BASKIN SAVUNMASI
# ====================================================
class BaskinSavunmaView(discord.ui.View):
    def __init__(self, baskin_gucu):
        super().__init__(timeout=120)
        self.baskin_gucu = baskin_gucu
        self.toplam_savunma_gucu = 0
        self.tıklayanlar = []

    @discord.ui.button(label="⚔️ Surlara Koş ve Müdahale Et!", style=discord.ButtonStyle.primary)
    async def mudahale_et(self, interaction: discord.Interaction, button: discord.ui.Button):
        u_id = str(interaction.user.id)

        if u_id not in db["sakinler"] or db["sakinler"][u_id].get("durum") == "Ölü":
            await interaction.response.send_message("❌ Ölüler veya kayıtsızlar sur savunmasına katılamaz!", ephemeral=True)
            return

        if u_id in self.tıklayanlar:
            await interaction.response.send_message("❌ Zaten savunma hattındasın, siperini koru!", ephemeral=True)
            return

        self.tıklayanlar.append(u_id)
        meslek = db["sakinler"][u_id].get("meslek_anahtar", "")
        taban_guc = 50 + (db["sakinler"][u_id].get("xp", 0) // 5)

        if meslek in ["muhafiz_komutani", "muhafiz", "nisanci"]:
            nihai_katki = int(taban_guc * 1.20)
            mesaj = f"🛡️ **Muhafız Gücü!** Surlara %+20 ekstra hasarla destek verdin! Katkın: `{nihai_katki}`"
        else:
            nihai_katki = int(taban_guc * 0.85)
            mesaj = f"👨‍🌾 **Sivil Seferberlik!** Köylü gücüyle kısıtlı hasar verdin. Katkın: `{nihai_katki}`"

        self.toplam_savunma_gucu += nihai_katki
        await interaction.response.send_message(mesaj)


async def setup(bot):
    await bot.add_cog(SavasCog(bot))

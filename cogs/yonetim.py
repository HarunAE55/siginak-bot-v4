"""
Cog: Yönetim & Siyaset
=====================
Komutlar:
- /aday-ol (500 akçe depozito ile başkan adayı)
- /secimi-baslat (sadece admin, 15+60 dk = 1 saat seçim)
- /yonetim (başkan paneli, sur/köy geliştirme)
- /tayin-et (başkan, 5 kadroluk atama)
- /maas-ode (başkan, tek sakin maaş)
- /meslek-maas-ode (başkan, meslek grubuna toplu maaş)
- /toplu-maas (başkan, tüm sakinlere maaş)
- /yargila (başkan, mahkeme açar)
"""

import discord
from discord import app_commands
from discord.ext import commands
import asyncio

from veritabani import (
    db, verileri_kaydet, olu_kontrolu, olum_protokolu,
    OlumEkraniView, haber_ekle
)


# ====================================================
# TAYİN EDİLEBİLİR KADROLAR
# ====================================================
TAYIN_KADROLARI = {
    "baskan_yardimcisi": {"rol_id": 1508535553434587238, "isim": "Başkan Yardımcısı"},
    "vergi_mufettisi": {"rol_id": 1508536734709973032, "isim": "Vergi Müfettişi"},
    "muhafiz_komutani": {"rol_id": 1508543542153187478, "isim": "Muhafızlar Komutanı"},
    "bas_simyaci": {"rol_id": 1508539755304845352, "isim": "Baş Simyacı"},
    "rahip": {"rol_id": 1515026155969843401, "isim": "Rahip"},
}


class YonetimCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ====================================================
    # /aday-ol
    # ====================================================
    @app_commands.command(name="aday-ol", description="[SİYASET] Sığınak Belediye Başkanlığı yarışı için adaylığınızı ve resmi vaadinizi tesciller.")
    @app_commands.describe(vaat="Sakinlere sunacağınız en önemli vaat")
    async def aday_ol(self, interaction: discord.Interaction, vaat: str):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Sicil kütüğünde kaydın yok!", ephemeral=True)
            return
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return

        sakin = db["sakinler"][u_id]

        if sakin.get("cuzdan", 0) < 500:
            await interaction.response.send_message(
                "❌ Adaylık için yeterli sermayeniz yok! Cüzdanınızda en az `500 Akçe` bulunmalıdır.",
                ephemeral=True
            )
            return

        if db["aktif_secim"]["durum"] != "adaylik_acik":
            await interaction.response.send_message(
                "❌ Şu anda aktif bir seçim dönemi veya adaylık süreci açık değil!",
                ephemeral=True
            )
            return

        if u_id in db["aktif_secim"]["adaylar"]:
            await interaction.response.send_message("❌ Zaten resmi olarak adaysınız!", ephemeral=True)
            return

        # Adaylık depozitosu
        sakin["cuzdan"] -= 500

        db["aktif_secim"]["adaylar"][u_id] = {
            "isim": sakin["isim"],
            "vaat": vaat,
            "oy_sayisi": 0
        }
        verileri_kaydet()

        embed = discord.Embed(title="👑 YENİ BELEDİYE BAŞKANI ADAYI!", color=0xF1C40F)
        embed.description = (
            f"👤 **Aday Sakin:** {interaction.user.mention}\n"
            f"📜 **Resmi Seçim Vaadi:** *\"{vaat}\"*\n\n"
            f"📢 *Sığınak idaresi adaylığını tescilledi! Seçimler başladığında oy pusulasında yerini alacak.*"
        )
        await interaction.response.send_message(embed=embed)

    # ====================================================
    # /secimi-baslat - SADECE ADMIN
    # ====================================================
    @app_commands.command(name="secimi-baslat", description="[YÖNETİM] 1 saat sürecek belediye başkanlığı seçimlerini başlatır. Sadece sunucu yöneticileri.")
    @app_commands.checks.has_permissions(administrator=True)
    async def secimi_baslat(self, interaction: discord.Interaction):
        from veritabani import admin_mi
        if not admin_mi(interaction):
            await interaction.response.send_message("❌ Bu komut sadece yetkili ekibe özeldir!", ephemeral=True)
            return
        if db["aktif_secim"]["durum"] == "kapali":
            db["aktif_secim"]["durum"] = "adaylik_acik"
            db["aktif_secim"]["adaylar"] = {}
            db["aktif_secim"]["oylar"] = {}
            verileri_kaydet()
            await interaction.response.send_message(
                "📢 **SIĞINAK YÜCE SEÇİM KURULU:** Resmi Belediye Başkanlığı adaylık süreci açılmıştır! `/aday-ol` komutuyla başvurularınızı ve vaatlerinizi sisteme işleyin. Sandıklar tam **30 dakika** sonra kurulacaktır!"
            )
            haber_ekle("📢 Belediye Başkanlığı seçim süreci başladı. 30 dakika adaylık süresi açıldı.")

            await asyncio.sleep(1800)  # 30 dk
        else:
            await interaction.response.send_message("❌ Seçim zaten devam ediyor!", ephemeral=True)
            return

        if not db["aktif_secim"]["adaylar"]:
            db["aktif_secim"]["durum"] = "kapali"
            verileri_kaydet()
            await interaction.channel.send("❌ Seçim iptal edildi! 30 dakikalık sürede hiçbir sakin başkanlığa aday olmadı.")
            return

        db["aktif_secim"]["durum"] = "oylama_aktif"
        verileri_kaydet()

        pusula_view = OyPusulasiView(db["aktif_secim"]["adaylar"])

        pusula_embed = discord.Embed(title="⚖️ SIĞINAK MERKEZİ BAŞKANLIK SEÇİM SANDIĞI", color=0x2980B9)
        pusula_text = "**Mevcut Resmi Adaylar ve Programları:**\n\n"
        for a_id, veri in db["aktif_secim"]["adaylar"].items():
            pusula_text += f"👑 **{veri['isim']}** \n• Vaadi: *\"{veri['vaat']}\"*\n\n"
        pusula_text += "⚠️ **NOT:** Oy vermek için aşağıdaki ilgili butona tıklayın. Sandıklar tam **60 dakika (2700 saniye)** sonra kapanacaktır!"
        pusula_embed.description = pusula_text

        await interaction.channel.send(embed=pusula_embed, view=pusula_view)
        haber_ekle("🗳️ Seçim sandıkları açıldı! 60 dakikalık oylama süresi başladı.")

        await asyncio.sleep(3600)  # 60 dk

        adaylar = db["aktif_secim"]["adaylar"]
        if not adaylar:
            return

        kazanan_id = max(adaylar, key=lambda k: adaylar[k]["oy_sayisi"])
        en_yuksek_oy = adaylar[kazanan_id]["oy_sayisi"]

        beraberlik_mi = list(map(lambda x: x["oy_sayisi"], adaylar.values())).count(en_yuksek_oy) > 1

        sonuc_embed = discord.Embed(title="📊 RESMİ SEÇİM SONUÇLARI AÇIKLANDI", color=0x27AE60)

        if beraberlik_mi:
            sonuc_embed.description = "⚖️ Oylar eşit çıktı! Sığınakta düzenin bozulmaması için mevcut idari mekanizma geçici olarak görevine devam ediyor."
            sonuc_embed.color = 0xE67E22
        else:
            baskan_rol_id = 1508463895692447926
            guild = interaction.guild
            yeni_baskan_uye = guild.get_member(int(kazanan_id))
            baskan_rolu = guild.get_role(baskan_rol_id)

            # Eski başkanı indir
            if baskan_rolu:
                for uye in baskan_rolu.members:
                    if uye.id != int(kazanan_id):
                        try:
                            await uye.remove_roles(baskan_rolu)
                            if str(uye.id) in db["sakinler"]:
                                db["sakinler"][str(uye.id)]["meslek_anahtar"] = "gezgin"
                                db["sakinler"][str(uye.id)]["meslek_isim"] = "Gezgin"
                        except:
                            pass

            # Yeni başkanı ata
            if yeni_baskan_uye and baskan_rolu:
                try:
                    await yeni_baskan_uye.add_roles(baskan_rolu)
                except Exception as e:
                    print(f"Rol atama hatası: {e}")

            db["sakinler"][kazanan_id]["meslek_anahtar"] = "belediye_baskani"
            db["sakinler"][kazanan_id]["meslek_isim"] = "Belediye Başkanı"

            sonuc_embed.description = (
                f"🏆 **SIĞINAĞIN YENİ BELEDİYE BAŞKANI:** {yeni_baskan_uye.mention}\n"
                f"📈 **Toplam Alınan Oy:** `{en_yuksek_oy}`\n\n"
                f"👑 Resmi `<@&{baskan_rol_id}>` rolü otomatik olarak atanmış, eski yönetimin yetkileri feshedilmiştir!"
            )
            haber_ekle(f"🏆 {db['sakinler'][kazanan_id]['isim']} belediye başkanlığına seçildi! ({en_yuksek_oy} oy)")

        db["aktif_secim"] = {"durum": "kapali", "adaylar": {}, "oylar": {}}
        verileri_kaydet()

        await interaction.channel.send(embed=sonuc_embed)

    # ====================================================
    # /yonetim - Başkan paneli
    # ====================================================
    @app_commands.command(name="yonetim", description="[BAŞKAN] Sadece aktif Belediye Başkanının sığınak altyapısını harita bütçesiyle yönetmesini sağlar.")
    async def baskan_yonetim(self, interaction: discord.Interaction):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Sığınak siciliniz yok!", ephemeral=True)
            return
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return

        if db["sakinler"][u_id].get("meslek_anahtar") != "belediye_baskani":
            await interaction.response.send_message(
                "❌ Bu paneli tetikleme yetkisi sadece resmi sığınak Belediye Başkanına aittir!",
                ephemeral=True
            )
            return

        embed = discord.Embed(title="👑 SIĞINAK YÜCE KABİNE VE ALTYAPI KONTROL MERKEZİ", color=0xF1C40F)
        embed.description = (
            f"**Mevcut Belediye Başkanı:** {interaction.user.mention}\n"
            f"--- \n"
            f"💰 **Sığınak Ortak Kasası (Vergiler):** `{db['sistem_ayarlari']['KASA_AKÇE_PLACEHOLDER']} Akçe`\n"
            f"🧱 **Mevcut Sur Savunma Seviyesi:** `🛡️ Seviye {db['sistem_ayarlari']['sur_seviyesi']}`\n"
            f"🏡 **Mevcut Köy Yapılaşma Seviyesi:** `🏛️ Seviye {db['sistem_ayarlari']['koy_seviyesi']}`\n\n"
            f"⚠️ *Aşağıdaki butonları kullanarak sığınak bütçesini halk yararına harcayabilirsiniz.*"
        )

        view = BaskanPaneliView(u_id)
        await interaction.response.send_message(embed=embed, view=view)

    # ====================================================
    # /tayin-et - Başkan kadro atar
    # ====================================================
    @app_commands.command(name="tayin-et", description="[BAŞKAN] Sığınaktaki kritik kabine unvanlarına ve rollerine resmi atama gerçekleştirir.")
    @app_commands.describe(hedef_sakin="Atama yapılacak üye", unvan="Atanacak resmi makam pozisyonu")
    @app_commands.choices(unvan=[
        app_commands.Choice(name="Müsteşar / Başkan Yardımcısı", value="baskan_yardimcisi"),
        app_commands.Choice(name="Vergi Müfettişi", value="vergi_mufettisi"),
        app_commands.Choice(name="Muhafızlar Komutanı", value="muhafiz_komutani"),
        app_commands.Choice(name="Baş Simyacı", value="bas_simyaci"),
        app_commands.Choice(name="Baş Doktor", value="bas_doktor"),
        app_commands.Choice(name="Sığınak Rahibi", value="rahip")
    ])
    async def tayin_et(self, interaction: discord.Interaction, hedef_sakin: discord.Member, unvan: str):
        u_id = str(interaction.user.id)
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return

        if db["sakinler"].get(u_id, {}).get("meslek_anahtar") != "belediye_baskani":
            await interaction.response.send_message(
                "❌ Atama kararnamesi yayınlama yetkiniz yok, sadece başkan yapabilir!",
                ephemeral=True
            )
            return

        if unvan not in TAYIN_KADROLARI:
            await interaction.response.send_message("❌ Geçersiz unvan!", ephemeral=True)
            return

        kadro = TAYIN_KADROLARI[unvan]
        await self.kabine_tayin_motoru(interaction, hedef_sakin, kadro["rol_id"], unvan, kadro["isim"])

    async def kabine_tayin_motoru(self, interaction: discord.Interaction, hedef_uye: discord.Member, rol_id: int, m_anahtar: str, m_isim: str):
        guild = interaction.guild
        hedef_rol = guild.get_role(rol_id)

        if not hedef_rol:
            await interaction.response.send_message("❌ Atanacak resmi rol sunucuda bulunamadı!", ephemeral=True)
            return

        h_id = str(hedef_uye.id)
        if h_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Atamak istediğiniz kişi sığınak kütüğüne kayıtlı değil!", ephemeral=True)
            return

        # Eski unvan sahibinden rolü geri al
        for uye in hedef_rol.members:
            try:
                await uye.remove_roles(hedef_rol)
                if str(uye.id) in db["sakinler"]:
                    db["sakinler"][str(uye.id)]["meslek_anahtar"] = "gezgin"
                    db["sakinler"][str(uye.id)]["meslek_isim"] = "Gezgin"
            except:
                pass

        # Yeni unvan sahibine rolü ata
        try:
            await hedef_uye.add_roles(hedef_rol)
            db["sakinler"][h_id]["meslek_anahtar"] = m_anahtar
            db["sakinler"][h_id]["meslek_isim"] = m_isim
            verileri_kaydet()

            embed = discord.Embed(title="📜 RESMİ SIĞINAK ATAMA KARARNAMESİ", color=0x2ECC71)
            embed.description = (
                f"👑 **Belediye Başkanı {interaction.user.mention}** yayınladığı kararname ile;\n\n"
                f"{hedef_uye.mention} sakininin sığınak bünyesinde resmi olarak `<@&{rol_id}>` (**{m_isim}**) kadrosuna tayin edilmesini uygun görmüştür!"
            )
            await interaction.response.send_message(embed=embed)
            haber_ekle(f"📜 {db['sakinler'][h_id]['isim']} {m_isim} olarak atandı.")
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Rol atama sırasında Discord yetki hatası oluştu: {e}",
                ephemeral=True
            )

    # ====================================================
    # /maas-ode - Tek sakin maaş
    # ====================================================
    @app_commands.command(name="maas-ode", description="[BAŞKAN] Sığınak kasasından belirli bir sakine esnek miktarda maaş/ikramiye ödemesi yapar.")
    @app_commands.describe(hedef_sakin="Ödeme yapılacak sakin", miktar="Dağıtılacak akçe miktarı")
    async def maas_ode(self, interaction: discord.Interaction, hedef_sakin: discord.Member, miktar: int):
        u_id = str(interaction.user.id)
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return
        h_id = str(hedef_sakin.id)

        if db["sakinler"].get(u_id, {}).get("meslek_anahtar") != "belediye_baskani":
            await interaction.response.send_message("❌ Sığınak darphanesini yönetme yetkisi sadece Belediye Başkanına aittir!", ephemeral=True)
            return

        if miktar <= 0:
            await interaction.response.send_message("❌ Ödenecek maaş miktarı pozitif bir sayı olmalıdır!", ephemeral=True)
            return

        if db["sistem_ayarlari"]["KASA_AKÇE_PLACEHOLDER"] < miktar:
            await interaction.response.send_message(
                f"❌ Sığınak ortak kasasında yeterli bütçe yok! Mevcut Kasa: `{db['sistem_ayarlari']['KASA_AKÇE_PLACEHOLDER']}` Akçe.",
                ephemeral=True
            )
            return

        if h_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Ödeme yapılmak istenen kişi sığınak kütüğünde kayıtlı değil!", ephemeral=True)
            return

        db["sistem_ayarlari"]["KASA_AKÇE_PLACEHOLDER"] -= miktar
        db["sakinler"][h_id]["cuzdan"] += miktar
        verileri_kaydet()

        embed = discord.Embed(title="💸 RESMİ MAAŞ VE İKRAMİYE BORDROSU", color=0x2ECC71)
        embed.description = (
            f"👑 **Makam:** Sığınak Belediye Başkanlığı\n"
            f"👤 **Ödeme Yapılan:** {hedef_sakin.mention}\n"
            f"🪙 **Aktarılan Tutar:** `{miktar} Akçe`\n"
            f"--- \n"
            f"📉 **Kalan Sığınak Kasası:** `{db['sistem_ayarlari']['KASA_AKÇE_PLACEHOLDER']} Akçe`"
        )
        await interaction.response.send_message(embed=embed)

    # ====================================================
    # /meslek-maas-ode - Meslek grubuna toplu maaş
    # ====================================================
    @app_commands.command(name="meslek-maas-ode", description="[BAŞKAN] Belirli bir meslek grubundaki tüm çalışanlara kasadan toplu maaş yatırır.")
    @app_commands.describe(meslek_grubu="Maaş ödenecek meslek grubu", miktar="Kişi başı akçe miktarı")
    @app_commands.choices(meslek_grubu=[
        app_commands.Choice(name="Muhafız Birliği", value="muhafiz"),
        app_commands.Choice(name="Sağlık Ekibi", value="saglik"),
        app_commands.Choice(name="Üreticiler (Çiftçi/Demirci/Maden vb.)", value="ureticiler"),
        app_commands.Choice(name="İdari Kadro (Müfettiş/Yardımcı)", value="idari")
    ])
    async def meslek_maas_ode(self, interaction: discord.Interaction, meslek_grubu: str, miktar: int):
        u_id = str(interaction.user.id)
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return
        if db["sakinler"].get(u_id, {}).get("meslek_anahtar") != "belediye_baskani":
            await interaction.response.send_message("❌ Bu komut sadece Belediye Başkanına özeldir!", ephemeral=True)
            return

        if miktar <= 0:
            await interaction.response.send_message("❌ Ödenecek miktar geçersiz!", ephemeral=True)
            return

        grup_eslesme = {
            "muhafiz": ["muhafiz_komutani", "muhafiz", "nisanci", "izci"],
            "saglik": ["bas_simyaci", "simyaci", "bas_doktor", "doktor", "karantinaci"],
            "idari": ["baskan_yardimcisi", "vergi_mufettisi"],
            "ureticiler": ["ciftci", "coban", "demirci", "oduncu", "madenci", "tuccar", "degirmenci", "hanci"]
        }

        hedef_anahtarlar = grup_eslesme.get(meslek_grubu, [])
        if not hedef_anahtarlar:
            await interaction.response.send_message("❌ Geçersiz meslek grubu!", ephemeral=True)
            return

        maas_alacaklar = []
        for s_id, veri in db["sakinler"].items():
            if veri.get("meslek_anahtar") in hedef_anahtarlar and veri.get("durum") != "Ölü":
                maas_alacaklar.append(s_id)

        if not maas_alacaklar:
            await interaction.response.send_message("❌ Sığınakta bu grupta çalışan aktif hiçbir sakin bulunamadı!", ephemeral=True)
            return

        toplam_maliyet = miktar * len(maas_alacaklar)

        if db["sistem_ayarlari"]["KASA_AKÇE_PLACEHOLDER"] < toplam_maliyet:
            await interaction.response.send_message(
                f"❌ Kasada toplu ödeme için yeterli akçe yok! Gereken: `{toplam_maliyet}`, Kasada Olan: `{db['sistem_ayarlari']['KASA_AKÇE_PLACEHOLDER']}`",
                ephemeral=True
            )
            return

        db["sistem_ayarlari"]["KASA_AKÇE_PLACEHOLDER"] -= toplam_maliyet
        rapor_listesi = []
        for s_id in maas_alacaklar:
            db["sakinler"][s_id]["cuzdan"] += miktar
            rapor_listesi.append(f"• <@{s_id}> (+{miktar} Akçe)")

        verileri_kaydet()

        embed = discord.Embed(title="📊 TOPLU MESLEK GRUBU MAAŞ ÖDEMESİ", color=0x3498DB)
        embed.description = (
            f"📢 **Belediye Başkanı** {interaction.user.mention}, belirli bir iş koluna toplu bütçe dağıtımı yaptı!\n\n"
            f"💼 **Ödeme Yapılan Grup:** `{meslek_grubu.upper()}`\n"
            f"👥 **Maaş Alan Toplam Kişi:** `{len(maas_alacaklar)} Sakin`\n"
            f"💰 **Kişi Başı Ödenen:** `{miktar} Akçe`\n"
            f"📉 **Kasadan Çıkan Toplam Bütçe:** `{toplam_maliyet} Akçe`\n"
            f"📦 **Kalan Ortak Kasa:** `{db['sistem_ayarlari']['KASA_AKÇE_PLACEHOLDER']} Akçe`\n\n"
            f"**Ödeme Yapılan Bazı Sakinler:**\n" + "\n".join(rapor_listesi[:10])
        )
        await interaction.response.send_message(embed=embed)

    # ====================================================
    # /toplu-maas - Tüm sakinlere maaş
    # ====================================================
    @app_commands.command(name="toplu-maas", description="[BAŞKAN] Sığınaktaki tüm aktif ve hayatta olan sakinlere kasadan eşit miktarda genel maaş dağıtır.")
    @app_commands.describe(miktar="Herkese tek tek dağıtılacak hayatta kalma maaşı")
    async def toplu_maas(self, interaction: discord.Interaction, miktar: int):
        u_id = str(interaction.user.id)
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return
        if db["sakinler"].get(u_id, {}).get("meslek_anahtar") != "belediye_baskani":
            await interaction.response.send_message("❌ Devlet hazinesini toplu dağıtma yetkisi sadece başkana aittir!", ephemeral=True)
            return

        if miktar <= 0:
            await interaction.response.send_message("❌ Miktar sıfırdan büyük olmalıdır!", ephemeral=True)
            return

        hayatta_olanlar = [s_id for s_id, veri in db["sakinler"].items() if veri.get("durum") != "Ölü"]

        if not hayatta_olanlar:
            await interaction.response.send_message("❌ Sığınakta hayatta kimse yok?!", ephemeral=True)
            return

        toplam_maliyet = miktar * len(hayatta_olanlar)

        if db["sistem_ayarlari"]["KASA_AKÇE_PLACEHOLDER"] < toplam_maliyet:
            await interaction.response.send_message(
                f"❌ Genel maaş dağıtımı için kasada yeterli bütçe yok! Gereken: `{toplam_maliyet}`, Kasada Olan: `{db['sistem_ayarlari']['KASA_AKÇE_PLACEHOLDER']}`",
                ephemeral=True
            )
            return

        db["sistem_ayarlari"]["KASA_AKÇE_PLACEHOLDER"] -= toplam_maliyet
        for s_id in hayatta_olanlar:
            db["sakinler"][s_id]["cuzdan"] += miktar

        verileri_kaydet()

        embed = discord.Embed(title="🏛️ SIĞINAK GENEL HALK MAAŞI ÖDEMESİ", color=0x9B59B6)
        embed.description = (
            f"👑 **Belediye Başkanı** {interaction.user.mention} sığınaktaki tüm halka **Genel Refah Maaşı** dağıttı!\n\n"
            f"👥 **Ödeme Yapılan Nüfus:** `{len(hayatta_olanlar)} Sakin`\n"
            f"🪙 **Kişi Başı Dağıtılan:** `{miktar} Akçe`\n"
            f"🔥 **Kasadan Karşılanan Toplam:** `{toplam_maliyet} Akçe`\n"
            f"💰 **Yeni Ortak Kasa Bakiyesi:** `{db['sistem_ayarlari']['KASA_AKÇE_PLACEHOLDER']} Akçe`"
        )
        await interaction.response.send_message(embed=embed)

    # ====================================================
    # /yargila - Başkan mahkeme açar
    # ====================================================
    @app_commands.command(name="yargila", description="[BAŞKAN] Sığınak kanunlarına karşı gelen bir sakini resmi başkanlık mahkemesine çıkarır.")
    @app_commands.describe(hedef_sakin="Mahkemeye çıkarılacak sanık", suc_nedeni="İsnat edilen suç ve gerekçe")
    async def yargila(self, interaction: discord.Interaction, hedef_sakin: discord.Member, suc_nedeni: str):
        u_id = str(interaction.user.id)
        olu_kontrol = olu_kontrolu(u_id)
        if olu_kontrol:
            await interaction.response.send_message(olu_kontrol, ephemeral=True)
            return
        s_id = str(hedef_sakin.id)

        if db["sakinler"].get(u_id, {}).get("meslek_anahtar") != "belediye_baskani":
            await interaction.response.send_message("❌ Mahkeme açma yetkisi sadece Belediye Başkanına aittir!", ephemeral=True)
            return

        if s_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Sanık olarak seçtiğiniz kişi sığınak kütüğünde kayıtlı değil!", ephemeral=True)
            return

        if db["sakinler"][s_id].get("durum") == "Ölü":
            await interaction.response.send_message("❌ Ölü bir sakini mahkemeye çıkaramazsınız!", ephemeral=True)
            return

        embed = discord.Embed(title="⚖️ SIĞINAK MERKEZİ ADALET MAHKEMESİ AÇILDI", color=0x9E9E9E)
        embed.description = (
            f"👑 **Yargıç / Başkan:** {interaction.user.mention}\n"
            f"👤 **Yargılanan Sanık:** {hedef_sakin.mention}\n"
            f"📜 **Gerekçe ve Suç Nedeni:** *\"{suc_nedeni}\"*\n\n"
            f"⚠️ **SAYIN BAŞKAN:** Aşağıdaki panelden davayı demokratik olarak halk oylamasına sunabilir veya doğrudan idam/sürgün infazı vererek tiranlaşabilirsiniz!"
        )

        view = MutlakHukumView(u_id, hedef_sakin, suc_nedeni)
        await interaction.response.send_message(embed=embed, view=view)


# ====================================================
# VIEW - OY PUSULASI
# ====================================================
class OyPusulasiView(discord.ui.View):
    def __init__(self, adaylar_verisi):
        super().__init__(timeout=2700)
        self.adaylar_verisi = adaylar_verisi
        for a_id, veri in self.adaylar_verisi.items():
            self.add_item(OyButonu(label=f"🗳️ {veri['isim']}", custom_id=f"oy_{a_id}", aday_id=a_id))


class OyButonu(discord.ui.Button):
    def __init__(self, label, custom_id, aday_id):
        super().__init__(label=label, style=discord.ButtonStyle.primary, custom_id=custom_id)
        self.aday_id = aday_id

    async def callback(self, interaction: discord.Interaction):
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"]:
            await interaction.response.send_message("❌ Sığınak dışından kimse oy kullanamaz!", ephemeral=True)
            return

        if u_id in db["aktif_secim"]["oylar"]:
            await interaction.response.send_message("❌ Zaten oy kullandınız! Hakkınız tektir.", ephemeral=True)
            return

        db["aktif_secim"]["oylar"][u_id] = self.aday_id
        db["aktif_secim"]["adaylar"][self.aday_id]["oy_sayisi"] += 1
        verileri_kaydet()

        await interaction.response.send_message(
            f"✔️ Oyun işlendi. Desteklenen Aday: **{db['aktif_secim']['adaylar'][self.aday_id]['isim']}**",
            ephemeral=True
        )


# ====================================================
# VIEW - BAŞKAN PANELİ
# ====================================================
class BaskanPaneliView(discord.ui.View):
    def __init__(self, baskan_id):
        super().__init__(timeout=180)
        self.baskan_id = baskan_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) != self.baskan_id:
            await interaction.response.send_message("❌ Sen Belediye Başkanı değilsin, bu devlet sırlarına erişemezsin!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🧱 Suru Geliştir (250 Akçe)", style=discord.ButtonStyle.danger)
    async def sur_gelistir_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        maliyet = 250
        if db["sistem_ayarlari"]["KASA_AKÇE_PLACEHOLDER"] < maliyet:
            await interaction.response.send_message("❌ Sığınak ortak kasasında yeterli akçe yok!", ephemeral=True)
            return

        db["sistem_ayarlari"]["KASA_AKÇE_PLACEHOLDER"] -= maliyet
        db["sistem_ayarlari"]["sur_seviyesi"] += 1
        verileri_kaydet()

        embed = discord.Embed(title="🏗️ ALTYAPI VE SUR GELİŞTİRME RAPORU", color=0xE74C3C)
        embed.description = (
            f"🧱 **Sığınak Surları Güçlendirildi!**\n"
            f"• Yeni Sur Seviyesi: `Seviye {db['sistem_ayarlari']['sur_seviyesi']}`\n"
            f"• Kalan Ortak Kasa: `{db['sistem_ayarlari']['KASA_AKÇE_PLACEHOLDER']} Akçe`"
        )
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="🏡 Köyü Geliştir (300 Akçe)", style=discord.ButtonStyle.success)
    async def koy_gelistir_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        maliyet = 300
        if db["sistem_ayarlari"]["KASA_AKÇE_PLACEHOLDER"] < maliyet:
            await interaction.response.send_message("❌ Sığınak ortak kasasında yeterli akçe yok!", ephemeral=True)
            return

        db["sistem_ayarlari"]["KASA_AKÇE_PLACEHOLDER"] -= maliyet
        db["sistem_ayarlari"]["koy_seviyesi"] += 1
        verileri_kaydet()

        embed = discord.Embed(title="🏛️ KÖY BİNALARI MODERNİZASYON RAPORU", color=0x2ECC71)
        embed.description = (
            f"🏡 **Köy Binaları ve Ambarlar Geliştirildi!**\n"
            f"• Yeni Köy Seviyesi: `Seviye {db['sistem_ayarlari']['koy_seviyesi']}`\n"
            f"• Kalan Ortak Kasa: `{db['sistem_ayarlari']['KASA_AKÇE_PLACEHOLDER']} Akçe`"
        )
        await interaction.response.send_message(embed=embed)


# ====================================================
# VIEW - MUTLAK HÜKÜM
# ====================================================
class MutlakHukumView(discord.ui.View):
    def __init__(self, baskan_id, sanik_uye, suc_nedeni):
        super().__init__(timeout=60)
        self.baskan_id = baskan_id
        self.sanik_uye = sanik_uye
        self.suc_nedeni = suc_nedeni

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) != self.baskan_id:
            await interaction.response.send_message("❌ Mutlak hüküm verme yetkisi sadece Belediye Başkanına aittir!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="👥 Köy Oylamasına Sun", style=discord.ButtonStyle.primary)
    async def koye_sun_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        s_id = str(self.sanik_uye.id)
        embed = discord.Embed(title="⚖️ SIĞINAK HALK MAHKEMESİ KURULDU", color=0x34495E)
        embed.description = (
            f"📢 **Sanık:** {self.sanik_uye.mention}\n"
            f"📜 **İsnat Edilen Suç:** *\"{self.suc_nedeni}\"*\n\n"
            f"⚠️ **KÖY HALKININ DİKKATİNE:** Belediye başkanı bu davayı sığınak jürisinin takdirine bıraktı! "
            f"Aşağıdaki butonları kullanarak **2 dakika** içinde hükmünüzü verin!"
        )

        view = MahkemeOylamaView(s_id)
        await interaction.response.send_message(embed=embed, view=view)
        self.stop()

        await asyncio.sleep(120)

        toplam_suclu = len(view.suclu_oylar)
        toplam_sucsuz = len(view.sucsuz_oylar)

        sonuc_embed = discord.Embed(title="⚖️ HALK MAHKEMESİ KARARI AÇIKLANDI", color=0x7F8C8D)

        if toplam_suclu > toplam_sucsuz:
            db["sakinler"][s_id]["durum"] = "Sürgün"
            db["mahkeme_kayitlari"]["toplam_surgun"] += 1
            verileri_kaydet()

            sonuc_embed.title = "🚨 JÜRİ KARARI: SANIK SUÇLU BULUNDU!"
            sonuc_embed.color = 0xD35400
            sonuc_embed.description = (
                f"⚖️ Oylama sonucu sığınak halkı `{toplam_suclu}` oyla {self.sanik_uye.mention} sakini suçlu buldu!\n\n"
                f"🚫 **Hüküm:** Sanık sığınaktan **SÜRGÜN** edilmiştir!"
            )
            haber_ekle(f"⚖️ {db['sakinler'][s_id]['isim']} halk oylamasıyla sürgün edildi.")
        else:
            sonuc_embed.title = "🕊️ JÜRİ KARARI: SANIK BERAAT ETTİ!"
            sonuc_embed.color = 0x2ECC71
            sonuc_embed.description = (
                f"⚖️ Oylama neticesinde sığınak halkı `{toplam_sucsuz}` oyla masumluktan yana karar verdi!\n\n"
                f"✔️ {self.sanik_uye.mention} üzerindeki tüm idari suçlamalar düşmüş, beraat tescillenmiştir!"
            )

        await interaction.channel.send(embed=sonuc_embed)

    @discord.ui.button(label="💀 Mutlak İdam İnfazı (Tiranlık Riski)", style=discord.ButtonStyle.danger)
    async def mutlak_idam_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        s_id = str(self.sanik_uye.id)

        ganimet_metni = olum_protokolu(s_id, olum_sebebi="diger")

        itibar_kaybi = 300
        db["sistem_ayarlari"]["KASA_AKÇE_PLACEHOLDER"] = max(0, db["sistem_ayarlari"].get("KASA_AKÇE_PLACEHOLDER", 0) - itibar_kaybi)
        db["mahkeme_kayitlari"]["toplam_idam"] += 1

        try:
            await self.sanik_uye.edit(roles=[])
        except:
            pass

        embed = discord.Embed(title="☠️ TİRANIN GAZABI: YARGISIZ İNFAZ!", color=0xC0392B)
        embed.description = (
            f"👑 **Belediye Başkanı {interaction.user.mention}** adalet terazisini hiçe saydı!\n\n"
            f"💀 {self.sanik_uye.mention} isimli sakini halka sormadan **İDAM ETTİ!**\n"
            f"🚨 **TİRANLIK RİSKİ:** Toplumsal İtibar sarsıldı, kasadan `{itibar_kaybi} Akçe` tazminat eksildi!\n\n"
            f"📦 **Miras Aktarımı:**\n"
            f"{ganimet_metni if ganimet_metni else 'Aktarılacak bir şey kalmamıştı.'}"
        )
        await interaction.response.send_message(embed=embed)

        olum_embed = discord.Embed(title="💀 HAYATIN SONA ERDİ", color=0x7F8C8D)
        olum_embed.description = (
            f"{self.sanik_uye.mention} İdam edilerek can verdin.\n\n"
            f"⚰️ Eşyaların sığınak kasasına aktarıldı.\n"
            f"🔄 Yeniden hayata dönmek için `/kayit` komutunu kullan."
        )
        await interaction.channel.send(embed=olum_embed, view=OlumEkraniView(self.sanik_uye))
        haber_ekle(f"☠️ {db['sakinler'][s_id]['isim']} yargısız infazla idam edildi! Tiranlık tırmanışta.")
        self.stop()

    @discord.ui.button(label="🧳 Mutlak Sürgün Et (Tiranlık Riski)", style=discord.ButtonStyle.secondary)
    async def mutlak_surgun_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        s_id = str(self.sanik_uye.id)

        db["sakinler"][s_id]["durum"] = "Sürgün"
        itibar_kaybi = 150
        db["sistem_ayarlari"]["KASA_AKÇE_PLACEHOLDER"] = max(0, db["sistem_ayarlari"].get("KASA_AKÇE_PLACEHOLDER", 0) - itibar_kaybi)
        db["mahkeme_kayitlari"]["toplam_surgun"] += 1
        verileri_kaydet()

        embed = discord.Embed(title="🧳 İDARİ SÜRGÜN KARARNAMESİ YAYINLANDI", color=0xD35400)
        embed.description = (
            f"👑 **Belediye Başkanı {interaction.user.mention}** yetkilerini kullanarak bir kararname çıkardı!\n\n"
            f"🚪 {self.sanik_uye.mention}, sığınak meclisine danışılmadan **SÜRGÜN EDİLDİ!**\n\n"
            f"⚠️ **TOPLUMSAL TEPKİ:** Kasadan `{itibar_kaybi} Akçe` dağıtıldı!"
        )
        await interaction.response.send_message(embed=embed)
        haber_ekle(f"🧳 {db['sakinler'][s_id]['isim']} idari kararnameden sürgün edildi.")
        self.stop()


class MahkemeOylamaView(discord.ui.View):
    def __init__(self, sanik_id):
        super().__init__(timeout=120)
        self.sanik_id = sanik_id
        self.suclu_oylar = set()
        self.sucsuz_oylar = set()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        u_id = str(interaction.user.id)
        if u_id not in db["sakinler"] or db["sakinler"][u_id].get("durum") == "Ölü":
            await interaction.response.send_message("❌ Sığınak dışından veya mezarlıktan kimse jüri olamaz!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="⚖️ SUÇLU", style=discord.ButtonStyle.danger, custom_id="juri_suclu")
    async def suclu_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        u_id = str(interaction.user.id)
        if u_id in self.sucsuz_oylar:
            self.sucsuz_oylar.remove(u_id)
        self.suclu_oylar.add(u_id)
        await interaction.response.send_message("🗳️ Suçlu oyunuz işlendi.", ephemeral=True)

    @discord.ui.button(label="🕊️ SUÇSUZ", style=discord.ButtonStyle.success, custom_id="juri_sucsuz")
    async def sucsuz_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        u_id = str(interaction.user.id)
        if u_id in self.suclu_oylar:
            self.suclu_oylar.remove(u_id)
        self.sucsuz_oylar.add(u_id)
        await interaction.response.send_message("🗳️ Masumiyet oyunuz işlendi.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(YonetimCog(bot))

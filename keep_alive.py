"""
Sığınak Bot - Keep Alive Web Server
===================================
Render'ın ücretsiz tier'ında botun uykuya geçmesini önlemek için
küçük bir HTTP sunucusu çalıştırır. UptimeRobot ile 5 dk'da bir
ping atılarak bot 7/24 canlı tutulur.
"""

from flask import Flask
from threading import Thread
import logging

# Flask loglarını sustur (bot loglarını temiz tutmak için)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask('')


@app.route('/')
def home():
    """Ana endpoint - botun canlı olduğunu döndürür"""
    return "🤖 Sığınak Bot çevrimiçi! Veba seni bulmadan sen onu bul."


@app.route('/health')
def health():
    """Health check endpoint - Render health check için"""
    return {"status": "alive", "bot": "SiginakRP", "version": "5.5"}, 200


def run():
    """Flask sunucusunu başlatır"""
    app.run(host='0.0.0.0', port=8080)


def keep_alive():
    """Keep-alive sunucusunu ayrı bir thread'de başlatır"""
    t = Thread(target=run, daemon=True)
    t.start()
    print("🌐 Keep-alive sunucusu 8080 portunda başlatıldı.")

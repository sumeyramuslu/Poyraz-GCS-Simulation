"""
simulasyon/sahte_sunucu.py
===========================
KİŞİ 6 — Yarışma Sunucusu Simülatörü
"""
from __future__ import annotations

import random
import time
import threading
from datetime import datetime, timezone

from flask import Flask, jsonify, request

from core.config import Config

app = Flask(__name__)

_giris_yapan_ipler: set[str] = set()
_son_telemetri_zamani: dict[str, float] = {}   
_hss_aktif = False   
_lock = threading.Lock() # Thread güvenliği eklendi

_KULLANICI_ADI = "test_takim"
_SIFRE = "test_sifre"
_TAKIM_NO = 42

def _kimlik_bilgilerini_yukle() -> None:
    global _KULLANICI_ADI, _SIFRE, _TAKIM_NO
    try:
        cfg = Config()
        _KULLANICI_ADI = cfg.sunucu_kullanici()
        _SIFRE = cfg.sunucu_sifre()
        _TAKIM_NO = cfg.takim_no()
    except FileNotFoundError:
        pass

def _sunucu_saati() -> dict:
    n = datetime.now(timezone.utc)
    return {
        "gun": n.day,
        "saat": n.hour,
        "dakika": n.minute,
        "saniye": n.second,
        "milisaniye": n.microsecond // 1000,
    }

def _kimlik_dogrula():
    with _lock:
        if request.remote_addr not in _giris_yapan_ipler:
            return jsonify({"hata": "401 Kimliksiz Erişim Denemesi"}), 401
    return None

@app.route("/api/sunucusaati", methods=["GET"])
def sunucusaati():
    return jsonify(_sunucu_saati()), 200

@app.route("/api/giris", methods=["POST"])
def giris():
    veri = request.get_json(silent=True)
    if not veri or "kadi" not in veri or "sifre" not in veri:
        return "", 204

    if veri.get("kadi") == _KULLANICI_ADI and veri.get("sifre") == _SIFRE:
        with _lock:
            _giris_yapan_ipler.add(request.remote_addr)
        return jsonify(_TAKIM_NO), 200

    return jsonify({"hata_kodu": 400, "mesaj": "Kullanıcı adı veya şifre hatalı"}), 400

_ZORUNLU_TELEMETRI_ALANLARI = [
    "takim_numarasi", "iha_enlem", "iha_boylam", "iha_irtifa", "iha_dikilme",
    "iha_yonelme", "iha_yatis", "iha_hiz", "iha_batarya", "iha_otonom",
    "iha_kilitlenme", "hedef_merkez_X", "hedef_merkez_Y", "hedef_genislik",
    "hedef_yukseklik", "gps_saati",
]

_MIN_TELEMETRI_ARALIGI_SN = 0.5

_SAHTE_RAKIPLER = {
    5: (40.1000, 29.2000),
    7: (40.1050, 29.1950),
}

def _telemetri_gecerli_mi(veri: dict) -> bool:
    if not all(alan in veri for alan in _ZORUNLU_TELEMETRI_ALANLARI):
        return False
    try:
        if not (-90 <= veri["iha_dikilme"] <= 90):
            return False
        if not (0 <= veri["iha_yonelme"] <= 360):
            return False
        if not (-90 <= veri["iha_yatis"] <= 90):
            return False
    except TypeError:
        return False
    gps = veri.get("gps_saati")
    if not isinstance(gps, dict) or not all(k in gps for k in ("saat", "dakika", "saniye", "milisaniye")):
        return False
    return True

def _sahte_rakip_konumlari(kendi_takim_no) -> list:
    rakipler = []
    for tno, (lat0, lon0) in _SAHTE_RAKIPLER.items():
        if tno == kendi_takim_no: continue
        rakipler.append({
            "takim_numarasi": tno,
            "iha_enlem": round(lat0 + random.uniform(-0.0006, 0.0006), 7),
            "iha_boylam": round(lon0 + random.uniform(-0.0006, 0.0006), 7),
            "iha_irtifa": round(random.uniform(80, 150), 1),
            "iha_dikilme": round(random.uniform(-10, 10), 1),
            "iha_yonelme": round(random.uniform(0, 360), 1),
            "iha_yatis": round(random.uniform(-20, 20), 1),
            "iha_hiz": round(random.uniform(15, 30), 1), # iha_hizi hatasi duzeltildi
            "zaman_farki": random.randint(20, 500),
        })
    return rakipler

@app.route("/api/telemetri_gonder", methods=["POST"])
def telemetri_gonder():
    hata = _kimlik_dogrula()
    if hata: return hata

    ip = request.remote_addr
    simdi = time.time()
    
    with _lock:
        son = _son_telemetri_zamani.get(ip)
        if son is not None and (simdi - son) < _MIN_TELEMETRI_ARALIGI_SN:
            return "3", 400
        _son_telemetri_zamani[ip] = simdi

    veri = request.get_json(silent=True)
    if not veri: return "", 204

    if not _telemetri_gecerli_mi(veri):
        return jsonify({"hata_kodu": 400, "mesaj": "Telemetri paketi hatalı"}), 400

    # HSS İhlal Simülasyonu
    if _hss_aktif:
        for hss in _SAHTE_HSS_LISTESI:
            dx = (veri["iha_enlem"] - hss["hssEnlem"]) * 111000
            dy = (veri["iha_boylam"] - hss["hssBoylam"]) * 111000
            mesafe = (dx**2 + dy**2)**0.5
            if mesafe <= hss["hssYaricap"]:
                print(f"\n[SahteSunucu] [CEZA] Takım {veri['takim_numarasi']} HSS bölgesinde! Mesafe: {mesafe:.1f}m / {hss['hssYaricap']}m")

    cevap = {
        "sunucusaati": _sunucu_saati(),
        "konumBilgileri": _sahte_rakip_konumlari(veri.get("takim_numarasi")),
    }
    return jsonify(cevap), 200

@app.route("/api/kilitlenme_bilgisi", methods=["POST"])
def kilitlenme_bilgisi():
    hata = _kimlik_dogrula()
    if hata: return hata
    veri = request.get_json(silent=True)
    if not veri or "kilitlenmeBitisZamani" not in veri or "otonom_kilitlenme" not in veri:
        return "", 204
    return jsonify({"mesaj": "Kilitlenme bilgisi alındı"}), 200

@app.route("/api/kamikaze_bilgisi", methods=["POST"])
def kamikaze_bilgisi():
    hata = _kimlik_dogrula()
    if hata: return hata
    veri = request.get_json(silent=True)
    zorunlu = ("kamikazeBaslangicZamani", "kamikazeBitisZamani", "qrMetni")
    if not veri or not all(alan in veri for alan in zorunlu):
        return "", 204
    return jsonify({"mesaj": "Kamikaze bilgisi alındı"}), 200

@app.route("/api/qr_koordinati", methods=["GET"])
def qr_koordinati():
    hata = _kimlik_dogrula()
    if hata: return hata
    return jsonify({"qrEnlem": 41.51238882, "qrBoylam": 36.11935778}), 200

_SAHTE_HSS_LISTESI = [
    {"id": 0, "hssEnlem": 40.23260922, "hssBoylam": 29.00573015, "hssYaricap": 50},
    {"id": 1, "hssEnlem": 40.23351019, "hssBoylam": 28.99976492, "hssYaricap": 50},
    {"id": 2, "hssEnlem": 40.23105297, "hssBoylam": 29.00744677, "hssYaricap": 75},
]

@app.route("/api/hss_koordinatlari", methods=["GET"])
def hss_koordinatlari():
    hata = _kimlik_dogrula()
    if hata: return hata
    liste = _SAHTE_HSS_LISTESI if _hss_aktif else []
    return jsonify({"sunucusaati": _sunucu_saati(), "hss_koordinat_bilgileri": liste}), 200

@app.route("/debug/hss_ac", methods=["POST"])
def debug_hss_ac():
    global _hss_aktif
    _hss_aktif = True
    return jsonify({"hss_aktif": True}), 200

@app.route("/debug/hss_kapat", methods=["POST"])
def debug_hss_kapat():
    global _hss_aktif
    _hss_aktif = False
    return jsonify({"hss_aktif": False}), 200

@app.errorhandler(404)
def bulunamadi(_e):
    return jsonify({"hata_kodu": 404, "mesaj": "Geçersiz URL"}), 404

def main():
    _kimlik_bilgilerini_yukle()
    try: port = Config().sunucu_port()
    except FileNotFoundError: port = 5000
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    main()
"""
core/config.py
==============
BTU-Poyraz YKİ — Tip-güvenli Konfigürasyon Okuyucu

config.json'ı okur ve her modüle temiz bir API sunar.
Kod içinde hiçbir IP, port veya baud rate sabit yazılmaz.

Kullanım:
    from core.config import Config
    cfg = Config()
    baglanti_str = cfg.mavlink_baglanti_str()   # "udp:127.0.0.1:14550"
    takim_no     = cfg.takim_no()               # 42
"""
from __future__ import annotations
import json
import os
from pathlib import Path


# config.json her zaman projenin köküne göre aranır
_PROJE_KOKU = Path(__file__).resolve().parent.parent
_CONFIG_YOLU = _PROJE_KOKU / "config.json"


class Config:
    """
    config.json'ı yükler ve tip-güvenli erişim sağlar.
    Singleton değil; istediğin kadar instance oluşturabilirsin.
    """

    def __init__(self, config_yolu: Path = _CONFIG_YOLU):
        if not config_yolu.exists():
            raise FileNotFoundError(
                f"config.json bulunamadı: {config_yolu}\n"
                "Proje kökündeki config.json'ı kontrol et."
            )
        with open(config_yolu, encoding="utf-8") as f:
            self._veri = json.load(f)

    # ── Takım ────────────────────────────────────────────────────────────────
    def takim_no(self) -> int:
        return int(self._veri["takim"]["no"])

    def takim_adi(self) -> str:
        return str(self._veri["takim"]["ad"])

    # ── MAVLink bağlantısı ───────────────────────────────────────────────────
    def mavlink_aktif_profil(self) -> dict:
        """Aktif profilin tüm ayarlarını döndürür."""
        ad = self._veri["mavlink"]["aktif_profil"]
        return self._veri["mavlink"]["profiller"][ad]

    def mavlink_baglanti_str(self) -> str:
        """
        pymavlink'e doğrudan verilecek bağlantı dizesi.
            "udp:127.0.0.1:14550"
            "COM3"
            "tcp:192.168.1.1:5760"
        """
        p = self.mavlink_aktif_profil()
        tip = p["tip"]
        if tip == "serial":
            return p["port"]          # pymavlink serial için sadece port adı
        elif tip in ("udp", "tcp"):
            return f"{tip}:{p['adres']}:{p['port']}"
        raise ValueError(f"Bilinmeyen bağlantı tipi: {tip}")

    def mavlink_baud(self) -> int:
        """Serial bağlantı için baud rate (UDP/TCP için kullanılmaz)."""
        return int(self.mavlink_aktif_profil().get("baud", 115200))

    def mavlink_profil_listesi(self) -> list[str]:
        """Tüm tanımlı profil isimlerini döndürür."""
        return list(self._veri["mavlink"]["profiller"].keys())

    def mavlink_profil(self, ad: str) -> dict:
        """
        Belirtilen isimdeki profilin ham ayarlarını döndürür (aktif profil
        olması şart değil). Örn. simulasyon/sitl.py, SITL'in çıkış portunu
        'sitl' adlı profilden okumak için bunu kullanır — böylece port sabit
        kodlanmaz, config.json üzerinden gelir.
        """
        return self._veri["mavlink"]["profiller"][ad]

    # ── Görev bilgisayarı ────────────────────────────────────────────────────
    def gb_adres(self) -> str:
        return str(self._veri["gorev_bilgisayari"]["adres"])

    def gb_port(self) -> int:
        return int(self._veri["gorev_bilgisayari"]["port"])

    def gb_kamera_indeks(self) -> int:
        return int(self._veri["gorev_bilgisayari"]["kamera_indeks"])

    def gb_sahte_mod(self) -> bool:
        """True → gerçek donanım yok, sahte veri kullan."""
        return bool(self._veri["gorev_bilgisayari"]["sahte_mod"])

    def gb_tip(self) -> str:
        """Görev bilgisayarı bağlantı tipi, örn. "tcp" veya "udp"."""
        return str(self._veri["gorev_bilgisayari"].get("tip", "tcp"))

    # ── Yarışma sunucusu ─────────────────────────────────────────────────────
    def sunucu_adres(self) -> str:
        return str(self._veri["sunucu"]["adres"])

    def sunucu_port(self) -> int:
        return int(self._veri["sunucu"]["port"])

    def sunucu_kullanici(self) -> str:
        return str(self._veri["sunucu"]["kullanici"])

    def sunucu_sifre(self) -> str:
        return str(self._veri["sunucu"]["sifre"])

    # ── Arayüz ───────────────────────────────────────────────────────────────
    def logo_yolu(self) -> Path:
        goreli = self._veri["arayuz"]["logo_yolu"]
        return _PROJE_KOKU / goreli

    def harita_html_yolu(self) -> Path:
        goreli = self._veri["arayuz"]["harita_html"]
        return _PROJE_KOKU / goreli

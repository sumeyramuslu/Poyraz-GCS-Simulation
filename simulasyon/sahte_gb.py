"""
simulasyon/sahte_gb.py
=======================
KİŞİ 6 — Sahte Görev Bilgisayarı (Raspberry Pi) Simülatörü

GÖREV:
  Gerçek Raspberry Pi / görev bilgisayarı donanımı yerine, TCP üzerinden
  hedef tespit kutusu (bbox) ve sistem sağlığı (CPU/RAM/sıcaklık) bilgilerini
  periyodik olarak yayınlayan sahte bir sunucudur.
"""
from __future__ import annotations

import json
import random
import socket
import threading
import time

from core.config import Config

_VARSAYILAN_ADRES = "0.0.0.0"
_VARSAYILAN_PORT = 6000


class SahteGorevBilgisayari:
    def __init__(self, gonderim_hz: float = 5.0):
        self._gonderim_hz = gonderim_hz
        self._sunucu_soketi = None
        self._calisiyor = False
        self._dinleyici_thread = None

        try:
            cfg = Config()
            self._adres = cfg.gb_adres()
            self._port = cfg.gb_port()
        except FileNotFoundError:
            self._adres = _VARSAYILAN_ADRES
            self._port = _VARSAYILAN_PORT
            print(
                f"[SahteGB] UYARI: config.json bulunamadı, varsayılan "
                f"{self._adres}:{self._port} kullanılıyor."
            )

    def baslat(self) -> None:
        if self._calisiyor:
            return

        self._sunucu_soketi = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sunucu_soketi.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sunucu_soketi.bind((self._adres, self._port))
        self._sunucu_soketi.listen(5)
        self._sunucu_soketi.settimeout(1.0)
        self._calisiyor = True

        self._dinleyici_thread = threading.Thread(target=self._dinle, daemon=True)
        self._dinleyici_thread.start()
        print(f"[SahteGB] Dinliyor → {self._adres}:{self._port}  ({self._gonderim_hz} Hz)")

    def durdur(self) -> None:
        self._calisiyor = False
        if self._dinleyici_thread:
            self._dinleyici_thread.join(timeout=2)
        if self._sunucu_soketi:
            try:
                self._sunucu_soketi.close()
            except OSError:
                pass
            self._sunucu_soketi = None
        print("[SahteGB] Durduruldu.")

    def calisiyior_mu(self) -> bool:
        return self._calisiyor

    def _dinle(self) -> None:
        while self._calisiyor:
            try:
                istemci, adres = self._sunucu_soketi.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            print(f"[SahteGB] Yeni bağlantı: {adres}")
            threading.Thread(
                target=self._istemciye_gonder, args=(istemci,), daemon=True
            ).start()

    def _istemciye_gonder(self, istemci: socket.socket) -> None:
        aralik = 1.0 / self._gonderim_hz
        kilitlenme_sayaci = 0

        try:
            while self._calisiyor:
                kilitli = kilitlenme_sayaci > 0

                paket = {
                    "hedef_merkez_X": random.randint(80, 560) if kilitli else 0,
                    "hedef_merkez_Y": random.randint(60, 400) if kilitli else 0,
                    # KTR'ye göre 640x480 çözünürlüğün en az %5'ini kapsaması için:
                    # Alan > 15360 px olmalı. 130x130 = 16900 px (Şartnameye uygun)
                    "hedef_genislik": random.randint(130, 200) if kilitli else 0,
                    "hedef_yukseklik": random.randint(130, 200) if kilitli else 0,
                    "kilitlenme_aktif": kilitli,
                    "cpu_yuzde": round(random.uniform(15, 55), 1),
                    "ram_yuzde": round(random.uniform(30, 70), 1),
                    "sicaklik": round(random.uniform(40, 65), 1),
                }

                if kilitlenme_sayaci == 0 and random.random() < 0.02:
                    kilitlenme_sayaci = max(1, int(4 * self._gonderim_hz))
                elif kilitlenme_sayaci > 0:
                    kilitlenme_sayaci -= 1

                mesaj = (json.dumps(paket) + "\n").encode("utf-8")
                istemci.sendall(mesaj)
                time.sleep(aralik)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            istemci.close()

    def __enter__(self) -> "SahteGorevBilgisayari":
        self.baslat()
        return self

    def __exit__(self, *exc_info) -> None:
        self.durdur()


def main():
    sahte = SahteGorevBilgisayari()
    sahte.baslat()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        sahte.durdur()


if __name__ == "__main__":
    main()
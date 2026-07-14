"""
simulasyon/sitl.py
===================
KİŞİ 6 — ArduPilot SITL Süreç Yöneticisi

GÖREV:
  ArduPilot SITL'i subprocess ile başlatır/durdurur.
  Yalnızca geliştirme ortamında kullanılır — gerçek uçuşta çalıştırılmaz.

KULLANIM:
  from simulasyon.sitl import SitlYonetici
  sitl = SitlYonetici()
  sitl.baslat()    # SITL'i başlatır, config.json'daki "sitl" profilinde
                    # tanımlı UDP adresinde dinler
  sitl.durdur()    # Süreci temiz kapatır

NOT:
  ArduPilot (sim_vehicle.py) kurulu değilse veya PATH'te bulunamazsa,
  baslat() sadece bir uyarı basar ve False döner; uygulamanın geri kalanı
  (config okuma, sahte sunucu, sahte GB) SITL olmadan da çalışmaya devam
  edebilmelidir — bu yüzden burada hiçbir exception dışarı sızdırılmaz.
"""
from __future__ import annotations

import shutil
import subprocess
import time

from core.config import Config

# config.json'da SITL çıkışı için kullanılacak profil adı.
# Sabit kodlama yasağı gereği yalnızca *isim* burada, IP/port config.json'dan gelir.
_SITL_PROFIL_ADI = "sitl"
_VARSAYILAN_ADRES = "127.0.0.1"
_VARSAYILAN_PORT = 14550

_ARAC_HARITASI = {
    "plane": "ArduPlane",
    "copter": "ArduCopter",
    "rover": "Rover",
    "sub": "ArduSub",
}


class SitlYonetici:
    """
    ArduPilot sim_vehicle.py'yi subprocess ile yönetir.
    ArduPilot kurulu değilse uyarı ver, çalışmaya devam et.
    """

    def __init__(self, arac_tipi: str = "plane"):
        """
        arac_tipi: "plane" (ArduPlane), "copter" (ArduCopter), vb.
        """
        self._arac_tipi = arac_tipi
        self._surec: subprocess.Popen | None = None

    # ------------------------------------------------------------------ #
    def _cikis_adresi(self) -> str:
        """SITL'in MAVLink çıkışını yollayacağı adres:port'u config.json'dan okur."""
        try:
            profil = Config().mavlink_profil(_SITL_PROFIL_ADI)
            adres = profil.get("adres", _VARSAYILAN_ADRES)
            port = profil.get("port", _VARSAYILAN_PORT)
            return f"{adres}:{port}"
        except (FileNotFoundError, KeyError):
            print(
                "[SITL] UYARI: config.json içinde 'sitl' profili bulunamadı, "
                f"varsayılan {_VARSAYILAN_ADRES}:{_VARSAYILAN_PORT} kullanılıyor."
            )
            return f"{_VARSAYILAN_ADRES}:{_VARSAYILAN_PORT}"

    def baslat(self) -> bool:
        """
        sim_vehicle.py'yi başlatır.
        Dönüş: başarılı mı?

        Örnek komut:
            python sim_vehicle.py -v ArduPlane --out udp:127.0.0.1:14550 --no-mavproxy
        """
        if self.calisiyior_mu():
            print("[SITL] Zaten çalışıyor, tekrar başlatılmadı.")
            return True

        sim_vehicle = shutil.which("sim_vehicle.py")
        if sim_vehicle is None:
            print(
                "[SITL] UYARI: 'sim_vehicle.py' PATH üzerinde bulunamadı. "
                "ArduPilot kurulu değil ya da PATH'e eklenmemiş olabilir. "
                "SITL başlatılamadı; diğer modüller etkilenmeden çalışmaya devam edebilir."
            )
            return False

        ardu_arac = _ARAC_HARITASI.get(self._arac_tipi, "ArduPlane")
        cikis = self._cikis_adresi()

        komut = [
            sim_vehicle,
            "-v", ardu_arac,
            "--out", f"udp:{cikis}",
            "--no-mavproxy",
        ]

        try:
            self._surec = subprocess.Popen(
                komut,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError as e:
            print(f"[SITL] Başlatma hatası: {e}")
            self._surec = None
            return False

        # sürecin hemen çökmediğini doğrulamak için kısa bir bekleme
        time.sleep(1.0)
        if not self.calisiyior_mu():
            print("[SITL] Süreç hemen sonlandı, başlatma başarısız oldu.")
            return False

        print(f"[SITL] Başlatıldı → udp:{cikis}  ({ardu_arac})")
        return True

    def durdur(self) -> None:
        """Süreci SIGTERM ile kapatır, 3 sn içinde kapanmazsa SIGKILL."""
        if self._surec is None:
            return
        if self._surec.poll() is not None:
            # zaten kendiliğinden kapanmış
            self._surec = None
            return

        self._surec.terminate()
        try:
            self._surec.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self._surec.kill()
            try:
                self._surec.wait(timeout=3)
            except subprocess.TimeoutExpired:
                print("[SITL] UYARI: süreç SIGKILL sonrası da kapanmadı.")

        print("[SITL] Durduruldu.")
        self._surec = None

    def calisiyior_mu(self) -> bool:
        """Süreç hâlâ çalışıyor mu?"""
        return self._surec is not None and self._surec.poll() is None

    # Geliştirme kolaylığı: "with SitlYonetici() as sitl:" kullanımı
    def __enter__(self) -> "SitlYonetici":
        self.baslat()
        return self

    def __exit__(self, *exc_info) -> None:
        self.durdur()


def main():
    """Elle test için: python -m simulasyon.sitl"""
    sitl = SitlYonetici()
    if sitl.baslat():
        print("Durdurmak için Ctrl+C...")
        try:
            while sitl.calisiyior_mu():
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            sitl.durdur()


if __name__ == "__main__":
    main()

from .sitl import SitlYonetici
from .sahte_gb import SahteGorevBilgisayari

# sahte_sunucu.py bilinçli olarak burada import edilmiyor: Flask'e bağımlıdır
# ve yalnızca `python -m simulasyon.sahte_sunucu` ile çalıştırılması yeterlidir.
# Böylece Flask kurulu değilken bile SitlYonetici / SahteGorevBilgisayari
# kullanılabilir.

__all__ = ["SitlYonetici", "SahteGorevBilgisayari"]

# Poyraz GCS Simulation

TEKNOFEST Savaşan İHA takımı seçme görevi kapsamında geliştirilen modüler bir yer kontrol istasyonu simülasyon altyapısıdır. Proje; gerçek uçuş donanımı ve yarışma sunucusu olmadan telemetri, görev bilgisayarı ve sunucu haberleşmesi bileşenlerinin geliştirme ortamında test edilmesini amaçlar.

## Özellikler

- JSON tabanlı merkezi bağlantı ve takım yapılandırması
- Telemetri, rakip İHA ve hava savunma sistemi veri modelleri
- Flask tabanlı sahte yarışma sunucusu
- Giriş, telemetri, kilitlenme, kamikaze, QR ve HSS API uç noktaları
- TCP üzerinden hedef tespit ve sistem sağlığı verisi üreten sahte görev bilgisayarı
- Birden fazla sahte rakip İHA konumu üretimi
- ArduPilot SITL sürecini başlatma ve durdurma desteği
- İş parçacığı tabanlı eş zamanlı istemci yönetimi

## Proje Yapısı

```text
.
|-- config.ornek.json       # Güvenli örnek yapılandırma
|-- core/
|   |-- config.py           # Yapılandırma okuyucu
|   `-- veri_modeli.py      # Ortak telemetri veri sözleşmesi
`-- simulasyon/
    |-- sahte_gb.py         # Sahte görev bilgisayarı
    |-- sahte_sunucu.py     # Sahte yarışma sunucusu
    `-- sitl.py             # ArduPilot SITL süreç yöneticisi
```

## Gereksinimler

- Python 3.10 veya üzeri
- Flask
- İsteğe bağlı: ArduPilot SITL (`sim_vehicle.py`)

## Kurulum

```bash
git clone https://github.com/sumeyramuslu/Poyraz-GCS-Simulation.git
cd Poyraz-GCS-Simulation
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
Copy-Item config.ornek.json config.json
pip install Flask
```

Linux/macOS:

```bash
source .venv/bin/activate
cp config.ornek.json config.json
pip install Flask
```

## Çalıştırma

Sahte yarışma sunucusu:

```bash
python -m simulasyon.sahte_sunucu
```

Sahte görev bilgisayarı:

```bash
python -m simulasyon.sahte_gb
```

ArduPilot kuruluysa SITL yöneticisi:

```bash
python -m simulasyon.sitl
```

## Yapılandırma

`config.ornek.json` yalnızca örnek ve test değerleri içerir. Gerçek bağlantı bilgileri için bu dosyayı `config.json` adıyla kopyalayın ve kendi ortamınıza göre düzenleyin. `config.json` Git tarafından izlenmez.

## Kullanım Amacı

Bu proje gerçek İHA'yı kontrol etmez ve resmî yarışma sunucusunun yerine geçmez. Yarışma öncesi geliştirme, entegrasyon ve haberleşme testleri için hazırlanmış bir prototiptir.

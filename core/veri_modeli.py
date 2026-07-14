"""
core/veri_modeli.py
===================
BTU-Poyraz YKİ — Modüller Arası Ortak Veri Sözleşmesi

Bu dosyayı YALNIZCA Kişi 6 düzenler.
Diğer herkes sadece import eder:
    from core.veri_modeli import TelemetriVerisi, RakipIha
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


RAKIP_RENK_PALETI = [
    "#e74c3c", "#3498db", "#2ecc71", "#f39c12", 
    "#9b59b6", "#1abc9c", "#e67e22", "#e91e63",
]

def rakip_rengi(takim_no: int) -> str:
    return RAKIP_RENK_PALETI[takim_no % len(RAKIP_RENK_PALETI)]


@dataclass
class RakipIha:
    takim_no:  int   = 0
    enlem:     float = 0.0
    boylam:    float = 0.0
    irtifa:    int   = 0     
    hiz:       int   = 0     
    yonelme:   float = 0.0   

    @property
    def renk(self) -> str:
        return rakip_rengi(self.takim_no)

    @staticmethod
    def sunucu_yaniti_parse(ham_liste: list) -> "List[RakipIha]":
        # TODO: Kişi 3 burayı dolduracak (GÖREV TANIMI: BURAYA DOKUNMA)
        pass


@dataclass
class HssBolgesi:
    enlem:  float = 0.0
    boylam: float = 0.0
    yaricap: int  = 0    
    aktif:  bool  = False


@dataclass
class TelemetriVerisi:
    latitude:           float = 0.0    
    longitude:          float = 0.0    
    altitude:           float = 0.0    
    relative_altitude:  float = 0.0    
    groundspeed:        float = 0.0    
    airspeed:           float = 0.0    
    heading:            float = 0.0    
    pitch:              float = 0.0    
    roll:               float = 0.0    
    yaw:                float = 0.0    
    climb_rate:         float = 0.0    

    battery_voltage:    float = 0.0    
    battery_current:    float = 0.0    
    battery_percentage: int   = 0      

    gps_fix:            int   = 0      
    satellites:         int   = 0

    armed:              bool  = False
    mode:               str   = "UNKNOWN"
    next_waypoint:      int   = 0

    gps_saat:           int   = 0
    gps_dakika:         int   = 0
    gps_saniye:         int   = 0
    gps_milisaniye:     int   = 0

    mavlink_bagli:      bool  = False

    kamera_aktif:       bool  = False
    hedef_x:            int   = 0      
    hedef_y:            int   = 0      
    hedef_genislik:     int   = 0      
    hedef_yukseklik:    int   = 0      
    kilitlenme_aktif:   bool  = False  

    gb_cpu_yuzde:       float = 0.0
    gb_ram_yuzde:       float = 0.0
    gb_sicaklik:        float = 0.0
    gb_baglanti:        bool  = False

    @property
    def pitch_deg(self) -> float:
        import math; return math.degrees(self.pitch)

    @property
    def roll_deg(self) -> float:
        import math; return math.degrees(self.roll)

    @property
    def yaw_deg(self) -> float:
        import math; return math.degrees(self.yaw) % 360

    @property
    def otonom_mu(self) -> bool:
        return self.mode.upper() in {"AUTO", "GUIDED", "RTL", "TAKEOFF"}

    def to_sunucu_paketi(self, takim_no: int) -> dict:
        return {
            "takim_numarasi": int(takim_no),
            "iha_enlem":      round(self.latitude,  7),
            "iha_boylam":     round(self.longitude, 7),
            "iha_irtifa":     int(round(self.altitude)),
            "iha_dikilme":    int(round(self.pitch_deg)),
            "iha_yonelme":    int(round(self.yaw_deg)) % 360,
            "iha_yatis":      int(round(self.roll_deg)),
            "iha_hiz":        int(round(self.groundspeed)),
            "iha_batarya":    int(self.battery_percentage),
            "iha_otonom":     self.otonom_mu,
            "iha_kilitlenme": self.kilitlenme_aktif,
            "hedef_merkez_X":  int(self.hedef_x),
            "hedef_merkez_Y":  int(self.hedef_y),
            "hedef_genislik":  int(self.hedef_genislik),
            "hedef_yukseklik": int(self.hedef_yukseklik),
            "gps_saati": {
                "saat":       int(self.gps_saat),
                "dakika":     int(self.gps_dakika),
                "saniye":     int(self.gps_saniye),
                "milisaniye": int(self.gps_milisaniye),
            },
        }
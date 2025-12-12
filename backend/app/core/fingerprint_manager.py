"""
🎭 FINGERPRINT MANAGER - Gestión de identidades virtuales únicas

Este módulo gestiona fingerprints únicos para cada componente,
garantizando que cada entidad aparezca como un dispositivo diferente.

INTEGRACIÓN:
- GoLogin: Perfiles de navegador aislados
- ADB: Dispositivos Android virtuales
- Fingerprinting: Canvas, WebGL, Audio, Fonts, etc.

Autor: STAKAZO Security Team
Fecha: Diciembre 2025
Versión: 1.0.0
"""

import os
import json
import hashlib
from typing import Dict, Optional, List
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
import random


class DeviceType(str, Enum):
    """Tipos de dispositivos simulados"""
    ANDROID_MOBILE = "android_mobile"
    IOS_MOBILE = "ios_mobile"
    WINDOWS_PC = "windows_pc"
    MAC_PC = "mac_pc"
    LINUX_PC = "linux_pc"
    GENERIC_PC = "generic_pc"  # Para TelegramBot


class BrowserType(str, Enum):
    """Tipos de navegadores"""
    CHROME = "chrome"
    FIREFOX = "firefox"
    SAFARI = "safari"
    EDGE = "edge"


class FingerprintProfile(BaseModel):
    """Perfil de fingerprint único"""
    profile_id: str
    device_type: DeviceType
    browser_type: BrowserType
    
    # User Agent
    user_agent: str
    
    # Screen & Hardware
    screen_width: int
    screen_height: int
    color_depth: int
    pixel_ratio: float
    
    # Browser Properties
    platform: str
    language: str
    timezone: str
    
    # Canvas Fingerprint
    canvas_fingerprint: str
    
    # WebGL Fingerprint
    webgl_vendor: str
    webgl_renderer: str
    
    # Audio Fingerprint
    audio_fingerprint: str
    
    # Fonts
    fonts: List[str]
    
    # Plugins
    plugins: List[str]
    
    # Media Devices
    has_microphone: bool
    has_camera: bool
    has_speakers: bool
    
    # Geolocation
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # GoLogin Profile (si aplica)
    gologin_profile_id: Optional[str] = None
    
    # ADB Device (si aplica)
    adb_device_id: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    assigned_to: Optional[str] = None


class FingerprintManager:
    """
    Gestor de fingerprints únicos
    
    Garantiza que cada componente tenga una identidad virtual única:
    - Satélites: Android/iOS realistas
    - TelegramBot: PC genérico neutral
    - Scrapers: Mobile variados
    """
    
    def __init__(self):
        self.profiles: Dict[str, FingerprintProfile] = {}
        self.gologin_api_key = os.getenv("GOLOGIN_API_KEY")
        self.gologin_enabled = bool(self.gologin_api_key)
        
        # Stats
        self.total_profiles = 0
        self.collisions_detected = 0
    
    def generate_fingerprint(
        self,
        component_id: str,
        device_type: DeviceType,
        country_code: Optional[str] = None
    ) -> FingerprintProfile:
        """
        Genera un fingerprint único para un componente
        
        Args:
            component_id: ID del componente
            device_type: Tipo de dispositivo a simular
            country_code: Código país para geolocation
        
        Returns:
            FingerprintProfile único
        """
        
        # Verificar si ya existe
        if component_id in self.profiles:
            return self.profiles[component_id]
        
        # Generar según tipo de dispositivo
        if device_type == DeviceType.ANDROID_MOBILE:
            profile = self._generate_android_profile(component_id, country_code)
        
        elif device_type == DeviceType.IOS_MOBILE:
            profile = self._generate_ios_profile(component_id, country_code)
        
        elif device_type == DeviceType.GENERIC_PC:
            profile = self._generate_generic_pc_profile(component_id, country_code)
        
        else:
            profile = self._generate_windows_pc_profile(component_id, country_code)
        
        # Verificar colisiones
        if self._detect_collision(profile):
            self.collisions_detected += 1
            # Regenerar con variación
            profile = self._add_variations(profile)
        
        # Guardar
        self.profiles[component_id] = profile
        self.total_profiles += 1
        
        return profile
    
    def _generate_android_profile(
        self,
        component_id: str,
        country_code: Optional[str]
    ) -> FingerprintProfile:
        """Genera perfil Android realista"""
        
        # Android versions y devices comunes
        android_versions = [
            ("13", "SM-G998B", "Samsung Galaxy S21 Ultra"),
            ("13", "SM-A525F", "Samsung Galaxy A52"),
            ("12", "Pixel 6 Pro", "Google Pixel 6 Pro"),
            ("12", "M2101K7BNY", "Xiaomi 11T Pro"),
            ("11", "OnePlus 9 Pro", "OnePlus 9 Pro")
        ]
        
        version, device_model, device_name = random.choice(android_versions)
        
        # User Agent
        chrome_version = random.randint(110, 120)
        user_agent = (
            f"Mozilla/5.0 (Linux; Android {version}; {device_model}) "
            f"AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/{chrome_version}.0.0.0 Mobile Safari/537.36"
        )
        
        # Screen resolutions comunes para móviles
        resolutions = [
            (1080, 2400), (1440, 3200), (1080, 2340), (720, 1600)
        ]
        width, height = random.choice(resolutions)
        
        # Canvas fingerprint único
        canvas_hash = hashlib.sha256(
            f"{component_id}_{device_model}_{datetime.utcnow()}".encode()
        ).hexdigest()[:16]
        
        # WebGL
        webgl_vendors = [
            "Qualcomm", "ARM", "Google", "Samsung"
        ]
        webgl_renderers = [
            "Adreno (TM) 650",
            "Mali-G78 MP14",
            "Adreno (TM) 730"
        ]
        
        # Geo
        lat, lon = self._get_coordinates_for_country(country_code)
        
        return FingerprintProfile(
            profile_id=f"android_{component_id}",
            device_type=DeviceType.ANDROID_MOBILE,
            browser_type=BrowserType.CHROME,
            user_agent=user_agent,
            screen_width=width,
            screen_height=height,
            color_depth=24,
            pixel_ratio=random.choice([2.0, 2.5, 3.0]),
            platform="Linux armv8l",
            language="en-US",
            timezone=self._get_timezone_for_country(country_code),
            canvas_fingerprint=canvas_hash,
            webgl_vendor=random.choice(webgl_vendors),
            webgl_renderer=random.choice(webgl_renderers),
            audio_fingerprint=hashlib.md5(f"audio_{canvas_hash}".encode()).hexdigest()[:12],
            fonts=[
                "Roboto", "Noto Sans", "Droid Sans", "Arial", "Helvetica"
            ],
            plugins=[],  # Chrome mobile no tiene plugins
            has_microphone=True,
            has_camera=True,
            has_speakers=True,
            latitude=lat,
            longitude=lon,
            assigned_to=component_id
        )
    
    def _generate_ios_profile(
        self,
        component_id: str,
        country_code: Optional[str]
    ) -> FingerprintProfile:
        """Genera perfil iOS realista"""
        
        # iOS versions y devices
        ios_devices = [
            ("16.5", "iPhone14,3", "iPhone 13 Pro Max"),
            ("16.2", "iPhone14,2", "iPhone 13 Pro"),
            ("15.7", "iPhone13,4", "iPhone 12 Pro Max"),
            ("16.0", "iPhone15,2", "iPhone 14 Pro")
        ]
        
        version, device_id, device_name = random.choice(ios_devices)
        
        # User Agent
        user_agent = (
            f"Mozilla/5.0 (iPhone; CPU iPhone OS {version.replace('.', '_')} like Mac OS X) "
            f"AppleWebKit/605.1.15 (KHTML, like Gecko) "
            f"Version/{version.split('.')[0]}.0 Mobile/15E148 Safari/604.1"
        )
        
        # Screen resolutions iOS
        resolutions = [
            (1170, 2532), (1284, 2778), (1125, 2436)
        ]
        width, height = random.choice(resolutions)
        
        canvas_hash = hashlib.sha256(
            f"{component_id}_{device_id}_{datetime.utcnow()}".encode()
        ).hexdigest()[:16]
        
        lat, lon = self._get_coordinates_for_country(country_code)
        
        return FingerprintProfile(
            profile_id=f"ios_{component_id}",
            device_type=DeviceType.IOS_MOBILE,
            browser_type=BrowserType.SAFARI,
            user_agent=user_agent,
            screen_width=width,
            screen_height=height,
            color_depth=32,
            pixel_ratio=3.0,
            platform="iPhone",
            language="en-US",
            timezone=self._get_timezone_for_country(country_code),
            canvas_fingerprint=canvas_hash,
            webgl_vendor="Apple Inc.",
            webgl_renderer="Apple GPU",
            audio_fingerprint=hashlib.md5(f"audio_{canvas_hash}".encode()).hexdigest()[:12],
            fonts=[
                "San Francisco", "Helvetica Neue", "Arial", "Georgia"
            ],
            plugins=[],
            has_microphone=True,
            has_camera=True,
            has_speakers=True,
            latitude=lat,
            longitude=lon,
            assigned_to=component_id
        )
    
    def _generate_generic_pc_profile(
        self,
        component_id: str,
        country_code: Optional[str]
    ) -> FingerprintProfile:
        """
        Genera perfil PC genérico NEUTRAL
        
        CRÍTICO: Para TelegramBot - debe parecer PC normal, no móvil
        """
        
        chrome_version = random.randint(110, 120)
        
        user_agent = (
            f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            f"AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/{chrome_version}.0.0.0 Safari/537.36"
        )
        
        # Resoluciones comunes de PC
        resolutions = [
            (1920, 1080), (2560, 1440), (1366, 768), (1920, 1200)
        ]
        width, height = random.choice(resolutions)
        
        canvas_hash = hashlib.sha256(
            f"{component_id}_generic_pc_{datetime.utcnow()}".encode()
        ).hexdigest()[:16]
        
        lat, lon = self._get_coordinates_for_country(country_code)
        
        return FingerprintProfile(
            profile_id=f"generic_pc_{component_id}",
            device_type=DeviceType.GENERIC_PC,
            browser_type=BrowserType.CHROME,
            user_agent=user_agent,
            screen_width=width,
            screen_height=height,
            color_depth=24,
            pixel_ratio=1.0,
            platform="Win32",
            language="en-US",
            timezone=self._get_timezone_for_country(country_code),
            canvas_fingerprint=canvas_hash,
            webgl_vendor="Google Inc. (Intel)",
            webgl_renderer="ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)",
            audio_fingerprint=hashlib.md5(f"audio_{canvas_hash}".encode()).hexdigest()[:12],
            fonts=[
                "Arial", "Calibri", "Times New Roman", "Verdana", "Tahoma",
                "Georgia", "Trebuchet MS", "Comic Sans MS"
            ],
            plugins=["Chrome PDF Plugin", "Chrome PDF Viewer"],
            has_microphone=True,
            has_camera=True,
            has_speakers=True,
            latitude=lat,
            longitude=lon,
            assigned_to=component_id
        )
    
    def _generate_windows_pc_profile(
        self,
        component_id: str,
        country_code: Optional[str]
    ) -> FingerprintProfile:
        """Genera perfil Windows PC"""
        return self._generate_generic_pc_profile(component_id, country_code)
    
    def _detect_collision(self, profile: FingerprintProfile) -> bool:
        """Detecta si hay colisión de fingerprints"""
        
        for existing_profile in self.profiles.values():
            # Verificar colisiones críticas
            if (
                existing_profile.canvas_fingerprint == profile.canvas_fingerprint
                or existing_profile.user_agent == profile.user_agent
            ):
                return True
        
        return False
    
    def _add_variations(self, profile: FingerprintProfile) -> FingerprintProfile:
        """Añade variaciones para evitar colisión"""
        
        # Regenerar canvas y audio
        new_seed = f"{profile.profile_id}_{datetime.utcnow().timestamp()}"
        profile.canvas_fingerprint = hashlib.sha256(new_seed.encode()).hexdigest()[:16]
        profile.audio_fingerprint = hashlib.md5(f"audio_{new_seed}".encode()).hexdigest()[:12]
        
        # Pequeñas variaciones en dimensiones
        profile.screen_width += random.randint(-10, 10)
        profile.screen_height += random.randint(-10, 10)
        
        return profile
    
    def _get_coordinates_for_country(self, country_code: Optional[str]) -> tuple:
        """Obtiene coordenadas aproximadas para un país"""
        
        coordinates = {
            "US": (37.0902, -95.7129),
            "UK": (51.5074, -0.1278),
            "ES": (40.4168, -3.7038),
            "MX": (19.4326, -99.1332),
            "CA": (43.6532, -79.3832),
            "AU": (-33.8688, 151.2093),
            "DE": (52.5200, 13.4050),
            "FR": (48.8566, 2.3522)
        }
        
        if country_code and country_code in coordinates:
            lat, lon = coordinates[country_code]
            # Añadir variación aleatoria (~50km)
            lat += random.uniform(-0.5, 0.5)
            lon += random.uniform(-0.5, 0.5)
            return lat, lon
        
        return None, None
    
    def _get_timezone_for_country(self, country_code: Optional[str]) -> str:
        """Obtiene timezone para un país"""
        
        timezones = {
            "US": "America/New_York",
            "UK": "Europe/London",
            "ES": "Europe/Madrid",
            "MX": "America/Mexico_City",
            "CA": "America/Toronto",
            "AU": "Australia/Sydney",
            "DE": "Europe/Berlin",
            "FR": "Europe/Paris"
        }
        
        return timezones.get(country_code, "America/New_York")
    
    def get_profile(self, component_id: str) -> Optional[FingerprintProfile]:
        """Obtiene perfil asignado a componente"""
        return self.profiles.get(component_id)
    
    async def create_gologin_profile(
        self,
        fingerprint: FingerprintProfile
    ) -> Optional[str]:
        """
        Crea perfil en GoLogin
        
        Returns:
            GoLogin profile ID o None si no está habilitado
        """
        
        if not self.gologin_enabled:
            return None
        
        # TODO: Implementar integración real con GoLogin API
        # Por ahora, retornar ID simulado
        
        gologin_profile_id = f"gologin_{fingerprint.profile_id}"
        fingerprint.gologin_profile_id = gologin_profile_id
        
        return gologin_profile_id
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del manager"""
        
        return {
            "total_profiles": self.total_profiles,
            "collisions_detected": self.collisions_detected,
            "gologin_enabled": self.gologin_enabled,
            "profiles_by_type": {
                "android": len([p for p in self.profiles.values() if p.device_type == DeviceType.ANDROID_MOBILE]),
                "ios": len([p for p in self.profiles.values() if p.device_type == DeviceType.IOS_MOBILE]),
                "generic_pc": len([p for p in self.profiles.values() if p.device_type == DeviceType.GENERIC_PC]),
                "windows_pc": len([p for p in self.profiles.values() if p.device_type == DeviceType.WINDOWS_PC])
            }
        }


# Singleton global
_fingerprint_manager_instance = None


def get_fingerprint_manager() -> FingerprintManager:
    """Obtiene instancia singleton del FingerprintManager"""
    global _fingerprint_manager_instance
    if _fingerprint_manager_instance is None:
        _fingerprint_manager_instance = FingerprintManager()
    return _fingerprint_manager_instance

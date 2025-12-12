"""
CAPTCHA Resolver - Sprint 7A
Resuelve CAPTCHAs al unirse a grupos de Telegram.
"""
import asyncio
import re
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta

from telethon import TelegramClient
from telethon.tl.types import Message, MessageMediaPhoto
from twocaptcha import TwoCaptcha

logger = logging.getLogger(__name__)


class CaptchaDetector:
    """Detector de CAPTCHAs en mensajes."""
    
    # Patrones de detección
    CAPTCHA_KEYWORDS = [
        "captcha", "verify", "verificación", "verificacion",
        "bot check", "human verification", "press button",
        "click button", "solve", "resolver", "presiona",
        "haz click", "confirma que eres humano"
    ]
    
    # Patrones de preguntas simples
    MATH_PATTERN = r'(\d+)\s*[\+\-\*\/]\s*(\d+)'
    
    @classmethod
    def is_captcha_message(cls, message: Message) -> bool:
        """
        Detecta si un mensaje es un CAPTCHA.
        
        Args:
            message: Mensaje de Telethon
            
        Returns:
            True si parece ser CAPTCHA
        """
        if not message:
            return False
        
        text = (message.text or "").lower()
        
        # Verificar keywords
        if any(kw in text for kw in cls.CAPTCHA_KEYWORDS):
            return True
        
        # Verificar si tiene imagen (posible imagen CAPTCHA)
        if message.media and isinstance(message.media, MessageMediaPhoto):
            return True
        
        # Verificar si tiene botones inline
        if message.reply_markup:
            return True
        
        return False
    
    @classmethod
    def extract_captcha_data(cls, message: Message) -> Dict:
        """
        Extrae datos del CAPTCHA.
        
        Returns:
            Dict con tipo, pregunta, opciones, etc.
        """
        data = {
            "type": "unknown",
            "question": None,
            "options": [],
            "has_image": False,
            "has_buttons": False
        }
        
        text = message.text or ""
        
        # Detectar tipo
        if message.media and isinstance(message.media, MessageMediaPhoto):
            data["type"] = "image"
            data["has_image"] = True
        
        if message.reply_markup:
            data["type"] = "button"
            data["has_buttons"] = True
            
            # Extraer botones
            if hasattr(message.reply_markup, 'rows'):
                for row in message.reply_markup.rows:
                    for button in row.buttons:
                        if hasattr(button, 'text'):
                            data["options"].append(button.text)
        
        # Detectar matemática simple
        math_match = re.search(cls.MATH_PATTERN, text)
        if math_match:
            data["type"] = "math"
            data["question"] = math_match.group(0)
        
        # Guardar texto completo
        data["text"] = text
        
        return data


class SimpleCaptchaSolver:
    """Resolver de CAPTCHAs simples (texto/botones)."""
    
    @staticmethod
    def solve_math(question: str) -> Optional[int]:
        """
        Resuelve CAPTCHA matemático simple.
        
        Args:
            question: Pregunta (ej: "2 + 2")
            
        Returns:
            Resultado o None
        """
        try:
            # Limpiar y evaluar (seguro para operaciones simples)
            cleaned = re.sub(r'[^\d\+\-\*\/\(\)]', '', question)
            result = eval(cleaned)
            return int(result)
        except Exception as e:
            logger.error(f"Error resolviendo matemática '{question}': {e}")
            return None
    
    @staticmethod
    def solve_text_captcha(text: str) -> Optional[str]:
        """
        Resuelve CAPTCHA de texto simple.
        
        Ejemplos:
        - "Type 'yes' to continue"
        - "Escribe 'confirmo' para verificar"
        
        Returns:
            Respuesta o None
        """
        text_lower = text.lower()
        
        # Detectar "type 'X'"
        type_match = re.search(r"type\s+'([^']+)'", text_lower)
        if type_match:
            return type_match.group(1)
        
        # Detectar "escribe 'X'"
        escribe_match = re.search(r"escribe\s+'([^']+)'", text_lower)
        if escribe_match:
            return escribe_match.group(1)
        
        # Detectar "press yes/no"
        if "press yes" in text_lower or "click yes" in text_lower:
            return "yes"
        
        if "presiona sí" in text_lower or "haz click en sí" in text_lower:
            return "sí"
        
        return None


class CaptchaResolver:
    """
    Resolver de CAPTCHAs.
    
    Estrategia:
    1. Detectar tipo de CAPTCHA
    2. Resolver localmente si es simple (texto/matemática/botones)
    3. Usar 2Captcha para imágenes/reCAPTCHA complejos
    """
    
    def __init__(
        self,
        client: TelegramClient,
        twocaptcha_api_key: Optional[str] = None
    ):
        """
        Args:
            client: Cliente de Telethon
            twocaptcha_api_key: API key de 2Captcha (opcional)
        """
        self.client = client
        self.use_2captcha = twocaptcha_api_key is not None
        
        if self.use_2captcha:
            self.captcha_service = TwoCaptcha(twocaptcha_api_key)
            logger.info("2Captcha habilitado")
        else:
            self.captcha_service = None
            logger.info("2Captcha deshabilitado (solo resolución local)")
        
        # Stats
        self.stats = {
            "captchas_detected": 0,
            "captchas_solved_local": 0,
            "captchas_solved_2captcha": 0,
            "captchas_failed": 0
        }
    
    async def detect_captcha(self, chat_id: int, timeout: int = 10) -> bool:
        """
        Detecta si hay un CAPTCHA activo en el chat.
        
        Args:
            chat_id: ID del chat/grupo
            timeout: Segundos a esperar por CAPTCHA
            
        Returns:
            True si se detectó CAPTCHA
        """
        try:
            # Obtener últimos mensajes
            messages = await self.client.get_messages(chat_id, limit=5)
            
            for msg in messages:
                if CaptchaDetector.is_captcha_message(msg):
                    logger.info(f"CAPTCHA detectado en chat {chat_id}")
                    self.stats["captchas_detected"] += 1
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error detectando CAPTCHA: {e}")
            return False
    
    async def solve_captcha(
        self,
        chat_id: int,
        max_attempts: int = 3
    ) -> bool:
        """
        Intenta resolver CAPTCHA.
        
        Args:
            chat_id: ID del chat
            max_attempts: Intentos máximos
            
        Returns:
            True si se resolvió exitosamente
        """
        for attempt in range(max_attempts):
            try:
                logger.info(f"Intento {attempt + 1}/{max_attempts} de resolver CAPTCHA")
                
                # Obtener mensaje CAPTCHA
                messages = await self.client.get_messages(chat_id, limit=5)
                captcha_msg = None
                
                for msg in messages:
                    if CaptchaDetector.is_captcha_message(msg):
                        captcha_msg = msg
                        break
                
                if not captcha_msg:
                    logger.info("No se encontró CAPTCHA")
                    return True  # Asumimos resuelto si no hay CAPTCHA
                
                # Extraer datos
                captcha_data = CaptchaDetector.extract_captcha_data(captcha_msg)
                
                # Intentar resolver según tipo
                if captcha_data["type"] == "math":
                    success = await self._solve_math_captcha(captcha_msg, captcha_data)
                    if success:
                        return True
                
                elif captcha_data["type"] == "button":
                    success = await self._solve_button_captcha(captcha_msg, captcha_data)
                    if success:
                        return True
                
                elif captcha_data["type"] == "image" and self.use_2captcha:
                    success = await self._solve_image_captcha_2captcha(captcha_msg)
                    if success:
                        return True
                
                else:
                    # Texto simple
                    success = await self._solve_text_captcha(captcha_msg, captcha_data)
                    if success:
                        return True
                
                # Esperar antes de reintentar
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.error(f"Error en intento {attempt + 1}: {e}")
                await asyncio.sleep(5)
        
        logger.error(f"No se pudo resolver CAPTCHA después de {max_attempts} intentos")
        self.stats["captchas_failed"] += 1
        return False
    
    async def _solve_math_captcha(
        self,
        message: Message,
        data: Dict
    ) -> bool:
        """Resuelve CAPTCHA matemático."""
        question = data["question"]
        result = SimpleCaptchaSolver.solve_math(question)
        
        if result is None:
            return False
        
        logger.info(f"Resolviendo matemática: {question} = {result}")
        
        # Responder
        await self.client.send_message(
            message.chat_id,
            str(result),
            reply_to=message.id
        )
        
        self.stats["captchas_solved_local"] += 1
        return True
    
    async def _solve_button_captcha(
        self,
        message: Message,
        data: Dict
    ) -> bool:
        """Resuelve CAPTCHA de botones."""
        # Buscar botón correcto
        buttons = data["options"]
        
        if not buttons:
            return False
        
        # Estrategia simple: buscar "Yes", "Sí", "Confirm", etc.
        target_buttons = ["yes", "sí", "si", "confirm", "confirmar", "verificar", "verify", "✓", "✅"]
        
        for i, button_text in enumerate(buttons):
            if any(target in button_text.lower() for target in target_buttons):
                logger.info(f"Presionando botón: {button_text}")
                
                # Click en botón
                await message.click(i)
                
                self.stats["captchas_solved_local"] += 1
                return True
        
        # Si no encontramos, presionar el primero
        logger.info(f"Presionando primer botón: {buttons[0]}")
        await message.click(0)
        
        self.stats["captchas_solved_local"] += 1
        return True
    
    async def _solve_text_captcha(
        self,
        message: Message,
        data: Dict
    ) -> bool:
        """Resuelve CAPTCHA de texto simple."""
        text = data["text"]
        answer = SimpleCaptchaSolver.solve_text_captcha(text)
        
        if not answer:
            logger.warning(f"No se pudo resolver CAPTCHA de texto: {text[:100]}")
            return False
        
        logger.info(f"Resolviendo texto CAPTCHA: respuesta='{answer}'")
        
        # Responder
        await self.client.send_message(
            message.chat_id,
            answer,
            reply_to=message.id
        )
        
        self.stats["captchas_solved_local"] += 1
        return True
    
    async def _solve_image_captcha_2captcha(self, message: Message) -> bool:
        """
        Resuelve CAPTCHA de imagen usando 2Captcha.
        
        Args:
            message: Mensaje con imagen CAPTCHA
            
        Returns:
            True si se resolvió
        """
        if not self.use_2captcha:
            logger.warning("2Captcha no disponible")
            return False
        
        try:
            logger.info("Resolviendo imagen CAPTCHA con 2Captcha...")
            
            # Descargar imagen
            photo = await message.download_media(bytes)
            
            if not photo:
                return False
            
            # Enviar a 2Captcha
            result = self.captcha_service.normal(photo)
            
            if not result or "code" not in result:
                logger.error("2Captcha no retornó resultado")
                return False
            
            answer = result["code"]
            logger.info(f"2Captcha resolvió: {answer}")
            
            # Enviar respuesta
            await self.client.send_message(
                message.chat_id,
                answer,
                reply_to=message.id
            )
            
            self.stats["captchas_solved_2captcha"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error con 2Captcha: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Retorna estadísticas."""
        return {
            **self.stats,
            "success_rate": (
                (self.stats["captchas_solved_local"] + self.stats["captchas_solved_2captcha"])
                / max(self.stats["captchas_detected"], 1)
            )
        }

"""
Emotional Message Generator - Sprint 7A
Genera mensajes naturales usando Gemini 2.0 Flash con fallback a templates.
"""
import json
import random
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum

from langdetect import detect, LangDetectException

from app.llm_providers.gemini_client import GeminiClient
from app.telegram_exchange_bot.models import (
    ExchangeMessage,
    OurContent,
    Platform,
    InteractionType
)

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Tipos de mensaje a generar."""
    ANNOUNCEMENT = "announcement"
    DM_INTRO = "dm_intro"
    DM_FOLLOWUP = "dm_followup"
    DM_REQUEST_LINK = "dm_request_link"
    DM_CONFIRMATION = "dm_confirmation"
    DM_THANKS = "dm_thanks"
    DM_OFFER_EXTRA = "dm_offer_extra"
    DM_REJECTION = "dm_rejection_polite"
    DEFENSE_ROLE = "defense_role"
    COMMENT = "comment"


class EmotionalMessageGenerator:
    """
    Generador de mensajes naturales con Gemini 2.0 Flash.
    
    Características:
    - Integración con Gemini 2.0 (cost-saving <€0.002/msg)
    - Fallback a templates si Gemini falla
    - Detección automática de idioma
    - Variación textual
    - Defensa de rol como fan
    """
    
    def __init__(
        self,
        gemini_client: Optional[GeminiClient] = None,
        use_gemini: bool = True,
        templates_dir: Optional[Path] = None
    ):
        """
        Args:
            gemini_client: Cliente Gemini 2.0 (se crea si no se proporciona)
            use_gemini: Si False, solo usa templates (útil para testing)
            templates_dir: Directorio de templates i18n
        """
        self.use_gemini = use_gemini
        self.gemini_client = gemini_client or GeminiClient()
        
        # Cargar templates
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "templates" / "i18n"
        self.templates = self._load_templates(templates_dir)
        
        logger.info(
            f"EmotionalMessageGenerator inicializado. "
            f"Gemini: {use_gemini}, Idiomas: {list(self.templates.keys())}"
        )
    
    def _load_templates(self, templates_dir: Path) -> Dict[str, Dict[str, Any]]:
        """Carga templates multilenguaje desde JSON."""
        templates = {}
        
        for lang_file in templates_dir.glob("*.json"):
            lang = lang_file.stem  # es, en, pt
            try:
                with open(lang_file, "r", encoding="utf-8") as f:
                    templates[lang] = json.load(f)
                logger.info(f"Templates cargados: {lang} ({len(templates[lang])} categorías)")
            except Exception as e:
                logger.error(f"Error cargando templates {lang}: {e}")
        
        if not templates:
            logger.warning("No se cargaron templates. Generación limitada a Gemini.")
        
        return templates
    
    def detect_language(self, text: str, default: str = "es") -> str:
        """
        Detecta idioma del texto.
        
        Args:
            text: Texto a analizar
            default: Idioma por defecto si falla detección
            
        Returns:
            Código de idioma (es/en/pt)
        """
        try:
            lang = detect(text)
            # Mapear a idiomas soportados
            if lang in ["es", "en", "pt"]:
                return lang
            # Fallback a español para otros idiomas latinos
            elif lang in ["fr", "it", "ca"]:
                return "es"
            else:
                return default
        except LangDetectException:
            logger.debug(f"No se pudo detectar idioma, usando {default}")
            return default
    
    async def generate_announcement(
        self,
        content: OurContent,
        group_name: str,
        language: Optional[str] = None
    ) -> str:
        """
        Genera anuncio para publicar en grupo.
        
        Args:
            content: Contenido oficial a promocionar
            group_name: Nombre del grupo
            language: Idioma (autodetecta si es None)
            
        Returns:
            Mensaje de anuncio
        """
        lang = language or "es"
        
        # Intentar con Gemini primero
        if self.use_gemini:
            try:
                gemini_msg = await self._generate_with_gemini(
                    message_type=MessageType.ANNOUNCEMENT,
                    context={
                        "link": content.url,
                        "platform": content.platform.value,
                        "language": lang,
                        "group_name": group_name
                    },
                    language=lang
                )
                if gemini_msg:
                    logger.info(f"Anuncio generado con Gemini ({lang})")
                    return gemini_msg
            except Exception as e:
                logger.warning(f"Gemini falló, usando template: {e}")
        
        # Fallback a template
        return self._generate_from_template(
            MessageType.ANNOUNCEMENT,
            lang,
            {"link": content.url}
        )
    
    async def generate_dm_intro(
        self,
        content: OurContent,
        group_name: str,
        user_message: Optional[str] = None,
        language: Optional[str] = None
    ) -> str:
        """
        Genera mensaje inicial para DM privado.
        
        Args:
            content: Contenido a promocionar
            group_name: Grupo donde se detectó al usuario
            user_message: Mensaje original del usuario (para contexto)
            language: Idioma (autodetecta del user_message si es None)
            
        Returns:
            Mensaje de introducción
        """
        # Detectar idioma del mensaje del usuario
        lang = language
        if not lang and user_message:
            lang = self.detect_language(user_message)
        lang = lang or "es"
        
        context = {
            "link": content.url,
            "group_name": group_name,
            "platform": content.platform.value
        }
        
        if user_message:
            context["user_context"] = user_message[:200]  # Primeros 200 chars
        
        # Intentar con Gemini
        if self.use_gemini:
            try:
                gemini_msg = await self._generate_with_gemini(
                    message_type=MessageType.DM_INTRO,
                    context=context,
                    language=lang
                )
                if gemini_msg:
                    return gemini_msg
            except Exception as e:
                logger.warning(f"Gemini falló en DM intro: {e}")
        
        # Fallback
        return self._generate_from_template(
            MessageType.DM_INTRO,
            lang,
            {"link": content.url, "group_name": group_name}
        )
    
    async def generate_comment(
        self,
        target_content: str,
        platform: Platform,
        language: Optional[str] = None
    ) -> str:
        """
        Genera comentario natural para contenido de otro usuario.
        
        Args:
            target_content: Descripción del contenido a comentar
            platform: Plataforma del contenido
            language: Idioma
            
        Returns:
            Comentario auténtico
        """
        lang = language or "es"
        
        if self.use_gemini:
            try:
                prompt = self._build_comment_prompt(target_content, platform, lang)
                response = await self.gemini_client.generate_text(
                    prompt=prompt,
                    max_tokens=100
                )
                if response:
                    comment = response.strip()
                    logger.info(f"Comentario generado con Gemini: {comment[:50]}...")
                    return comment
            except Exception as e:
                logger.warning(f"Gemini falló en comentario: {e}")
        
        # Fallback a comentarios genéricos
        generic_comments = {
            "es": [
                "🔥 Muy bueno!",
                "💪 Excelente contenido",
                "🎵 Me encanta!",
                "🚀 Sigue así crack",
                "👏 Increíble trabajo"
            ],
            "en": [
                "🔥 Amazing!",
                "💪 Great content",
                "🎵 Love it!",
                "🚀 Keep it up!",
                "👏 Awesome work"
            ],
            "pt": [
                "🔥 Muito bom!",
                "💪 Conteúdo excelente",
                "🎵 Adorei!",
                "🚀 Continua assim",
                "👏 Trabalho incrível"
            ]
        }
        
        return random.choice(generic_comments.get(lang, generic_comments["es"]))
    
    async def generate_followup(
        self,
        content: OurContent,
        conversation_history: List[str],
        language: str = "es"
    ) -> str:
        """
        Genera mensaje de seguimiento en conversación DM.
        
        Args:
            content: Contenido promocionado
            conversation_history: Historial de mensajes (últimos 5)
            language: Idioma
            
        Returns:
            Mensaje de seguimiento
        """
        # Para followups simples, usar templates (son efectivos)
        return self._generate_from_template(
            MessageType.DM_FOLLOWUP,
            language,
            {"link": content.url}
        )
    
    async def defend_fan_role(self, language: str = "es") -> str:
        """
        Genera respuesta defensiva para mantener rol de fan.
        Usado cuando alguien sospecha que es bot.
        """
        return self._generate_from_template(
            MessageType.DEFENSE_ROLE,
            language,
            {}
        )
    
    def vary_text(self, text: str, variation_level: float = 0.3) -> str:
        """
        Añade variación sutil a un texto (emojis, orden, etc).
        
        Args:
            text: Texto original
            variation_level: 0.0 (sin cambios) a 1.0 (máxima variación)
            
        Returns:
            Texto con variaciones
        """
        # Por ahora retorna el texto original
        # TODO: Implementar variaciones sutiles
        return text
    
    async def _generate_with_gemini(
        self,
        message_type: MessageType,
        context: Dict[str, Any],
        language: str
    ) -> Optional[str]:
        """
        Genera mensaje usando Gemini 2.0 Flash.
        
        Returns:
            Mensaje generado o None si falla
        """
        prompt = self._build_gemini_prompt(message_type, context, language)
        
        try:
            response = await self.gemini_client.generate_text(
                prompt=prompt,
                max_tokens=150,
                temperature=0.9  # Alta creatividad
            )
            
            if response:
                # Limpiar respuesta
                message = response.strip()
                # Remover comillas si las añadió
                if message.startswith('"') and message.endswith('"'):
                    message = message[1:-1]
                return message
            
            return None
            
        except Exception as e:
            logger.error(f"Error en Gemini: {e}")
            return None
    
    def _build_gemini_prompt(
        self,
        message_type: MessageType,
        context: Dict[str, Any],
        language: str
    ) -> str:
        """Construye prompt para Gemini según tipo de mensaje."""
        
        lang_names = {"es": "español", "en": "English", "pt": "português"}
        lang_name = lang_names.get(language, "español")
        
        base_instruction = f"""Eres un fan de música urbana (artista: Stakas) que busca intercambio de likes/subs en redes sociales.
Escribe mensajes cortos, naturales y auténticos en {lang_name}.
NO uses formato de chat, SOLO escribe el mensaje directo.
NO uses comillas ni etiquetas.
Usa emojis con moderación (2-3 máximo).
"""
        
        if message_type == MessageType.ANNOUNCEMENT:
            return f"""{base_instruction}
Tarea: Crear mensaje para grupo de Telegram anunciando intercambio.
Link del contenido: {context.get('link')}
Plataforma: {context.get('platform', 'YouTube')}
Grupo: {context.get('group_name', 'grupo')}

Estructura: 
- Frase llamativa sobre intercambio (like x like, sub x sub)
- Link
- Llamado a acción (DM/respuesta)

Máximo 3 líneas.
"""
        
        elif message_type == MessageType.DM_INTRO:
            user_ctx = context.get('user_context', '')
            ctx_line = f"\nContexto del usuario: {user_ctx}" if user_ctx else ""
            
            return f"""{base_instruction}
Tarea: Primer mensaje privado a usuario que busca intercambio.
Link de tu contenido: {context.get('link')}
Grupo donde se detectó: {context.get('group_name')}{ctx_line}

Estructura:
- Saludo amigable
- Mencionar que viste su mensaje en el grupo
- Pasar tu link
- Proponer intercambio específico (like + comment + sub)

Máximo 4 líneas.
"""
        
        elif message_type == MessageType.COMMENT:
            return f"""{base_instruction}
Tarea: Comentar en contenido de otro usuario en {context.get('platform', 'YouTube')}.
Descripción del contenido: {context.get('content', 'video musical')}

Escribe comentario auténtico de fan (máx 50 caracteres).
NO digas que es intercambio, comenta genuinamente.
"""
        
        else:
            # Otros tipos: usar templates
            return ""
    
    def _build_comment_prompt(
        self,
        target_content: str,
        platform: Platform,
        language: str
    ) -> str:
        """Construye prompt específico para comentarios."""
        lang_names = {"es": "español", "en": "English", "pt": "português"}
        
        return f"""Eres un fan genuino de música. Escribe un comentario auténtico en {lang_names.get(language, 'español')}.

Plataforma: {platform.value}
Contenido: {target_content}

Reglas:
- Máximo 50 caracteres
- Actúa como fan real, NO como bot
- Usa 1-2 emojis relevantes
- NO menciones intercambio
- Sé positivo y natural

SOLO escribe el comentario (sin comillas ni etiquetas):"""
    
    def _generate_from_template(
        self,
        message_type: MessageType,
        language: str,
        variables: Dict[str, str]
    ) -> str:
        """
        Genera mensaje desde templates JSON.
        
        Args:
            message_type: Tipo de mensaje
            language: Idioma
            variables: Variables para interpolar {link}, {group_name}, etc
            
        Returns:
            Mensaje con variables interpoladas
        """
        # Mapear MessageType a key en JSON
        type_to_key = {
            MessageType.ANNOUNCEMENT: "announcement_variants",
            MessageType.DM_INTRO: "dm_intro_variants",
            MessageType.DM_FOLLOWUP: "dm_followup",
            MessageType.DM_REQUEST_LINK: "dm_request_link",
            MessageType.DM_CONFIRMATION: "dm_confirmation",
            MessageType.DM_THANKS: "dm_thanks",
            MessageType.DM_OFFER_EXTRA: "dm_offer_extra",
            MessageType.DM_REJECTION: "dm_rejection_polite",
            MessageType.DEFENSE_ROLE: "defense_role"
        }
        
        template_key = type_to_key.get(message_type)
        if not template_key:
            logger.warning(f"No hay template para {message_type}")
            return f"Hola! {variables.get('link', '')}"
        
        # Obtener templates del idioma
        lang_templates = self.templates.get(language, self.templates.get("es", {}))
        templates_list = lang_templates.get(template_key, [])
        
        if not templates_list:
            logger.warning(f"No hay templates para {template_key} en {language}")
            return f"Hola! {variables.get('link', '')}"
        
        # Seleccionar template aleatorio
        template = random.choice(templates_list)
        
        # Interpolar variables
        try:
            message = template.format(**variables)
        except KeyError as e:
            logger.warning(f"Variable faltante en template: {e}")
            message = template  # Retornar sin interpolar
        
        return message

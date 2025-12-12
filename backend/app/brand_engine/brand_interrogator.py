"""
Brand Interrogator - Dynamic Artist Identity Q&A System (Sprint 4)

Sistema de interrogatorio adaptativo que aprende TODO sobre la identidad del artista.

Características:
- Preguntas dinámicas (contextuales, adaptativas)
- NO contiene presets ni ejemplos predeterminados
- Aprende: estética, narrativa, tono, cultura, restricciones, coherencia visual, visión
- Sesiones iterativas con follow-ups inteligentes
- Output: BrandProfile completo basado 100% en respuestas del artista

NO asume nada. TODO se pregunta y aprende.
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

from .models import (
    InterrogationQuestion,
    InterrogationResponse,
    BrandProfile,
    QuestionType,
)

logger = logging.getLogger(__name__)


class BrandInterrogator:
    """
    Dynamic interrogation system that learns artist identity from scratch.
    
    NO PRESETS. NO ASSUMPTIONS.
    Everything learned through intelligent questioning.
    """
    
    def __init__(self):
        """Initialize interrogator with empty session."""
        self.session_id: Optional[str] = None
        self.questions: List[InterrogationQuestion] = []
        self.responses: List[InterrogationResponse] = []
        self.profile: Optional[BrandProfile] = None
        
    # ========================================
    # Question Bank Generation (Dynamic)
    # ========================================
    
    def generate_initial_questions(self) -> List[InterrogationQuestion]:
        """
        Generate initial question set.
        
        These are broad, open questions to establish baseline understanding.
        NO assumptions about style, genre, or aesthetic.
        """
        initial_questions = [
            # 1. Core Identity
            InterrogationQuestion(
                question_id="identity_001",
                question_text="¿Cuál es tu nombre artístico o el nombre del proyecto?",
                question_type=QuestionType.OPEN_TEXT,
                category="identity",
                required=True,
            ),
            InterrogationQuestion(
                question_id="identity_002",
                question_text="¿Cómo describirías tu proyecto en una frase? ¿Qué representa?",
                question_type=QuestionType.OPEN_TEXT,
                category="identity",
                required=True,
            ),
            
            # 2. Visual Aesthetic (NO PRESETS)
            InterrogationQuestion(
                question_id="aesthetic_001",
                question_text="¿Qué colores sientes que representan mejor tu marca? (Puedes elegir hasta 5)",
                question_type=QuestionType.COLOR_PICKER,
                category="aesthetic",
                required=True,
            ),
            InterrogationQuestion(
                question_id="aesthetic_002",
                question_text="¿Cómo describirías la estética visual de tu proyecto? Usa las palabras que prefieras.",
                question_type=QuestionType.OPEN_TEXT,
                category="aesthetic",
                required=True,
                follow_up_questions=["aesthetic_003"],
            ),
            InterrogationQuestion(
                question_id="aesthetic_003",
                question_text="¿Hay algún artista, marca o movimiento visual que inspire tu estética?",
                question_type=QuestionType.OPEN_TEXT,
                category="aesthetic",
                required=False,
            ),
            
            # 3. Narrative & Story
            InterrogationQuestion(
                question_id="narrative_001",
                question_text="¿Qué historia quieres contar con tu proyecto? ¿De dónde vienes y hacia dónde vas?",
                question_type=QuestionType.OPEN_TEXT,
                category="narrative",
                required=True,
            ),
            InterrogationQuestion(
                question_id="narrative_002",
                question_text="¿Qué mensajes clave quieres que tu audiencia recuerde de ti?",
                question_type=QuestionType.OPEN_TEXT,
                category="narrative",
                required=True,
            ),
            
            # 4. Tone & Voice
            InterrogationQuestion(
                question_id="tone_001",
                question_text="¿Cómo describirías el tono de tu comunicación? (Ej: serio, juguetón, poético, crudo, etc.)",
                question_type=QuestionType.OPEN_TEXT,
                category="tone",
                required=True,
            ),
            InterrogationQuestion(
                question_id="tone_002",
                question_text="Del 1 al 10, ¿qué tan directo/explícito vs. sutil/metafórico quieres ser?",
                question_type=QuestionType.RATING_SCALE,
                category="tone",
                required=True,
            ),
            
            # 5. Cultural Context
            InterrogationQuestion(
                question_id="culture_001",
                question_text="¿Qué raíces culturales o geográficas son importantes para tu identidad?",
                question_type=QuestionType.OPEN_TEXT,
                category="culture",
                required=False,
            ),
            InterrogationQuestion(
                question_id="culture_002",
                question_text="¿Qué influencias musicales/artísticas definen tu sonido y estilo?",
                question_type=QuestionType.OPEN_TEXT,
                category="culture",
                required=True,
            ),
            
            # 6. Content Rules (What's allowed/prohibited)
            InterrogationQuestion(
                question_id="rules_001",
                question_text="¿Qué tipo de contenido DEFINITIVAMENTE quieres incluir en tu canal oficial?",
                question_type=QuestionType.OPEN_TEXT,
                category="rules",
                required=True,
            ),
            InterrogationQuestion(
                question_id="rules_002",
                question_text="¿Hay algún tipo de contenido que NUNCA quieres mostrar en tu canal oficial?",
                question_type=QuestionType.OPEN_TEXT,
                category="rules",
                required=True,
            ),
            
            # 7. Visual Scenes & Settings
            InterrogationQuestion(
                question_id="scenes_001",
                question_text="¿En qué tipos de escenarios o localizaciones te ves representado? (Ej: urbano, rural, nocturno, estudio, etc.)",
                question_type=QuestionType.OPEN_TEXT,
                category="scenes",
                required=True,
            ),
            InterrogationQuestion(
                question_id="scenes_002",
                question_text="¿Hay escenarios que NO encajan con tu imagen?",
                question_type=QuestionType.OPEN_TEXT,
                category="scenes",
                required=False,
            ),
            
            # 8. Visual Coherence
            InterrogationQuestion(
                question_id="coherence_001",
                question_text="¿Qué elementos visuales SIEMPRE deberían estar presentes para que el contenido se sienta 'tuyo'?",
                question_type=QuestionType.OPEN_TEXT,
                category="coherence",
                required=True,
            ),
            InterrogationQuestion(
                question_id="coherence_002",
                question_text="Del 1 al 10, ¿qué tan consistente quieres que sea tu estética? (1=experimental, 10=muy consistente)",
                question_type=QuestionType.RATING_SCALE,
                category="coherence",
                required=True,
            ),
            
            # 9. Target Audience
            InterrogationQuestion(
                question_id="audience_001",
                question_text="¿A quién te diriges? Describe tu audiencia ideal.",
                question_type=QuestionType.OPEN_TEXT,
                category="audience",
                required=True,
            ),
            
            # 10. Long-term Vision
            InterrogationQuestion(
                question_id="vision_001",
                question_text="¿Dónde te ves en 2-3 años? ¿Qué quieres haber logrado?",
                question_type=QuestionType.OPEN_TEXT,
                category="vision",
                required=True,
            ),
            InterrogationQuestion(
                question_id="vision_002",
                question_text="¿Cómo medirías el éxito de tu proyecto? ¿Qué métricas importan?",
                question_type=QuestionType.OPEN_TEXT,
                category="vision",
                required=False,
            ),
        ]
        
        return initial_questions
    
    def generate_follow_up_questions(
        self,
        response: InterrogationResponse,
        current_profile: Optional[BrandProfile] = None
    ) -> List[InterrogationQuestion]:
        """
        Generate contextual follow-up questions based on artist's responses.
        
        This is the "intelligence" layer - adapts questioning based on what's learned.
        
        Args:
            response: Latest response from artist
            current_profile: Current state of profile (if exists)
            
        Returns:
            List of follow-up questions
        """
        follow_ups = []
        
        # Aesthetic follow-ups
        if response.question_id == "aesthetic_002" and response.response_text:
            keywords = response.response_text.lower()
            
            # If mentions darkness/night
            if any(word in keywords for word in ["oscuro", "nocturno", "noche", "dark"]):
                follow_ups.append(InterrogationQuestion(
                    question_id="aesthetic_followup_night",
                    question_text="Veo que la estética nocturna es importante. ¿Qué elementos nocturnos específicos definen tu visual? (luces de neón, sombras, ciudad de noche, etc.)",
                    question_type=QuestionType.OPEN_TEXT,
                    category="aesthetic",
                    required=False,
                ))
            
            # If mentions urban
            if any(word in keywords for word in ["urbano", "calle", "ciudad", "urban", "street"]):
                follow_ups.append(InterrogationQuestion(
                    question_id="aesthetic_followup_urban",
                    question_text="El contexto urbano parece clave. ¿Qué elementos urbanos son más relevantes? (graffiti, coches, arquitectura, asfalto, etc.)",
                    question_type=QuestionType.OPEN_TEXT,
                    category="aesthetic",
                    required=False,
                ))
        
        # Cultural follow-ups
        if response.question_id == "culture_001" and response.response_text:
            follow_ups.append(InterrogationQuestion(
                question_id="culture_followup_001",
                question_text="¿Cómo quieres que estas raíces culturales se reflejen visualmente en tu contenido?",
                question_type=QuestionType.OPEN_TEXT,
                category="culture",
                required=False,
            ))
        
        # Content rules follow-ups
        if response.question_id == "rules_001" and response.response_text:
            follow_ups.append(InterrogationQuestion(
                question_id="rules_followup_001",
                question_text="De ese contenido que mencionaste, ¿hay algún elemento que debe aparecer con más frecuencia que otros?",
                question_type=QuestionType.OPEN_TEXT,
                category="rules",
                required=False,
            ))
        
        return follow_ups
    
    # ========================================
    # Session Management
    # ========================================
    
    def start_session(self, artist_name: Optional[str] = None) -> str:
        """
        Start new interrogation session.
        
        Args:
            artist_name: Optional artist name (can be provided later)
            
        Returns:
            Session ID
        """
        self.session_id = f"session_{uuid.uuid4().hex[:12]}"
        self.questions = self.generate_initial_questions()
        self.responses = []
        
        logger.info(f"Started interrogation session {self.session_id} with {len(self.questions)} initial questions")
        
        return self.session_id
    
    def get_next_question(self) -> Optional[InterrogationQuestion]:
        """
        Get next unanswered question.
        
        Returns:
            Next question or None if all answered
        """
        answered_ids = {r.question_id for r in self.responses}
        
        for question in self.questions:
            if question.question_id not in answered_ids:
                if question.required or len(self.responses) > 0:
                    return question
        
        return None
    
    def submit_response(self, response: InterrogationResponse) -> Dict[str, Any]:
        """
        Submit artist's response to a question.
        
        Args:
            response: Artist's response
            
        Returns:
            Status dict with next steps
        """
        # Validate question exists
        question = next((q for q in self.questions if q.question_id == response.question_id), None)
        if not question:
            raise ValueError(f"Question {response.question_id} not found in current question set")
        
        # Store response
        self.responses.append(response)
        logger.info(f"Received response for {response.question_id}: {response.response_text[:50] if response.response_text else 'N/A'}...")
        
        # Generate follow-ups if applicable
        follow_ups = self.generate_follow_up_questions(response, self.profile)
        if follow_ups:
            self.questions.extend(follow_ups)
            logger.info(f"Generated {len(follow_ups)} follow-up questions")
        
        # Check if session complete
        next_question = self.get_next_question()
        is_complete = next_question is None
        
        return {
            "session_id": self.session_id,
            "response_recorded": True,
            "follow_ups_generated": len(follow_ups),
            "next_question": next_question,
            "session_complete": is_complete,
            "total_responses": len(self.responses),
            "questions_remaining": len([q for q in self.questions if q.question_id not in {r.question_id for r in self.responses}])
        }
    
    # ========================================
    # Profile Building
    # ========================================
    
    def build_profile(self) -> BrandProfile:
        """
        Build BrandProfile from all interrogation responses.
        
        This is where we synthesize raw responses into structured profile.
        NO assumptions - everything comes from responses.
        
        Returns:
            Complete BrandProfile
        """
        if not self.responses:
            raise ValueError("Cannot build profile without responses")
        
        profile_id = f"profile_{uuid.uuid4().hex[:12]}"
        
        # Helper to get response text by question ID
        def get_response(question_id: str) -> Optional[str]:
            response = next((r for r in self.responses if r.question_id == question_id), None)
            return response.response_text if response and response.response_text else None
        
        # Helper to get all responses by category
        def get_responses_by_category(category: str) -> List[InterrogationResponse]:
            question_ids = [q.question_id for q in self.questions if q.category == category]
            return [r for r in self.responses if r.question_id in question_ids]
        
        # Extract artist name
        artist_name = get_response("identity_001") or "Unknown Artist"
        
        # Build aesthetic section
        primary_colors = []
        secondary_colors = []
        for response in self.responses:
            if response.question_id == "aesthetic_001" and response.response_color:
                primary_colors.append(response.response_color)
        
        aesthetic_keywords = []
        aesthetic_text = get_response("aesthetic_002")
        if aesthetic_text:
            # Extract keywords (simple split, could use NLP in future)
            aesthetic_keywords = [word.strip() for word in aesthetic_text.lower().split(",")]
        
        visual_references = []
        references_text = get_response("aesthetic_003")
        if references_text:
            visual_references = [ref.strip() for ref in references_text.split(",")]
        
        # Build narrative section
        brand_narrative = get_response("narrative_001") or ""
        key_messages = []
        messages_text = get_response("narrative_002")
        if messages_text:
            key_messages = [msg.strip() for msg in messages_text.split(".") if msg.strip()]
        
        # Build tone section
        tone_of_voice = []
        tone_text = get_response("tone_001")
        if tone_text:
            tone_of_voice = [tone.strip() for tone in tone_text.lower().split(",")]
        
        # Build cultural section
        cultural_context = []
        culture_text = get_response("culture_001")
        if culture_text:
            cultural_context = [ctx.strip() for ctx in culture_text.lower().split(",")]
        
        musical_influences = []
        influences_text = get_response("culture_002")
        if influences_text:
            musical_influences = [inf.strip() for inf in influences_text.split(",")]
        
        # Build content rules section
        allowed_content = []
        allowed_text = get_response("rules_001")
        if allowed_text:
            allowed_content = [item.strip() for item in allowed_text.split(",")]
        
        prohibited_content = []
        prohibited_text = get_response("rules_002")
        if prohibited_text:
            prohibited_content = [item.strip() for item in prohibited_text.split(",")]
        
        # Build visual coherence section
        preferred_scenes = []
        scenes_text = get_response("scenes_001")
        if scenes_text:
            preferred_scenes = [scene.strip() for scene in scenes_text.lower().split(",")]
        
        prohibited_scenes = []
        prohibited_scenes_text = get_response("scenes_002")
        if prohibited_scenes_text:
            prohibited_scenes = [scene.strip() for scene in prohibited_scenes_text.lower().split(",")]
        
        # Build vision section
        brand_vision = get_response("vision_001") or ""
        target_audience = get_response("audience_001") or ""
        
        success_metrics = []
        metrics_text = get_response("vision_002")
        if metrics_text:
            success_metrics = [metric.strip() for metric in metrics_text.split(",")]
        
        # Create profile
        profile = BrandProfile(
            profile_id=profile_id,
            artist_name=artist_name,
            primary_colors=primary_colors,
            secondary_colors=secondary_colors,
            aesthetic_keywords=aesthetic_keywords,
            visual_references=visual_references,
            brand_narrative=brand_narrative,
            tone_of_voice=tone_of_voice,
            key_messages=key_messages,
            cultural_context=cultural_context,
            musical_influences=musical_influences,
            allowed_content=allowed_content,
            prohibited_content=prohibited_content,
            preferred_scenes=preferred_scenes,
            prohibited_scenes=prohibited_scenes,
            brand_vision=brand_vision,
            target_audience=target_audience,
            success_metrics=success_metrics,
            interrogation_responses=self.responses,
        )
        
        self.profile = profile
        logger.info(f"Built BrandProfile {profile_id} from {len(self.responses)} responses")
        
        return profile
    
    # ========================================
    # Utilities
    # ========================================
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current interrogation session."""
        answered_ids = {r.question_id for r in self.responses}
        
        return {
            "session_id": self.session_id,
            "total_questions": len(self.questions),
            "questions_answered": len(self.responses),
            "questions_remaining": len([q for q in self.questions if q.question_id not in answered_ids]),
            "session_complete": self.get_next_question() is None,
            "profile_ready": self.profile is not None,
            "responses_by_category": self._group_responses_by_category(),
        }
    
    def _group_responses_by_category(self) -> Dict[str, int]:
        """Group responses by category for summary."""
        category_counts: Dict[str, int] = {}
        
        for response in self.responses:
            question = next((q for q in self.questions if q.question_id == response.question_id), None)
            if question:
                category = question.category
                category_counts[category] = category_counts.get(category, 0) + 1
        
        return category_counts
    
    def export_session(self) -> Dict[str, Any]:
        """Export complete session data for persistence."""
        return {
            "session_id": self.session_id,
            "questions": [q.model_dump() for q in self.questions],
            "responses": [r.model_dump() for r in self.responses],
            "profile": self.profile.model_dump() if self.profile else None,
            "exported_at": datetime.utcnow().isoformat(),
        }
    
    @classmethod
    def load_session(cls, session_data: Dict[str, Any]) -> "BrandInterrogator":
        """Load session from exported data."""
        interrogator = cls()
        interrogator.session_id = session_data["session_id"]
        interrogator.questions = [
            InterrogationQuestion(**q) for q in session_data["questions"]
        ]
        interrogator.responses = [
            InterrogationResponse(**r) for r in session_data["responses"]
        ]
        if session_data.get("profile"):
            interrogator.profile = BrandProfile(**session_data["profile"])
        
        return interrogator

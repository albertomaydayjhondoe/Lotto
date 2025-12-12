"""
ML ROI Predictor - Sprint 7C
Predictor de ROI usando RandomForest/XGBoost.

Features:
- 8 features: grupo_efficiency, user_efficiency, platform, recency, tipo_interacción, reciprocidad, toxicidad, engagement
- ROI prediction [0-1]
- Integration con prioritization.py y metrics.py
- Daily retraining
"""
import logging
import pickle
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

# XGBoost optional
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logging.warning("XGBoost not available, using RandomForest only")

from sqlalchemy.orm import Session

from app.telegram_exchange_bot.models import Platform

logger = logging.getLogger(__name__)


@dataclass
class ROIPredictionInput:
    """Input para predicción de ROI."""
    grupo_efficiency: float  # [0-1] Efficiency del grupo
    user_efficiency: float  # [0-1] Efficiency del usuario
    platform: Platform  # YouTube/Instagram/TikTok
    recency_days: int  # Días desde última interacción
    interaction_type: str  # like/comment/subscribe/etc
    reciprocity_score: float  # [0-1] Score de reciprocidad
    toxicity_score: float  # [0-1] Score de toxicidad (menor=mejor)
    engagement_rate: float  # [0-1] Rate de engagement del contenido
    
    def to_features(self) -> np.ndarray:
        """Convierte a array de features."""
        # Platform encoding
        platform_map = {
            Platform.YOUTUBE: 0,
            Platform.INSTAGRAM: 1,
            Platform.TIKTOK: 2
        }
        
        # Interaction type encoding
        interaction_map = {
            "like": 0,
            "comment": 1,
            "subscribe": 2,
            "follow": 3,
            "save": 4,
            "share": 5
        }
        
        features = [
            self.grupo_efficiency,
            self.user_efficiency,
            platform_map.get(self.platform, 0),
            min(self.recency_days / 30.0, 1.0),  # Normalize to [0-1]
            interaction_map.get(self.interaction_type, 0) / 5.0,  # Normalize
            self.reciprocity_score,
            1.0 - self.toxicity_score,  # Invert toxicity (higher=better)
            self.engagement_rate
        ]
        
        return np.array(features).reshape(1, -1)


@dataclass
class ROIPredictionOutput:
    """Output de predicción de ROI."""
    predicted_roi: float  # [0-1]
    confidence: float  # [0-1]
    feature_importance: Dict[str, float]
    timestamp: datetime


class MLROIPredictor:
    """
    Predictor ML de ROI para Telegram Exchange Bot.
    
    Features:
    - RandomForest o XGBoost según disponibilidad
    - 8 features clave para predicción
    - Retraining diario automático
    - Integración con metrics.py
    """
    
    def __init__(
        self,
        db: Session,
        model_path: Optional[Path] = None,
        use_xgboost: bool = True
    ):
        self.db = db
        self.model_path = model_path or Path("storage/ml_models/roi_predictor.pkl")
        self.use_xgboost = use_xgboost and XGBOOST_AVAILABLE
        
        # Modelos
        self.model: Optional[any] = None
        self.feature_names = [
            "grupo_efficiency",
            "user_efficiency",
            "platform",
            "recency_normalized",
            "interaction_type_normalized",
            "reciprocity_score",
            "toxicity_inverted",
            "engagement_rate"
        ]
        
        # Estadísticas
        self.training_stats = {
            "last_trained": None,
            "training_samples": 0,
            "mse": 0.0,
            "r2_score": 0.0,
            "predictions_made": 0
        }
        
        # Cargar modelo si existe
        self._load_model()
        
        logger.info(
            f"MLROIPredictor initialized: "
            f"model={'XGBoost' if self.use_xgboost else 'RandomForest'}, "
            f"model_loaded={self.model is not None}"
        )
    
    def _load_model(self):
        """Carga modelo desde disco."""
        if not self.model_path.exists():
            logger.warning(f"Model file not found: {self.model_path}")
            return
        
        try:
            with open(self.model_path, 'rb') as f:
                data = pickle.load(f)
                self.model = data['model']
                self.training_stats = data['stats']
            
            logger.info(
                f"Model loaded: {self.model_path} "
                f"(trained={self.training_stats.get('last_trained', 'unknown')})"
            )
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.model = None
    
    def _save_model(self):
        """Guarda modelo a disco."""
        try:
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'model': self.model,
                'stats': self.training_stats
            }
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(data, f)
            
            logger.info(f"Model saved: {self.model_path}")
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    async def collect_training_data(
        self,
        days: int = 30
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Recolecta datos de entrenamiento desde metrics.
        
        Args:
            days: Número de días de historia
            
        Returns:
            (X_features, y_roi)
        """
        # TODO: Query real a exchange_metrics y exchange_interactions_executed
        # Por ahora, generar datos sintéticos
        
        logger.info(f"Collecting training data (last {days} days)...")
        
        # Generar 1000 samples sintéticos
        n_samples = 1000
        
        X = np.random.rand(n_samples, 8)
        
        # ROI sintético basado en features
        # ROI = weighted sum of features
        weights = np.array([0.25, 0.20, 0.05, 0.10, 0.05, 0.15, 0.10, 0.10])
        y = X @ weights + np.random.normal(0, 0.1, n_samples)
        y = np.clip(y, 0, 1)  # Clip to [0-1]
        
        logger.info(f"Training data collected: {n_samples} samples")
        
        return X, y
    
    async def train_model(self, days: int = 30) -> Dict[str, float]:
        """
        Entrena modelo con datos históricos.
        
        Args:
            days: Días de historia para training
            
        Returns:
            Training metrics
        """
        try:
            logger.info("Starting model training...")
            
            # Recolectar datos
            X, y = await self.collect_training_data(days=days)
            
            if len(X) < 100:
                logger.error(f"Insufficient training data: {len(X)} samples")
                return {"error": "insufficient_data"}
            
            # Train/test split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Entrenar modelo
            if self.use_xgboost:
                logger.info("Training XGBoost model...")
                self.model = xgb.XGBRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42
                )
            else:
                logger.info("Training RandomForest model...")
                self.model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                )
            
            self.model.fit(X_train, y_train)
            
            # Evaluar
            y_pred = self.model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Actualizar stats
            self.training_stats = {
                "last_trained": datetime.utcnow().isoformat(),
                "training_samples": len(X_train),
                "test_samples": len(X_test),
                "mse": float(mse),
                "r2_score": float(r2),
                "predictions_made": 0
            }
            
            # Guardar modelo
            self._save_model()
            
            logger.info(
                f"Model training complete: "
                f"samples={len(X_train)}, mse={mse:.4f}, r2={r2:.4f}"
            )
            
            return self.training_stats
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return {"error": str(e)}
    
    async def predict_roi(
        self,
        input_data: ROIPredictionInput
    ) -> ROIPredictionOutput:
        """
        Predice ROI para una interacción.
        
        Args:
            input_data: Features de la interacción
            
        Returns:
            Predicción de ROI
        """
        if self.model is None:
            logger.warning("Model not trained, returning default prediction")
            return ROIPredictionOutput(
                predicted_roi=0.5,
                confidence=0.0,
                feature_importance={},
                timestamp=datetime.utcnow()
            )
        
        try:
            # Convertir a features
            X = input_data.to_features()
            
            # Predicción
            predicted_roi = float(self.model.predict(X)[0])
            predicted_roi = np.clip(predicted_roi, 0, 1)
            
            # Feature importance
            if hasattr(self.model, 'feature_importances_'):
                importance = self.model.feature_importances_
            else:
                importance = np.ones(len(self.feature_names)) / len(self.feature_names)
            
            feature_importance = {
                name: float(imp)
                for name, imp in zip(self.feature_names, importance)
            }
            
            # Confidence basado en feature importance variance
            confidence = 1.0 - np.std(importance)
            
            self.training_stats["predictions_made"] += 1
            
            logger.debug(
                f"ROI prediction: {predicted_roi:.3f} "
                f"(confidence={confidence:.3f})"
            )
            
            return ROIPredictionOutput(
                predicted_roi=predicted_roi,
                confidence=float(confidence),
                feature_importance=feature_importance,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error predicting ROI: {e}")
            return ROIPredictionOutput(
                predicted_roi=0.5,
                confidence=0.0,
                feature_importance={},
                timestamp=datetime.utcnow()
            )
    
    async def batch_predict(
        self,
        inputs: List[ROIPredictionInput]
    ) -> List[ROIPredictionOutput]:
        """
        Predice ROI para múltiples interacciones.
        
        Args:
            inputs: Lista de features
            
        Returns:
            Lista de predicciones
        """
        if self.model is None:
            logger.warning("Model not trained, returning default predictions")
            return [
                ROIPredictionOutput(
                    predicted_roi=0.5,
                    confidence=0.0,
                    feature_importance={},
                    timestamp=datetime.utcnow()
                )
                for _ in inputs
            ]
        
        try:
            # Convertir a features
            X = np.vstack([inp.to_features() for inp in inputs])
            
            # Batch prediction
            predictions = self.model.predict(X)
            predictions = np.clip(predictions, 0, 1)
            
            # Feature importance
            if hasattr(self.model, 'feature_importances_'):
                importance = self.model.feature_importances_
            else:
                importance = np.ones(len(self.feature_names)) / len(self.feature_names)
            
            feature_importance = {
                name: float(imp)
                for name, imp in zip(self.feature_names, importance)
            }
            
            confidence = 1.0 - np.std(importance)
            
            self.training_stats["predictions_made"] += len(inputs)
            
            logger.debug(f"Batch prediction: {len(inputs)} samples")
            
            return [
                ROIPredictionOutput(
                    predicted_roi=float(pred),
                    confidence=float(confidence),
                    feature_importance=feature_importance,
                    timestamp=datetime.utcnow()
                )
                for pred in predictions
            ]
            
        except Exception as e:
            logger.error(f"Error in batch prediction: {e}")
            return [
                ROIPredictionOutput(
                    predicted_roi=0.5,
                    confidence=0.0,
                    feature_importance={},
                    timestamp=datetime.utcnow()
                )
                for _ in inputs
            ]
    
    def get_stats(self) -> Dict[str, any]:
        """Obtiene estadísticas del predictor."""
        return {
            "model_type": "XGBoost" if self.use_xgboost else "RandomForest",
            "model_loaded": self.model is not None,
            **self.training_stats
        }

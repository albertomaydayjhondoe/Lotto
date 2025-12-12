"""
Color Extractor - Dominant Palette & Aesthetic Scoring

Sprint 3: Vision Engine

Features:
- Extract dominant color palette from frames/clips
- Purple aesthetic scoring (Stakazo brand color)
- Color heatmaps
- Aesthetic classification for orchestrator
"""

import logging
from typing import List, Optional, Tuple
import numpy as np
from collections import Counter

try:
    from PIL import Image
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not installed. Color extraction will be limited.")

from .models import ColorPalette

logger = logging.getLogger(__name__)


class ColorExtractor:
    """
    Extract color palettes and compute aesthetic scores.
    
    Uses:
    - K-means clustering for dominant colors
    - Purple aesthetic scoring (Stakazo brand)
    - HSV color space analysis
    """
    
    # Stakazo brand purple range (HSV)
    PURPLE_HUE_RANGE = (260, 320)  # Degrees
    PURPLE_SATURATION_MIN = 0.3
    
    def __init__(self, num_colors: int = 5):
        """
        Initialize color extractor.
        
        Args:
            num_colors: Number of dominant colors to extract (default: 5)
        """
        self.num_colors = num_colors
        logger.info(f"ColorExtractor initialized with num_colors={num_colors}")
    
    def extract_palette(
        self,
        image: np.ndarray,
        num_colors: Optional[int] = None
    ) -> ColorPalette:
        """
        Extract dominant color palette from an image.
        
        Args:
            image: Image as numpy array (H, W, 3) RGB
            num_colors: Number of colors to extract. If None, uses self.num_colors.
        
        Returns:
            ColorPalette with dominant colors and purple score
        """
        if not SKLEARN_AVAILABLE:
            raise RuntimeError("scikit-learn not installed. Install with: pip install scikit-learn")
        
        num_colors = num_colors or self.num_colors
        
        # Reshape image to list of pixels
        pixels = image.reshape(-1, 3)
        
        # Remove pure black/white for better color extraction
        pixels = pixels[(pixels.sum(axis=1) > 10) & (pixels.sum(axis=1) < 745)]
        
        if len(pixels) < num_colors:
            logger.warning(f"Not enough valid pixels ({len(pixels)}). Using fallback.")
            return self._fallback_palette()
        
        try:
            # K-means clustering
            kmeans = KMeans(n_clusters=num_colors, random_state=42, n_init=10)
            kmeans.fit(pixels)
            
            # Get cluster centers (dominant colors)
            colors_rgb = kmeans.cluster_centers_.astype(int)
            
            # Get cluster sizes (percentages)
            labels = kmeans.labels_
            label_counts = Counter(labels)
            total_pixels = len(labels)
            percentages = [label_counts[i] / total_pixels for i in range(num_colors)]
            
            # Sort by percentage (descending)
            sorted_indices = np.argsort(percentages)[::-1]
            colors_rgb = colors_rgb[sorted_indices]
            percentages = [percentages[i] for i in sorted_indices]
            
            # Convert to hex
            colors_hex = [self._rgb_to_hex(tuple(color)) for color in colors_rgb]
            
            # Calculate purple score
            purple_score = self._calculate_purple_score(colors_rgb, percentages)
            morado_ratio = self._calculate_purple_ratio(colors_rgb, percentages)
            
            dominant_color = colors_hex[0]
            
            return ColorPalette(
                colors_hex=colors_hex,
                percentages=percentages,
                purple_score=purple_score,
                morado_ratio=morado_ratio,
                dominant_color=dominant_color
            )
        
        except Exception as e:
            logger.error(f"Color extraction failed: {e}")
            return self._fallback_palette()
    
    def extract_average_palette(
        self,
        images: List[np.ndarray]
    ) -> ColorPalette:
        """
        Extract average color palette across multiple frames.
        
        Args:
            images: List of images as numpy arrays
        
        Returns:
            Averaged ColorPalette
        """
        if not images:
            return self._fallback_palette()
        
        # Extract palette for each image
        palettes = [self.extract_palette(img) for img in images]
        
        # Aggregate colors across all palettes
        all_colors = []
        all_weights = []
        
        for palette in palettes:
            for color_hex, percentage in zip(palette.colors_hex, palette.percentages):
                rgb = self._hex_to_rgb(color_hex)
                all_colors.append(rgb)
                all_weights.append(percentage)
        
        # Cluster aggregated colors
        colors_array = np.array(all_colors)
        weights_array = np.array(all_weights)
        
        try:
            # Weighted K-means
            kmeans = KMeans(n_clusters=self.num_colors, random_state=42, n_init=10)
            kmeans.fit(colors_array, sample_weight=weights_array)
            
            colors_rgb = kmeans.cluster_centers_.astype(int)
            
            # Recalculate percentages
            labels = kmeans.labels_
            label_counts = Counter(labels)
            total = len(labels)
            percentages = [label_counts[i] / total for i in range(self.num_colors)]
            
            # Sort
            sorted_indices = np.argsort(percentages)[::-1]
            colors_rgb = colors_rgb[sorted_indices]
            percentages = [percentages[i] for i in sorted_indices]
            
            colors_hex = [self._rgb_to_hex(tuple(color)) for color in colors_rgb]
            
            purple_score = self._calculate_purple_score(colors_rgb, percentages)
            morado_ratio = self._calculate_purple_ratio(colors_rgb, percentages)
            
            return ColorPalette(
                colors_hex=colors_hex,
                percentages=percentages,
                purple_score=purple_score,
                morado_ratio=morado_ratio,
                dominant_color=colors_hex[0]
            )
        
        except Exception as e:
            logger.error(f"Average palette extraction failed: {e}")
            return self._fallback_palette()
    
    def _calculate_purple_score(
        self,
        colors_rgb: np.ndarray,
        percentages: List[float]
    ) -> float:
        """
        Calculate purple aesthetic score.
        
        Stakazo brand uses purple (#8B44FF and similar tones).
        
        Args:
            colors_rgb: Array of RGB colors
            percentages: Percentage of each color
        
        Returns:
            Purple score (0-1)
        """
        purple_score = 0.0
        
        for color_rgb, percentage in zip(colors_rgb, percentages):
            # Convert to HSV
            hsv = self._rgb_to_hsv(color_rgb)
            hue, saturation, value = hsv
            
            # Check if in purple range
            if (self.PURPLE_HUE_RANGE[0] <= hue <= self.PURPLE_HUE_RANGE[1] and
                saturation >= self.PURPLE_SATURATION_MIN):
                purple_score += percentage
        
        return min(1.0, purple_score)
    
    def _calculate_purple_ratio(
        self,
        colors_rgb: np.ndarray,
        percentages: List[float]
    ) -> float:
        """Calculate ratio of purple tones (same as purple_score for now)."""
        return self._calculate_purple_score(colors_rgb, percentages)
    
    def _rgb_to_hsv(self, rgb: np.ndarray) -> Tuple[float, float, float]:
        """
        Convert RGB to HSV.
        
        Args:
            rgb: RGB color (0-255)
        
        Returns:
            (hue, saturation, value) where hue is in degrees (0-360)
        """
        r, g, b = rgb / 255.0
        
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        delta = max_val - min_val
        
        # Value
        v = max_val
        
        # Saturation
        if max_val == 0:
            s = 0
        else:
            s = delta / max_val
        
        # Hue
        if delta == 0:
            h = 0
        elif max_val == r:
            h = 60 * (((g - b) / delta) % 6)
        elif max_val == g:
            h = 60 * (((b - r) / delta) + 2)
        else:
            h = 60 * (((r - g) / delta) + 4)
        
        return (h, s, v)
    
    def _rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex string."""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex string to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _fallback_palette(self) -> ColorPalette:
        """Return a fallback palette when extraction fails."""
        return ColorPalette(
            colors_hex=["#1A1A2E", "#16213E", "#0F3460", "#533483", "#E94560"],
            percentages=[0.25, 0.20, 0.20, 0.20, 0.15],
            purple_score=0.20,
            morado_ratio=0.20,
            dominant_color="#1A1A2E"
        )
    
    def is_purple_aesthetic(self, palette: ColorPalette, threshold: float = 0.5) -> bool:
        """
        Check if palette matches Stakazo's purple aesthetic.
        
        Args:
            palette: ColorPalette
            threshold: Minimum purple_score to consider purple aesthetic
        
        Returns:
            True if purple aesthetic
        """
        return palette.purple_score >= threshold
    
    def get_aesthetic_category(self, palette: ColorPalette) -> str:
        """
        Categorize palette into aesthetic categories.
        
        Args:
            palette: ColorPalette
        
        Returns:
            Aesthetic category name
        """
        if palette.purple_score > 0.6:
            return "morado_dominante"
        elif palette.purple_score > 0.3:
            return "morado_presente"
        
        # Check brightness
        avg_brightness = self._get_brightness_from_hex(palette.dominant_color)
        
        if avg_brightness < 0.3:
            return "oscuro"
        elif avg_brightness > 0.7:
            return "luminoso"
        else:
            return "equilibrado"
    
    def _get_brightness_from_hex(self, hex_color: str) -> float:
        """Calculate brightness from hex color."""
        rgb = self._hex_to_rgb(hex_color)
        r, g, b = [c / 255.0 for c in rgb]
        # Relative luminance
        return 0.299 * r + 0.587 * g + 0.114 * b

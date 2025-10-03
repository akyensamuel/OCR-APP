"""
Smart Image Preprocessing Module
Handles complex real-world document images with advanced preprocessing techniques
"""
import cv2
import numpy as np
from PIL import Image, ImageEnhance
import logging
from typing import Tuple, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ImageQualityMetrics:
    """Metrics for assessing image quality"""
    brightness: float
    contrast: float
    sharpness: float
    noise_level: float
    skew_angle: float
    resolution: Tuple[int, int]
    quality_score: float  # 0-100


class SmartImagePreprocessor:
    """
    Advanced image preprocessing for complex real-world documents
    Handles handwriting, skew, shadows, low contrast, and more
    """
    
    def __init__(self):
        self.min_quality_score = 60
        
    def analyze_image_quality(self, image: np.ndarray) -> ImageQualityMetrics:
        """
        Analyze image to determine optimal preprocessing strategy
        
        Args:
            image: Input image (BGR or grayscale)
            
        Returns:
            ImageQualityMetrics with analysis results
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Measure brightness (mean intensity)
        brightness = np.mean(gray)
        
        # Measure contrast (standard deviation)
        contrast = np.std(gray)
        
        # Measure sharpness (Laplacian variance)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = laplacian.var()
        
        # Estimate noise level
        noise_level = self._estimate_noise(gray)
        
        # Detect skew angle
        skew_angle = self._detect_skew_angle(gray)
        
        # Calculate overall quality score
        quality_score = self._calculate_quality_score(
            brightness, contrast, sharpness, noise_level
        )
        
        metrics = ImageQualityMetrics(
            brightness=brightness,
            contrast=contrast,
            sharpness=sharpness,
            noise_level=noise_level,
            skew_angle=skew_angle,
            resolution=gray.shape,
            quality_score=quality_score
        )
        
        logger.info(f"Image Quality - Score: {quality_score:.1f}, "
                   f"Brightness: {brightness:.1f}, Contrast: {contrast:.1f}, "
                   f"Sharpness: {sharpness:.1f}, Skew: {skew_angle:.2f}°")
        
        return metrics
    
    def _estimate_noise(self, gray: np.ndarray) -> float:
        """Estimate noise level using median absolute deviation"""
        H, W = gray.shape
        M = [[1, -2, 1],
             [-2, 4, -2],
             [1, -2, 1]]
        sigma = np.sum(np.sum(np.absolute(cv2.filter2D(gray, -1, np.array(M)))))
        sigma = sigma * np.sqrt(0.5 * np.pi) / (6 * (W-2) * (H-2))
        return sigma
    
    def _detect_skew_angle(self, gray: np.ndarray) -> float:
        """
        Detect document skew angle using Hough Line Transform
        
        Returns:
            Skew angle in degrees
        """
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Detect lines
        lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
        
        if lines is None:
            return 0.0
        
        # Calculate angles
        angles = []
        for rho, theta in lines[:, 0]:
            angle = np.degrees(theta) - 90
            # Filter out vertical and horizontal lines
            if -45 < angle < 45:
                angles.append(angle)
        
        if not angles:
            return 0.0
        
        # Return median angle
        return float(np.median(angles))
    
    def _calculate_quality_score(self, brightness: float, contrast: float, 
                                 sharpness: float, noise: float) -> float:
        """Calculate overall image quality score (0-100)"""
        # Normalize metrics
        brightness_score = 100 * (1 - abs(brightness - 127.5) / 127.5)  # Ideal: 127.5
        contrast_score = min(100, contrast / 50 * 100)  # Ideal: 50+
        sharpness_score = min(100, sharpness / 500 * 100)  # Ideal: 500+
        noise_score = max(0, 100 - noise * 2)  # Lower is better
        
        # Weighted average
        score = (
            brightness_score * 0.3 +
            contrast_score * 0.3 +
            sharpness_score * 0.2 +
            noise_score * 0.2
        )
        
        return score
    
    def auto_rotate(self, image: np.ndarray, angle: float) -> np.ndarray:
        """
        Rotate image to correct skew
        
        Args:
            image: Input image
            angle: Rotation angle in degrees
            
        Returns:
            Rotated image
        """
        if abs(angle) < 0.5:
            return image
        
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        
        # Calculate rotation matrix
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Calculate new image size to avoid cropping
        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])
        new_w = int((h * sin) + (w * cos))
        new_h = int((h * cos) + (w * sin))
        
        # Adjust transformation matrix
        M[0, 2] += (new_w / 2) - center[0]
        M[1, 2] += (new_h / 2) - center[1]
        
        # Rotate with white background
        rotated = cv2.warpAffine(
            image, M, (new_w, new_h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=255
        )
        
        logger.info(f"Rotated image by {angle:.2f}°")
        return rotated
    
    def remove_shadows(self, image: np.ndarray) -> np.ndarray:
        """
        Remove shadows and lighting variations using morphological operations
        
        Args:
            image: Grayscale image
            
        Returns:
            Shadow-corrected image
        """
        # Dilate to remove text, leaving only background
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        dilated = cv2.dilate(image, kernel, iterations=2)
        
        # Blur the background
        background = cv2.medianBlur(dilated, 21)
        
        # Subtract background from original
        corrected = cv2.absdiff(image, background)
        
        # Invert if needed
        corrected = 255 - corrected
        
        logger.info("Shadow removal applied")
        return corrected
    
    def enhance_contrast_adaptive(self, image: np.ndarray) -> np.ndarray:
        """
        Apply adaptive histogram equalization (CLAHE)
        
        Args:
            image: Grayscale image
            
        Returns:
            Contrast-enhanced image
        """
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(image)
        
        logger.info("Adaptive contrast enhancement applied")
        return enhanced
    
    def denoise_smart(self, image: np.ndarray, noise_level: float) -> np.ndarray:
        """
        Apply noise reduction based on detected noise level
        
        Args:
            image: Grayscale image
            noise_level: Estimated noise level
            
        Returns:
            Denoised image
        """
        if noise_level < 5:
            # Low noise - no denoising needed
            return image
        elif noise_level < 15:
            # Medium noise - gentle denoising
            denoised = cv2.fastNlMeansDenoising(image, None, h=10, templateWindowSize=7, searchWindowSize=21)
        else:
            # High noise - aggressive denoising
            denoised = cv2.fastNlMeansDenoising(image, None, h=15, templateWindowSize=7, searchWindowSize=21)
        
        logger.info(f"Denoising applied (noise level: {noise_level:.2f})")
        return denoised
    
    def sharpen_if_needed(self, image: np.ndarray, sharpness: float) -> np.ndarray:
        """
        Apply sharpening if image is blurry
        
        Args:
            image: Grayscale image
            sharpness: Measured sharpness score
            
        Returns:
            Sharpened image
        """
        if sharpness > 300:
            # Image is sharp enough
            return image
        
        # Create sharpening kernel
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        
        sharpened = cv2.filter2D(image, -1, kernel)
        
        logger.info(f"Sharpening applied (sharpness: {sharpness:.1f})")
        return sharpened
    
    def normalize_brightness(self, image: np.ndarray, target: float = 180) -> np.ndarray:
        """
        Normalize image brightness to target level
        
        Args:
            image: Grayscale image
            target: Target mean brightness (0-255)
            
        Returns:
            Brightness-normalized image
        """
        current_mean = np.mean(image)
        
        if abs(current_mean - target) < 10:
            return image
        
        # Calculate adjustment factor
        factor = target / current_mean
        
        # Apply adjustment
        normalized = np.clip(image * factor, 0, 255).astype(np.uint8)
        
        logger.info(f"Brightness normalized from {current_mean:.1f} to {target:.1f}")
        return normalized
    
    def binarize_adaptive(self, image: np.ndarray, method: str = "auto") -> np.ndarray:
        """
        Apply adaptive binarization for better text/background separation
        
        Args:
            image: Grayscale image
            method: "otsu", "adaptive", or "auto"
            
        Returns:
            Binary image
        """
        if method == "auto":
            # Try both methods and pick best
            otsu_binary = self._apply_otsu(image)
            adaptive_binary = self._apply_adaptive(image)
            
            # Compare results (prefer higher text-to-background ratio)
            otsu_ratio = np.sum(otsu_binary == 0) / otsu_binary.size
            adaptive_ratio = np.sum(adaptive_binary == 0) / adaptive_binary.size
            
            # Pick method with ratio closer to 15-20% (typical for documents)
            otsu_score = abs(otsu_ratio - 0.175)
            adaptive_score = abs(adaptive_ratio - 0.175)
            
            if otsu_score < adaptive_score:
                logger.info(f"Using Otsu binarization (ratio: {otsu_ratio:.2%})")
                return otsu_binary
            else:
                logger.info(f"Using adaptive binarization (ratio: {adaptive_ratio:.2%})")
                return adaptive_binary
        
        elif method == "otsu":
            return self._apply_otsu(image)
        else:
            return self._apply_adaptive(image)
    
    def _apply_otsu(self, image: np.ndarray) -> np.ndarray:
        """Apply Otsu's thresholding"""
        _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary
    
    def _apply_adaptive(self, image: np.ndarray) -> np.ndarray:
        """Apply adaptive thresholding"""
        binary = cv2.adaptiveThreshold(
            image, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=11,
            C=2
        )
        return binary
    
    def preprocess_for_table_detection(self, image: np.ndarray) -> Tuple[np.ndarray, ImageQualityMetrics]:
        """
        Complete preprocessing pipeline optimized for table detection
        
        Args:
            image: Input image (BGR or grayscale)
            
        Returns:
            Tuple of (preprocessed_image, quality_metrics)
        """
        logger.info("Starting smart preprocessing pipeline")
        
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Analyze image quality
        metrics = self.analyze_image_quality(gray)
        
        # Step 1: Remove shadows
        gray = self.remove_shadows(gray)
        
        # Step 2: Normalize brightness
        gray = self.normalize_brightness(gray, target=180)
        
        # Step 3: Denoise based on noise level
        gray = self.denoise_smart(gray, metrics.noise_level)
        
        # Step 4: Enhance contrast
        gray = self.enhance_contrast_adaptive(gray)
        
        # Step 5: Sharpen if needed
        gray = self.sharpen_if_needed(gray, metrics.sharpness)
        
        # Step 6: Rotate to correct skew
        if abs(metrics.skew_angle) > 0.5:
            gray = self.auto_rotate(gray, metrics.skew_angle)
        
        logger.info("Smart preprocessing completed")
        
        return gray, metrics
    
    def preprocess_for_ocr(self, image: np.ndarray, enhance_handwriting: bool = True) -> np.ndarray:
        """
        Preprocessing pipeline optimized for OCR (especially handwriting)
        
        Args:
            image: Input image
            enhance_handwriting: Apply handwriting-specific enhancements
            
        Returns:
            Preprocessed image ready for OCR
        """
        logger.info("Starting OCR preprocessing")
        
        # Basic preprocessing
        processed, metrics = self.preprocess_for_table_detection(image)
        
        if enhance_handwriting:
            # Additional steps for handwriting
            # Slight blur to connect broken characters
            processed = cv2.GaussianBlur(processed, (3, 3), 0)
            
            # Morphological closing to connect broken strokes
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
            processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
        
        # Final binarization
        binary = self.binarize_adaptive(processed, method="auto")
        
        logger.info("OCR preprocessing completed")
        
        return binary

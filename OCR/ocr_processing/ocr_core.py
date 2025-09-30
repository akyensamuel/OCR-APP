"""
OCR Core Processing Module
Handles text extraction from images using multiple OCR engines
"""
import cv2
import numpy as np
import pytesseract
import easyocr
from PIL import Image, ImageEnhance
import json
import logging
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class OCRResult:
    """Container for OCR processing results"""
    text: str
    confidence: float
    bbox: Optional[Tuple[int, int, int, int]] = None
    engine: str = "unknown"
    
@dataclass
class FieldData:
    """Container for extracted field data"""
    name: str
    value: str
    confidence: float
    bbox: Optional[Tuple[int, int, int, int]] = None

class ImagePreprocessor:
    """Image preprocessing for better OCR results"""
    
    @staticmethod
    def denoise_image(image: np.ndarray) -> np.ndarray:
        """Apply denoising filter to image"""
        return cv2.fastNlMeansDenoising(image)
    
    @staticmethod
    def deskew_image(image: np.ndarray) -> np.ndarray:
        """Correct skew in scanned documents"""
        coords = np.column_stack(np.where(image > 0))
        if len(coords) == 0:
            return image
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        if abs(angle) < 0.5:
            return image
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return rotated
    
    @staticmethod
    def enhance_contrast(image: np.ndarray) -> np.ndarray:
        """Enhance image contrast using CLAHE"""
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        return clahe.apply(image)
    
    @classmethod
    def preprocess_image(cls, image_path: str, 
                        denoise: bool = True,
                        deskew: bool = True, 
                        enhance: bool = True) -> np.ndarray:
        """Complete image preprocessing pipeline"""
        # Load image
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Apply preprocessing steps
        if denoise:
            image = cls.denoise_image(image)
        if enhance:
            image = cls.enhance_contrast(image)
        if deskew:
            image = cls.deskew_image(image)
            
        return image

class OCREngine:
    """Main OCR processing engine supporting multiple backends"""
    
    def __init__(self, preferred_engine: str = "tesseract"):
        self.preferred_engine = preferred_engine
        self.tesseract_available = self._check_tesseract()
        self.easyocr_reader = None
        if preferred_engine == "easyocr":
            self._init_easyocr()
    
    def _check_tesseract(self) -> bool:
        """Check if Tesseract is available"""
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
    
    def _init_easyocr(self):
        """Initialize EasyOCR reader"""
        try:
            self.easyocr_reader = easyocr.Reader(['en'])
        except Exception as e:
            logger.warning(f"Could not initialize EasyOCR: {e}")
    
    def extract_text_tesseract(self, image: np.ndarray) -> OCRResult:
        """Extract text using Tesseract OCR"""
        if not self.tesseract_available:
            raise RuntimeError("Tesseract not available")
        
        # Convert numpy array to PIL Image
        pil_image = Image.fromarray(image)
        
        # Extract text with confidence
        data = pytesseract.image_to_data(pil_image, output_type=pytesseract.Output.DICT)
        text_parts = []
        confidences = []
        
        for i in range(len(data['text'])):
            if int(data['conf'][i]) > 0:  # Filter out low confidence
                text_parts.append(data['text'][i])
                confidences.append(float(data['conf'][i]))
        
        text = ' '.join(text_parts).strip()
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return OCRResult(
            text=text,
            confidence=avg_confidence,
            engine="tesseract"
        )
    
    def extract_text_easyocr(self, image: np.ndarray) -> OCRResult:
        """Extract text using EasyOCR"""
        if self.easyocr_reader is None:
            raise RuntimeError("EasyOCR not available")
        
        results = self.easyocr_reader.readtext(image)
        text_parts = []
        confidences = []
        
        for (bbox, text, conf) in results:
            if conf > 0.1:  # Filter low confidence
                text_parts.append(text)
                confidences.append(conf)
        
        text = ' '.join(text_parts).strip()
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return OCRResult(
            text=text,
            confidence=avg_confidence * 100,  # Convert to percentage
            engine="easyocr"
        )
    
    def extract_text(self, image_path: str, preprocess: bool = True) -> OCRResult:
        """Main text extraction method"""
        try:
            # Preprocess image if requested
            if preprocess:
                image = ImagePreprocessor.preprocess_image(image_path)
            else:
                image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            
            # Try preferred engine first
            if self.preferred_engine == "tesseract" and self.tesseract_available:
                return self.extract_text_tesseract(image)
            elif self.preferred_engine == "easyocr" and self.easyocr_reader:
                return self.extract_text_easyocr(image)
            
            # Fallback to available engine
            if self.tesseract_available:
                return self.extract_text_tesseract(image)
            elif self.easyocr_reader:
                return self.extract_text_easyocr(image)
            else:
                raise RuntimeError("No OCR engine available")
                
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return OCRResult(text="", confidence=0.0, engine="error")

class TemplateProcessor:
    """Process documents using predefined templates"""
    
    def __init__(self, ocr_engine: OCREngine):
        self.ocr_engine = ocr_engine
    
    def extract_structure_from_template(self, image_path: str) -> Dict[str, Any]:
        """Extract field structure from a template document"""
        ocr_result = self.ocr_engine.extract_text(image_path)
        
        # Basic structure extraction - identify potential form fields
        lines = ocr_result.text.split('\n')
        fields = []
        
        for line in lines:
            line = line.strip()
            if ':' in line or '_' in line or line.endswith('?'):
                # Potential field detected
                field_name = line.replace(':', '').replace('_', ' ').strip()
                if field_name:
                    fields.append({
                        'name': field_name,
                        'type': 'text',
                        'required': True
                    })
        
        return {
            'fields': fields,
            'total_fields': len(fields),
            'extraction_confidence': ocr_result.confidence,
            'ocr_engine': ocr_result.engine
        }
    
    def process_document_with_template(self, image_path: str, template_structure: Dict) -> List[FieldData]:
        """Process a document using a template structure"""
        ocr_result = self.ocr_engine.extract_text(image_path)
        extracted_fields = []
        
        if not template_structure.get('fields'):
            return extracted_fields
        
        # Simple field matching based on proximity and keywords
        text_lines = ocr_result.text.split('\n')
        
        for field_info in template_structure['fields']:
            field_name = field_info['name']
            field_value = self._extract_field_value(text_lines, field_name)
            
            extracted_fields.append(FieldData(
                name=field_name,
                value=field_value,
                confidence=ocr_result.confidence,
                bbox=None
            ))
        
        return extracted_fields
    
    def _extract_field_value(self, text_lines: List[str], field_name: str) -> str:
        """Extract value for a specific field from text lines"""
        field_keywords = field_name.lower().split()
        
        for i, line in enumerate(text_lines):
            line_lower = line.lower()
            
            # Check if line contains field keywords
            if any(keyword in line_lower for keyword in field_keywords):
                # Look for value in same line or next line
                if ':' in line:
                    value = line.split(':', 1)[1].strip()
                    if value:
                        return value
                
                # Check next line
                if i + 1 < len(text_lines):
                    next_line = text_lines[i + 1].strip()
                    if next_line and not ':' in next_line:
                        return next_line
        
        return ""  # Field not found

# Utility functions
def get_supported_formats() -> List[str]:
    """Get list of supported image formats"""
    return ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']

def validate_image_format(filename: str) -> bool:
    """Validate if file format is supported"""
    import os
    ext = os.path.splitext(filename)[1].lower()
    return ext in get_supported_formats()

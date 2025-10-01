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
            # Fix Windows Unicode issues by setting proper locale
            import os
            import locale
            
            # Set UTF-8 encoding for Windows
            if os.name == 'nt':  # Windows
                try:
                    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
                except:
                    try:
                        locale.setlocale(locale.LC_ALL, '')
                    except:
                        pass
            
            # Initialize with verbose=False to avoid Unicode progress bar issues
            self.easyocr_reader = easyocr.Reader(['en'], verbose=False)
        except Exception as e:
            logger.warning(f"Could not initialize EasyOCR: {e}")
            self.easyocr_reader = None
    
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
            # Check if it's a PDF file
            if image_path.lower().endswith('.pdf'):
                return self._process_pdf(image_path, preprocess)
            
            # Preprocess image if requested
            if preprocess:
                image = ImagePreprocessor.preprocess_image(image_path)
            else:
                image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
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
    
    def _process_pdf(self, pdf_path: str, preprocess: bool = True) -> OCRResult:
        """Process PDF file by converting to images first"""
        try:
            # Try to process PDF if pdf2image is available
            try:
                from pdf2image import convert_from_path
                
                # Convert PDF to images
                images = convert_from_path(pdf_path, first_page=1, last_page=1)  # Process first page only
                if not images:
                    raise ValueError("No images extracted from PDF")
                
                # Convert PIL image to numpy array
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    images[0].save(tmp.name, 'PNG')
                    
                    # Process the image with OCR
                    if preprocess:
                        image = ImagePreprocessor.preprocess_image(tmp.name)
                    else:
                        image = cv2.imread(tmp.name, cv2.IMREAD_GRAYSCALE)
                    
                    # Extract text using available engine
                    if self.preferred_engine == "tesseract" and self.tesseract_available:
                        result = self.extract_text_tesseract(image)
                    elif self.preferred_engine == "easyocr" and self.easyocr_reader:
                        result = self.extract_text_easyocr(image)
                    elif self.tesseract_available:
                        result = self.extract_text_tesseract(image)
                    elif self.easyocr_reader:
                        result = self.extract_text_easyocr(image)
                    else:
                        return OCRResult(text="", confidence=0.0, engine="no_engine")
                    
                    # Clean up temp file
                    import os
                    os.unlink(tmp.name)
                    
                    return OCRResult(
                        text=result.text,
                        confidence=result.confidence,
                        engine=f"pdf_{result.engine}"
                    )
                    
            except ImportError:
                # pdf2image not available, return informative message
                return OCRResult(
                    text="PDF processing requires pdf2image library. Please install it for PDF support.",
                    confidence=0.0,
                    engine="pdf_missing_dependency"
                )
                
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            return OCRResult(
                text=f"PDF processing error: {str(e)}",
                confidence=0.0,
                engine="pdf_error"
            )

class TemplateProcessor:
    """Process documents using predefined templates"""
    
    def __init__(self, ocr_engine: OCREngine):
        self.ocr_engine = ocr_engine
    
    def extract_structure_from_template(self, image_path: str) -> Dict[str, Any]:
        """Extract field structure from a template document"""
        ocr_result = self.ocr_engine.extract_text(image_path)
        
        # Check if OCR was successful
        if not ocr_result.text or ocr_result.engine == "error":
            # Return empty structure with error information
            return {
                'fields': [],
                'total_fields': 0,
                'extraction_confidence': 0.0,
                'ocr_engine': ocr_result.engine,
                'error': 'OCR extraction failed - no text extracted'
            }
        
        # Enhanced structure extraction - identify potential form fields
        lines = ocr_result.text.split('\n')
        fields = []
        
        for line in lines:
            line = line.strip()
            if line:  # Skip empty lines
                # More flexible field detection patterns
                potential_field = None
                
                # Pattern 1: "Label:" format
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        label = parts[0].strip()
                        if label and not label.isupper() or len(label.split()) <= 3:  # Reasonable field names
                            potential_field = label
                
                # Pattern 2: "Label ___" format (underscores indicating blank space)
                elif '_' in line and line.count('_') >= 3:
                    # Find text before underscores
                    underscore_pos = line.find('_')
                    if underscore_pos > 0:
                        label = line[:underscore_pos].strip()
                        if label and len(label.split()) <= 4:
                            potential_field = label
                
                # Pattern 3: Question format
                elif line.endswith('?'):
                    if len(line) < 50:  # Reasonable question length
                        potential_field = line[:-1].strip()
                
                # Pattern 4: Common form words
                elif any(word in line.lower() for word in ['name', 'address', 'phone', 'email', 'date', 'number', 'id']):
                    if len(line) < 30:  # Short enough to be a field label
                        potential_field = line
                
                # Add field if detected and valid
                if potential_field:
                    # Clean up the field name
                    field_name = potential_field.replace('_', ' ').strip()
                    if field_name and field_name not in [f['name'] for f in fields]:  # Avoid duplicates
                        fields.append({
                            'name': field_name,
                            'type': 'text',
                            'required': True
                        })
        
        return {
            'fields': fields,
            'total_fields': len(fields),
            'extraction_confidence': ocr_result.confidence,
            'ocr_engine': ocr_result.engine,
            'raw_text': ocr_result.text  # Include raw text for debugging
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

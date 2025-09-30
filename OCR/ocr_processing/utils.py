"""
OCR Processing Utilities
Common helper functions for file handling, validation, and processing
"""
import os
import uuid
import mimetypes
from typing import List, Optional, Tuple
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Supported file formats
SUPPORTED_IMAGE_FORMATS = ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif']
SUPPORTED_PDF_FORMATS = ['.pdf']
SUPPORTED_FORMATS = SUPPORTED_IMAGE_FORMATS + SUPPORTED_PDF_FORMATS

# File size limits (in bytes)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_IMAGE_DIMENSION = 4000  # Max width/height in pixels

def validate_uploaded_file(uploaded_file: UploadedFile) -> Tuple[bool, str]:
    """
    Validate uploaded file for OCR processing
    
    Args:
        uploaded_file: Django UploadedFile instance
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file size
    if uploaded_file.size > MAX_FILE_SIZE:
        return False, f"File size ({uploaded_file.size / 1024 / 1024:.1f}MB) exceeds maximum allowed size (50MB)"
    
    # Check file extension
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    if file_ext not in SUPPORTED_FORMATS:
        return False, f"Unsupported file format: {file_ext}. Supported formats: {', '.join(SUPPORTED_FORMATS)}"
    
    # Check MIME type
    mime_type, _ = mimetypes.guess_type(uploaded_file.name)
    allowed_mime_types = [
        'image/png', 'image/jpeg', 'image/tiff', 'image/bmp', 'image/gif',
        'application/pdf'
    ]
    
    if mime_type not in allowed_mime_types:
        return False, f"Invalid MIME type: {mime_type}"
    
    return True, ""

def generate_unique_filename(original_filename: str, prefix: str = "") -> str:
    """
    Generate unique filename to avoid conflicts
    
    Args:
        original_filename: Original uploaded filename
        prefix: Optional prefix for the filename
        
    Returns:
        Unique filename with original extension
    """
    name, ext = os.path.splitext(original_filename)
    unique_id = str(uuid.uuid4())[:8]
    
    if prefix:
        return f"{prefix}_{unique_id}_{name}{ext}"
    else:
        return f"{unique_id}_{name}{ext}"

def get_file_upload_path(instance, filename: str) -> str:
    """
    Generate upload path for files
    
    Args:
        instance: Model instance
        filename: Original filename
        
    Returns:
        Upload path relative to MEDIA_ROOT
    """
    # Determine subfolder based on file type
    file_ext = os.path.splitext(filename)[1].lower()
    
    if file_ext in SUPPORTED_PDF_FORMATS:
        subfolder = 'pdfs'
    elif file_ext in SUPPORTED_IMAGE_FORMATS:
        subfolder = 'images'
    else:
        subfolder = 'others'
    
    # Generate unique filename
    unique_filename = generate_unique_filename(filename)
    
    return os.path.join('uploads', subfolder, unique_filename)

def cleanup_temporary_files(file_paths: List[str]) -> None:
    """
    Clean up temporary files after processing
    
    Args:
        file_paths: List of file paths to delete
    """
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup file {file_path}: {e}")

def ensure_media_directories() -> None:
    """
    Ensure all required media directories exist
    """
    base_dirs = [
        'uploads/images',
        'uploads/pdfs',
        'uploads/others',
        'processed',
        'templates',
        'exports'
    ]
    
    media_root = getattr(settings, 'MEDIA_ROOT', 'media')
    
    for dir_path in base_dirs:
        full_path = os.path.join(media_root, dir_path)
        try:
            os.makedirs(full_path, exist_ok=True)
            logger.debug(f"Ensured directory exists: {full_path}")
        except Exception as e:
            logger.error(f"Failed to create directory {full_path}: {e}")

def get_file_info(file_path: str) -> dict:
    """
    Get comprehensive file information
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file information
    """
    if not os.path.exists(file_path):
        return {'error': 'File not found'}
    
    stat = os.stat(file_path)
    file_info = {
        'path': file_path,
        'name': os.path.basename(file_path),
        'size': stat.st_size,
        'size_mb': round(stat.st_size / 1024 / 1024, 2),
        'extension': os.path.splitext(file_path)[1].lower(),
        'mime_type': mimetypes.guess_type(file_path)[0],
        'created': stat.st_ctime,
        'modified': stat.st_mtime,
        'is_image': os.path.splitext(file_path)[1].lower() in SUPPORTED_IMAGE_FORMATS,
        'is_pdf': os.path.splitext(file_path)[1].lower() in SUPPORTED_PDF_FORMATS
    }
    
    return file_info

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent security issues
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = os.path.basename(filename)
    
    # Replace problematic characters
    problematic_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
    for char in problematic_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    return name + ext

def convert_pdf_to_images(pdf_path: str, output_dir: str) -> List[str]:
    """
    Convert PDF pages to images for OCR processing
    Note: This function requires pdf2image library
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save converted images
        
    Returns:
        List of paths to converted image files
    """
    try:
        from pdf2image import convert_from_path
        
        # Convert PDF to images
        pages = convert_from_path(pdf_path, dpi=300)
        image_paths = []
        
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        
        for i, page in enumerate(pages):
            image_path = os.path.join(output_dir, f"{base_name}_page_{i+1}.png")
            page.save(image_path, 'PNG')
            image_paths.append(image_path)
            
        logger.info(f"Converted PDF to {len(image_paths)} images")
        return image_paths
        
    except ImportError:
        logger.error("pdf2image library not installed. Cannot convert PDF to images.")
        return []
    except Exception as e:
        logger.error(f"Error converting PDF to images: {e}")
        return []

def calculate_processing_confidence(confidences: List[float]) -> float:
    """
    Calculate overall processing confidence from individual confidences
    
    Args:
        confidences: List of confidence scores (0-100)
        
    Returns:
        Overall confidence score (0-100)
    """
    if not confidences:
        return 0.0
    
    # Use weighted average with emphasis on higher confidences
    sorted_confidences = sorted(confidences, reverse=True)
    weights = [1.0 / (i + 1) for i in range(len(sorted_confidences))]
    
    weighted_sum = sum(conf * weight for conf, weight in zip(sorted_confidences, weights))
    weight_sum = sum(weights)
    
    return weighted_sum / weight_sum if weight_sum > 0 else 0.0

def format_processing_time(seconds: float) -> str:
    """
    Format processing time in human-readable format
    
    Args:
        seconds: Processing time in seconds
        
    Returns:
        Formatted time string
    """
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"

def get_processing_status_display(status: str) -> str:
    """
    Get human-readable display text for processing status
    
    Args:
        status: Processing status code
        
    Returns:
        Display text for status
    """
    status_mapping = {
        'pending': 'Pending Processing',
        'processing': 'Processing...',
        'completed': 'Completed Successfully',
        'failed': 'Processing Failed',
        'error': 'Error Occurred'
    }
    
    return status_mapping.get(status, status.title())

# Initialize media directories on import
try:
    ensure_media_directories()
except Exception:
    pass  # Ignore errors during initialization

"""
Utility functions for handling file storage in database
"""
import io
import mimetypes
from django.http import HttpResponse, FileResponse
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile


def save_file_to_db(uploaded_file):
    """
    Save an uploaded file to database-compatible format
    
    Args:
        uploaded_file: Django UploadedFile object
        
    Returns:
        dict with file_data, file_name, file_type, file_size
    """
    # Read file data
    if hasattr(uploaded_file, 'read'):
        file_data = uploaded_file.read()
    else:
        file_data = uploaded_file
    
    # Get file metadata
    file_name = getattr(uploaded_file, 'name', 'unknown_file')
    file_type = getattr(uploaded_file, 'content_type', None)
    
    if not file_type:
        file_type, _ = mimetypes.guess_type(file_name)
        if not file_type:
            file_type = 'application/octet-stream'
    
    file_size = len(file_data)
    
    return {
        'file_data': file_data,
        'file_name': file_name,
        'file_type': file_type,
        'file_size': file_size
    }


def get_temp_file_path(file_data, file_name):
    """
    Create a temporary file from binary data for processing
    
    Args:
        file_data: Binary file data
        file_name: Original filename
        
    Returns:
        Path to temporary file
    """
    import tempfile
    import os
    
    # Create temp file with original extension
    _, ext = os.path.splitext(file_name)
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
        temp_file.write(file_data)
        temp_path = temp_file.name
    
    return temp_path


def serve_file_from_db(file_data, file_name, file_type, as_attachment=True):
    """
    Serve a file from database storage
    
    Args:
        file_data: Binary file data
        file_name: Filename for download
        file_type: MIME type
        as_attachment: Whether to force download
        
    Returns:
        HttpResponse with file
    """
    response = HttpResponse(file_data, content_type=file_type)
    
    if as_attachment:
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    else:
        response['Content-Disposition'] = f'inline; filename="{file_name}"'
    
    response['Content-Length'] = len(file_data)
    
    return response


def create_file_response_from_db(file_data, file_name, file_type):
    """
    Create a FileResponse from database binary data
    
    Args:
        file_data: Binary file data
        file_name: Filename
        file_type: MIME type
        
    Returns:
        FileResponse
    """
    file_stream = io.BytesIO(file_data)
    response = FileResponse(file_stream, content_type=file_type)
    response['Content-Disposition'] = f'inline; filename="{file_name}"'
    return response


def read_file_from_path(file_path):
    """
    Read a file from path and return binary data
    
    Args:
        file_path: Path to file
        
    Returns:
        dict with file_data, file_name, file_type, file_size
    """
    import os
    
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    file_name = os.path.basename(file_path)
    file_type, _ = mimetypes.guess_type(file_path)
    if not file_type:
        file_type = 'application/octet-stream'
    
    file_size = len(file_data)
    
    return {
        'file_data': file_data,
        'file_name': file_name,
        'file_type': file_type,
        'file_size': file_size
    }


def cleanup_temp_file(temp_path):
    """
    Delete temporary file
    
    Args:
        temp_path: Path to temporary file
    """
    import os
    try:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not delete temp file {temp_path}: {e}")

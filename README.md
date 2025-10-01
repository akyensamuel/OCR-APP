# OCR Web Application

A comprehensive Django-based OCR (Optical Character Recognition) web application that supports multiple workflows for document processing and text extraction.

## Features

### 🔍 Template-Based Processing
- Upload template forms to extract field structure
- Process multiple documents using the same template
- Automatic field detection and data extraction
- Structured JSON output for extracted data

### 📄 General OCR Processing  
- Extract text from any document (PDF, images)
- Support for multiple OCR engines (Tesseract, EasyOCR)
- Image preprocessing for better accuracy
- Manual text editing and correction

### ✏️ Text Editor Mode
- Upload documents for OCR text extraction
- Rich text editing interface
- Export to multiple formats (PDF, Word, HTML, etc.)
- Version control and change tracking

### ⚙️ Advanced Features
- Multiple OCR engine support
- Image preprocessing (denoising, deskewing, contrast enhancement)
- Confidence scoring and quality metrics
- Processing task tracking
- Admin interface for configuration

## Technology Stack

- **Backend**: Django 5.2.6, Django REST Framework
- **OCR Engines**: Tesseract, EasyOCR
- **Image Processing**: OpenCV, Pillow
- **Document Handling**: pdf2image, pdfplumber
- **Frontend**: Bootstrap 5, HTML5, JavaScript
- **Database**: SQLite (development), PostgreSQL (production ready)

## Installation

### Prerequisites
- Python 3.8+
- Tesseract OCR engine
- Virtual environment (recommended)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/akyensamuel/OCR-APP.git
   cd OCR-APP
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv virtual
   # Windows
   virtual\Scripts\activate
   # Linux/Mac
   source virtual/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Tesseract OCR**
   - **Windows**: Download from [GitHub Tesseract releases](https://github.com/UB-Mannheim/tesseract/wiki)
   - **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
   - **macOS**: `brew install tesseract`

5. **Database setup**
   ```bash
   cd OCR
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Web interface: http://127.0.0.1:8000/
   - Admin interface: http://127.0.0.1:8000/admin/

## Usage

### Template-Based Processing

1. **Upload Template**
   - Go to Templates → Upload New Template
   - Upload a blank form (PDF/image)
   - System automatically detects field positions
   - Review extracted field structure

2. **Process Documents**
   - Select an existing template
   - Upload filled documents
   - System extracts data based on template structure
   - Review and export results

### General OCR Processing

1. **Upload Document**
   - Go to Documents → Upload Document
   - Select "General OCR" mode
   - Upload any document or image
   - System extracts all text

2. **Edit and Export**
   - Review extracted text
   - Make corrections if needed
   - Export to desired format

### Text Editor Mode

1. **OCR & Edit**
   - Go to Text Editor → OCR & Edit
   - Upload document for text extraction
   - Use rich text editor for formatting
   - Save versions and track changes
   - Export to multiple formats

## Project Structure

```
OCR/
├── OCR/                    # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── templates/              # Template management app
├── documents/              # Document processing app
├── editor/                 # Text editor app
├── ocr_processing/         # Core OCR engine
├── basemode/              # Base app
├── templates/             # HTML templates
├── static/                # Static files
├── media/                 # User uploads
└── manage.py
```

## Configuration

### OCR Settings
- Configure OCR engines in Admin → OCR Processing → Configurations
- Adjust preprocessing parameters
- Set confidence thresholds
- Language settings

### File Upload Settings
- Supported formats: PDF, PNG, JPG, JPEG, TIFF, BMP
- Maximum file size: 10MB (configurable)
- Upload paths configurable in settings.py

## API Endpoints

The application provides REST API endpoints for integration:

- `/ocr/api/extract-text/` - General text extraction
- `/ocr/api/extract-template/` - Template structure extraction  
- `/ocr/api/process-document/` - Template-based processing
- `/ocr/api/task/<task_id>/` - Processing status

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Email: support@ocr-app.com

## Roadmap

- [ ] Cloud OCR API integration (Google Vision, AWS Textract)
- [ ] Batch processing capabilities
- [ ] Advanced form field detection
- [ ] Mobile app support
- [ ] Docker containerization
- [ ] Advanced export options
- [ ] OCR accuracy improvements
- [ ] Multi-language support enhancement

## Acknowledgments

- Tesseract OCR team
- EasyOCR developers
- Django community
- Bootstrap team
- All contributors

---

**Version**: 1.0.0  
**Last Updated**: September 2025  
**Author**: Akyen Samuel  
**Repository**: https://github.com/akyensamuel/OCR-APP
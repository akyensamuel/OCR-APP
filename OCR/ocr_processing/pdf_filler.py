"""
PDF Form Filling and Generation Utilities
Handles filling PDF forms with OCR data and creating new PDF documents
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from PyPDF2 import PdfReader, PdfWriter
from datetime import datetime
import os
import io


class PDFFiller:
    """Fill PDF forms and create PDF documents from OCR data"""
    
    def __init__(self):
        self.page_width, self.page_height = letter
        self.margin = 0.75 * inch
        self.styles = getSampleStyleSheet()
        
        # Create custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            spaceAfter=6,
            fontName='Helvetica'
        )
    
    def create_pdf_from_text(self, text, output_path, title="Document", metadata=None):
        """
        Create a PDF from plain text
        
        Args:
            text: The text content
            output_path: Path where the PDF will be saved
            title: Document title
            metadata: Optional dictionary with metadata
        
        Returns:
            Path to the created PDF
        """
        try:
            # Create PDF
            pdf_canvas = canvas.Canvas(output_path, pagesize=letter)
            
            # Set metadata
            pdf_canvas.setTitle(title)
            pdf_canvas.setAuthor("OCR Application")
            pdf_canvas.setSubject("OCR Extracted Document")
            
            # Draw title
            pdf_canvas.setFont("Helvetica-Bold", 16)
            pdf_canvas.drawCentredString(self.page_width / 2, self.page_height - self.margin, title)
            
            # Draw metadata if provided
            y_position = self.page_height - self.margin - 40
            if metadata:
                pdf_canvas.setFont("Helvetica", 9)
                pdf_canvas.setFillColor(colors.grey)
                for key, value in metadata.items():
                    text_line = f"{key}: {value}"
                    pdf_canvas.drawString(self.margin, y_position, text_line)
                    y_position -= 15
                y_position -= 10
            
            # Draw separator line
            pdf_canvas.setStrokeColor(colors.grey)
            pdf_canvas.setLineWidth(0.5)
            pdf_canvas.line(self.margin, y_position, self.page_width - self.margin, y_position)
            y_position -= 20
            
            # Draw text content
            pdf_canvas.setFont("Helvetica", 10)
            pdf_canvas.setFillColor(colors.black)
            
            # Split text into lines that fit the page width
            max_width = self.page_width - (2 * self.margin)
            lines = text.split('\n')
            
            for line in lines:
                # Handle long lines by wrapping
                words = line.split(' ')
                current_line = ""
                
                for word in words:
                    test_line = current_line + word + " "
                    if pdf_canvas.stringWidth(test_line, "Helvetica", 10) < max_width:
                        current_line = test_line
                    else:
                        if current_line:
                            pdf_canvas.drawString(self.margin, y_position, current_line.strip())
                            y_position -= 14
                            current_line = word + " "
                        else:
                            # Word is too long, force it
                            pdf_canvas.drawString(self.margin, y_position, word)
                            y_position -= 14
                    
                    # Check if we need a new page
                    if y_position < self.margin + 20:
                        pdf_canvas.showPage()
                        pdf_canvas.setFont("Helvetica", 10)
                        y_position = self.page_height - self.margin
                
                # Draw remaining text in current_line
                if current_line.strip():
                    pdf_canvas.drawString(self.margin, y_position, current_line.strip())
                    y_position -= 14
                
                # Check if we need a new page
                if y_position < self.margin + 20:
                    pdf_canvas.showPage()
                    pdf_canvas.setFont("Helvetica", 10)
                    y_position = self.page_height - self.margin
            
            # Add footer
            pdf_canvas.setFont("Helvetica", 8)
            pdf_canvas.setFillColor(colors.grey)
            footer_text = f"Generated by OCR Application - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            pdf_canvas.drawCentredString(self.page_width / 2, self.margin / 2, footer_text)
            
            pdf_canvas.save()
            return output_path
            
        except Exception as e:
            raise Exception(f"Error creating PDF from text: {str(e)}")
    
    def create_pdf_from_template_data(self, document, template, output_path):
        """
        Create a clean PDF from template-based document data with minimal metadata
        
        Args:
            document: Document model instance
            template: Template model instance
            output_path: Path where the PDF will be saved
        
        Returns:
            Path to the created PDF
        """
        try:
            # Create document with custom page template for header/footer
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=self.margin,
                leftMargin=self.margin,
                topMargin=self.margin + 20,  # Extra space for header
                bottomMargin=self.margin + 15  # Extra space for footer
            )
            
            # Container for the 'Flowable' objects
            elements = []
            
            # Add minimal header with document name (small)
            header_style = ParagraphStyle(
                'MinimalHeader',
                parent=self.normal_style,
                fontSize=8,
                textColor=colors.grey,
                alignment=1  # Center
            )
            header_text = f"{document.name} | Template: {template.name} | {document.created_at.strftime('%Y-%m-%d %H:%M')}"
            header = Paragraph(header_text, header_style)
            elements.append(header)
            elements.append(Spacer(1, 8))
            
            # Extract and format data - FOCUS ON THE TABLE
            extracted_data = document.extracted_data
            
            if 'cells' in extracted_data:
                # Table format - PRIMARY USE CASE
                cells = extracted_data['cells']
                rows_count = extracted_data.get('rows', 0)
                cols_count = extracted_data.get('cols', 0)
                
                if cells and rows_count > 0 and cols_count > 0:
                    # Build table data
                    table_data = [['' for _ in range(cols_count)] for _ in range(rows_count)]
                    
                    for cell_data in cells:
                        row = cell_data.get('row', 0)
                        col = cell_data.get('col', 0)
                        text = cell_data.get('text', '')
                        
                        if row < rows_count and col < cols_count:
                            table_data[row][col] = text
                    
                    # Calculate optimal column widths based on content
                    available_width = 6.5 * inch  # Page width minus margins
                    col_widths = [available_width / cols_count] * cols_count
                    
                    # Create clean, professional table
                    data_table = Table(table_data, colWidths=col_widths)
                    
                    # Clean table style with professional colors
                    table_style = [
                        # Header row styling
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                        
                        # Data rows styling
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 11),
                        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                        
                        # Grid and spacing
                        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                        ('TOPPADDING', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                        
                        # Alternating row colors for readability
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
                    ]
                    
                    data_table.setStyle(TableStyle(table_style))
                    elements.append(data_table)
            
            elif 'fields' in extracted_data:
                # Template-based format (fallback)
                data_rows = [['Field Name', 'Value']]
                
                for field in extracted_data['fields']:
                    field_name = field.get('name', '')
                    value = str(field.get('value', ''))
                    data_rows.append([field_name, value])
                
                # Cleaner two-column layout
                col_widths = [2.5*inch, 4*inch]
                data_table = Table(data_rows, colWidths=col_widths)
                data_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 11),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
                ]))
                
                elements.append(data_table)
            
            # Add minimal footer with metadata
            elements.append(Spacer(1, 0.3*inch))
            footer_style = ParagraphStyle(
                'MinimalFooter',
                parent=self.normal_style,
                fontSize=7,
                textColor=colors.grey,
                alignment=1  # Center
            )
            footer_text = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Status: {document.get_processing_status_display()}"
            if document.confidence_score:
                footer_text += f" | Avg. Confidence: {document.confidence_score:.1f}%"
            footer = Paragraph(footer_text, footer_style)
            elements.append(footer)
            
            # Build PDF
            doc.build(elements)
            return output_path
            
        except Exception as e:
            raise Exception(f"Error creating PDF from template data: {str(e)}")
    
    def create_consolidated_pdf(self, documents, template, output_path):
        """
        Create a consolidated PDF report from multiple documents
        
        Args:
            documents: List of Document model instances
            template: Template model instance
            output_path: Path where the PDF will be saved
        
        Returns:
            Path to the created PDF
        """
        try:
            # Create document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=self.margin,
                leftMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin
            )
            
            elements = []
            
            # Add title
            title = Paragraph(f"Consolidated Report: {template.name}", self.title_style)
            elements.append(title)
            elements.append(Spacer(1, 12))
            
            # Add summary info
            summary_data = [
                ['Total Documents:', str(len(documents))],
                ['Template:', template.name],
                ['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                ['Fields:', str(template.field_count)],
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8e8e8')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(summary_table)
            elements.append(Spacer(1, 20))
            
            # Add consolidated data table
            header = Paragraph("Data Summary", self.heading_style)
            elements.append(header)
            elements.append(Spacer(1, 12))
            
            # Get field names
            field_names = template.get_field_names()
            
            if field_names:
                # Build table data
                table_data = [['Document'] + field_names]
                
                for doc_obj in documents:
                    row = [doc_obj.name[:30]]  # Truncate long names
                    
                    extracted_data = doc_obj.extracted_data
                    
                    if 'fields' in extracted_data:
                        for field in extracted_data['fields']:
                            value = str(field.get('value', ''))[:50]  # Truncate long values
                            row.append(value)
                    elif 'cells' in extracted_data:
                        # Extract from table format - add ALL data rows (skip header row 0)
                        cells = extracted_data['cells']
                        # Group cells by row
                        cell_rows = {}
                        for cell_data in cells:
                            cell_row = cell_data.get('row', 0)
                            col = cell_data.get('col', 0)
                            text = cell_data.get('text', '')
                            if cell_row not in cell_rows:
                                cell_rows[cell_row] = {}
                            cell_rows[cell_row][col] = text
                        
                        # Add a row for each data row in the table (skip header at row 0)
                        for data_row_idx in sorted(cell_rows.keys()):
                            if data_row_idx > 0:  # Skip header row
                                if data_row_idx > 1:
                                    # Add new row with repeated document name
                                    row = [doc_obj.name[:30]]
                                
                                for col_idx in range(len(field_names)):
                                    value = cell_rows[data_row_idx].get(col_idx, '')[:50]
                                    row.append(value)
                                
                                table_data.append(row)
                                
                        # Continue to next document (skip default row.append)
                        continue
                    else:
                        row.extend([''] * len(field_names))
                    
                    table_data.append(row)
                
                # Calculate column widths
                available_width = 6.5 * inch
                col_widths = [1.5*inch] + [(available_width - 1.5*inch) / len(field_names)] * len(field_names)
                
                consolidated_table = Table(table_data, colWidths=col_widths)
                consolidated_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                ]))
                
                elements.append(consolidated_table)
            
            # Add page break before individual details
            elements.append(PageBreak())
            
            # Add individual document details
            header = Paragraph("Individual Document Details", self.heading_style)
            elements.append(header)
            elements.append(Spacer(1, 12))
            
            for i, doc_obj in enumerate(documents, 1):
                # Document heading
                doc_heading = Paragraph(f"{i}. {doc_obj.name}", self.heading_style)
                elements.append(doc_heading)
                elements.append(Spacer(1, 6))
                
                # Document data
                extracted_data = doc_obj.extracted_data
                
                if 'fields' in extracted_data:
                    data_rows = [['Field', 'Value']]
                    for field in extracted_data['fields']:
                        data_rows.append([field.get('name', ''), str(field.get('value', ''))])
                    
                    detail_table = Table(data_rows, colWidths=[2*inch, 4*inch])
                    detail_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8e8e8')),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('LEFTPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ]))
                    
                    elements.append(detail_table)
                
                # Add spacing between documents
                if i < len(documents):
                    elements.append(Spacer(1, 20))
            
            # Build PDF
            doc.build(elements)
            return output_path
            
        except Exception as e:
            raise Exception(f"Error creating consolidated PDF: {str(e)}")

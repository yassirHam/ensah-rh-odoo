"""
Document Generator Service for ENSA HR Module
Handles PDF generation, QR codes, and AI-powered document content
"""
import logging
import base64
import io
import qrcode
from typing import Dict, Any, Optional
from datetime import datetime
from odoo import api, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Try to import pdfkit (optional dependency)
try:
    import pdfkit
    PDFKIT_AVAILABLE = True
except ImportError:
    PDFKIT_AVAILABLE = False
    _logger.warning("pdfkit not available - PDF generation will use fallback method")


class DocumentGenerator:
    """Document generation service with AI content"""
    
    def __init__(self, ai_service):
        """
        Initialize document generator
        
        Args:
            ai_service: AIService instance for content generation
        """
        self.ai_service = ai_service
    
    def generate_qr_code(self, data: str, size: int = 200) -> bytes:
        """
        Generate QR code image
        
        Args:
            data: Data to encode (URL, text, etc.)
            size: QR code size in pixels
            
        Returns:
            QR code image as bytes
        """
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            return img_buffer.getvalue()
            
        except Exception as e:
            _logger.error(f"QR code generation error: {str(e)}")
            return b''
    
    def generate_performance_report_html(self, evaluation_data: Dict[str, Any]) -> str:
        """
        Generate HTML for performance report
        
        Args:
            evaluation_data: Evaluation information
            
        Returns:
            HTML content
        """
        # Generate AI commentary
        ai_commentary = self.ai_service.generate_document_content('performance_report', {
            'employee_name': evaluation_data.get('employee_name'),
            'period': evaluation_data.get('period'),
            'overall_score': evaluation_data.get('overall_score'),
            'technical_score': evaluation_data.get('technical_score'),
            'teamwork_score': evaluation_data.get('teamwork_score'),
            'productivity_score': evaluation_data.get('productivity_score'),
            'innovation_score': evaluation_data.get('innovation_score')
        })
        
        # Generate QR code for verification
        verification_url = evaluation_data.get('verification_url', '#')
        qr_bytes = self.generate_qr_code(verification_url)
        qr_base64 = base64.b64encode(qr_bytes).decode('utf-8') if qr_bytes else ''
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px;
            color: #333;
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #2c3e50;
            margin: 0;
        }}
        .section {{
            margin: 20px 0;
        }}
        .section h2 {{
            color: #34495e;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }}
        .score-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin: 20px 0;
        }}
        .score-item {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
        }}
        .score-item label {{
            display: block;
            font-weight: bold;
            color: #7f8c8d;
            margin-bottom: 5px;
        }}
        .score-item .value {{
            font-size: 24px;
            color: #2c3e50;
            font-weight: bold;
        }}
        .overall-score {{
            background: #3498db;
            color: white;
            text-align: center;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .overall-score .value {{
            font-size: 48px;
            font-weight: bold;
        }}
        .ai-commentary {{
            background: #f9f9f9;
            border-left: 4px solid #27ae60;
            padding: 20px;
            margin: 20px 0;
            font-style: italic;
        }}
        .footer {{
            margin-top: 40px;
            text-align: center;
            color: #95a5a6;
            font-size: 12px;
        }}
        .qr-code {{
            text-align: center;
            margin: 20px 0;
        }}
        .qr-code img {{
            max-width: 150px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Performance Evaluation Report</h1>
        <p><strong>{evaluation_data.get('employee_name')}</strong></p>
        <p>Period: {evaluation_data.get('period')} | Date: {evaluation_data.get('date')}</p>
    </div>
    
    <div class="overall-score">
        <div>Overall Performance Score</div>
        <div class="value">{evaluation_data.get('overall_score')}/10</div>
    </div>
    
    <div class="section">
        <h2>Performance Breakdown</h2>
        <div class="score-grid">
            <div class="score-item">
                <label>Technical Skills</label>
                <div class="value">{evaluation_data.get('technical_score')}/10</div>
            </div>
            <div class="score-item">
                <label>Productivity</label>
                <div class="value">{evaluation_data.get('productivity_score')}/10</div>
            </div>
            <div class="score-item">
                <label>Teamwork</label>
                <div class="value">{evaluation_data.get('teamwork_score')}/10</div>
            </div>
            <div class="score-item">
                <label>Innovation</label>
                <div class="value">{evaluation_data.get('innovation_score')}/10</div>
            </div>
        </div>
    </div>
    
    <div class="section ai-commentary">
        <h3>📊 AI Performance Analysis</h3>
        <p>{ai_commentary}</p>
    </div>
    
    <div class="section">
        <h2>Evaluator Comments</h2>
        <p>{evaluation_data.get('comments', 'No additional comments')}</p>
    </div>
    
    <div class="section">
        <h2>Improvement Plan</h2>
        <p>{evaluation_data.get('improvement_plan', 'Continue current performance trajectory')}</p>
    </div>
    
    <div class="qr-code">
        <p><strong>Verify this report:</strong></p>
        <img src="data:image/png;base64,{qr_base64}" alt="Verification QR Code" />
        <p style="font-size: 10px;">Scan to verify authenticity</p>
    </div>
    
    <div class="footer">
        <p>© {datetime.now().year} ENSA Hoceima - HR Department</p>
        <p>Report ID: {evaluation_data.get('evaluation_id')} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
</body>
</html>
"""
        return html
    
    def generate_certificate_html(self, certificate_data: Dict[str, Any]) -> str:
        """
        Generate HTML for training certificate
        
        Args:
            certificate_data: Certificate information
            
        Returns:
            HTML content
        """
        # Generate verification QR code
        verification_url = certificate_data.get('verification_url', '#')
        qr_bytes = self.generate_qr_code(verification_url)
        qr_base64 = base64.b64encode(qr_bytes).decode('utf-8') if qr_bytes else ''
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Georgia', serif;
            text-align: center;
            padding: 60px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #2c3e50;
        }}
        .certificate {{
            background: white;
            padding: 60px;
            border: 10px solid gold;
            box-shadow: 0 0 30px rgba(0,0,0,0.3);
            max-width: 800px;
            margin: 0 auto;
        }}
        .certificate h1 {{
            font-size: 48px;
            color: #2c3e50;
            margin: 20px 0;
        }}
        .certificate h2 {{
            font-size: 24px;
            color: #7f8c8d;
            font-weight: normal;
            margin: 10px 0;
        }}
        .recipient {{
            font-size: 36px;
            color: #16a085;
            margin: 30px 0;
            font-weight: bold;
        }}
        .achievement {{
            font-size: 18px;
            line-height: 1.6;
            margin: 30px 0;
            color: #34495e;
        }}
        .signature {{
            margin-top: 50px;
            display: flex;
            justify-content: space-around;
        }}
        .signature div {{
            text-align: center;
        }}
        .signature-line {{
            border-top: 2px solid #2c3e50;
            width: 200px;
            margin: 10px auto;
        }}
        .qr-container {{
            position: absolute;
            bottom: 30px;
            right: 30px;
        }}
    </style>
</head>
<body>
    <div class="certificate">
        <h1>🏆 CERTIFICATE OF ACHIEVEMENT</h1>
        <h2>ENSA Hoceima - School of Engineering</h2>
        
        <p style="margin: 40px 0;">This is to certify that</p>
        
        <div class="recipient">{certificate_data.get('recipient_name')}</div>
        
        <div class="achievement">
            <p>has successfully completed</p>
            <p><strong>{certificate_data.get('course_name')}</strong></p>
            <p>with a score of <strong>{certificate_data.get('score')}/10</strong></p>
            <p>on {certificate_data.get('completion_date')}</p>
        </div>
        
        <div class="signature">
            <div>
                <div class="signature-line"></div>
                <p><strong>HR Director</strong></p>
                <p>ENSA Hoceima</p>
            </div>
            <div>
                <div class="signature-line"></div>
                <p><strong>Training Coordinator</strong></p>
                <p>Professional Development</p>
            </div>
        </div>
        
        <div class="qr-container">
            <img src="data:image/png;base64,{qr_base64}" alt="Verification" style="width: 100px;" />
            <p style="font-size: 8px;">Verify Online</p>
        </div>
        
        <p style="margin-top: 40px; font-size: 12px; color: #95a5a6;">
            Certificate ID: {certificate_data.get('certificate_id')} | Issued: {datetime.now().strftime('%Y-%m-%d')}
        </p>
    </div>
</body>
</html>
"""
        return html


class OdooDocumentGenerator(models.AbstractModel):
    """Odoo model wrapper for Document Generator"""
    _name = 'ensa.document.generator'
    _description = 'Document Generator Service'
    
    @api.model
    def get_document_generator(self):
        """Get configured document generator instance"""
        ai_service = self.env['ensa.ai.service'].get_ai_service()
        return DocumentGenerator(ai_service)
    
    @api.model
    def generate_qr_code(self, data: str) -> bytes:
        """Generate QR code (Odoo-friendly wrapper)"""
        generator = self.get_document_generator()
        return generator.generate_qr_code(data)

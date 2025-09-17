import qrcode
import io
import base64
from PIL import Image
from typing import Dict, Any

class QRService:
    def __init__(self):
        pass

    def generate_qr_code(self, session_url: str, size: int = 200) -> Dict[str, Any]:
        """Generate QR code for session URL"""
        try:
            # Create QR code instance
            qr = qrcode.QRCode(
                version=1,  # Controls the size of the QR Code
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )

            # Add data
            qr.add_data(session_url)
            qr.make(fit=True)

            # Create image
            qr_image = qr.make_image(fill_color="black", back_color="white")

            # Resize to desired size
            qr_image = qr_image.resize((size, size), Image.Resampling.LANCZOS)

            # Convert to base64
            img_buffer = io.BytesIO()
            qr_image.save(img_buffer, format='PNG')
            img_buffer.seek(0)

            # Encode to base64
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
            img_data_url = f"data:image/png;base64,{img_base64}"

            return {
                'success': True,
                'image_data': img_data_url,
                'raw_data': img_buffer.getvalue(),
                'size': size
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_qr_download_data(self, session_url: str, size: int = 400) -> bytes:
        """Generate QR code for download (larger size)"""
        result = self.generate_qr_code(session_url, size)
        if result['success']:
            return result['raw_data']
        else:
            raise Exception(f"Failed to generate QR code: {result['error']}")

# Singleton instance
_qr_service = QRService()

def get_qr_service() -> QRService:
    return _qr_service
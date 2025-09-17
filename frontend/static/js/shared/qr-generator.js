// QR Code Generator Utility

class QRGenerator {
    constructor() {
        this.canvas = null;
        this.ctx = null;
    }

    displayQRCode(canvas, qrDataUrl) {
        if (!canvas || !qrDataUrl) {
            console.error('Canvas or QR data URL not provided');
            return false;
        }

        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');

        const img = new Image();
        img.onload = () => {
            this.ctx.clearRect(0, 0, canvas.width, canvas.height);
            this.ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        };
        img.onerror = () => {
            console.error('Failed to load QR code image');
        };
        img.src = qrDataUrl;

        return true;
    }

    downloadQRCode(canvas, filename = 'qr-code.png') {
        if (!canvas) {
            console.error('Canvas not provided');
            return false;
        }

        try {
            // Create download link
            const link = document.createElement('a');
            link.download = filename;
            link.href = canvas.toDataURL('image/png');

            // Trigger download
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            return true;
        } catch (error) {
            console.error('Failed to download QR code:', error);
            return false;
        }
    }

    copyToClipboard(text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            return navigator.clipboard.writeText(text)
                .then(() => {
                    console.log('Link copied to clipboard');
                    return true;
                })
                .catch(err => {
                    console.error('Failed to copy link:', err);
                    return false;
                });
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();

            try {
                const successful = document.execCommand('copy');
                document.body.removeChild(textArea);
                if (successful) {
                    console.log('Link copied to clipboard (fallback)');
                    return Promise.resolve(true);
                } else {
                    return Promise.resolve(false);
                }
            } catch (err) {
                document.body.removeChild(textArea);
                console.error('Failed to copy link (fallback):', err);
                return Promise.resolve(false);
            }
        }
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.QRGenerator = QRGenerator;
}
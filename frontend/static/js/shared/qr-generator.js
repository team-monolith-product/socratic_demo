// QR Code Generator Utility

class QRGenerator {
    constructor() {
        this.canvas = null;
        this.ctx = null;
    }

    async generateQRCode(canvas, text, size = 256) {
        if (!canvas || !text) {
            throw new Error('Canvas or text not provided');
        }

        // For now, we'll use a simple text-based QR representation
        // In a real implementation, you'd use a QR code library like qrcode.js
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');

        canvas.width = size;
        canvas.height = size;

        // Clear canvas
        this.ctx.fillStyle = '#ffffff';
        this.ctx.fillRect(0, 0, size, size);

        // Create a simple placeholder QR pattern
        this.ctx.fillStyle = '#000000';
        const blockSize = Math.floor(size / 25);

        // Draw QR code pattern (simplified)
        for (let i = 0; i < 25; i++) {
            for (let j = 0; j < 25; j++) {
                if ((i + j) % 3 === 0 || (i % 4 === 0 && j % 4 === 0)) {
                    this.ctx.fillRect(i * blockSize, j * blockSize, blockSize, blockSize);
                }
            }
        }

        // Add corner markers
        this.drawCornerMarkers(size, blockSize);

        return canvas;
    }

    drawCornerMarkers(size, blockSize) {
        const markerSize = blockSize * 7;

        // Top-left corner
        this.ctx.fillStyle = '#000000';
        this.ctx.fillRect(0, 0, markerSize, markerSize);
        this.ctx.fillStyle = '#ffffff';
        this.ctx.fillRect(blockSize, blockSize, markerSize - 2 * blockSize, markerSize - 2 * blockSize);
        this.ctx.fillStyle = '#000000';
        this.ctx.fillRect(2 * blockSize, 2 * blockSize, markerSize - 4 * blockSize, markerSize - 4 * blockSize);

        // Top-right corner
        const topRightX = size - markerSize;
        this.ctx.fillStyle = '#000000';
        this.ctx.fillRect(topRightX, 0, markerSize, markerSize);
        this.ctx.fillStyle = '#ffffff';
        this.ctx.fillRect(topRightX + blockSize, blockSize, markerSize - 2 * blockSize, markerSize - 2 * blockSize);
        this.ctx.fillStyle = '#000000';
        this.ctx.fillRect(topRightX + 2 * blockSize, 2 * blockSize, markerSize - 4 * blockSize, markerSize - 4 * blockSize);

        // Bottom-left corner
        const bottomLeftY = size - markerSize;
        this.ctx.fillStyle = '#000000';
        this.ctx.fillRect(0, bottomLeftY, markerSize, markerSize);
        this.ctx.fillStyle = '#ffffff';
        this.ctx.fillRect(blockSize, bottomLeftY + blockSize, markerSize - 2 * blockSize, markerSize - 2 * blockSize);
        this.ctx.fillStyle = '#000000';
        this.ctx.fillRect(2 * blockSize, bottomLeftY + 2 * blockSize, markerSize - 4 * blockSize, markerSize - 4 * blockSize);
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
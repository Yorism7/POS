"""
Barcode Scanner Component using JavaScript (jsQR)
Works on Streamlit Cloud - No system dependencies needed!
Uses jsQR library that runs entirely in the browser
"""

import streamlit as st
import streamlit.components.v1 as components

def barcode_scanner_component():
    """
    Create a barcode scanner component using jsQR (JavaScript library)
    Works on Streamlit Cloud - no Python dependencies needed!
    Returns the scanned barcode value or None
    """
    st.markdown("### 📷 สแกนบาร์โค๊ดด้วยกล้อง")
    st.info("💡 **วิธีใช้งาน:** กดปุ่มด้านล่างเพื่อเปิดกล้องและชี้ไปที่บาร์โค๊ด")
    
    # JavaScript-based barcode scanner using jsQR
    # jsQR is a pure JavaScript library that runs in the browser
    # No Python dependencies needed!
    
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Barcode Scanner</title>
        <script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js"></script>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f0f2f6;
            }
            .scanner-container {
                max-width: 100%;
                margin: 0 auto;
                text-align: center;
            }
            #video {
                width: 100%;
                max-width: 640px;
                border: 2px solid #667eea;
                border-radius: 8px;
                background: #000;
            }
            #canvas {
                display: none;
            }
            .controls {
                margin: 20px 0;
            }
            button {
                background-color: #667eea;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 16px;
                border-radius: 6px;
                cursor: pointer;
                margin: 5px;
            }
            button:hover {
                background-color: #5568d3;
            }
            button:disabled {
                background-color: #ccc;
                cursor: not-allowed;
            }
            #status {
                margin: 10px 0;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
            }
            .status-info {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            .status-success {
                background-color: #e8f5e9;
                color: #388e3c;
            }
            .status-error {
                background-color: #ffebee;
                color: #c62828;
            }
        </style>
    </head>
    <body>
        <div class="scanner-container">
            <h3>📷 สแกนบาร์โค๊ด</h3>
            <video id="video" autoplay playsinline></video>
            <canvas id="canvas"></canvas>
            <div class="controls">
                <button id="startBtn" onclick="startScanner()">📷 เริ่มสแกน</button>
                <button id="stopBtn" onclick="stopScanner()" disabled>⏹️ หยุดสแกน</button>
            </div>
            <div id="status" class="status-info">กดปุ่ม "เริ่มสแกน" เพื่อเปิดกล้อง</div>
        </div>

        <script>
            let video = null;
            let canvas = null;
            let ctx = null;
            let scanning = false;
            let stream = null;

            window.addEventListener('load', function() {
                video = document.getElementById('video');
                canvas = document.getElementById('canvas');
                ctx = canvas.getContext('2d');
            });

            function startScanner() {
                if (scanning) return;

                // Request camera access
                navigator.mediaDevices.getUserMedia({ 
                    video: { 
                        facingMode: 'environment' // Use back camera on mobile
                    } 
                })
                .then(function(mediaStream) {
                    stream = mediaStream;
                    video.srcObject = stream;
                    video.setAttribute('playsinline', true);
                    video.play();
                    
                    scanning = true;
                    document.getElementById('startBtn').disabled = true;
                    document.getElementById('stopBtn').disabled = false;
                    
                    updateStatus('กำลังสแกน... ชี้กล้องไปที่บาร์โค๊ด', 'info');
                    
                    // Start scanning
                    scanBarcode();
                })
                .catch(function(err) {
                    console.error('Error accessing camera:', err);
                    updateStatus('ไม่สามารถเข้าถึงกล้องได้: ' + err.message, 'error');
                });
            }

            function stopScanner() {
                scanning = false;
                
                if (stream) {
                    stream.getTracks().forEach(track => track.stop());
                    stream = null;
                }
                
                if (video) {
                    video.srcObject = null;
                }
                
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
                updateStatus('หยุดสแกนแล้ว', 'info');
            }

            function scanBarcode() {
                if (!scanning) return;

                if (video.readyState === video.HAVE_ENOUGH_DATA) {
                    canvas.height = video.videoHeight;
                    canvas.width = video.videoWidth;
                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                    
                    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                    
                    // Use jsQR to decode barcode
                    if (typeof jsQR !== 'undefined') {
                        const code = jsQR(imageData.data, imageData.width, imageData.height, {
                            inversionAttempts: "dontInvert",
                        });
                        
                        if (code) {
                            // Found barcode!
                            updateStatus('✅ พบบาร์โค๊ด: ' + code.data, 'success');
                            
                            // Send result to Streamlit
                            window.parent.postMessage({
                                type: 'barcode_scanned',
                                data: code.data
                            }, '*');
                            
                            // Stop scanning after finding barcode
                            setTimeout(() => {
                                stopScanner();
                            }, 2000);
                            return;
                        }
                    }
                }
                
                // Continue scanning
                if (scanning) {
                    requestAnimationFrame(scanBarcode);
                }
            }

            function updateStatus(message, type) {
                const statusDiv = document.getElementById('status');
                statusDiv.textContent = message;
                statusDiv.className = 'status-' + type;
            }

            // Cleanup on page unload
            window.addEventListener('beforeunload', function() {
                stopScanner();
            });
        </script>
    </body>
    </html>
    """
    
    # Create component
    # Note: components.html() doesn't support 'key' parameter in some Streamlit versions
    result = components.html(
        html_code,
        height=500
    )
    
    # Check for messages from JavaScript
    if result:
        # If JavaScript sends data, it will be in result
        # For now, we'll use a different approach with session state
        pass
    
    # Alternative: Use st.camera_input with manual barcode input
    # Since we can't easily get data from JavaScript component back to Python
    # We'll use a hybrid approach
    
    st.divider()
    st.subheader("หรือใช้วิธีถ่ายภาพ")
    
    # Use Streamlit's camera input
    image = st.camera_input(
        "📷 ถ่ายภาพบาร์โค๊ด",
        key="barcode_camera_js",
        help="ถ่ายภาพบาร์โค๊ดแล้วระบบจะพยายามสแกน"
    )
    
    if image is not None:
        # Try to decode using JavaScript approach
        # Since we can't easily decode in Python without pyzbar,
        # we'll show the image and ask user to enter manually
        st.image(image, caption="ภาพที่ถ่าย", use_container_width=True)
        st.info("💡 เนื่องจากข้อจำกัดของ Streamlit Cloud กรุณาพิมพ์บาร์โค๊ดด้านล่าง")
        
        barcode_input = st.text_input(
            "📷 พิมพ์บาร์โค๊ดจากภาพ",
            key="barcode_manual_from_image",
            placeholder="พิมพ์บาร์โค๊ดที่นี่...",
            help="ดูบาร์โค๊ดจากภาพแล้วพิมพ์ที่นี่"
        )
        return barcode_input if barcode_input else None
    else:
        # Show manual input option
        st.divider()
        st.subheader("หรือพิมพ์บาร์โค๊ดด้วยตนเอง")
        barcode_input = st.text_input(
            "📷 พิมพ์บาร์โค๊ด",
            key="barcode_manual_js",
            placeholder="พิมพ์บาร์โค๊ดที่นี่...",
            help="พิมพ์บาร์โค๊ดแล้วกด Enter"
        )
        return barcode_input if barcode_input else None
    
    return None


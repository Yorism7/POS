"""
Real-time Barcode Scanner Component using JavaScript (jsQR)
สแกนบาร์โค๊ดทันทีแบบ real-time - ไม่ต้องถ่ายภาพ!
Works on Streamlit Cloud - No system dependencies needed!
"""

import streamlit as st
import streamlit.components.v1 as components
import urllib.parse

def barcode_scanner_realtime():
    """
    Real-time barcode scanner using JavaScript (jsQR)
    สแกนบาร์โค๊ดทันทีแบบ real-time - ไม่ต้องถ่ายภาพ!
    
    Returns:
        str: Barcode value if scanned, None otherwise
    """
    st.markdown("### 📷 สแกนบาร์โค๊ดแบบ Real-time")
    st.info("💡 **วิธีใช้งาน:** กดปุ่ม 'เริ่มสแกน' แล้วชี้กล้องไปที่บาร์โค๊ด ระบบจะสแกนทันที!")
    
    # Check if barcode was scanned (from URL parameter)
    # Use new st.query_params API (Streamlit 1.28+)
    try:
        if hasattr(st, 'query_params'):
            query_params_raw = st.query_params
            # Convert to dict format
            query_params = {}
            for key, value in query_params_raw.items():
                if isinstance(value, list):
                    query_params[key] = value
                else:
                    query_params[key] = [value]
        else:
            query_params = st.experimental_get_query_params()
    except:
        query_params = {}
    
    scanned_barcode = query_params.get('barcode', [None])[0]
    
    if scanned_barcode:
        # Clear URL parameter - use new API if available
        try:
            if hasattr(st, 'query_params'):
                st.query_params.clear()
            else:
                st.experimental_set_query_params()
        except:
            pass
        # Store in session state
        st.session_state['scanned_barcode'] = scanned_barcode
        st.success(f"✅ สแกนบาร์โค๊ดสำเร็จ: {scanned_barcode}")
        return scanned_barcode
    
    # Check session state
    if 'scanned_barcode' in st.session_state:
        barcode = st.session_state['scanned_barcode']
        del st.session_state['scanned_barcode']
        return barcode
    
    # JavaScript-based real-time barcode scanner
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Real-time Barcode Scanner</title>
        <script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js"></script>
        <script>
            // Check if jsQR loaded successfully
            window.addEventListener('load', function() {
                setTimeout(function() {
                    if (typeof jsQR === 'undefined') {
                        console.error('❌ jsQR library failed to load!');
                        const statusDiv = document.getElementById('status');
                        if (statusDiv) {
                            statusDiv.textContent = '❌ ไม่สามารถโหลด jsQR library ได้ กรุณารีเฟรชหน้าเว็บ';
                            statusDiv.className = 'status-error';
                        }
                    } else {
                        console.log('✅ jsQR library loaded successfully');
                    }
                }, 1500);
            });
        </script>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                min-height: 100vh;
            }
            .scanner-container {
                max-width: 100%;
                margin: 0 auto;
                background: white;
                border-radius: 16px;
                padding: 20px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            }
            h3 {
                text-align: center;
                color: #333;
                margin-bottom: 20px;
                font-size: 24px;
            }
            #video {
                width: 100%;
                max-width: 640px;
                border: 3px solid #667eea;
                border-radius: 12px;
                background: #000;
                display: block;
                margin: 0 auto;
            }
            #canvas {
                display: none;
            }
            .controls {
                margin: 20px 0;
                text-align: center;
            }
            button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 14px 28px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                cursor: pointer;
                margin: 5px;
                transition: all 0.3s;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            }
            button:hover:not(:disabled) {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
            }
            button:active:not(:disabled) {
                transform: translateY(0);
            }
            button:disabled {
                background: #ccc;
                cursor: not-allowed;
                box-shadow: none;
            }
            #status {
                margin: 15px 0;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
                text-align: center;
                min-height: 50px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .status-info {
                background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
                color: #1976d2;
                border: 2px solid #2196f3;
            }
            .status-success {
                background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
                color: #2e7d32;
                border: 2px solid #4caf50;
                animation: pulse 0.5s;
            }
            .status-error {
                background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
                color: #c62828;
                border: 2px solid #f44336;
            }
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }
            .scanner-overlay {
                position: relative;
                display: inline-block;
            }
            .scanner-frame {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 80%;
                height: 200px;
                border: 3px solid #4caf50;
                border-radius: 8px;
                pointer-events: none;
                box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.5);
            }
            .scanner-frame::before {
                content: '';
                position: absolute;
                top: -3px;
                left: -3px;
                right: -3px;
                bottom: -3px;
                border: 2px solid #4caf50;
                border-radius: 8px;
                animation: scanline 2s linear infinite;
            }
            @keyframes scanline {
                0% { transform: translateY(-100%); }
                100% { transform: translateY(100%); }
            }
        </style>
    </head>
    <body>
        <div class="scanner-container">
            <h3>📷 สแกนบาร์โค๊ดแบบ Real-time</h3>
            <div class="scanner-overlay">
                <video id="video" autoplay playsinline></video>
                <div class="scanner-frame" id="scannerFrame" style="display: none;"></div>
            </div>
            <canvas id="canvas"></canvas>
            <div class="controls">
                <button id="startBtn" onclick="startScanner()">📷 เริ่มสแกน</button>
                <button id="stopBtn" onclick="stopScanner()" disabled>⏹️ หยุดสแกน</button>
            </div>
            <div id="status" class="status-info">กดปุ่ม "เริ่มสแกน" เพื่อเปิดกล้องและเริ่มสแกน</div>
        </div>

        <script>
            let video = null;
            let canvas = null;
            let ctx = null;
            let scanning = false;
            let stream = null;
            let scanFrame = null;

            window.addEventListener('load', function() {
                video = document.getElementById('video');
                canvas = document.getElementById('canvas');
                // Use willReadFrequently for better performance when reading image data frequently
                ctx = canvas.getContext('2d', { willReadFrequently: true });
                scanFrame = document.getElementById('scannerFrame');
            });

            function startScanner() {
                if (scanning) return;

                // Request camera access
                navigator.mediaDevices.getUserMedia({ 
                    video: { 
                        facingMode: 'environment', // Use back camera on mobile
                        width: { ideal: 1280 },
                        height: { ideal: 720 }
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
                    scanFrame.style.display = 'block';
                    
                    updateStatus('🔍 กำลังสแกน... ชี้กล้องไปที่บาร์โค๊ด', 'info');
                    
                    // Start scanning loop
                    scanBarcode();
                })
                .catch(function(err) {
                    console.error('Error accessing camera:', err);
                    let errorMsg = 'ไม่สามารถเข้าถึงกล้องได้';
                    if (err.name === 'NotAllowedError') {
                        errorMsg = 'กรุณาอนุญาตให้เข้าถึงกล้อง';
                    } else if (err.name === 'NotFoundError') {
                        errorMsg = 'ไม่พบกล้องในอุปกรณ์นี้';
                    }
                    updateStatus('❌ ' + errorMsg, 'error');
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
                
                scanFrame.style.display = 'none';
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
                        try {
                            const code = jsQR(imageData.data, imageData.width, imageData.height, {
                                inversionAttempts: "dontInvert",
                            });
                            
                            if (code && code.data) {
                                // Found barcode!
                                const barcodeData = code.data.trim();
                                
                                // Validate barcode (should not be empty)
                                if (barcodeData.length > 0) {
                                    console.log('✅ Barcode found:', barcodeData);
                                    updateStatus('✅ พบบาร์โค๊ด: ' + barcodeData, 'success');
                                    
                                    // Stop scanning immediately
                                    stopScanner();
                                    
                                    // Send result to Streamlit via URL parameter
                                    try {
                                        // Get current URL
                                        const currentUrl = window.location.href;
                                        const url = new URL(currentUrl);
                                        
                                        // Remove existing barcode parameter if any
                                        url.searchParams.delete('barcode');
                                        
                                        // Add new barcode parameter
                                        url.searchParams.set('barcode', barcodeData);
                                        
                                        console.log('✅ Barcode scanned:', barcodeData);
                                        console.log('Redirecting to:', url.toString());
                                        
                                        // Use window.location to navigate (preserves Streamlit routing)
                                        // This is the safest method for Streamlit Cloud
                                        window.location.href = url.toString();
                                        
                                        return;
                                    } catch (e) {
                                        console.error('Error sending barcode:', e);
                                        updateStatus('❌ เกิดข้อผิดพลาดในการส่งข้อมูล: ' + e.message, 'error');
                                        // Continue scanning if error
                                        if (scanning) {
                                            requestAnimationFrame(scanBarcode);
                                        }
                                    }
                                } else {
                                    console.warn('⚠️ Barcode data is empty');
                                }
                            }
                        } catch (e) {
                            console.error('Error decoding barcode:', e);
                        }
                    } else {
                        // jsQR not loaded - show error once
                        if (scanning && !window.jsQRWarningShown) {
                            console.error('❌ jsQR library not loaded!');
                            updateStatus('⚠️ กำลังโหลด jsQR library... กรุณารอสักครู่', 'error');
                            window.jsQRWarningShown = true;
                        }
                    }
                }
                
                // Continue scanning (real-time loop)
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
    components.html(
        html_code,
        height=600
    )
    
    # Check for scanned barcode from URL or session state
    try:
        if hasattr(st, 'query_params'):
            query_params_raw = st.query_params
            query_params = {}
            for key, value in query_params_raw.items():
                if isinstance(value, list):
                    query_params[key] = value
                else:
                    query_params[key] = [value]
        else:
            query_params = st.experimental_get_query_params()
    except:
        query_params = {}
    
    # Check URL parameter first
    if 'barcode' in query_params:
        barcode = query_params['barcode'][0] if isinstance(query_params['barcode'], list) else query_params['barcode']
        if barcode:
            # Clear query params
            try:
                if hasattr(st, 'query_params'):
                    # Create new dict without barcode
                    new_params = dict(st.query_params)
                    if 'barcode' in new_params:
                        del new_params['barcode']
                        st.query_params = new_params
                else:
                    st.experimental_set_query_params()
            except Exception as e:
                print(f"[DEBUG] Error clearing query params: {e}")
            print(f"[DEBUG] Barcode scanned from URL: {barcode}")
            return barcode
    
    # Check session state (for postMessage communication)
    if 'scanned_barcode_realtime' in st.session_state:
        barcode = st.session_state['scanned_barcode_realtime']
        del st.session_state['scanned_barcode_realtime']
        print(f"[DEBUG] Barcode scanned from session state: {barcode}")
        return barcode
    
    return None


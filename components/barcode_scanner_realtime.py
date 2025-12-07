"""
Real-time Barcode Scanner Component using JavaScript (QuaggaJS)
สแกนบาร์โค๊ดทันทีแบบ real-time - รองรับบาร์โค๊ดทุกประเภท!
Works on Streamlit Cloud - No system dependencies needed!

รองรับบาร์โค๊ด:
- QR Code
- EAN-13 (บาร์โค๊ดสินค้าทั่วไป)
- Code 128
- UPC-A
- Code 39
- และอื่นๆ
"""

import streamlit as st
import streamlit.components.v1 as components
import urllib.parse

def barcode_scanner_realtime():
    """
    Real-time barcode scanner using JavaScript (QuaggaJS)
    สแกนบาร์โค๊ดทันทีแบบ real-time - รองรับบาร์โค๊ดทุกประเภท!
    
    Returns:
        str: Barcode value if scanned, None otherwise
    """
    st.markdown("### 📷 สแกนบาร์โค๊ดแบบ Real-time")
    st.info("💡 **วิธีใช้งาน:** กดปุ่ม 'เริ่มสแกน' แล้วชี้กล้องไปที่บาร์โค๊ด ระบบจะสแกนทันที!")
    st.success("✅ **รองรับบาร์โค๊ด:** QR Code, EAN-13, Code 128, UPC-A, Code 39 และอื่นๆ")
    
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
    
    # JavaScript-based real-time barcode scanner using QuaggaJS
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Real-time Barcode Scanner</title>
        <!-- QuaggaJS - รองรับบาร์โค๊ด 1D (EAN-13, Code 128, UPC-A, Code 39, etc.) -->
        <script src="https://cdn.jsdelivr.net/npm/quagga@0.12.1/dist/quagga.min.js"></script>
        <!-- jsQR - รองรับ QR Code (2D) -->
        <script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js"></script>
        <script>
            // Check if libraries loaded successfully
            window.addEventListener('load', function() {
                setTimeout(function() {
                    let allLoaded = true;
                    if (typeof Quagga === 'undefined') {
                        console.error('❌ QuaggaJS library failed to load!');
                        allLoaded = false;
                    } else {
                        console.log('✅ QuaggaJS library loaded successfully');
                    }
                    if (typeof jsQR === 'undefined') {
                        console.error('❌ jsQR library failed to load!');
                        allLoaded = false;
                    } else {
                        console.log('✅ jsQR library loaded successfully');
                    }
                    if (!allLoaded) {
                        const statusDiv = document.getElementById('status');
                        if (statusDiv) {
                            statusDiv.textContent = '❌ ไม่สามารถโหลด library ได้ กรุณารีเฟรชหน้าเว็บ';
                            statusDiv.className = 'status-error';
                        }
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
            #interactive {
                width: 100%;
                max-width: 640px;
                height: 480px;
                border: 3px solid #667eea;
                border-radius: 12px;
                background: #000;
                display: block;
                margin: 0 auto;
                position: relative;
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
            .barcode-type {
                margin-top: 10px;
                padding: 8px;
                background: #f5f5f5;
                border-radius: 6px;
                font-size: 14px;
                color: #666;
            }
        </style>
    </head>
    <body>
        <div class="scanner-container">
            <h3>📷 สแกนบาร์โค๊ดแบบ Real-time</h3>
            <div id="interactive"></div>
            <div class="controls">
                <button id="startBtn" onclick="startScanner()">📷 เริ่มสแกน</button>
                <button id="stopBtn" onclick="stopScanner()" disabled>⏹️ หยุดสแกน</button>
            </div>
            <div id="status" class="status-info">กดปุ่ม "เริ่มสแกน" เพื่อเปิดกล้องและเริ่มสแกน</div>
            <div id="barcodeType" class="barcode-type" style="display: none;"></div>
        </div>

        <script>
            let scanning = false;
            let lastScannedCode = null;
            let scanCount = 0;
            let video = null;
            let canvas = null;
            let ctx = null;
            let qrScanning = false;
            
            // รองรับบาร์โค๊ด 1D หลายประเภท (QuaggaJS)
            const readers = [
                'code_128_reader',
                'ean_reader',
                'ean_8_reader',
                'code_39_reader',
                'code_39_vin_reader',
                'codabar_reader',
                'upc_reader',
                'upc_e_reader',
                'i2of5_reader'
            ];
            
            // ตั้งค่า canvas สำหรับ jsQR (QR Code)
            window.addEventListener('load', function() {
                canvas = document.createElement('canvas');
                ctx = canvas.getContext('2d', { willReadFrequently: true });
            });
            
            function startScanner() {
                if (scanning) return;
                
                if (typeof Quagga === 'undefined') {
                    updateStatus('❌ QuaggaJS library ยังไม่โหลดเสร็จ กรุณารอสักครู่...', 'error');
                    return;
                }
                
                // ตั้งค่า QuaggaJS
                Quagga.init({
                    inputStream: {
                        name: "Live",
                        type: "LiveStream",
                        target: document.querySelector('#interactive'),
                        constraints: {
                            width: 640,
                            height: 480,
                            facingMode: "environment" // ใช้กล้องหลังบนมือถือ
                        }
                    },
                    locator: {
                        patchSize: "medium",
                        halfSample: true
                    },
                    numOfWorkers: 2,
                    frequency: 10, // สแกนทุก 10 frames
                    decoder: {
                        readers: readers
                    },
                    locate: true
                }, function(err) {
                    if (err) {
                        console.error('QuaggaJS initialization error:', err);
                        let errorMsg = 'ไม่สามารถเริ่มต้นสแกนเนอร์ได้';
                        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
                            errorMsg = 'กรุณาอนุญาตให้เข้าถึงกล้อง';
                        } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
                            errorMsg = 'ไม่พบกล้องในอุปกรณ์นี้';
                        } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
                            errorMsg = 'กล้องถูกใช้งานโดยแอปอื่นอยู่';
                        }
                        updateStatus('❌ ' + errorMsg, 'error');
                        return;
                    }
                    
                    console.log('✅ QuaggaJS initialized successfully');
                    scanning = true;
                    document.getElementById('startBtn').disabled = true;
                    document.getElementById('stopBtn').disabled = false;
                    updateStatus('🔍 กำลังสแกน... ชี้กล้องไปที่บาร์โค๊ด', 'info');
                    
                    // เริ่มสแกน
                    Quagga.start();
                    
                    // เริ่มสแกน QR Code ด้วย jsQR (ทำงานควบคู่กับ QuaggaJS)
                    startQRCodeScanning();
                });
                
                // ฟังก์ชันเมื่อพบบาร์โค๊ด 1D (QuaggaJS)
                Quagga.onDetected(function(result) {
                    if (!scanning) return;
                    
                    const code = result.codeResult.code;
                    const format = result.codeResult.format || 'unknown';
                    
                    // ป้องกันการสแกนซ้ำ (debounce)
                    if (lastScannedCode === code) {
                        return;
                    }
                    
                    lastScannedCode = code;
                    scanCount++;
                    
                    console.log('✅ Barcode detected:', code, 'Type:', format);
                    console.log('📍 Scan count:', scanCount);
                    
                    // แสดงผลลัพธ์
                    const formatNames = {
                        'code_128': 'Code 128',
                        'ean_13': 'EAN-13',
                        'ean_8': 'EAN-8',
                        'code_39': 'Code 39',
                        'codabar': 'Codabar',
                        'upc': 'UPC-A',
                        'upc_e': 'UPC-E',
                        'i2of5': 'Interleaved 2 of 5',
                        'qr_code': 'QR Code'
                    };
                    
                    const formatName = formatNames[format] || format;
                    handleBarcodeDetected(code, formatName);
                });
            }
            
            // ฟังก์ชันสแกน QR Code ด้วย jsQR
            function startQRCodeScanning() {
                if (!scanning || qrScanning) return;
                qrScanning = true;
                
                function scanQRCode() {
                    if (!scanning) {
                        qrScanning = false;
                        return;
                    }
                    
                    // หา video element จาก QuaggaJS
                    const quaggaVideo = document.querySelector('#interactive video');
                    if (!quaggaVideo || quaggaVideo.readyState !== quaggaVideo.HAVE_ENOUGH_DATA) {
                        requestAnimationFrame(scanQRCode);
                        return;
                    }
                    
                    // ตั้งค่า canvas
                    if (canvas.width !== quaggaVideo.videoWidth || canvas.height !== quaggaVideo.videoHeight) {
                        canvas.width = quaggaVideo.videoWidth;
                        canvas.height = quaggaVideo.videoHeight;
                    }
                    
                    // วาด video frame ลง canvas
                    ctx.drawImage(quaggaVideo, 0, 0, canvas.width, canvas.height);
                    
                    // ดึง image data
                    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                    
                    // สแกน QR Code ด้วย jsQR
                    if (typeof jsQR !== 'undefined') {
                        try {
                            let code = jsQR(imageData.data, imageData.width, imageData.height, {
                                inversionAttempts: "dontInvert",
                            });
                            
                            // ถ้าไม่พบ ลอง invert
                            if (!code) {
                                code = jsQR(imageData.data, imageData.width, imageData.height, {
                                    inversionAttempts: "attemptBoth",
                                });
                            }
                            
                            if (code && code.data) {
                                const qrData = code.data.trim();
                                if (qrData.length > 0) {
                                    // ป้องกันการสแกนซ้ำ
                                    if (lastScannedCode === qrData) {
                                        requestAnimationFrame(scanQRCode);
                                        return;
                                    }
                                    
                                    lastScannedCode = qrData;
                                    scanCount++;
                                    
                                    console.log('✅ QR Code detected:', qrData);
                                    handleBarcodeDetected(qrData, 'QR Code');
                                    return;
                                }
                            }
                        } catch (e) {
                            console.error('Error scanning QR Code:', e);
                        }
                    }
                    
                    // วนสแกนต่อ
                    requestAnimationFrame(scanQRCode);
                }
                
                // เริ่มสแกน QR Code
                scanQRCode();
            }
            
            // ฟังก์ชันจัดการเมื่อพบบาร์โค๊ด (ใช้ร่วมกันทั้ง 1D และ QR Code)
            function handleBarcodeDetected(code, formatName) {
                updateStatus('✅ พบบาร์โค๊ด: ' + code, 'success');
                document.getElementById('barcodeType').textContent = 'ประเภท: ' + formatName;
                document.getElementById('barcodeType').style.display = 'block';
                
                // หยุดสแกน
                stopScanner();
                
                // ส่งผลลัพธ์กลับไปยัง Streamlit
                try {
                    const currentUrl = window.location.href;
                    const url = new URL(currentUrl);
                    
                    // Remove existing barcode parameter if any
                    url.searchParams.delete('barcode');
                    
                    // Add new barcode parameter
                    url.searchParams.set('barcode', code);
                    
                    console.log('✅ Barcode scanned:', code, 'Type:', formatName);
                    console.log('🔄 Redirecting to:', url.toString());
                    
                    // Use window.location to navigate (preserves Streamlit routing)
                    window.location.href = url.toString();
                } catch (e) {
                    console.error('❌ Error sending barcode:', e);
                    updateStatus('❌ เกิดข้อผิดพลาดในการส่งข้อมูล: ' + e.message, 'error');
                }
            }
            
            // ฟังก์ชันสแกน QR Code ด้วย jsQR
            function startQRCodeScanning() {
                if (!scanning) return;
                
                function scanQRCode() {
                    if (!scanning) return;
                    
                    // หา video element จาก QuaggaJS
                    const quaggaVideo = document.querySelector('#interactive video');
                    if (!quaggaVideo || quaggaVideo.readyState !== quaggaVideo.HAVE_ENOUGH_DATA) {
                        requestAnimationFrame(scanQRCode);
                        return;
                    }
                    
                    // ตั้งค่า canvas
                    if (canvas.width !== quaggaVideo.videoWidth || canvas.height !== quaggaVideo.videoHeight) {
                        canvas.width = quaggaVideo.videoWidth;
                        canvas.height = quaggaVideo.videoHeight;
                    }
                    
                    // วาด video frame ลง canvas
                    ctx.drawImage(quaggaVideo, 0, 0, canvas.width, canvas.height);
                    
                    // ดึง image data
                    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                    
                    // สแกน QR Code ด้วย jsQR
                    if (typeof jsQR !== 'undefined') {
                        try {
                            let code = jsQR(imageData.data, imageData.width, imageData.height, {
                                inversionAttempts: "dontInvert",
                            });
                            
                            // ถ้าไม่พบ ลอง invert
                            if (!code) {
                                code = jsQR(imageData.data, imageData.width, imageData.height, {
                                    inversionAttempts: "attemptBoth",
                                });
                            }
                            
                            if (code && code.data) {
                                const qrData = code.data.trim();
                                if (qrData.length > 0) {
                                    // ป้องกันการสแกนซ้ำ
                                    if (lastScannedCode === qrData) {
                                        requestAnimationFrame(scanQRCode);
                                        return;
                                    }
                                    
                                    lastScannedCode = qrData;
                                    scanCount++;
                                    
                                    console.log('✅ QR Code detected:', qrData);
                                    handleBarcodeDetected(qrData, 'QR Code');
                                    return;
                                }
                            }
                        } catch (e) {
                            console.error('Error scanning QR Code:', e);
                        }
                    }
                    
                    // วนสแกนต่อ
                    requestAnimationFrame(scanQRCode);
                }
                
                // เริ่มสแกน QR Code
                scanQRCode();
            }
            
            // ฟังก์ชันจัดการเมื่อพบบาร์โค๊ด (ใช้ร่วมกันทั้ง 1D และ QR Code)
            function handleBarcodeDetected(code, formatName) {
                updateStatus('✅ พบบาร์โค๊ด: ' + code, 'success');
                document.getElementById('barcodeType').textContent = 'ประเภท: ' + formatName;
                document.getElementById('barcodeType').style.display = 'block';
                
                // หยุดสแกน
                stopScanner();
                
                // ส่งผลลัพธ์กลับไปยัง Streamlit
                try {
                    const currentUrl = window.location.href;
                    const url = new URL(currentUrl);
                    
                    // Remove existing barcode parameter if any
                    url.searchParams.delete('barcode');
                    
                    // Add new barcode parameter
                    url.searchParams.set('barcode', code);
                    
                    console.log('✅ Barcode scanned:', code, 'Type:', formatName);
                    console.log('🔄 Redirecting to:', url.toString());
                    
                    // Use window.location to navigate (preserves Streamlit routing)
                    window.location.href = url.toString();
                } catch (e) {
                    console.error('❌ Error sending barcode:', e);
                    updateStatus('❌ เกิดข้อผิดพลาดในการส่งข้อมูล: ' + e.message, 'error');
                }
            }
            
            function stopScanner() {
                if (!scanning) return;
                
                scanning = false;
                qrScanning = false;
                lastScannedCode = null;
                
                try {
                    Quagga.stop();
                } catch (e) {
                    console.error('Error stopping Quagga:', e);
                }
                
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
                document.getElementById('barcodeType').style.display = 'none';
                updateStatus('หยุดสแกนแล้ว', 'info');
            }
            
            function updateStatus(message, type) {
                const statusDiv = document.getElementById('status');
                if (statusDiv) {
                    statusDiv.textContent = message;
                    statusDiv.className = 'status-' + type;
                }
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
    components.html(html_code, height=700)
    
    return None

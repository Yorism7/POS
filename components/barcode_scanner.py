"""
Barcode Scanner Component using Camera
Uses HTML5 getUserMedia API with JavaScript barcode scanner
"""

import streamlit.components.v1 as components

def barcode_scanner_component(key: str = "barcode_scanner"):
    """Create a barcode scanner component using camera"""
    
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Barcode Scanner</title>
        <script src="https://cdn.jsdelivr.net/npm/quagga@0.12.1/dist/quagga.min.js"></script>
        <style>
            #scanner-container {
                position: relative;
                width: 100%;
                max-width: 640px;
                margin: 0 auto;
            }
            #scanner {
                width: 100%;
                height: auto;
                border: 2px solid #4CAF50;
                border-radius: 8px;
            }
            #scanner-overlay {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 80%;
                height: 30%;
                border: 3px solid #4CAF50;
                border-radius: 8px;
                pointer-events: none;
            }
            .scanner-controls {
                margin-top: 10px;
                text-align: center;
            }
            .scanner-btn {
                padding: 10px 20px;
                margin: 5px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }
            .scanner-btn:hover {
                background-color: #45a049;
            }
            .scanner-btn.stop {
                background-color: #f44336;
            }
            .scanner-btn.stop:hover {
                background-color: #da190b;
            }
            #scanner-status {
                margin-top: 10px;
                padding: 10px;
                text-align: center;
                font-weight: bold;
            }
            #scanner-status.scanning {
                color: #4CAF50;
            }
            #scanner-status.stopped {
                color: #f44336;
            }
        </style>
    </head>
    <body>
        <div id="scanner-container">
            <video id="scanner" autoplay playsinline></video>
            <div id="scanner-overlay"></div>
        </div>
        <div class="scanner-controls">
            <button class="scanner-btn" id="start-btn" onclick="startScanner()">📷 เริ่มสแกน</button>
            <button class="scanner-btn stop" id="stop-btn" onclick="stopScanner()" style="display:none;">⏹️ หยุดสแกน</button>
        </div>
        <div id="scanner-status" class="stopped">กดปุ่มเพื่อเริ่มสแกนบาร์โค๊ด</div>
        
        <script>
            let stream = null;
            let scanning = false;
            
            function startScanner() {
                if (scanning) return;
                
                const video = document.getElementById('scanner');
                const startBtn = document.getElementById('start-btn');
                const stopBtn = document.getElementById('stop-btn');
                const status = document.getElementById('scanner-status');
                
                navigator.mediaDevices.getUserMedia({ 
                    video: { 
                        facingMode: 'environment', // ใช้กล้องหลังบนมือถือ
                        width: { ideal: 1280 },
                        height: { ideal: 720 }
                    } 
                })
                .then(function(mediaStream) {
                    stream = mediaStream;
                    video.srcObject = stream;
                    scanning = true;
                    
                    startBtn.style.display = 'none';
                    stopBtn.style.display = 'inline-block';
                    status.textContent = 'กำลังสแกนบาร์โค๊ด...';
                    status.className = 'scanning';
                    
                    // Initialize QuaggaJS
                    Quagga.init({
                        inputStream: {
                            name: "Live",
                            type: "LiveStream",
                            target: video,
                            constraints: {
                                width: 640,
                                height: 480,
                                facingMode: "environment"
                            }
                        },
                        decoder: {
                            readers: [
                                "code_128_reader",
                                "ean_reader",
                                "ean_8_reader",
                                "code_39_reader",
                                "code_39_vin_reader",
                                "codabar_reader",
                                "upc_reader",
                                "upc_e_reader",
                                "i2of5_reader"
                            ]
                        },
                        locate: true
                    }, function(err) {
                        if (err) {
                            console.error('QuaggaJS initialization error:', err);
                            status.textContent = 'เกิดข้อผิดพลาด: ' + err.message;
                            status.className = 'stopped';
                            return;
                        }
                        Quagga.start();
                    });
                    
                    Quagga.onDetected(function(result) {
                        const code = result.codeResult.code;
                        console.log('Barcode detected:', code);
                        
                        // Play beep sound
                        playBeepSound();
                        
                        // Send barcode to Streamlit
                        window.parent.postMessage({
                            type: 'streamlit:setComponentValue',
                            value: code
                        }, '*');
                        
                        status.textContent = 'พบบาร์โค๊ด: ' + code;
                        status.className = 'scanning';
                        
                        // Stop scanning after detection
                        setTimeout(() => {
                            stopScanner();
                        }, 1000);
                    });
                    
                    // Function to play beep sound
                    function playBeepSound() {
                        // Create audio context for beep sound
                        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                        const oscillator = audioContext.createOscillator();
                        const gainNode = audioContext.createGain();
                        
                        oscillator.connect(gainNode);
                        gainNode.connect(audioContext.destination);
                        
                        oscillator.frequency.value = 800; // 800 Hz beep
                        oscillator.type = 'sine';
                        
                        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
                        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
                        
                        oscillator.start(audioContext.currentTime);
                        oscillator.stop(audioContext.currentTime + 0.1);
                    }
                })
                .catch(function(err) {
                    console.error('Error accessing camera:', err);
                    status.textContent = 'ไม่สามารถเข้าถึงกล้องได้: ' + err.message;
                    status.className = 'stopped';
                });
            }
            
            function stopScanner() {
                if (!scanning) return;
                
                const startBtn = document.getElementById('start-btn');
                const stopBtn = document.getElementById('stop-btn');
                const status = document.getElementById('scanner-status');
                const video = document.getElementById('scanner');
                
                if (stream) {
                    stream.getTracks().forEach(track => track.stop());
                    stream = null;
                }
                
                if (Quagga) {
                    Quagga.stop();
                }
                
                video.srcObject = null;
                scanning = false;
                
                startBtn.style.display = 'inline-block';
                stopBtn.style.display = 'none';
                status.textContent = 'หยุดสแกนแล้ว';
                status.className = 'stopped';
            }
            
            // Cleanup on page unload
            window.addEventListener('beforeunload', function() {
                stopScanner();
            });
        </script>
    </body>
    </html>
    """
    
    return components.html(html_code, height=500, key=key)


"""
Sound utilities for POS system
"""

import platform
import streamlit.components.v1 as components

def play_beep_sound():
    """Play beep sound using HTML5 Audio API"""
    html_code = """
    <script>
    (function() {
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
    })();
    </script>
    """
    components.html(html_code, height=0, width=0)




import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pyaudio
import threading
import queue
from scipy.fft import fft

class MusicVisualizer:
    def __init__(self, chunk_size=1024, sample_rate=44100, num_bars=50):
        self.chunk_size = chunk_size
        self.sample_rate = sample_rate
        self.num_bars = num_bars
        self.audio_queue = queue.Queue()
        
        # Audio setup
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
        # Visualization setup
        self.fig, self.ax = plt.subplots(figsize=(12, 6))
        self.bars = self.ax.bar(range(self.num_bars), [0] * self.num_bars, 
                               color='cyan', alpha=0.7)
        self.ax.set_xlim(0, self.num_bars)
        self.ax.set_ylim(0, 1000)
        self.ax.set_title('Real-time Audio Visualizer')
        self.ax.set_xlabel('Frequency Bins')
        self.ax.set_ylabel('Amplitude')
        
        # Frequency bins (logarithmic spacing for better visualization)
        self.freq_bins = np.logspace(np.log10(20), np.log10(self.sample_rate//2), 
                                    self.num_bars + 1)
        
    def audio_callback(self):
        """Continuously capture audio data"""
        while True:
            try:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                self.audio_queue.put(audio_data)
            except Exception as e:
                print(f"Audio error: {e}")
                break
    
    def process_audio(self, audio_data):
        """Process audio data and return frequency amplitudes"""
        # Apply FFT
        fft_data = np.abs(fft(audio_data))
        fft_data = fft_data[:len(fft_data)//2]  # Only positive frequencies
        
        # Create frequency array
        freqs = np.fft.fftfreq(len(audio_data), 1/self.sample_rate)
        freqs = freqs[:len(freqs)//2]
        
        # Bin the FFT data into our visualization bars
        bar_heights = []
        for i in range(self.num_bars):
            # Find frequencies in this bin
            freq_mask = (freqs >= self.freq_bins[i]) & (freqs < self.freq_bins[i+1])
            if np.any(freq_mask):
                # Average amplitude in this frequency range
                amplitude = np.mean(fft_data[freq_mask])
                bar_heights.append(amplitude)
            else:
                bar_heights.append(0)
        
        return np.array(bar_heights)
    
    def animate(self, frame):
        """Animation function for matplotlib"""
        if not self.audio_queue.empty():
            audio_data = self.audio_queue.get()
            bar_heights = self.process_audio(audio_data)
            
            # Smooth the visualization
            bar_heights = np.clip(bar_heights, 0, 1000)
            
            # Update bars
            for bar, height in zip(self.bars, bar_heights):
                bar.set_height(height)
        
        return self.bars
    
    def start(self):
        """Start the visualizer"""
        # Start audio capture thread
        audio_thread = threading.Thread(target=self.audio_callback, daemon=True)
        audio_thread.start()
        
        # Start animation
        ani = animation.FuncAnimation(self.fig, self.animate, interval=50, 
                                    blit=True, cache_frame_data=False)
        plt.show()
        
        # Cleanup
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

# Alternative: File-based visualizer (if you don't have microphone access)
class FileVisualizer:
    def __init__(self, audio_file, num_bars=50):
        import librosa
        
        self.num_bars = num_bars
        # Load audio file
        self.y, self.sr = librosa.load(audio_file)
        self.hop_length = 512
        
        # Compute spectrogram
        self.stft = librosa.stft(self.y, hop_length=self.hop_length)
        self.magnitude = np.abs(self.stft)
        
        # Setup visualization
        self.fig, self.ax = plt.subplots(figsize=(12, 6))
        self.bars = self.ax.bar(range(self.num_bars), [0] * self.num_bars, 
                               color='lime', alpha=0.8)
        self.ax.set_xlim(0, self.num_bars)
        self.ax.set_ylim(0, np.max(self.magnitude) * 0.1)
        self.ax.set_title('Audio File Visualizer')
        
        self.frame_count = self.magnitude.shape[1]
        
    def animate(self, frame):
        if frame < self.frame_count:
            # Get frequency data for this frame
            freq_data = self.magnitude[:, frame]
            
            # Bin into bars (take every nth frequency)
            step = len(freq_data) // self.num_bars
            bar_heights = []
            
            for i in range(self.num_bars):
                start_idx = i * step
                end_idx = min((i + 1) * step, len(freq_data))
                bar_heights.append(np.mean(freq_data[start_idx:end_idx]))
            
            # Update bars
            for bar, height in zip(self.bars, bar_heights):
                bar.set_height(height)
        
        return self.bars
    
    def start(self):
        ani = animation.FuncAnimation(self.fig, self.animate, 
                                    frames=self.frame_count, 
                                    interval=50, blit=True)
        plt.show()

if __name__ == "__main__":
    print("Choose visualizer type:")
    print("1. Real-time microphone input")
    print("2. Audio file")
    
    choice = input("Enter choice (1 or 2): ")
    
    if choice == "1":
        # Real-time visualizer
        visualizer = MusicVisualizer()
        print("Starting real-time visualizer... Speak or play music!")
        visualizer.start()
    
    elif choice == "2":
        # File visualizer
        audio_file = input("Enter path to audio file: ")
        try:
            visualizer = FileVisualizer(audio_file)
            print("Starting file visualizer...")
            visualizer.start()
        except Exception as e:
            print(f"Error loading file: {e}")
            print("Make sure you have librosa installed: pip install librosa")

# Required packages:
# pip install numpy matplotlib pyaudio scipy librosa
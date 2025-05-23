import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import librosa
import os
import time
import pygame
import threading
import math

class CircularAudioVisualizer:
    def __init__(self, audio_file, num_bars=100):
        self.audio_file = audio_file
        self.num_bars = num_bars
        self.is_playing = False
        self.start_time = None
        self.audio_start_time = None
        
        # Circle parameters
        self.center_x = 0.5  # Normalized center (polar coordinates)
        self.center_y = 0.5
        self.inner_radius = 0.2
        self.max_radius = 0.9
        
        # Initialize pygame mixer with optimized settings
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
        pygame.mixer.init()
        
        print("Loading audio file...")
        # Load audio file with duration limit for safety
        self.y, self.sr = librosa.load(audio_file, duration=300)  # Limit to 5 minutes max
        
        # Critical sync parameters
        self.hop_length = 256  # Smaller hop = better time resolution
        self.smoothing_factor = 0.5  # Responsive but smooth animation
        
        print("Computing spectrogram...")
        # Compute spectrogram with optimized parameters
        self.stft = librosa.stft(self.y, hop_length=self.hop_length)
        self.magnitude = np.abs(self.stft)
        
        # Apply logarithmic scaling and normalization
        self.magnitude = np.log1p(self.magnitude)
        self.magnitude /= np.max(self.magnitude)  # Global normalization
        
        self.frame_count = self.magnitude.shape[1]
        self.total_duration = self.frame_count * self.hop_length / self.sr
        self.fps = self.sr / self.hop_length
        
        # VIBGYOR colors with RGB values (0-1 range for matplotlib)
        self.vibgyor_colors = [
            (0.545, 0.0, 1.0),    # Violet
            (0.294, 0.0, 0.510),  # Indigo
            (0.0, 0.0, 1.0),       # Blue
            (0.0, 1.0, 0.0),       # Green
            (1.0, 1.0, 0.0),       # Yellow
            (1.0, 0.5, 0.0),       # Orange
            (1.0, 0.0, 0.0)        # Red
        ]

        # Precompute all animation data
        print("Precomputing circular animation data...")
        self.precompute_circular_data()
        
        # Initialize matplotlib figure with performance optimizations
        plt.ioff()
        self.fig, self.ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        self.fig.patch.set_facecolor('black')
        self.ax.set_facecolor('black')
        self.ax.set_ylim(0, 1)
        self.ax.set_theta_zero_location('N')  # Start from top
        self.ax.grid(False)
        self.ax.set_xticklabels([])
        self.ax.set_yticklabels([])
        
        # Initialize bars
        self.bars = []
        angles = np.linspace(0, 2*np.pi, self.num_bars, endpoint=False)
        for angle in angles:
            bar = self.ax.bar(angle, self.inner_radius, 
                             width=2*np.pi/self.num_bars*0.9,  # Slightly smaller width for gaps
                             bottom=self.inner_radius, 
                             alpha=0.8, 
                             edgecolor='none')
            self.bars.append(bar)
        
        # Add timestamp text
        self.timestamp_text = self.ax.text(0.02, 0.95, '', transform=self.ax.transAxes,
                                         fontsize=12, color='white',
                                         bbox=dict(boxstyle='round', facecolor='black', alpha=0.8))
        
        # Performance tracking
        self.frame_times = []
        self.sync_adjustments = 0
        self.adaptive_interval = max(16, 1000/self.fps * 0.8)  # Start 20% faster
        
        print(f"Audio analysis:")
        print(f"  Sample rate: {self.sr} Hz")
        print(f"  Hop length: {self.hop_length}")
        print(f"  Target FPS: {self.fps:.2f}")
        print(f"  Adaptive interval: {self.adaptive_interval:.2f}ms")
        print("Precomputation complete! Ready to play.")

    def precompute_circular_data(self):
        """Precompute all bar heights and colors with sync optimizations"""
        self.precomputed_heights = []
        self.precomputed_colors = []
        
        prev_heights = None
        angle_step = 2 * math.pi / self.num_bars
        
        for frame in range(self.frame_count):
            # Get frequency data for this frame
            freq_data = self.magnitude[:, frame]
            
            # Apply frequency weighting
            freq_weights = np.linspace(1.0, 0.3, len(freq_data))
            freq_data = freq_data * freq_weights
            
            # Bin into bars with RMS calculation
            num_freq_bins = len(freq_data)
            bins_per_bar = num_freq_bins // self.num_bars
            
            bar_heights = []
            for i in range(self.num_bars):
                start_idx = i * bins_per_bar
                end_idx = min((i + 1) * bins_per_bar, num_freq_bins)
                
                if end_idx > start_idx:
                    height = np.sqrt(np.mean(freq_data[start_idx:end_idx] ** 2))
                    bar_heights.append(max(height, 0.01))
                else:
                    bar_heights.append(0.01)
            
            # Apply smoothing from original visualizer
            if prev_heights is not None:
                bar_heights = [self.smoothing_factor * prev + (1 - self.smoothing_factor) * curr 
                             for prev, curr in zip(prev_heights, bar_heights)]
            
            prev_heights = bar_heights.copy()
            self.precomputed_heights.append(bar_heights)
            
            # Calculate colors with animation
            colors = []
            frame_offset = (frame * 0.002) % len(self.vibgyor_colors)
            bars_per_color = self.num_bars / len(self.vibgyor_colors)
            
            for i in range(self.num_bars):
                position = (i + frame_offset * bars_per_color) / bars_per_color
                color_idx = int(position) % len(self.vibgyor_colors)
                next_idx = (color_idx + 1) % len(self.vibgyor_colors)
                factor = position - int(position)
                
                color = [
                    self.vibgyor_colors[color_idx][0] * (1-factor) + self.vibgyor_colors[next_idx][0] * factor,
                    self.vibgyor_colors[color_idx][1] * (1-factor) + self.vibgyor_colors[next_idx][1] * factor,
                    self.vibgyor_colors[color_idx][2] * (1-factor) + self.vibgyor_colors[next_idx][2] * factor
                ]
                colors.append(color)
            
            self.precomputed_colors.append(colors)

    def play_audio(self):
        """Play audio with precise timing"""
        try:
            pygame.mixer.music.load(self.audio_file)
            pygame.mixer.music.play()
            self.is_playing = True
            self.audio_start_time = time.time()
            print("🎵 Audio playback started!")
        except Exception as e:
            print(f"Audio playback error: {e}")
            self.is_playing = False

    def stop_audio(self):
        """Stop audio playback"""
        pygame.mixer.music.stop()
        self.is_playing = False
        print("🔇 Audio playback stopped!")

    def get_audio_position(self):
        """Get current audio playback position in seconds"""
        if self.audio_start_time and self.is_playing:
            return time.time() - self.audio_start_time
        return 0

    def format_timestamp(self, seconds):
        """Format seconds into MM:SS format"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def get_current_frame_from_audio(self):
        """Calculate which frame we should be showing based on audio position"""
        if not self.is_playing:
            return None
        
        audio_time = self.get_audio_position()
        expected_frame = int((audio_time * self.sr) / self.hop_length)
        return min(expected_frame, self.frame_count - 1)

    def animate(self, frame):
        """Animation function with all sync features from original"""
        current_time = time.time()
        
        # Start audio on first frame
        if frame == 0 and not self.is_playing:
            self.play_audio()
            self.start_time = current_time
            actual_frame = 0
        else:
            # Sync with actual audio position
            audio_frame = self.get_current_frame_from_audio()
            if audio_frame is not None and abs(audio_frame - frame) > 2:  # More than 2 frames off
                actual_frame = audio_frame
                self.sync_adjustments += 1
            else:
                actual_frame = frame
        
        # Ensure we don't go out of bounds
        actual_frame = min(actual_frame, len(self.precomputed_heights) - 1)
        
        if actual_frame < len(self.precomputed_heights):
            # Calculate times for display
            expected_time = actual_frame * self.hop_length / self.sr
            
            if self.is_playing:
                actual_audio_time = self.get_audio_position()
                sync_diff = actual_audio_time - expected_time
                
                timestamp_str = f"Time: {self.format_timestamp(actual_audio_time)} / {self.format_timestamp(self.total_duration)}"
                
                # Show sync status if significantly off
                if abs(sync_diff) > 0.2:  # More than 200ms off
                    sync_status = f" [Sync: {sync_diff:+.1f}s]"
                    timestamp_str += sync_status
            else:
                timestamp_str = f"Time: {self.format_timestamp(expected_time)} / {self.format_timestamp(self.total_duration)}"
            
            self.timestamp_text.set_text(timestamp_str)
            
            # Update bars with precomputed values
            bar_heights = self.precomputed_heights[actual_frame]
            colors = self.precomputed_colors[actual_frame]

            for bar, height, color in zip(self.bars, bar_heights, colors):
                bar[0].set_height(height * (self.max_radius - self.inner_radius))
                bar[0].set_color(color)
        
        # Performance monitoring
        if len(self.frame_times) > 100:
            self.frame_times.pop(0)
        self.frame_times.append(current_time)
            
        return [bar[0] for bar in self.bars] + [self.timestamp_text]

    def on_close(self, event):
        """Handle window close event"""
        self.stop_audio()
        plt.close('all')

    def start(self):
        """Start the animation with all optimizations"""
        print(f"\nStarting circular visualizer:")
        print(f"  Adaptive interval: {self.adaptive_interval:.1f}ms")
        print(f"  Total frames: {self.frame_count}")
        print(f"  Duration: {self.total_duration:.1f}s")
        
        # Connect close event
        self.fig.canvas.mpl_connect('close_event', self.on_close)
        
        # Use adaptive interval for better sync
        ani = animation.FuncAnimation(self.fig, self.animate, 
                                    frames=self.frame_count, 
                                    interval=self.adaptive_interval,
                                    blit=True, 
                                    repeat=False,
                                    cache_frame_data=False)
        
        plt.show()
        return ani

if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    audio_file = os.path.join(base_dir, "audio3.mp3")
    try:
        print("Initializing Circular Audio Visualizer...")
        visualizer = CircularAudioVisualizer(audio_file, num_bars=120)
        print("\n" + "="*50)
        print("READY TO PLAY!")
        print("="*50)
        visualizer.start()
    except Exception as e:
        print(f"Error: {e}\nMake sure the audio file path is correct and libraries are installed.")
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import librosa
import os
import time
import pygame
import threading

class FileVisualizer:
    def __init__(self, audio_file, num_bars=100):
        self.audio_file = audio_file
        self.num_bars = num_bars
        self.is_playing = False
        self.start_time = None
        self.audio_start_time = None
        
        # Initialize pygame mixer for audio playback
        pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
        
        print("Loading audio file...")
        # Load audio file
        self.y, self.sr = librosa.load(audio_file)
        
        # CRITICAL: Reduce hop_length for better time resolution
        self.hop_length = 256  # Smaller hop = more frames, better sync (was 512)

        print("Computing spectrogram...")
        # Compute spectrogram
        self.stft = librosa.stft(self.y, hop_length=self.hop_length)
        self.magnitude = np.abs(self.stft)
        
        # Apply logarithmic scaling and normalization for better visualization
        self.magnitude = np.log1p(self.magnitude)  # log(1+x) to avoid log(0)
        
        # Normalize each frequency bin across time to reduce frequency bias
        for i in range(self.magnitude.shape[0]):
            freq_data = self.magnitude[i, :]
            if np.max(freq_data) > 0:
                self.magnitude[i, :] = freq_data / np.max(freq_data)

        # Frequency axis setup
        self.freqs = librosa.fft_frequencies(sr=self.sr)

        # Setup visualization with optimized figure
        plt.ioff()  # Turn off interactive mode for better performance
        self.fig, self.ax = plt.subplots(figsize=(12, 6))
        self.fig.patch.set_facecolor('black')  # Black background for better performance
        self.ax.set_facecolor('black')

        # VIBGYOR gradient colors for cycling animation
        self.vibgyor_colors = [
            '#8B00FF',  # Violet
            '#4B0082',  # Indigo
            '#0000FF',  # Blue
            '#00FF00',  # Green
            '#FFFF00',  # Yellow
            '#FF7F00',  # Orange
            '#FF0000'   # Red
        ]

        # Pre-compute all color combinations for better performance
        print("Precomputing colors...")
        self.precompute_colors()

        # Initialize bars with optimized settings
        initial_colors = self.get_vibgyor_colors(0)
        self.bars = self.ax.bar(range(self.num_bars), [1e-6] * self.num_bars, 
                                color=initial_colors, alpha=0.8, edgecolor='none')  # No edges for performance

        self.ax.set_xlim(0, self.num_bars)
        self.ax.set_ylim(0, 1.05)  # Linear scale, normalized data
        self.ax.set_title('Audio File Visualizer', color='white')
        self.ax.set_xlabel('Frequency (approx bins)', color='white')
        self.ax.set_ylabel('Normalized Amplitude', color='white')
        self.ax.tick_params(colors='white')
        
        # Add timestamp text
        self.timestamp_text = self.ax.text(0.02, 0.95, '', transform=self.ax.transAxes,
                                         fontsize=12, verticalalignment='top', color='white',
                                         bbox=dict(boxstyle='round', facecolor='black', alpha=0.8))
        
        # Frequency axis labels
        tick_positions = np.linspace(0, self.num_bars, 6).astype(int)
        tick_labels = []
        for i in tick_positions:
            freq_idx = min(int(i * len(self.freqs) / self.num_bars), len(self.freqs) - 1)
            freq_khz = int(self.freqs[freq_idx] / 1000)
            tick_labels.append(f"{freq_khz}kHz")
        
        self.ax.set_xticks(tick_positions)
        self.ax.set_xticklabels(tick_labels)

        self.frame_count = self.magnitude.shape[1]
        
        # Calculate total duration for timestamp
        self.total_duration = self.frame_count * self.hop_length / self.sr
        
        # Calculate proper frame rate and interval
        self.fps = self.sr / self.hop_length  # Actual FPS based on audio analysis
        self.target_interval = 1000 / self.fps  # Target interval in milliseconds
        
        # Adaptive interval - start more aggressive
        self.adaptive_interval = max(16, self.target_interval * 0.8)  # Start 20% faster
        
        print(f"Audio analysis:")
        print(f"  Sample rate: {self.sr} Hz")
        print(f"  Hop length: {self.hop_length}")
        print(f"  Target FPS: {self.fps:.2f}")
        print(f"  Target interval: {self.target_interval:.2f}ms")
        print(f"  Adaptive interval: {self.adaptive_interval:.2f}ms")
        
        # Precompute all animation data
        print("Precomputing animation data...")
        self.precompute_animation_data()
        
        # Performance tracking
        self.frame_times = []
        self.sync_adjustments = 0
        
        print("Precomputation complete! Ready to play.")

    def precompute_animation_data(self):
        """Precompute all bar heights, colors, and timestamps for smooth playback"""
        self.precomputed_heights = []
        self.precomputed_colors = []
        self.precomputed_timestamps = []
        
        prev_heights = None
        
        # Show progress for long computations
        progress_interval = max(1, self.frame_count // 20)
        
        for frame in range(self.frame_count):
            if frame % progress_interval == 0:
                progress = (frame / self.frame_count) * 100
                print(f"  Progress: {progress:.1f}%")
            
            # Calculate current timestamp
            current_time = frame * self.hop_length / self.sr
            timestamp_str = f"Time: {self.format_timestamp(current_time)} / {self.format_timestamp(self.total_duration)}"
            self.precomputed_timestamps.append(timestamp_str)
            
            # Get frequency data for this frame
            freq_data = self.magnitude[:, frame]

            # Apply frequency weighting to reduce high-frequency dominance
            freq_weights = np.linspace(1.0, 0.3, len(freq_data))
            freq_data = freq_data * freq_weights

            # Bin into bars with improved averaging
            num_freq_bins = len(freq_data)
            bins_per_bar = num_freq_bins // self.num_bars
            
            bar_heights = []
            for i in range(self.num_bars):
                start_idx = i * bins_per_bar
                if i == self.num_bars - 1:
                    end_idx = num_freq_bins
                else:
                    end_idx = (i + 1) * bins_per_bar
                
                end_idx = min(end_idx, num_freq_bins)
                
                if end_idx > start_idx:
                    # Use RMS instead of mean for better representation
                    height = np.sqrt(np.mean(freq_data[start_idx:end_idx] ** 2))
                    bar_heights.append(max(height, 1e-6))
                else:
                    bar_heights.append(1e-6)

            # Apply lighter smoothing to reduce jitter but maintain responsiveness
            if prev_heights is not None:
                smoothing_factor = 0.5  # Reduced from 0.7 for more responsiveness
                bar_heights = [smoothing_factor * prev + (1 - smoothing_factor) * curr 
                             for prev, curr in zip(prev_heights, bar_heights)]
            
            prev_heights = bar_heights.copy()
            self.precomputed_heights.append(bar_heights)

            # Get colors for this frame
            colors = self.get_vibgyor_colors(frame)
            self.precomputed_colors.append(colors)

    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def rgb_to_hex(self, rgb):
        """Convert RGB tuple to hex color"""
        return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
    
    def interpolate_color(self, color1, color2, factor):
        """Interpolate between two colors"""
        rgb1 = self.hex_to_rgb(color1)
        rgb2 = self.hex_to_rgb(color2)
        
        interpolated = [
            rgb1[i] + factor * (rgb2[i] - rgb1[i])
            for i in range(3)
        ]
        return self.rgb_to_hex(interpolated)

    def precompute_colors(self):
        """Pre-compute color transitions for better performance"""
        self.color_cache = {}
        steps = 50  # Reduced steps for better performance (was 100)
        
        for i in range(len(self.vibgyor_colors)):
            next_i = (i + 1) % len(self.vibgyor_colors)
            color1 = self.vibgyor_colors[i]
            color2 = self.vibgyor_colors[next_i]
            
            interpolated_colors = []
            for step in range(steps):
                factor = step / steps
                interpolated_colors.append(self.interpolate_color(color1, color2, factor))
            
            self.color_cache[i] = interpolated_colors

    def get_vibgyor_colors(self, frame):
        """Generate smooth VIBGYOR spectrum colors that cycle right to left"""
        colors = []
        bars_per_color = self.num_bars / len(self.vibgyor_colors)
        
        # Calculate offset for right-to-left movement (faster movement)
        frame_offset = (frame * 0.002) % len(self.vibgyor_colors)
        
        for i in range(self.num_bars):
            # Calculate position in the color spectrum with frame offset
            position = (i + frame_offset * bars_per_color) / bars_per_color
            
            # Which color segment are we in?
            color_idx = int(position) % len(self.vibgyor_colors)
            
            # How far through this color segment?
            interpolation_factor = position - int(position)
            
            # Use pre-computed colors for better performance
            if color_idx in self.color_cache:
                step_idx = int(interpolation_factor * (len(self.color_cache[color_idx]) - 1))
                colors.append(self.color_cache[color_idx][step_idx])
            else:
                colors.append(self.vibgyor_colors[color_idx])
        
        return colors

    def play_audio(self):
        """Play audio using pygame in a separate thread"""
        try:
            pygame.mixer.music.load(self.audio_file)
            pygame.mixer.music.play()
            self.is_playing = True
            self.audio_start_time = time.time()  # Track audio start time separately
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
        """Animation function - with improved audio synchronization"""
        current_time = time.time()
        
        # Start audio on first frame
        if frame == 0 and not self.is_playing:
            self.play_audio()
            self.start_time = current_time
            actual_frame = 0
        else:
            # Try to sync with actual audio position
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
            
            # Get precomputed data
            bar_heights = self.precomputed_heights[actual_frame]
            colors = self.precomputed_colors[actual_frame]

            # Update bars with precomputed values - optimized loop
            for bar, height, color in zip(self.bars, bar_heights, colors):
                bar.set_height(height)
                bar.set_color(color)
        
        # Track frame times for performance monitoring
        if len(self.frame_times) > 100:
            self.frame_times.pop(0)
        if len(self.frame_times) > 0:
            frame_time = current_time - self.frame_times[-1] if self.frame_times else 0
            self.frame_times.append(current_time)
            
            # Show performance stats occasionally
            if frame % 60 == 0 and frame > 0:  # Every 60 frames
                avg_frame_time = np.mean(np.diff(self.frame_times[-30:])) * 1000  # Last 30 frames in ms
                actual_fps = 1000 / avg_frame_time if avg_frame_time > 0 else 0
                print(f"Frame {frame}: Avg frame time: {avg_frame_time:.1f}ms, FPS: {actual_fps:.1f}, Sync adjustments: {self.sync_adjustments}")
        else:
            self.frame_times.append(current_time)

        return list(self.bars) + [self.timestamp_text]

    def on_close(self, event):
        """Handle window close event"""
        self.stop_audio()
        plt.close('all')

    def start(self):
        """Start the animation with real-time playback"""
        print(f"\nStarting real-time playback:")
        print(f"  Adaptive interval: {self.adaptive_interval:.1f}ms")
        print(f"  Total frames: {self.frame_count}")
        print(f"  Duration: {self.total_duration:.1f}s")
        print(f"  Target FPS: {self.fps:.1f}")
        
        # Connect close event
        self.fig.canvas.mpl_connect('close_event', self.on_close)
        
        # Use adaptive interval for better sync
        ani = animation.FuncAnimation(self.fig, self.animate, 
                                      frames=self.frame_count, 
                                      interval=self.adaptive_interval,  # Use adaptive interval
                                      blit=True, 
                                      repeat=False,
                                      cache_frame_data=False)  # Don't cache for better memory usage
        
        plt.show()
        return ani  # Return animation object to keep reference

if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    audio_file = os.path.join(base_dir, "audio4.mp3")
    try:
        print("Initializing Audio File Visualizer...")
        visualizer = FileVisualizer(audio_file, num_bars=100)
        print("\n" + "="*50)
        print("READY TO PLAY!")
        print("="*50)
        visualizer.start()
    except Exception as e:
        print(f"Error: {e}\nMake sure the audio file path is correct and librosa is installed.")
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import librosa
import os

class FileVisualizer:
    def __init__(self, audio_file, num_bars=100):
        self.num_bars = num_bars
        
        # Load audio file
        self.y, self.sr = librosa.load(audio_file)
        self.hop_length = 256

        # Compute spectrogram
        self.stft = librosa.stft(self.y, hop_length=self.hop_length)
        self.magnitude = np.abs(self.stft)
        

        # Frequency axis setup
        self.freqs = librosa.fft_frequencies(sr=self.sr)

        # Setup visualization
        self.fig, self.ax = plt.subplots(figsize=(12, 6))

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
        self.precompute_colors()

        # Initialize bars
        initial_colors = self.get_vibgyor_colors(0)
        self.bars = self.ax.bar(range(self.num_bars), [1e-6] * self.num_bars, 
                                color=initial_colors, alpha=0.8)

        self.ax.set_xlim(0, self.num_bars)
        # Use logarithmic scale for y-axis
        self.ax.set_yscale('linear')  # Now we use linear since it's normalized
        self.ax.set_ylim(0, 1.05)
        self.ax.set_title('Audio File Visualizer')
        self.ax.set_xlabel('Frequency (approx bins)')
        
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
        steps = 100  # Number of interpolation steps between colors
        
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

    def animate(self, frame):
        if frame < self.frame_count:
            # Get frequency data for this frame
            freq_data = self.magnitude[:, frame]

            # Bin into bars
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
                    height = np.mean(freq_data[start_idx:end_idx])
                    bar_heights.append(max(height, 1e-6))
                else:
                    bar_heights.append(1e-6)

            # Get colors for this frame
            colors = self.get_vibgyor_colors(frame)

            # Update bars
            for i, (bar, height) in enumerate(zip(self.bars, bar_heights)):
                bar.set_height(height)
                bar.set_color(colors[i])

        return self.bars

    def start(self):
        # Calculate proper interval for smooth animation
        # The interval should match the audio frame rate
        interval = (self.hop_length / self.sr) * 1000  # Convert to milliseconds
        
        print(f"Animation interval: {interval:.1f}ms")
        print(f"Total frames: {self.frame_count}")
        print(f"Duration: {self.frame_count * interval / 1000:.1f}s")
        
        ani = animation.FuncAnimation(self.fig, self.animate, 
                                      frames=self.frame_count, 
                                      interval=interval, 
                                      blit=True, 
                                      repeat=False)
        
        plt.show()

if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    audio_file = os.path.join(base_dir, "audio2.mp3")
    try:
        visualizer = FileVisualizer(audio_file, num_bars=100)
        print("Starting file visualizer...")
        visualizer.start()
    except Exception as e:
        print(f"Error: {e}\nMake sure the audio file path is correct and librosa is installed.")
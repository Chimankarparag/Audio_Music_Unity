import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import librosa
import os
import time
import pygame
import threading
import math

# For alternative backends (install separately)
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

try:
    from OpenGL.GL import *
    import glfw
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False

class CircularAudioVisualizer:
    def __init__(self, audio_file, num_bars=100, backend='matplotlib'):
        """
        Initialize circular audio visualizer
        
        Args:
            audio_file: Path to audio file
            num_bars: Number of frequency bars
            backend: 'matplotlib', 'pygame', 'opencv', or 'opengl'
        """
        self.audio_file = audio_file
        self.num_bars = num_bars
        self.backend = backend
        self.is_playing = False
        self.start_time = None
        self.audio_start_time = None
        
        # Circle parameters
        self.center_x = 400
        self.center_y = 400
        self.inner_radius = 100
        self.max_radius = 300
        
        # Initialize pygame mixer for audio playback
        pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
        
        print("Loading audio file...")
        # Load audio file
        self.y, self.sr = librosa.load(audio_file)
        self.hop_length = 256
        
        print("Computing spectrogram...")
        # Compute spectrogram
        self.stft = librosa.stft(self.y, hop_length=self.hop_length)
        self.magnitude = np.abs(self.stft)
        
        # Apply logarithmic scaling and normalization
        self.magnitude = np.log1p(self.magnitude)
        
        # Normalize each frequency bin
        for i in range(self.magnitude.shape[0]):
            freq_data = self.magnitude[i, :]
            if np.max(freq_data) > 0:
                self.magnitude[i, :] = freq_data / np.max(freq_data)
        
        self.frame_count = self.magnitude.shape[1]
        self.total_duration = self.frame_count * self.hop_length / self.sr
        self.fps = self.sr / self.hop_length
        
        # VIBGYOR colors
        self.vibgyor_colors = [
            (139, 0, 255),    # Violet
            (75, 0, 130),     # Indigo
            (0, 0, 255),      # Blue
            (0, 255, 0),      # Green
            (255, 255, 0),    # Yellow
            (255, 127, 0),    # Orange
            (255, 0, 0)       # Red
        ]
        
        # Precompute animation data
        print("Precomputing animation data...")
        self.precompute_circular_data()
        
        # Initialize backend
        self.init_backend()
        
        print("Circular visualizer ready!")

    def precompute_circular_data(self):
        """Precompute all bar positions, heights, and colors for circular display"""
        self.precomputed_bars = []
        self.precomputed_colors = []
        
        # Calculate angle step
        angle_step = 2 * math.pi / self.num_bars
        
        prev_heights = None
        
        for frame in range(self.frame_count):
            if frame % (self.frame_count // 20) == 0:
                progress = (frame / self.frame_count) * 100
                print(f"  Progress: {progress:.1f}%")
            
            # Get frequency data for this frame
            freq_data = self.magnitude[:, frame]
            
            # Apply frequency weighting
            freq_weights = np.linspace(1.0, 0.3, len(freq_data))
            freq_data = freq_data * freq_weights
            
            # Bin into bars
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
            
            # Apply smoothing
            if prev_heights is not None:
                smoothing_factor = 0.5
                bar_heights = [smoothing_factor * prev + (1 - smoothing_factor) * curr 
                             for prev, curr in zip(prev_heights, bar_heights)]
            
            prev_heights = bar_heights.copy()
            
            # Calculate circular bar positions
            bars = []
            colors = []
            
            for i in range(self.num_bars):
                angle = i * angle_step - math.pi/2  # Start from top
                
                # Calculate bar properties
                bar_height = bar_heights[i] * (self.max_radius - self.inner_radius)
                outer_radius = self.inner_radius + bar_height
                
                # Calculate bar endpoints
                inner_x = self.center_x + self.inner_radius * math.cos(angle)
                inner_y = self.center_y + self.inner_radius * math.sin(angle)
                outer_x = self.center_x + outer_radius * math.cos(angle)
                outer_y = self.center_y + outer_radius * math.sin(angle)
                
                bars.append({
                    'angle': angle,
                    'inner_x': inner_x,
                    'inner_y': inner_y,
                    'outer_x': outer_x,
                    'outer_y': outer_y,
                    'height': bar_height,
                    'thickness': max(2, angle_step * self.inner_radius * 0.8)  # Bar thickness
                })
                
                # Calculate color based on position and frame
                color_index = (i + frame * 0.1) % len(self.vibgyor_colors)
                color1_idx = int(color_index) % len(self.vibgyor_colors)
                color2_idx = (color1_idx + 1) % len(self.vibgyor_colors)
                factor = color_index - int(color_index)
                
                color1 = self.vibgyor_colors[color1_idx]
                color2 = self.vibgyor_colors[color2_idx]
                
                interpolated_color = tuple(
                    int(color1[j] + factor * (color2[j] - color1[j]))
                    for j in range(3)
                )
                colors.append(interpolated_color)
            
            self.precomputed_bars.append(bars)
            self.precomputed_colors.append(colors)

    def init_backend(self):
        """Initialize the selected backend"""
        if self.backend == 'matplotlib':
            self.init_matplotlib()
        elif self.backend == 'pygame':
            if PYGAME_AVAILABLE:
                self.init_pygame()
            else:
                print("Pygame not available, falling back to matplotlib")
                self.backend = 'matplotlib'
                self.init_matplotlib()
        elif self.backend == 'opencv':
            if OPENCV_AVAILABLE:
                self.init_opencv()
            else:
                print("OpenCV not available, falling back to matplotlib")
                self.backend = 'matplotlib'
                self.init_matplotlib()
        elif self.backend == 'opengl':
            if OPENGL_AVAILABLE:
                self.init_opengl()
            else:
                print("OpenGL not available, falling back to matplotlib")
                self.backend = 'matplotlib'
                self.init_matplotlib()

    def init_matplotlib(self):
        """Initialize matplotlib circular visualizer"""
        plt.ioff()
        self.fig, self.ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        self.fig.patch.set_facecolor('black')
        self.ax.set_facecolor('black')
        self.ax.set_ylim(0, self.max_radius)
        self.ax.set_title('Circular Audio Visualizer', color='white', pad=20)
        self.ax.grid(True, alpha=0.3)
        self.ax.set_theta_zero_location('N')  # Start from top
        
        # Initialize bars
        self.bars = []
        angles = np.linspace(0, 2*np.pi, self.num_bars, endpoint=False)
        for angle in angles:
            bar = self.ax.bar(angle, self.inner_radius, width=2*np.pi/self.num_bars, 
                            bottom=self.inner_radius, alpha=0.8, edgecolor='none')
            self.bars.append(bar)

    def init_pygame(self):
        """Initialize Pygame circular visualizer"""
        pygame.init()
        self.screen_size = (800, 800)
        self.screen = pygame.display.set_mode(self.screen_size)
        pygame.display.set_caption("Circular Audio Visualizer - Pygame")
        self.clock = pygame.time.Clock()

    def init_opencv(self):
        """Initialize OpenCV circular visualizer"""
        self.canvas_size = (800, 800)
        cv2.namedWindow('Circular Audio Visualizer - OpenCV', cv2.WINDOW_AUTOSIZE)

    def init_opengl(self):
        """Initialize OpenGL circular visualizer"""
        if not glfw.init():
            return
        
        self.window = glfw.create_window(800, 800, "Circular Audio Visualizer - OpenGL", None, None)
        if not self.window:
            glfw.terminate()
            return
        
        glfw.make_context_current(self.window)
        glClearColor(0.0, 0.0, 0.0, 1.0)

    def play_audio(self):
        """Play audio using pygame"""
        try:
            pygame.mixer.music.load(self.audio_file)
            pygame.mixer.music.play()
            self.is_playing = True
            self.audio_start_time = time.time()
            print("🎵 Audio playback started!")
        except Exception as e:
            print(f"Audio playback error: {e}")
            self.is_playing = False

    def get_audio_position(self):
        """Get current audio playback position"""
        if self.audio_start_time and self.is_playing:
            return time.time() - self.audio_start_time
        return 0

    def get_current_frame(self):
        """Get current frame based on audio position"""
        if not self.is_playing:
            return 0
        
        audio_time = self.get_audio_position()
        frame = int((audio_time * self.sr) / self.hop_length)
        return min(frame, self.frame_count - 1)

    def draw_circular_bars_pygame(self, frame_idx):
        """Draw circular bars using Pygame"""
        self.screen.fill((0, 0, 0))  # Black background
        
        if frame_idx < len(self.precomputed_bars):
            bars = self.precomputed_bars[frame_idx]
            colors = self.precomputed_colors[frame_idx]
            
            for bar, color in zip(bars, colors):
                # Draw bar as a thick line
                pygame.draw.line(self.screen, color,
                               (int(bar['inner_x']), int(bar['inner_y'])),
                               (int(bar['outer_x']), int(bar['outer_y'])),
                               max(2, int(bar['thickness'])))
        
        # Draw center circle
        pygame.draw.circle(self.screen, (50, 50, 50), 
                         (self.center_x, self.center_y), self.inner_radius, 2)
        
        # Draw timestamp
        font = pygame.font.Font(None, 36)
        time_text = f"{self.get_audio_position():.1f}s / {self.total_duration:.1f}s"
        text_surface = font.render(time_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(self.center_x, self.center_y))
        self.screen.blit(text_surface, text_rect)
        
        pygame.display.flip()

    def draw_circular_bars_opencv(self, frame_idx):
        """Draw circular bars using OpenCV"""
        canvas = np.zeros((self.canvas_size[1], self.canvas_size[0], 3), dtype=np.uint8)
        
        if frame_idx < len(self.precomputed_bars):
            bars = self.precomputed_bars[frame_idx]
            colors = self.precomputed_colors[frame_idx]
            
            for bar, color in zip(bars, colors):
                # Draw bar as a thick line
                cv2.line(canvas,
                        (int(bar['inner_x']), int(bar['inner_y'])),
                        (int(bar['outer_x']), int(bar['outer_y'])),
                        color[::-1],  # BGR format for OpenCV
                        max(2, int(bar['thickness'])))
        
        # Draw center circle
        cv2.circle(canvas, (self.center_x, self.center_y), self.inner_radius, (50, 50, 50), 2)
        
        # Draw timestamp
        time_text = f"{self.get_audio_position():.1f}s / {self.total_duration:.1f}s"
        cv2.putText(canvas, time_text, (self.center_x - 100, self.center_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.imshow('Circular Audio Visualizer - OpenCV', canvas)

    def animate_matplotlib(self, frame):
        """Matplotlib animation function"""
        if frame == 0:
            self.play_audio()
        
        current_frame = self.get_current_frame()
        
        if current_frame < len(self.precomputed_bars):
            bars_data = self.precomputed_bars[current_frame]
            colors = self.precomputed_colors[current_frame]
            
            for i, (bar_container, color) in enumerate(zip(self.bars, colors)):
                bar = bar_container[0]  # Get the bar patch
                bar_height = bars_data[i]['height'] 
                bar.set_height(bar_height)
                bar.set_color([c/255.0 for c in color])  # Convert to 0-1 range
        
        return [bar[0] for bar in self.bars]

    def start(self):
        """Start the circular visualizer"""
        print(f"\nStarting circular visualizer with {self.backend} backend...")
        
        if self.backend == 'matplotlib':
            ani = animation.FuncAnimation(self.fig, self.animate_matplotlib,
                                        frames=self.frame_count,
                                        interval=max(16, 1000/self.fps * 0.8),
                                        blit=True, repeat=False)
            plt.show()
            return ani
            
        elif self.backend == 'pygame':
            self.play_audio()
            running = True
            frame_count = 0
            
            while running and frame_count < self.frame_count:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                
                current_frame = self.get_current_frame()
                self.draw_circular_bars_pygame(current_frame)
                self.clock.tick(60)  # 60 FPS
                frame_count += 1
            
            pygame.quit()
            
        elif self.backend == 'opencv':
            self.play_audio()
            frame_count = 0
            
            while frame_count < self.frame_count:
                current_frame = self.get_current_frame()
                self.draw_circular_bars_opencv(current_frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
                frame_count += 1
                time.sleep(1/60)  # 60 FPS
            
            cv2.destroyAllWindows()

# Convenience functions
def create_circular_visualizer(audio_file, backend='pygame', num_bars=100):
    """
    Create and start a circular audio visualizer
    
    Args:
        audio_file: Path to audio file
        backend: 'matplotlib', 'pygame', 'opencv', or 'opengl'
        num_bars: Number of frequency bars
    
    Returns:
        CircularAudioVisualizer instance
    """
    visualizer = CircularAudioVisualizer(audio_file, num_bars, backend)
    return visualizer

def compare_backends(audio_file):
    """Compare different backend performance"""
    backends = []
    
    if PYGAME_AVAILABLE:
        backends.append('pygame')
    if OPENCV_AVAILABLE:
        backends.append('opencv')
    backends.append('matplotlib')  # Always available
    
    print("Available backends for comparison:")
    for i, backend in enumerate(backends):
        print(f"{i+1}. {backend}")
    
    return backends

if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    audio_file = os.path.join(base_dir, "audio3.mp3")
    
    # Show available backends
    available_backends = compare_backends(audio_file)
    
    try:
        print("\nChoose backend:")
        print("1. Pygame (Recommended - Fastest)")
        print("2. OpenCV (Good performance)")
        print("3. Matplotlib (Slowest but most compatible)")
        
        choice = input("Enter choice (1-3) or press Enter for Pygame: ").strip()
        
        if choice == '2':
            backend = 'opencv'
        elif choice == '3':
            backend = 'matplotlib'
        else:
            backend = 'pygame'
        
        print(f"\nInitializing circular visualizer with {backend} backend...")
        visualizer = create_circular_visualizer(audio_file, backend=backend, num_bars=120)
        visualizer.start()
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the audio file exists and required libraries are installed.")
        print("\nTo install additional backends:")
        print("pip install pygame opencv-python PyOpenGL glfw")
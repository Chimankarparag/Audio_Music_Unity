import numpy as np
import sounddevice as sd
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
from scipy.signal import butter, lfilter

class RealTimeVisualizer:
    def __init__(self, sample_rate=44100, chunk_size=1024, silence_threshold=0.01):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.silence_threshold = silence_threshold
        self.window = np.hanning(chunk_size)
        self.freqs = np.fft.rfftfreq(chunk_size, d=1/sample_rate)

        # Initialize smoothing
        self.prev_fft = np.zeros(len(self.freqs))
        self.smooth_alpha = 0.8  # 0 = no smoothing, 1 = full smoothing

        # Set up PyQtGraph window
        self.app = QtWidgets.QApplication([])
        self.win = pg.GraphicsLayoutWidget(title="Live Audio Spectrum")
        self.plot = self.win.addPlot(title="Frequency Domain")
        self.curve = self.plot.plot(pen='y')
        self.plot.setLogMode(x=True, y=False)
        self.plot.setYRange(0, 1, padding=0)
        self.plot.setXRange(np.log10(50), np.log10(15000))
        self.plot.setLabel('bottom', 'Frequency (Hz)')
        self.plot.setLabel('left', 'Amplitude')
        self.plot.setLimits(xMin=0, xMax=self.freqs[-1])

        # Optional: high-pass filter setup
        self.use_highpass = False
        self.hp_b, self.hp_a = butter(2, 50 / (0.5 * self.sample_rate), btype='high')

    def highpass_filter(self, data):
        return lfilter(self.hp_b, self.hp_a, data)

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status)

        audio = indata[:, 0]

        # Optional: apply high-pass filter
        if self.use_highpass:
            audio = self.highpass_filter(audio)

        # Check for silence
        rms = np.sqrt(np.mean(audio**2))
        if rms < self.silence_threshold:
            self.curve.setData(self.freqs, np.zeros_like(self.freqs))
            return

        # Apply window and FFT
        windowed = audio * self.window
        fft_result = np.abs(np.fft.rfft(windowed))

        if np.max(fft_result) > 0:
            fft_result /= np.max(fft_result)  # Normalize

        # Smooth FFT output
        smoothed_fft = self.smooth_alpha * self.prev_fft + (1 - self.smooth_alpha) * fft_result
        self.prev_fft = smoothed_fft

        # Update curve
        self.curve.setData(self.freqs, smoothed_fft)

    def run(self):
        self.win.show()

        stream = sd.InputStream(
            callback=self.audio_callback,
            channels=1,
            samplerate=self.sample_rate,
            blocksize=self.chunk_size
        )

        with stream:
            timer = QtCore.QTimer()
            timer.timeout.connect(lambda: None)
            timer.start(10)
            QtWidgets.QApplication.instance().exec_()

if __name__ == '__main__':
    print("Real-Time Audio Visualizer Running...")
    print("Press Ctrl+C in terminal to stop.")
    visualizer = RealTimeVisualizer()
    visualizer.run()

import numpy as np
import sounddevice as sd
import tkinter as tk
from tkinter import ttk
from scipy.signal import lfilter

class SoundGeneratorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sound Generator and Resonator Filter")
        self.geometry("400x800")

        self.create_widgets()

    def create_widgets(self):
        # Wave type selection
        self.wave_type_label = ttk.Label(self, text="Wave Type:")
        self.wave_type_label.pack()
        self.wave_type_var = tk.StringVar(value="sine")
        self.wave_type_combobox = ttk.Combobox(self, textvariable=self.wave_type_var, values=["sine", "square", "sawtooth"])
        self.wave_type_combobox.pack()

        # Duration input
        self.duration_label = ttk.Label(self, text="Duration (s):")
        self.duration_label.pack()
        self.duration_entry = ttk.Entry(self)
        self.duration_entry.pack()

        # Frequency input
        self.frequency_label = ttk.Label(self, text="Frequency (Hz):")
        self.frequency_label.pack()
        self.frequency_entry = ttk.Entry(self)
        self.frequency_entry.pack()

        # Amplitude input
        self.amplitude_label = ttk.Label(self, text="Amplitude (0.0 to 1.0):")
        self.amplitude_label.pack()
        self.amplitude_entry = ttk.Entry(self)
        self.amplitude_entry.pack()

        # Cutoff frequency input
        self.cutoff_frequency_label = ttk.Label(self, text="Cutoff Frequency (Hz):")
        self.cutoff_frequency_label.pack()
        self.cutoff_frequency_entry = ttk.Entry(self)
        self.cutoff_frequency_entry.pack()

        # Resonance input
        self.resonance_label = ttk.Label(self, text="Resonance (0.0 to 1.0):")
        self.resonance_label.pack()
        self.resonance_entry = ttk.Entry(self)
        self.resonance_entry.pack()

        # Equalizer gains
        self.equalizer_label = ttk.Label(self, text="Equalizer Gains (dB):")
        self.equalizer_label.pack()

        self.gain_entries = []
        self.frequency_labels = []
        for i, freq in enumerate([60, 170, 310, 600, 1000, 3000, 6000, 12000, 14000, 16000]):
            label = ttk.Label(self, text=f"{freq} Hz:")
            label.pack()
            self.frequency_labels.append(label)
            entry = ttk.Entry(self)
            entry.pack()
            self.gain_entries.append(entry)

        # Resonator filter checkbox
        self.resonator_check = ttk.Checkbutton(self, text="Enable Resonator Filter")
        self.resonator_check.pack()

        # Equalizer checkbox
        self.equalizer_check = ttk.Checkbutton(self, text="Enable Equalizer")
        self.equalizer_check.pack()

        # Generate and play button
        self.generate_button = ttk.Button(self, text="Generate and Play", command=self.generate_and_play)
        self.generate_button.pack()

    def generate_wave(self, duration, frequency, sampling_rate, amplitude=1.0, wave_type='sine'):
        t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)
        if wave_type == 'sine':
            wave = amplitude * np.sin(2 * np.pi * frequency * t)
        elif wave_type == 'square':
            wave = amplitude * np.sign(np.sin(2 * np.pi * frequency * t))
        elif wave_type == 'sawtooth':
            wave = amplitude * (2 * (t * frequency - np.floor(t * frequency + 0.5)))
        else:
            raise ValueError("Invalid wave type. Choose from 'sine', 'square', or 'sawtooth'.")
        return wave

    def resonator_filter(self, wave, sampling_rate, cutoff_frequency, resonance):
        # Design the resonator filter coefficients
        f = cutoff_frequency / (sampling_rate / 2)  # Normalize cutoff frequency
        Q = resonance
        b, a = self.calculate_resonator_filter_coefficients(f, Q)

        # Apply the filter
        filtered_wave = lfilter(b, a, wave)

        return filtered_wave

    def calculate_resonator_filter_coefficients(self, f, Q):
        w0 = 2 * np.pi * f
        alpha = np.sin(w0) / (2 * Q)
        b0 = 1 / (1 + alpha)
        b1 = -2 * np.cos(w0)
        b2 = 1 / (1 + alpha)
        a0 = 1 + alpha
        a1 = -2 * np.cos(w0)
        a2 = 1 - alpha

        b = [b0, b1, b2]
        a = [a0, a1, a2]

        return b, a

    def apply_equalizer(self, wave, sampling_rate, gains):
        # Apply equalizer gains
        for i, gain in enumerate(gains):
            frequency = [60, 170, 310, 600, 1000, 3000, 6000, 12000, 14000, 16000][i]
            b, a = self.calculate_equalizer_coefficients(frequency, gain, sampling_rate)
            wave = lfilter(b, a, wave).astype(np.float32)  # Cast to compatible data type
        return wave

    def calculate_equalizer_coefficients(self, frequency, gain, sampling_rate):
        # Design equalizer filter coefficients
        b, a = np.zeros(3), np.zeros(3)
        f = frequency / (sampling_rate / 2)  # Normalize frequency
        A = 10 ** (gain / 40)  # Convert gain from dB to amplitude ratio
        w = 2 * np.pi * f

        denom = 4 + 2 * np.sqrt(2) * w + w ** 2
        b[0] = A * (w ** 2 / denom)
        b[1] = A * (2 * w ** 2 / denom)
        b[2] = A * (w ** 2 / denom)
        a[0] = 1
        a[1] = (2 * (w ** 2 - 4) / denom)
        a[2] = (4 - 2 * np.sqrt(2) * w + w ** 2) / denom

        return b, a

    def play_wave(self, wave, sampling_rate):
        if wave is None:
            print("Waveform is None. Unable to play.")
            return

        if not isinstance(wave, np.ndarray):
            raise TypeError("Wave must be a NumPy array.")

        if wave.dtype != np.float32:
            wave = wave.astype(np.float32)  # Cast to np.float32

        sd.play(wave, samplerate=sampling_rate)
        sd.wait()
    def generate_and_play(self):
        wave_type = self.wave_type_var.get()
        duration = float(self.duration_entry.get())
        frequency = float(self.frequency_entry.get())
        amplitude = float(self.amplitude_entry.get())
        cutoff_frequency = float(self.cutoff_frequency_entry.get())
        resonance = float(self.resonance_entry.get())
        enable_resonator = self.resonator_check.instate(['selected'])
        enable_equalizer = self.equalizer_check.instate(['selected'])

        sampling_rate = 44100  # Default sampling rate

        # Generate wave
        wave = self.generate_wave(duration, frequency, sampling_rate, amplitude, wave_type)

        # Apply equalizer if enabled
        if enable_equalizer:
            gains = [float(entry.get()) for entry in self.gain_entries]
            wave = self.apply_equalizer(wave, sampling_rate, gains)

        # Apply resonator filter if enabled
        if enable_resonator:
            wave = self.resonator_filter(wave, sampling_rate, cutoff_frequency, resonance)

        # Play wave
        self.play_wave(wave, sampling_rate)

if __name__ == "__main__":
    app = SoundGeneratorApp()
    app.mainloop()

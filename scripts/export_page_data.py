#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导出页面数据: 波形 JSON / 脊线 JSON / 音频 WAV / 谱图 PNG"""
import json
import h5py
import numpy as np
from scipy.signal import butter, filtfilt, welch, spectrogram
from scipy.io import wavfile

ROOT = '/Users/yushi/Projects/gw150914'
FS = 4096.0
T_C = 1126259462.42

f = h5py.File(f'{ROOT}/data/H1.hdf5', 'r')
strain = f['strain']['Strain'][:]
gps0 = float(f['meta']['GPSstart'][()])
f.close()
N = len(strain)
t = gps0 + np.arange(N) / FS

# 白化
off = np.abs(t - T_C) > 2.0
freqs, psd = welch(strain[off], fs=FS, nperseg=4096, noverlap=2048)
ff = np.fft.rfftfreq(N, 1 / FS)
psd_i = np.interp(ff, freqs, psd)
w = np.fft.irfft(np.fft.rfft(strain) / np.sqrt(psd_i), n=N)
w = w / np.std(w[off])
b, a = butter(4, [30.0, 300.0], btype='band', fs=FS)
wb = filtfilt(b, a, w)

# 1) 波形 JSON: ±0.35s, 降采样 x16
WIN = 0.35
m = np.abs(t - T_C) < WIN
idx = np.where(m)[0][::16]
data = {
    't_ms': [round((t[i] - T_C) * 1e3, 2) for i in idx],
    'h_raw': [float(x) for x in strain[idx]],
    'h_whit': [float(x) for x in wb[idx]],
}
json.dump(data, open(f'{ROOT}/data/waveform.json', 'w'))
print('waveform.json:', len(data['t_ms']), 'points')

# 2) 脊线 JSON
d = np.load(f'{ROOT}/data/chirp_ridge.npz')
json.dump({
    'tau': [float(x) for x in d['tau']],
    'f': [float(x) for x in d['f_ridge']],
    'C': float(d['C_fixed']),
    'Mc': float(d['Mc_fixed']),
    'p': 0.375,
}, open(f'{ROOT}/data/chirp_ridge.json', 'w'))
print('chirp_ridge.json: C=%.2f Mc=%.1f' % (d['C_fixed'], d['Mc_fixed']))

# 3) 音频: 真实应变 (白化带通) ±0.35s, 加速 8x -> 280-2000 Hz
seg = wb[m]
speed = 8
audio = seg[::speed]
audio = audio / np.abs(audio).max() * 0.85
wavfile.write(f'{ROOT}/data/chirp_real.wav', int(FS / speed), (audio * 32767).astype(np.int16))
print('chirp_real.wav:', len(audio) / (FS / speed), 's')

# 4) 音频: 理论模板 chirp (f=C tau^-3/8, 35->150 Hz) 加速 8x
tau_arr = np.arange(0.25, 0.002, -1 / FS)
Cp = 18.55
f_t = Cp * tau_arr ** (-3 / 8)
phase = np.cumsum(2 * np.pi * f_t / FS)
amp = (tau_arr / 0.25) ** (-0.25)
sig = amp * np.sin(phase)
sig = sig / np.abs(sig).max() * 0.85
wavfile.write(f'{ROOT}/data/chirp_template.wav', int(FS / speed), (sig * 32767).astype(np.int16))
print('chirp_template.wav:', len(sig) / (FS / speed), 's')

# 5) 谱图 PNG (高分辨率, 页面直接用)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fq, tt, Sxx = spectrogram(filtfilt(butter(4, [30, 300], btype='band', fs=FS)[0],
                                   butter(4, [30, 300], btype='band', fs=FS)[1], strain),
                          fs=FS, nperseg=1024, noverlap=768)
tm = (tt - (T_C - gps0)) * 1e3
mask_s = (tm > -1000) & (tm < 1000)
plt.figure(figsize=(12, 5))
plt.pcolormesh(tm[mask_s], fq, 10 * np.log10(Sxx[:, mask_s] + 1e-30), shading='auto', cmap='magma')
plt.yscale('log'); plt.ylim(30, 800)
plt.colorbar(label='dB')
plt.xlabel('ms from merger'); plt.ylabel('Hz')
plt.tight_layout()
plt.savefig(f'{ROOT}/assets/spectrogram.png', dpi=130)
plt.close()
print('assets/spectrogram.png saved')

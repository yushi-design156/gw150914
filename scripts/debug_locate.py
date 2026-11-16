#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""调试: 匹配滤波定位验证 (合成注入对照 + 真实数据全局峰值位置)"""
import h5py
import numpy as np
from scipy.signal import welch

FS = 4096.0
T_C = 1126259462.42
f = h5py.File('/Users/yushi/Projects/gw150914/data/H1.hdf5', 'r')
strain = f['strain']['Strain'][:]
gps0 = float(f['meta']['GPSstart'][()])
f.close()
N = len(strain)
t = gps0 + np.arange(N) / FS

off = np.abs(t - T_C) > 2
freqs, psd = welch(strain[off], fs=FS, nperseg=4096, noverlap=2048)
ff = np.fft.rfftfreq(N, 1 / FS)
psd_i = np.interp(ff, freqs, psd)
w = np.fft.irfft(np.fft.rfft(strain) / np.sqrt(psd_i), n=N)
w = w / np.std(w[off])

# 参照模板 (28.6, 3/8), 无 taper
j0 = int((T_C - 0.30 - gps0) * FS)
j1 = int((T_C - 0.0035 - gps0) * FS)
tau_s = T_C - t[j0:j1]
Cp = 150.9 * 28.6 ** -0.625
phi = -2 * np.pi * Cp * tau_s ** 0.625 / 0.625
amp = tau_s ** -0.25
sc = np.zeros(N); ss = np.zeros(N)
sc[j0:j1] = amp * np.cos(phi)
ss[j0:j1] = amp * np.sin(phi)

def rho_of(data):
    zc = np.fft.irfft(np.fft.rfft(sc) * np.conj(np.fft.rfft(data)), n=N)
    zs = np.fft.irfft(np.fft.rfft(ss) * np.conj(np.fft.rfft(data)), n=N)
    r = np.sqrt((zc / np.sqrt(np.sum(sc**2)))**2 + (zs / np.sqrt(np.sum(ss**2)))**2)
    sig = np.std(r[off])
    return r / (sig + 1e-12)

# 1) 合成注入: 白噪声 + 放大50倍的信号 → 峰值应出现在 t=T_C
np.random.seed(1)
noise = np.random.randn(N)
inj = noise.copy()
inj[j0:j1] += amp * np.cos(phi) * 50
r_syn = rho_of(inj)
i_syn = np.argmax(r_syn)
print(f'[合成注入] rho 峰值 {r_syn.max():.1f} @ t-gps0={t[i_syn]-gps0:.4f} (期望 {T_C-gps0:.4f})')

# 2) 真实数据: 全局峰值在哪
r_real = rho_of(w)
i_real = np.argmax(r_real)
print(f'[真实数据] rho 全局峰值 {r_real.max():.1f} @ t-gps0={t[i_real]-gps0:.4f} (T_C-gps0={T_C-gps0:.4f})')
m = np.abs(t - T_C) < 0.1
print(f'[真实数据] T_C±100ms 内 rho 峰值 {r_real[m].max():.1f}')
m2 = np.abs(t - T_C) < 0.01
print(f'[真实数据] T_C±10ms 内 rho 峰值 {r_real[m2].max():.1f}')

# 3) 白化数据的响亮点在哪
print(f'[白化数据] 全局 |w| 峰值 {np.abs(w).max():.1f} @ t-gps0={t[np.argmax(np.abs(w))]-gps0:.4f}')
print(f'[白化数据] T_C±100ms |w| 峰值 {np.abs(w[m]).max():.1f}')
print(f'[白化数据] T_C±10ms |w| 峰值 {np.abs(w[m2]).max():.1f}')

# 4) 谱图脊线: 信号频率爬升在数据里实际发生的时间
from scipy.signal import spectrogram
fq, tt, Sxx = spectrogram(w, fs=FS, nperseg=256, noverlap=224)
band = (fq > 40) & (fq < 300)
ridge = fq[band][np.argmax(Sxx[band, :], axis=0)]
tc_axis = gps0 + tt + 0.5 * 256 / FS
m_r = np.abs(tc_axis - T_C) < 0.5
print('[谱图] 峰值频率最高的时间: t-gps0 =',
      tc_axis[m_r][np.argmax(ridge[m_r])] - gps0, 'ridge f =', ridge[m_r].max())

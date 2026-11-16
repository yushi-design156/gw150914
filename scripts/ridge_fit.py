#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""谱图脊线拟合 chirp 定律 f = C * tau^(-p) (v2: 带通数据, 温和裁剪)"""
import h5py
import numpy as np
from scipy.signal import butter, filtfilt, spectrogram

FS = 4096.0
T_C = 1126259462.42
f = h5py.File('/Users/yushi/Projects/gw150914/data/H1.hdf5', 'r')
strain = f['strain']['Strain'][:]
gps0 = float(f['meta']['GPSstart'][()])
f.close()
N = len(strain)
t = gps0 + np.arange(N) / FS

b, a = butter(4, [30.0, 300.0], btype='band', fs=FS)
hbp = filtfilt(b, a, strain)

fq, tt, S = spectrogram(hbp, fs=FS, nperseg=512, noverlap=480)
band = (fq >= 30) & (fq <= 250)
ridge = fq[band][np.argmax(S[band, :], axis=0)]
ttc = gps0 + tt + 0.5 * 512 / FS
tau = T_C - ttc

m = (tau > 0.04) & (tau < 0.28) & (ridge > 30) & (ridge < 240)
lt, lf = np.log(tau[m]), np.log(ridge[m])
print(f'拟合候选点: {m.sum()}')

mask = np.ones(m.sum(), bool)
for it in range(3):
    if mask.sum() < 15:
        break
    k = np.polyfit(lt[mask], lf[mask], 1)
    res = lf - (k[0] * lt + k[1])
    sigma = np.std(res[mask])
    if sigma < 0.05:
        break
    mask[mask] = np.abs(res[mask]) < 3 * sigma

k_final = np.polyfit(lt[mask], lf[mask], 1)
p_free = -k_final[0]
C_free = np.exp(k_final[1])
Mc_free = (C_free / 150.9) ** (-8 / 5)
print(f'自由拟合 ({mask.sum()} 点): p = {p_free:.3f} (理论 0.375), C = {C_free:.2f} Hz·s^(3/8)')
print(f'  -> M_c = {Mc_free:.1f} M_sun (文献 28.6)')

C_fixed = np.exp(np.mean(lf[mask] + 0.375 * lt[mask]))
Mc_fixed = (C_fixed / 150.9) ** (-8 / 5)
print(f'固定 p=3/8: C = {C_fixed:.2f} -> M_c = {Mc_fixed:.1f} M_sun (文献 28.6)')

t35 = (35 / C_fixed) ** (-8 / 3)
t250 = (250 / C_fixed) ** (-8 / 3)
print(f'由拟合: 35→250 Hz 用时 {t35 - t250:.3f} s (文献 ~0.2 s)')

np.savez('/Users/yushi/Projects/gw150914/data/chirp_ridge.npz',
         tau=tau[m][mask], f_ridge=ridge[m][mask],
         tau_full=tau, ridge_full=ridge,
         p_free=p_free, C_free=C_free, Mc_free=Mc_free,
         C_fixed=C_fixed, Mc_fixed=Mc_fixed)
print('saved: data/chirp_ridge.npz, 拟合点数:', mask.sum())

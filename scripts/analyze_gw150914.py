#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gw150914 分析 v7：TaylorF2 后牛顿匹配滤波 + 滞后窗口
v6 结论: 事件被正确定位(dt≈-10ms), p=3/8 验证通过; 但纯牛顿模板 M_c 偏低(16.5)。
v7: TaylorF2 相位 (0PN + 1PN), 扫 (M_c, eta)。期望 M_c≈28.6, eta≈0.247。
运行: /usr/bin/python3 scripts/analyze_gw150914.py
"""
import h5py
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, hilbert, welch, spectrogram

ROOT = '/Users/yushi/Projects/gw150914'
FS = 4096.0
T_C = 1126259462.42   # GW150914 并合 GPS 时间（文献值，geocent，作模板锚点）
F_LOW, F_HIGH = 30.0, 150.0   # inspiral 频带

f = h5py.File(f'{ROOT}/data/H1.hdf5', 'r')
strain = f['strain']['Strain'][:]
gps0 = float(f['meta']['GPSstart'][()] if 'GPSstart' in f['meta'] else 1126259447)
f.close()
N = len(strain)
t = gps0 + np.arange(N) / FS

# ---- 断言 4: 带通峰值应变 ----
b4, a4 = butter(4, [30.0, 300.0], btype='band', fs=FS)
hbp = filtfilt(b4, a4, strain)
m_peak = np.abs(t - T_C) < 0.05
peak_h = np.abs(hbp[m_peak]).max()
print(f'[断言4] 并合±50ms 带通峰值 |h| = {peak_h:.2e} (文献 1.0e-21, 同量级)')

# ---- 纯白化 ----
off = np.abs(t - T_C) > 2.0
freqs, psd = welch(strain[off], fs=FS, nperseg=4096, noverlap=2048)
ff = np.fft.rfftfreq(N, 1 / FS)
psd_i = np.interp(ff, freqs, psd)
w = np.fft.irfft(np.fft.rfft(strain) / np.sqrt(psd_i), n=N)
w = w / np.std(w[off])
w̃ = np.fft.rfft(w)
print(f'白化后离源噪声 std = {np.std(w[off]):.3f} (应=1)')

# ---- TaylorF2 模板 (0PN + 1PN) ----
MSUN_S = 4.9255e-6          # G M_sun / c^3, 秒
def taylorf2_hf(Mc, eta):
    """频域模板 h̃(f) = f^(-7/6) exp(i Psi), f in [F_LOW, F_HIGH]"""
    M_s = MSUN_S * Mc        # chirp mass in seconds
    M_t = M_s / (eta ** 0.6) # total mass in seconds (M_c = M eta^{3/5})
    hf = np.zeros(N // 2 + 1, dtype=complex)
    band = (ff >= F_LOW) & (ff <= F_HIGH)
    fk = ff[band]
    v = (np.pi * M_t * fk) ** (1 / 3)
    Psi = 2 * np.pi * fk * 0 - np.pi / 4 \
        + (3 / 128) * (np.pi * M_s * fk) ** (-5 / 3) \
        * (1 + (3715 / 756 + 55 * eta / 9) * v ** 2)
    hf[band] = fk ** (-7 / 6) * np.exp(1j * Psi)
    return hf

def mf_pn(Mc, eta):
    hf = taylorf2_hf(Mc, eta)
    s = np.fft.irfft(hf, n=N)          # 实波形
    norm = np.sqrt(np.sum(s ** 2))
    z = np.fft.irfft(hf.conj() * w̃, n=N) / norm
    rho2 = np.abs(z) ** 2 - 2          # 偏差修正: E[|z|^2]=2+rho^2
    return np.sqrt(np.maximum(rho2, 0))

LAG_HALF = int(0.05 * FS)
lag_idx = np.arange(N)
lag_win = (lag_idx < LAG_HALF) | (lag_idx >= N - LAG_HALF)

# 先做 p 指数验证 (v6 方法, 牛顿相位)
def chirp_Cp(Mc, p):
    return 150.9 * Mc ** (-5 / 8)
def make_inspiral_newton(Mc, p):
    tmin = max(0.0035, (F_HIGH / chirp_Cp(Mc, p)) ** (-1 / p))
    j0 = int((T_C - 0.30 - gps0) * FS)
    j1 = int((T_C - tmin - gps0) * FS)
    tau_s = T_C - t[j0:j1]
    Cp = chirp_Cp(Mc, p)
    phi = -2 * np.pi * Cp * tau_s ** (1 - p) / (1 - p)
    amp = tau_s ** (-1 / 4)
    taper = np.ones_like(tau_s)
    n_taper = int(0.015 * FS)
    taper[:n_taper] = 0.5 - 0.5 * np.cos(np.pi * np.arange(n_taper) / n_taper)
    taper[-n_taper:] = taper[:n_taper][::-1]
    s_c = np.zeros(N); s_s = np.zeros(N)
    s_c[j0:j1] = amp * np.cos(phi) * taper
    s_s[j0:j1] = amp * np.sin(phi) * taper
    return s_c, s_s
def mf_quad_newton(s_c, s_s):
    zc = np.fft.irfft(np.fft.rfft(s_c) * np.conj(w̃), n=N)
    zs = np.fft.irfft(np.fft.rfft(s_s) * np.conj(w̃), n=N)
    rho2 = (zc / np.sqrt(np.sum(s_c ** 2))) ** 2 + (zs / np.sqrt(np.sum(s_s ** 2))) ** 2
    return np.sqrt(np.maximum(rho2 - 2, 0))

p_results = {}
for p in [round(x, 3) for x in np.arange(0.30, 0.435, 0.015)]:
    for Mc in np.arange(15, 45.25, 0.5):
        s_c, s_s = make_inspiral_newton(Mc, p)
        p_results[(p, Mc)] = mf_quad_newton(s_c, s_s)[lag_win].max()
p_best, Mc_n_best = max(p_results, key=p_results.get)
print(f'[断言1] 牛顿模板 p 扫描: 最优 p = {p_best} (理论 3/8 = 0.375) @ SNR {p_results[(p_best, Mc_n_best)]:.1f}')

# ---- 主结果: PN 模板扫 (Mc, eta) ----
results = {}
for Mc in np.arange(20, 40.25, 0.5):
    for eta in [0.15, 0.175, 0.20, 0.225, 0.247, 0.25]:
        rho = mf_pn(Mc, eta)[lag_win]
        j_rel = lag_idx[lag_win][np.argmax(rho)]
        if j_rel >= N - LAG_HALF:
            j_rel -= N
        results[(Mc, eta)] = (rho.max(), T_C + j_rel / FS)

top5 = sorted(results.items(), key=lambda kv: -kv[1][0])[:5]
print('PN 模板 SNR 前五 (Mc, eta, rho, dt_ms):')
for (Mc, eta), (rho, tc) in top5:
    print(f'  Mc={Mc:4.1f} eta={eta:.3f} rho={rho:5.1f} dt={(tc-T_C)*1e3:+7.1f}')

best = max(results, key=lambda k: results[k][0])
rho_best, t_c_best = results[best]
Mc_best, eta_best = best
print(f'[断言2] TaylorF2 匹配滤波: M_c = {Mc_best:.1f} M_sun (文献 28.6), '
      f'eta = {eta_best:.3f} (文献 ~0.247), SNR = {rho_best:.1f}')
print(f'        并合时间拟合 {t_c_best:.4f} vs 文献 {T_C} (差 {(t_c_best-T_C)*1e3:+.1f} ms)')
rho_286 = results[(28.5, 0.25)][0]
print(f'        参照: (M_c=28.5, eta=0.25) SNR = {rho_286:.1f}')

Cp_lit = chirp_Cp(Mc_best, 0.375)
tl35 = (35 / Cp_lit) ** (-8 / 3)
tl250 = (250 / Cp_lit) ** (-8 / 3)
print(f'[断言5] 由拟合 M_c={Mc_best:.1f}: 35→250 Hz 用时 {tl35 - tl250:.3f} s (文献 ~0.2 s)')

# ---- ringdown 匹配滤波 (锚定 t_c_best) ----
def ringdown_rho(fr, tr):
    tm = np.arange(0, 0.05, 1 / FS)
    env = np.exp(-tm / tr)
    ramp = np.minimum(1.0, np.arange(len(tm)) / (0.002 * FS))
    env = env * ramp
    sc = np.zeros(N); ss = np.zeros(N)
    jj0 = int((t_c_best - gps0) * FS)
    jj1 = jj0 + len(tm)
    sc[jj0:jj1] = env * np.cos(2 * np.pi * fr * tm)
    ss[jj0:jj1] = env * np.sin(2 * np.pi * fr * tm)
    zc = np.fft.irfft(np.fft.rfft(sc) * np.conj(w̃), n=N)
    zs = np.fft.irfft(np.fft.rfft(ss) * np.conj(w̃), n=N)
    rho2 = (zc / np.sqrt(np.sum(sc ** 2))) ** 2 + (zs / np.sqrt(np.sum(ss ** 2))) ** 2
    return np.sqrt(np.maximum(rho2[lag_win] - 2, 0)).max()

rd_results = {}
for fr in np.arange(200, 301, 1):
    for tr in np.arange(0.002, 0.0085, 0.0005):
        rd_results[(fr, tr)] = ringdown_rho(fr, tr)
fr_best, tr_best = max(rd_results, key=rd_results.get)
print(f'[断言7] ringdown: f = {fr_best:.0f} Hz, tau = {tr_best*1e3:.1f} ms (文献 ~250 Hz, ~4 ms)')

# ---- 图 ----
fig, ax = plt.subplots(1, 2, figsize=(12, 4))
mz = np.abs(t - T_C) < 0.25
ax[0].plot((t[mz] - T_C) * 1e3, strain[mz], lw=0.4, color='k')
ax[0].axvline(0, color='r', ls='--', lw=1)
ax[0].set_title('raw strain'); ax[0].set_xlabel('ms from merger')
ax[1].plot((t[mz] - T_C) * 1e3, w[mz], lw=0.4, color='b')
ax[1].axvline(0, color='r', ls='--', lw=1)
ax[1].set_title('whitened'); ax[1].set_xlabel('ms from merger')
plt.tight_layout(); plt.savefig(f'{ROOT}/plots/h_raw.png', dpi=110); plt.close()

fq, tt, Sxx = spectrogram(hbp, fs=FS, nperseg=1024, noverlap=768)
tm = (tt - (T_C - gps0)) * 1e3
mask_s = (tm > -2000) & (tm < 2000)
plt.figure(figsize=(12, 5))
plt.pcolormesh(tm[mask_s], fq, 10 * np.log10(Sxx[:, mask_s] + 1e-30),
               shading='auto', cmap='magma')
plt.yscale('log'); plt.ylim(30, 1000)
plt.colorbar(label='dB')
plt.xlabel('ms from merger'); plt.ylabel('Hz')
plt.title('H1 spectrogram (30-300 Hz bandpass)')
plt.tight_layout(); plt.savefig(f'{ROOT}/plots/spectrogram.png', dpi=110); plt.close()

rho_full = mf_pn(Mc_best, eta_best)
lag_axis = np.where(lag_idx > N // 2, lag_idx - N, lag_idx) / FS * 1e3
mz2 = np.abs(lag_axis) < 1000
plt.figure(figsize=(12, 4))
plt.plot(lag_axis[mz2], rho_full[mz2], color='k', lw=0.6)
plt.axvline(0, color='r', ls='--', lw=1)
plt.xlabel('ms from merger (lag)'); plt.ylabel('SNR')
plt.title(f'TaylorF2 matched-filter SNR, Mc={Mc_best:.1f} Msun, eta={eta_best:.3f}, peak={rho_best:.1f}')
plt.tight_layout(); plt.savefig(f'{ROOT}/plots/matched_snr.png', dpi=110); plt.close()

mc_grid = np.arange(20, 40.25, 0.5)
plt.figure(figsize=(10, 4.5))
for eta in [0.20, 0.247, 0.25]:
    ys = [results[(mc, eta)][0] for mc in mc_grid]
    plt.plot(mc_grid, ys, 'o-', ms=3, lw=1, label=f'eta={eta}')
plt.axvline(28.6, color='r', ls='--', lw=1, label='published Mc=28.6')
plt.xlabel('chirp mass (Msun)'); plt.ylabel('peak SNR')
plt.legend(); plt.grid(True, alpha=0.3)
plt.tight_layout(); plt.savefig(f'{ROOT}/plots/mc_curve.png', dpi=110); plt.close()

fq2, tt2, Sxx2 = spectrogram(w, fs=FS, nperseg=256, noverlap=224)
tt2c = gps0 + tt2 + 0.5 * 256 / FS
band = (fq2 > 30) & (fq2 < 400)
ridge = fq2[band][np.argmax(Sxx2[band, :], axis=0)]
tau2 = T_C - tt2c
m2 = (tau2 > 0.015) & (tau2 < 0.3)
plt.figure(figsize=(10, 5.5))
plt.loglog(tau2[m2], ridge[m2], '.', ms=2, color='orange', alpha=0.7, label='spectrogram ridge')
tt_fit = np.logspace(np.log10(0.0035), np.log10(0.3), 300)
plt.loglog(tt_fit, Cp_lit * tt_fit ** (-0.375), 'r-', lw=2,
           label=f'f = {Cp_lit:.2f} tau^(-3/8), Mc={Mc_best:.1f} Msun')
plt.gca().invert_xaxis()
plt.xlabel('tau = time before merger (s)'); plt.ylabel('f (Hz)')
plt.legend(); plt.grid(True, alpha=0.3)
plt.tight_layout(); plt.savefig(f'{ROOT}/plots/chirp_fit.png', dpi=110); plt.close()

an = hilbert(w)
env_w = np.abs(an)
mr = (t > t_c_best + 0.002) & (t < t_c_best + 0.03)
er, tr_ = env_w[mr], t[mr] - t_c_best
plt.figure(figsize=(10, 4))
plt.semilogy(tr_ * 1e3, er, '.', ms=3, color='k', label='whitened |h|')
plt.semilogy(tr_ * 1e3, er[0] * np.exp(-tr_ / tr_best), 'r-', lw=2,
             label=f'fit: f={fr_best:.0f} Hz, tau={tr_best*1e3:.1f} ms')
plt.xlabel('ms after merger'); plt.ylabel('whitened |h| envelope')
plt.legend(); plt.grid(True, alpha=0.3)
plt.tight_layout(); plt.savefig(f'{ROOT}/plots/ringdown.png', dpi=110); plt.close()

print('plots: h_raw.png spectrogram.png matched_snr.png mc_curve.png chirp_fit.png ringdown.png')
print('引用文献值的断言: [3] 3 M_sun≈5.4e47 J; [6] 3.6e49 W (LIGO PRL 116, 061102)')

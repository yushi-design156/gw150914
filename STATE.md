# 引力波账单 · 状态记录

## 已完成（2026-11-16，全部由 Hermes 执行）

1. 数据：GWOSC 官方 API 下载 H1 4kHz 并合前后 32s（H-H1_GWOSC_4KHZ_R1-1126259447-32.hdf5，1.0MB，已验证）
2. 分析管线（scripts/analyze_gw150914.py v7）：PSD 白化 → 双正交匹配滤波（TaylorF2 后牛顿模板扫 Mc/eta + 牛顿模板扫 p）→ ringdown 模板库
   - 关键坑（v3→v6 教训）：z[j] 的 j 是滞后量不是绝对时间；搜索窗必须放在 |j|<50ms（滞后空间），
     放在绝对时间 T_C 附近 = 滞后 15.4s = 匹配文件尾部伪影。合成注入对照实验定位此 bug。
   - 牛顿模板高频段伸进 merger burst 造成边界假解 → 模板在 f=150Hz（文献并合频率）处截断。
3. 脊线拟合（scripts/ridge_fit.py）：带通谱图脊线，固定 p=3/8 拟合 C
4. 页面：index.html + src/main.js + server.mjs（8788 端口，含 .wav MIME）
   - 轨道动画（牛顿轨道 + chirp 频率 + 并合涟漪）、白化波形、谱图、脊线拟合图、7 断言表、双音频
5. 验证：node --check 通过；8 个资源全部 200；真实浏览器渲染（canvas 像素统计确认三图都画了）

## 7 条断言实测（本机数据，文献对照 LIGO PRL 116, 061102）

1. f ∝ τ^(-3/8)：脊线固定斜率拟合 C = 19.62 Hz·s^(3/8)，曲线贴合实测点 → ✅
2. M_c = 28.6 M_sun：由 C 反推 26.2（偏差 8%）；匹配滤波单探测器弱约束（4.6σ vs 3.6σ，网格噪声）→ ⚠️ 同量级
3. 3 M_sun ≈ 5.4×10^47 J 辐射：需双探测器参数估计 → 📖 文献值
4. 峰值应变：带通实测 2.67×10^-21（文献 1.0×10^-21）→ ✅ 同量级
5. 35→250 Hz 用时：由拟合反推 0.213 s（文献 ~0.2 s）→ ✅
6. 峰值功率 3.6×10^49 W：需距离+方向估计 → 📖 文献值
7. ringdown：匹配滤波 288 Hz / 3.5 ms（文献 ~251 Hz / ~4 ms）→ ✅ 同量级

事件定位：匹配滤波 dt = -12.5 ms（相对 geocent；Hanford 探测器系早 ~10ms，物理正确）

## 工具白名单遵守情况
本轮只用：python3(+scipy/matplotlib/h5py, 清华镜像) + node + 浏览器。
Dify / Xinference / RAG / Ollama / qwen3.6 / OrbStack / Codex / Cursor 全程未动用。

## 下一步
1. 用户在 GitHub 建空仓 yushi-design156/gw150914（无 gh CLI 无法代建）
2. Hermes 推送 + 用户开 Pages（同第一件的路径）
3. 手机同 Wi-Fi 打开 http://IP:8788 检查排版与音频

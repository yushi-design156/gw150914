# 引力波账单（gw150914）
系列第二件 · 「相对论账单」系列
状态：数据 + 物理验证 + 页面已完成（2026-11-16，全部由 Hermes 执行），待上线 Pages。实测明细见 STATE.md。

一句话：双黑洞并合，宇宙开出 3 个太阳质量的引力波账单；把 GW150914 最后 0.2 秒做成看得见、听得见、算得清的一页。

系列：
- 第一件《星际穿越时间账单》已上线：https://yushi-design156.github.io/interstellar-time-bill/
- 本件是第二件。两件同系列，作品集从「一页」变「一个系列」。

## 本地运行
    node server.mjs        # http://localhost:8788，手机同 Wi-Fi 走局域网 IP

## 验收标准（7 条物理断言）与实测状态
1. 并合前频率按 (t_c - t)^(-3/8) 发散 → 脊线拟合 C=19.62 ✅
2. GW150914 chirp mass ≈ 28.6 M_sun → 反推 26.2（偏差 8%）⚠️ 同量级
3. 约 3 个太阳质量辐射掉（≈ 5.4×10^47 J）→ 📖 文献值
4. 峰值应变 h ≈ 10^-21 → 实测 2.67e-21 ✅ 同量级
5. 35→250 Hz 用时 ~0.2 s → 反推 0.213 s ✅
6. 峰值功率 ≈ 3.6×10^49 W → 📖 文献值
7. 残余 Kerr 黑洞 ringdown ~4 ms → 实测 288 Hz / 3.5 ms ✅ 同量级

数字出处：LIGO PRL 116, 061102 (2016)。

## 复现分析
    /usr/bin/python3 scripts/analyze_gw150914.py     # 白化 + 匹配滤波（TaylorF2），输出全部断言与图
    /usr/bin/python3 scripts/ridge_fit.py           # 谱图脊线拟合 chirp 定律
    /usr/bin/python3 scripts/export_page_data.py    # 导出页面 JSON/WAV/PNG

## 数据源（已验证可下载）
- 事件索引：https://gwosc.org/eventapi/json/GWTC-1-confident/GW150914/v3/
- H1 4kHz 并合前后 32 秒：data/H1.hdf5（已入库）

## 工具白名单（本轮只用这 3 类）
1. python3（numpy/scipy/matplotlib/h5py，走清华镜像）—— 分析管线
2. node —— 本地服务
3. 浏览器 —— 渲染验证

冻结（本轮未动用）：Dify、Xinference、RAG/BGE-M3、Ollama、qwen3.6:35b、OrbStack、Codex、Cursor。
解冻条件：出现真实需求（接单要用 RAG、要发本地模型产品）——不是「我想学」。

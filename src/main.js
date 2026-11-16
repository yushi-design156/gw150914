/* 引力波账单 · GW150914
 * 轨道动画 / 波形 / chirp 拟合 / 音频 —— 全部数据来自 data/*.json 与 data/*.wav
 */
(function () {
  'use strict';

  /* ══════════ 1. 轨道动画 (hero) ══════════ */
  const orbit = document.getElementById('orbit');
  const octx = orbit.getContext('2d');
  const Cp = 18.55;          // f_GW = Cp * tau^(-3/8)  (Hz, tau in s, M_c=28.6)
  const GM = 65 * 1.3271244e20;   // m^3/s^2, 总质量 65 M_sun
  const M1 = 36, M2 = 29;
  const R_MIN = 3.43e5;      // tau=0.004s 时的轨道半径 (m)

  let tAnim = 0;
  const LOOP = 12;           // 动画循环秒数: 10s inspiral + 2s 并合余韵
  const trails = [[], []];

  function tauOf(tA) { return 1.0 * Math.pow(0.004, tA / 10); }

  function resize() {
    const dpr = window.devicePixelRatio || 1;
    const w = orbit.clientWidth, h = orbit.clientHeight;
    orbit.width = w * dpr; orbit.height = h * dpr;
    octx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  window.addEventListener('resize', resize);

  function drawOrbit() {
    tAnim += 1 / 60;
    if (tAnim >= LOOP) { tAnim = 0; trails[0].length = 0; trails[1].length = 0; }

    const w = orbit.clientWidth, h = orbit.clientHeight;
    const cx = w / 2, cy = h / 2;
    octx.clearRect(0, 0, w, h);

    if (tAnim < 10) {
      const tau = tauOf(tAnim);
      const fOrb = (Cp / 2) * Math.pow(tau, -3 / 8);
      const r = Math.pow(GM / (4 * Math.PI * Math.PI * fOrb * fOrb), 1 / 3);
      const rPx = 62 * Math.pow(r / R_MIN, 0.9);
      // 相位积分
      if (!orbit._phi) orbit._phi = 0;
      orbit._phi += 2 * Math.PI * fOrb * (1 / 60);
      const x1 = cx + rPx * (M2 / 65) * Math.cos(orbit._phi);
      const y1 = cy + rPx * (M2 / 65) * Math.sin(orbit._phi);
      const x2 = cx - rPx * (M1 / 65) * Math.cos(orbit._phi);
      const y2 = cy - rPx * (M1 / 65) * Math.sin(orbit._phi);

      // 轨迹
      for (const [arr, p] of [[trails[0], [x1, y1]], [trails[1], [x2, y2]]]) {
        arr.push([p[0], p[1]]);
        if (arr.length > 90) arr.shift();
      }
      for (let i = 0; i < 2; i++) {
        for (let k = 1; k < trails[i].length; k++) {
          const a = k / trails[i].length;
          octx.strokeStyle = `rgba(255,180,84,${(a * 0.35).toFixed(3)})`;
          octx.lineWidth = 1;
          octx.beginPath();
          octx.moveTo(trails[i][k - 1][0], trails[i][k - 1][1]);
          octx.lineTo(trails[i][k][0], trails[i][k][1]);
          octx.stroke();
        }
      }
      // 黑洞 (发光圆盘)
      for (const [x, y, mr] of [[x1, y1, 11], [x2, y2, 10]]) {
        const g = octx.createRadialGradient(x, y, 0, x, y, mr * 3.2);
        g.addColorStop(0, 'rgba(255,255,255,0.95)');
        g.addColorStop(0.35, 'rgba(255,180,84,0.55)');
        g.addColorStop(1, 'rgba(255,107,53,0)');
        octx.fillStyle = g;
        octx.beginPath(); octx.arc(x, y, mr * 3.2, 0, 7); octx.fill();
        octx.fillStyle = '#000';
        octx.beginPath(); octx.arc(x, y, mr * 0.62, 0, 7); octx.fill();
      }
      // 文字
      octx.fillStyle = '#9aa1b0';
      octx.font = '13px -apple-system, sans-serif';
      octx.textAlign = 'center';
      octx.fillText(`并合前 τ = ${tau.toFixed(3)} s　·　f_GW = ${(Cp * Math.pow(tau, -3/8)).toFixed(0)} Hz`, cx, h - 26);
    } else {
      const tt = tAnim - 10;   // 0..2
      // 闪光 + 涟漪
      const g = octx.createRadialGradient(cx, cy, 0, cx, cy, 190);
      const a = Math.max(0, 1 - tt * 2.2);
      g.addColorStop(0, `rgba(255,240,220,${(a * 0.9).toFixed(3)})`);
      g.addColorStop(0.3, `rgba(255,180,84,${(a * 0.5).toFixed(3)})`);
      g.addColorStop(1, 'rgba(255,107,53,0)');
      octx.fillStyle = g;
      octx.beginPath(); octx.arc(cx, cy, 190, 0, 7); octx.fill();
      for (let k = 0; k < 3; k++) {
        const rr = 20 + ((tt * 120 + k * 40) % 160);
        const aa = Math.max(0, 0.5 - tt * 0.3 - k * 0.08);
        octx.strokeStyle = `rgba(255,180,84,${aa.toFixed(3)})`;
        octx.lineWidth = 2;
        octx.beginPath(); octx.arc(cx, cy, rr, 0, 7); octx.stroke();
      }
      octx.fillStyle = '#ffb454';
      octx.font = '600 22px -apple-system, sans-serif';
      octx.textAlign = 'center';
      octx.fillText('−3 M_sun → 引力波', cx, cy - 34);
      octx.fillStyle = '#9aa1b0';
      octx.font = '13px -apple-system, sans-serif';
      octx.fillText('峰值功率 ≈ 3.6×10^49 W · 超过可观测宇宙全部恒星的光', cx, cy + 54);
    }
    requestAnimationFrame(drawOrbit);
  }

  /* ══════════ 2. 波形 ══════════ */
  const wf = document.getElementById('waveform');
  const wctx = wf.getContext('2d');

  function drawWaveform(d) {
    const dpr = window.devicePixelRatio || 1;
    const w = wf.clientWidth, h = wf.clientHeight;
    wf.width = w * dpr; wf.height = h * dpr;
    wctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    wctx.clearRect(0, 0, w, h);

    const padL = 46, padR = 16, padT = 18, padB = 30;
    const x0 = padL, x1 = w - padR, y0 = padT, y1 = h - padB;
    const tms = d.t_ms, hs = d.h_whit;
    const tMin = tms[0], tMax = tms[tms.length - 1];
    let vMax = 0; for (const v of hs) vMax = Math.max(vMax, Math.abs(v));
    vMax *= 1.15;

    // 网格 + 轴
    wctx.strokeStyle = '#262b38'; wctx.lineWidth = 1;
    wctx.fillStyle = '#9aa1b0'; wctx.font = '11px -apple-system, sans-serif';
    for (let i = 0; i <= 4; i++) {
      const y = y0 + (y1 - y0) * i / 4;
      wctx.beginPath(); wctx.moveTo(x0, y); wctx.lineTo(x1, y); wctx.stroke();
      wctx.textAlign = 'right';
      wctx.fillText(((vMax * (1 - i / 2)).toFixed(1)), x0 - 6, y + 4);
    }
    for (let i = 0; i <= 5; i++) {
      const x = x0 + (x1 - x0) * i / 5;
      wctx.beginPath(); wctx.moveTo(x, y0); wctx.lineTo(x, y1); wctx.stroke();
      wctx.textAlign = 'center';
      wctx.fillText((tMin + (tMax - tMin) * i / 5).toFixed(0) + 'ms', x, y1 + 16);
    }
    // 曲线
    wctx.strokeStyle = '#ffb454'; wctx.lineWidth = 1.4;
    wctx.beginPath();
    for (let i = 0; i < tms.length; i++) {
      const x = x0 + (tms[i] - tMin) / (tMax - tMin) * (x1 - x0);
      const y = y0 + (1 - hs[i] / vMax) / 2 * (y1 - y0);
      i === 0 ? wctx.moveTo(x, y) : wctx.lineTo(x, y);
    }
    wctx.stroke();
    // 并合红线
    const xm = x0 + (0 - tMin) / (tMax - tMin) * (x1 - x0);
    wctx.strokeStyle = '#ff6b35'; wctx.lineWidth = 1.2;
    wctx.setLineDash([4, 4]);
    wctx.beginPath(); wctx.moveTo(xm, y0); wctx.lineTo(xm, y1); wctx.stroke();
    wctx.setLineDash([]);
    wctx.fillStyle = '#ff6b35'; wctx.textAlign = 'center';
    wctx.fillText('并合', xm, y0 - 5);
  }

  /* ══════════ 3. chirp 拟合 ══════════ */
  const cf = document.getElementById('chirpfit');
  const cctx = cf.getContext('2d');

  function drawChirp(d) {
    const dpr = window.devicePixelRatio || 1;
    const w = cf.clientWidth, h = cf.clientHeight;
    cf.width = w * dpr; cf.height = h * dpr;
    cctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    cctx.clearRect(0, 0, w, h);

    const padL = 52, padR = 18, padT = 18, padB = 40;
    const x0 = padL, x1 = w - padR, y0 = padT, y1 = h - padB;
    const tLo = 0.3, tHi = 0.02, fLo = 30, fHi = 260;
    const lx = t => x0 + (Math.log(t) - Math.log(tHi)) / (Math.log(tLo) - Math.log(tHi)) * (x1 - x0);
    const ly = f => y0 + (Math.log(fHi) - Math.log(f)) / (Math.log(fHi) - Math.log(fLo)) * (y1 - y0);

    cctx.strokeStyle = '#262b38'; cctx.lineWidth = 1;
    cctx.fillStyle = '#9aa1b0'; cctx.font = '11px -apple-system, sans-serif';
    for (const f of [30, 50, 100, 250]) {
      const y = ly(f);
      cctx.beginPath(); cctx.moveTo(x0, y); cctx.lineTo(x1, y); cctx.stroke();
      cctx.textAlign = 'right'; cctx.fillText(f + '', x0 - 6, y + 4);
    }
    for (const t of [0.25, 0.1, 0.05, 0.02]) {
      const x = lx(t);
      cctx.beginPath(); cctx.moveTo(x, y0); cctx.lineTo(x, y1); cctx.stroke();
      cctx.textAlign = 'center'; cctx.fillText(t.toFixed(2) + 's', x, y1 + 16);
    }
    cctx.fillStyle = '#9aa1b0'; cctx.textAlign = 'center';
    cctx.save(); cctx.translate(14, (y0 + y1) / 2); cctx.rotate(-Math.PI / 2);
    cctx.fillText('f (Hz)', 0, 0); cctx.restore();
    cctx.fillText('τ = 并合前时间 (s)', (x0 + x1) / 2, h - 8);

    // 脊线点
    cctx.fillStyle = 'rgba(255,150,60,0.85)';
    for (let i = 0; i < d.tau.length; i++) {
      if (d.tau[i] > tLo || d.tau[i] < tHi) continue;
      cctx.beginPath();
      cctx.arc(lx(d.tau[i]), ly(d.f[i]), 2.6, 0, 7);
      cctx.fill();
    }
    // 拟合曲线 f = C tau^(-3/8)
    cctx.strokeStyle = '#ff4d4d'; cctx.lineWidth = 2;
    cctx.beginPath();
    for (let i = 0; i <= 400; i++) {
      const t = tHi * Math.pow(tLo / tHi, i / 400);
      const f = d.C * Math.pow(t, -d.p);
      const x = lx(t), y = ly(f);
      i === 0 ? cctx.moveTo(x, y) : cctx.lineTo(x, y);
    }
    cctx.stroke();
    // 标注
    cctx.fillStyle = '#ff4d4d'; cctx.textAlign = 'left'; cctx.font = '12px -apple-system, sans-serif';
    cctx.fillText(`f = ${d.C.toFixed(2)} · τ^(−3/8)`, lx(0.23) + 6, ly(d.C * Math.pow(0.23, -d.p)) - 6);
    document.getElementById('chirp-note').textContent =
      `拟合 C = ${d.C.toFixed(2)} Hz·s^(3/8) → 反推 chirp 质量 M_c = ${d.Mc.toFixed(1)} M_sun（文献 28.6 M_sun，偏差 ${Math.abs(28.6 - d.Mc).toFixed(1)} M_sun）。` +
      `由拟合反推 35→250 Hz 用时 0.213 s（文献 ~0.2 s）。`;
  }

  /* ══════════ 4. 音频 ══════════ */
  function bindAudio(btnId, src) {
    const btn = document.getElementById(btnId);
    const audio = new Audio(src);
    audio.addEventListener('ended', () => btn.classList.remove('playing'));
    btn.addEventListener('click', () => {
      if (btn.classList.contains('playing')) {
        audio.pause(); audio.currentTime = 0;
        btn.classList.remove('playing');
      } else {
        audio.currentTime = 0; audio.play();
        btn.classList.add('playing');
      }
    });
  }
  bindAudio('play-real', 'data/chirp_real.wav');
  bindAudio('play-tpl', 'data/chirp_template.wav');

  /* ══════════ 启动 ══════════ */
  resize();
  drawOrbit();
  fetch('data/waveform.json').then(r => r.json()).then(drawWaveform);
  fetch('data/chirp_ridge.json').then(r => r.json()).then(drawChirp);
  window.addEventListener('resize', () => {
    fetch('data/waveform.json').then(r => r.json()).then(drawWaveform);
    fetch('data/chirp_ridge.json').then(r => r.json()).then(drawChirp);
  });
})();

import React, { useRef, useEffect, useCallback } from 'react';

const PAD        = { top: 16, right: 64, bottom: 32, left: 8 };
const BULL       = '#26a69a';
const BEAR       = '#ef5350';
const EMA50_CLR  = '#6366f1';
const EMA200_CLR = '#ef4444';
const BB_CLR     = 'rgba(99,102,241,0.15)';
const BB_LINE    = 'rgba(99,102,241,0.55)';
const BB_MID_CLR = 'rgba(99,102,241,0.35)';
const GRID_CLR   = 'rgba(0,0,0,0.05)';
const TEXT_CLR   = '#9ca3af';
const TIP_BG     = '#1e293b';
const TIP_TEXT   = '#f1f5f9';
const TP_FILL    = 'rgba(38,166,154,0.10)';
const SL_FILL    = 'rgba(239,83,80,0.10)';
const TP_LINE    = 'rgba(38,166,154,0.75)';
const SL_LINE    = 'rgba(239,83,80,0.75)';

function niceStep(range, ticks = 6) {
  const raw  = range / ticks;
  const mag  = Math.pow(10, Math.floor(Math.log10(raw)));
  const norm = raw / mag;
  return (norm < 1.5 ? 1 : norm < 3 ? 2 : norm < 7 ? 5 : 10) * mag;
}

function drawTriangle(ctx, x, y, size, up, fillColor) {
  ctx.beginPath();
  if (up) {
    ctx.moveTo(x, y - size);
    ctx.lineTo(x + size * 0.85, y + size * 0.55);
    ctx.lineTo(x - size * 0.85, y + size * 0.55);
  } else {
    ctx.moveTo(x, y + size);
    ctx.lineTo(x + size * 0.85, y - size * 0.55);
    ctx.lineTo(x - size * 0.85, y - size * 0.55);
  }
  ctx.closePath();
  ctx.fillStyle = fillColor;
  ctx.fill();
  ctx.strokeStyle = '#fff';
  ctx.lineWidth = 1;
  ctx.stroke();
}

function matchBar(pred, labels) {
  const ts  = pred.price_timestamp || pred.timestamp;
  // DB stores UTC without Z — normalize before parsing
  const normalized = ts.endsWith('Z') || ts.includes('+') ? ts : ts + 'Z';
  const d   = new Date(normalized);
  // labels are UTC+7 (shiftLabels applied in parent)
  const local = new Date(d.getTime() + 7 * 60 * 60 * 1000);
  const mm  = String(local.getUTCMonth() + 1).padStart(2, '0');
  const dd  = String(local.getUTCDate()).padStart(2, '0');
  const hh  = String(local.getUTCHours()).padStart(2, '0');
  return labels.findIndex(l => l === `${mm}/${dd} ${hh}:00`);
}

export default function CandleChart({
  labels = [], open = [], high = [], low = [], close = [],
  ema50 = [], ema200 = [],
  bbUpper = [], bbMid = [], bbLower = [],
  predictions = [],
  height = 288,
}) {
  const canvasRef = useRef(null);
  const hoverRef  = useRef(null);
  const rafRef    = useRef(null);
  const n = labels.length;

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || n === 0) return;
    const dpr = window.devicePixelRatio || 1;
    const W   = canvas.clientWidth;
    const H   = canvas.clientHeight;
    if (canvas.width !== W * dpr || canvas.height !== H * dpr) {
      canvas.width = W * dpr; canvas.height = H * dpr;
    }
    const ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);

    const chartW = W - PAD.left - PAD.right;
    const chartH = H - PAD.top  - PAD.bottom;

    const validLows  = low.filter(v => v != null && isFinite(v));
    const validHighs = high.filter(v => v != null && isFinite(v));
    if (!validLows.length) return;
    const pad  = (Math.max(...validHighs) - Math.min(...validLows)) * 0.06;
    const yMin = Math.min(...validLows)  - pad;
    const yMax = Math.max(...validHighs) + pad;
    const yRange = yMax - yMin || 1;
    const toY = v => PAD.top + chartH * (1 - (v - yMin) / yRange);

    const slotW   = chartW / n;
    const candleW = Math.max(1, Math.min(slotW * 0.7, 14));
    const toX     = i => PAD.left + (i + 0.5) * slotW;

    /* grid + y-axis */
    const step = niceStep(yRange, 6);
    ctx.font = '10px sans-serif'; ctx.textAlign = 'left';
    for (let v = Math.ceil(yMin / step) * step; v <= yMax; v += step) {
      const y = toY(v);
      ctx.strokeStyle = GRID_CLR; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(PAD.left, y); ctx.lineTo(PAD.left + chartW, y); ctx.stroke();
      ctx.fillStyle = TEXT_CLR;
      ctx.fillText(v.toLocaleString('en-US', { maximumFractionDigits: 0 }), PAD.left + chartW + 4, y + 3.5);
    }

    /* x labels */
    ctx.textAlign = 'center';
    const lStep = Math.max(1, Math.ceil(n / 8));
    for (let i = 0; i < n; i += lStep) {
      ctx.fillStyle = TEXT_CLR;
      ctx.fillText(labels[i], toX(i), H - 6);
    }

    /* clip */
    ctx.save();
    ctx.beginPath(); ctx.rect(PAD.left, PAD.top, chartW, chartH); ctx.clip();

    /* prediction zones */
    const predBars = predictions
      .map(p => ({ ...p, idx: matchBar(p, labels) }))
      .filter(p => p.idx >= 0 && p.action !== 'HOLD');

    predBars.forEach(({ idx, action, entry_price, tp_price, sl_price }) => {
      const x1 = toX(idx);
      const x2 = PAD.left + chartW;
      const yE = toY(entry_price), yT = toY(tp_price), yS = toY(sl_price);
      // TP zone
      ctx.fillStyle = TP_FILL;
      ctx.fillRect(x1, Math.min(yT, yE), x2 - x1, Math.abs(yT - yE));
      // SL zone
      ctx.fillStyle = SL_FILL;
      ctx.fillRect(x1, Math.min(yS, yE), x2 - x1, Math.abs(yS - yE));
      // lines
      [[yT, TP_LINE, `TP ${tp_price.toFixed(0)}`], [yS, SL_LINE, `SL ${sl_price.toFixed(0)}`]].forEach(([y, clr, lbl]) => {
        ctx.setLineDash([4, 3]); ctx.strokeStyle = clr; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(x1, y); ctx.lineTo(x2, y); ctx.stroke();
        ctx.setLineDash([]);
        ctx.font = 'bold 9px sans-serif'; ctx.textAlign = 'right'; ctx.fillStyle = clr;
        ctx.fillText(lbl, x2 - 2, y + (y < yE ? -2 : 9));
      });
      ctx.strokeStyle = 'rgba(148,163,184,0.45)'; ctx.lineWidth = 1; ctx.setLineDash([2, 3]);
      ctx.beginPath(); ctx.moveTo(x1, yE); ctx.lineTo(x2, yE); ctx.stroke();
      ctx.setLineDash([]);
    });

    /* Bollinger */
    if (bbUpper.some(Boolean) && bbLower.some(Boolean)) {
      ctx.beginPath();
      let s = false;
      for (let i = 0; i < n; i++) {
        if (!bbUpper[i]) continue;
        if (!s) { ctx.moveTo(toX(i), toY(bbUpper[i])); s = true; }
        else ctx.lineTo(toX(i), toY(bbUpper[i]));
      }
      for (let i = n - 1; i >= 0; i--) {
        if (!bbLower[i]) continue;
        ctx.lineTo(toX(i), toY(bbLower[i]));
      }
      ctx.closePath(); ctx.fillStyle = BB_CLR; ctx.fill();
      const drawBB = (arr, clr, dash) => {
        ctx.beginPath(); ctx.strokeStyle = clr; ctx.lineWidth = 1; ctx.setLineDash(dash); let s2 = false;
        for (let i = 0; i < n; i++) {
          if (!arr[i]) { s2 = false; continue; }
          if (!s2) { ctx.moveTo(toX(i), toY(arr[i])); s2 = true; } else ctx.lineTo(toX(i), toY(arr[i]));
        }
        ctx.stroke(); ctx.setLineDash([]);
      };
      drawBB(bbUpper, BB_LINE, [4, 3]); drawBB(bbLower, BB_LINE, [4, 3]); drawBB(bbMid, BB_MID_CLR, [2, 3]);
    }

    /* EMA */
    const drawEma = (arr, clr, dash = []) => {
      ctx.beginPath(); ctx.strokeStyle = clr; ctx.lineWidth = 1.5; ctx.setLineDash(dash); let s = false;
      for (let i = 0; i < n; i++) {
        if (!arr[i]) { s = false; continue; }
        if (!s) { ctx.moveTo(toX(i), toY(arr[i])); s = true; } else ctx.lineTo(toX(i), toY(arr[i]));
      }
      ctx.stroke(); ctx.setLineDash([]);
    };
    if (ema200.some(Boolean)) drawEma(ema200, EMA200_CLR, [5, 4]);
    if (ema50.some(Boolean))  drawEma(ema50,  EMA50_CLR);

    /* candles */
    for (let i = 0; i < n; i++) {
      if (close[i] == null) continue;
      const bull    = close[i] >= open[i];
      const clr     = bull ? BULL : BEAR;
      const x       = toX(i);
      const bTop    = Math.min(toY(open[i]), toY(close[i]));
      const bH      = Math.max(1, Math.abs(toY(open[i]) - toY(close[i])));
      ctx.strokeStyle = clr; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x, toY(high[i])); ctx.lineTo(x, toY(low[i])); ctx.stroke();
      ctx.fillStyle = clr;
      ctx.fillRect(x - candleW / 2, bTop, candleW, bH);
      if (bull) { ctx.strokeStyle = clr; ctx.strokeRect(x - candleW / 2, bTop, candleW, bH); }
    }

    /* prediction triangles */
    predBars.forEach(({ idx, action, entry_price }) => {
      const x     = toX(idx);
      const isBuy = action === 'BUY';
      const yRef  = isBuy
        ? toY(low[idx]  ?? entry_price) + 10
        : toY(high[idx] ?? entry_price) - 10;
      drawTriangle(ctx, x, yRef, 6, isBuy, isBuy ? BULL : BEAR);
    });

    ctx.restore();

    /* crosshair + tooltip */
    const hi = hoverRef.current;
    if (hi !== null && hi >= 0 && hi < n && close[hi] != null) {
      const x = toX(hi);
      ctx.strokeStyle = 'rgba(100,116,139,0.5)'; ctx.lineWidth = 1; ctx.setLineDash([4, 3]);
      ctx.beginPath(); ctx.moveTo(x, PAD.top); ctx.lineTo(x, PAD.top + chartH); ctx.stroke();
      ctx.setLineDash([]);

      const bull  = close[hi] >= open[hi];
      const lines = [
        labels[hi],
        `O: ${open[hi]?.toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
        `H: ${high[hi]?.toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
        `L: ${low[hi]?.toLocaleString('en-US',  { minimumFractionDigits: 2 })}`,
        `C: ${close[hi]?.toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
      ];
      if (ema50[hi])   lines.push(`EMA50: ${ema50[hi].toFixed(2)}`);
      if (ema200[hi])  lines.push(`EMA200: ${ema200[hi].toFixed(2)}`);
      if (bbUpper[hi]) lines.push(`BB: ${bbLower[hi]?.toFixed(2)} – ${bbUpper[hi]?.toFixed(2)}`);

      const ph = predBars.find(p => p.idx === hi);
      if (ph) {
        lines.push('──────────');
        lines.push(`${ph.action}  conf ${(ph.confidence * 100).toFixed(0)}%`);
        lines.push(`TP: ${ph.tp_price.toFixed(2)}`);
        lines.push(`SL: ${ph.sl_price.toFixed(2)}`);
      }

      const bw = 145, bh = lines.length * 15 + 14;
      let bx = x + 10;
      if (bx + bw > W - PAD.right) bx = x - bw - 10;
      const by = PAD.top + 8;

      ctx.fillStyle = TIP_BG;
      ctx.beginPath(); ctx.roundRect(bx, by, bw, bh, 6); ctx.fill();
      ctx.textAlign = 'left';
      lines.forEach((ln, k) => {
        let clr = TIP_TEXT;
        if (k === 0)              clr = bull ? BULL : BEAR;
        else if (k === 4)         clr = bull ? BULL : BEAR;
        else if (ln.startsWith('──')) clr = 'rgba(148,163,184,0.4)';
        else if (ln.startsWith('BUY'))  clr = BULL;
        else if (ln.startsWith('SELL')) clr = BEAR;
        else if (ln.startsWith('TP'))   clr = TP_LINE;
        else if (ln.startsWith('SL'))   clr = SL_LINE;
        ctx.font = k === 0 ? 'bold 10px sans-serif' : '10px sans-serif';
        ctx.fillStyle = clr;
        ctx.fillText(ln, bx + 8, by + 14 + k * 15);
      });
    }
  }, [n, labels, open, high, low, close, ema50, ema200, bbUpper, bbMid, bbLower, predictions]);

  useEffect(() => {
    const canvas = canvasRef.current; if (!canvas) return;
    const ro = new ResizeObserver(() => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(draw);
    });
    ro.observe(canvas); return () => ro.disconnect();
  }, [draw]);

  useEffect(() => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    rafRef.current = requestAnimationFrame(draw);
  }, [draw]);

  const handleMouseMove = useCallback((e) => {
    const canvas = canvasRef.current; if (!canvas || !n) return;
    const rect  = canvas.getBoundingClientRect();
    const slotW = (canvas.clientWidth - PAD.left - PAD.right) / n;
    const idx   = Math.floor((e.clientX - rect.left - PAD.left) / slotW);
    hoverRef.current = (idx >= 0 && idx < n) ? idx : null;
    draw();
  }, [n, draw]);

  const handleMouseLeave = useCallback(() => { hoverRef.current = null; draw(); }, [draw]);

  return (
    <canvas ref={canvasRef}
      style={{ width: '100%', height: `${height}px`, display: 'block', cursor: 'crosshair' }}
      onMouseMove={handleMouseMove} onMouseLeave={handleMouseLeave} />
  );
}

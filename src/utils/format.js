export const pct = (v) => `${Number(v).toFixed(1)}%`;
export const ms = (v) => `${Math.round(v).toLocaleString()} ms`;
export const fmtTime = (t) => new Date(t).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
export const fmtClock = (t) => new Date(t).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
export const dur = (min) => (min >= 60 ? `${Math.floor(min / 60)}h ${min % 60}m` : `${min}m`);
export const avg = (arr, k) => (arr.length ? arr.reduce((a, x) => a + x[k], 0) / arr.length : 0);

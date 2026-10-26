/* Kalshi pull for the /odds/ page. Run in the browser ON A kalshi.com PAGE
   (the public API at api.elections.kalshi.com answers fetches from kalshi.com,
   but not from the API's own JSON pages or from the cloud shell).
   Paste the whole file into the javascript tool. It returns a short status line
   and replaces the page's content with the dump as plain text, so the page-text
   tool returns the whole dump in one read (about 25,000 characters). Save that
   text exactly as the dump file for tools/kalshi.py. Fallback: window.__kalshiChunk(i)
   returns 900-character pieces to join in order. Read only; it never trades or signs in. */
(async () => {
  const API = 'https://api.elections.kalshi.com/trade-api/v2';
  const MARKETS = [
    ['CONTROLS', 'CONTROLS-2026-D'], ['CONTROLS', 'CONTROLS-2026-R'],
    ['SENATETX', 'SENATETX-26-D'], ['SENATETX', 'SENATETX-26-R'],
    ['SENATEOHS', 'SENATEOHS-26-D'], ['SENATEOHS', 'SENATEOHS-26-R'],
    ['SENATEME', 'SENATEME-26-D'], ['SENATEME', 'SENATEME-26-R'],
    ['SENATEMI', 'SENATEMI-26-D'], ['SENATEMI', 'SENATEMI-26-R'],
    ['SENATEIA', 'SENATEIA-26-D'], ['SENATEIA', 'SENATEIA-26-R'],
    ['SENATEAK', 'SENATEAK-26-D'], ['SENATEAK', 'SENATEAK-26-R'],
    ['SENATENE', 'SENATENE-26-DOSB'], ['SENATENE', 'SENATENE-26-R'],
    ['SENATENC', 'SENATENC-26-D'], ['SENATENC', 'SENATENC-26-R'],
    ['SENATEGA', 'SENATEGA-26-D'], ['SENATEGA', 'SENATEGA-26-R'],
    ['SENATENH', 'SENATENH-26-D'], ['SENATENH', 'SENATENH-26-R'],
    ['SENATEMN', 'SENATEMN-26-D'], ['SENATEMN', 'SENATEMN-26-R'],
  ];
  const BIG = 25000;           // contracts in one second on one side
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const errs = [];
  async function get(url) {
    for (let i = 0; i < 6; i++) {
      try { const r = await fetch(url); if (r.ok) return await r.json(); errs.push(r.status); } catch (e) { errs.push(String(e.message || e)); }
      await sleep(1500 * (i + 1));
    }
    throw new Error('failed ' + url);
  }
  const ctDate = iso => new Date(iso).toLocaleDateString('en-CA', { timeZone: 'America/Chicago' });
  const etDay = ts => new Date((ts - 1) * 1000).toLocaleDateString('en-CA', { timeZone: 'America/New_York' });
  const now = Math.floor(Date.now() / 1000);
  // scan window: from 00:00 Central two days ago, so a missed day is covered
  const startCT = new Date(new Date().toLocaleString('en-US', { timeZone: 'America/Chicago' }));
  startCT.setHours(0, 0, 0, 0); startCT.setDate(startCT.getDate() - 2);
  const offset = new Date().getTime() - new Date(new Date().toLocaleString('en-US', { timeZone: 'America/Chicago' })).getTime();
  const minTs = Math.floor((startCT.getTime() + offset) / 1000);

  const dump = { pulled: new Date().toISOString().slice(0, 19) + 'Z', scan_from: new Date(minTs * 1000).toISOString().slice(0, 19) + 'Z', live: {}, candles: {}, big: [], taker: {}, book: {} };
  for (const [series, t] of MARKETS) {
    try {
      const m = (await get(`${API}/markets/${t}`)).market;
      const last = parseFloat(m.last_price_dollars);
      dump.live[t] = { last, bid: parseFloat(m.yes_bid_dollars), ask: parseFloat(m.yes_ask_dollars),
        vol24: Math.round(parseFloat(m.volume_24h_fp || 0)), oi: Math.round(parseFloat(m.open_interest_fp || 0)) };
      await sleep(120);
      const c = await get(`${API}/series/${series}/markets/${t}/candlesticks?start_ts=${now - 6 * 86400}&end_ts=${now}&period_interval=1440`);
      dump.candles[t] = (c.candlesticks || []).filter(x => x.price && x.price.close_dollars != null)
        .map(x => [etDay(x.end_period_ts), parseFloat(x.price.close_dollars), Math.round(parseFloat(x.volume_fp || 0))]);
      await sleep(120);
      const ob = (await get(`${API}/markets/${t}/orderbook?depth=40`)).orderbook_fp || {};
      let pro = 0, con = 0;
      for (const [p, q] of ob.yes_dollars || []) if (parseFloat(p) >= last - 0.0301) pro += parseFloat(q);
      for (const [p, q] of ob.no_dollars || []) if (1 - parseFloat(p) <= last + 0.0301) con += parseFloat(q);
      dump.book[t] = { for: Math.round(pro), against: Math.round(con) };
      await sleep(120);
      let cur = '', pages = 0; const cl = {}, day = {};
      do {
        const j = await get(`${API}/markets/trades?ticker=${t}&min_ts=${minTs}&max_ts=${now}&limit=1000` + (cur ? `&cursor=${cur}` : ''));
        pages++;
        for (const x of j.trades || []) {
          const n = parseFloat(x.count_fp); const side = x.taker_side;
          const k = x.created_time.slice(0, 19) + '|' + side;
          const px = side === 'yes' ? parseFloat(x.yes_price_dollars) : parseFloat(x.no_price_dollars);
          const o = cl[k] || (cl[k] = { n: 0, usd: 0, p: parseFloat(x.yes_price_dollars) });
          o.n += n; o.usd += n * px;
          const d = ctDate(x.created_time); const dd = day[d] || (day[d] = [0, 0]); dd[side === 'yes' ? 0 : 1] += n;
        }
        cur = j.cursor; await sleep(200);
      } while (cur && pages < 40);
      for (const [k, o] of Object.entries(cl)) if (o.n >= BIG) {
        const [ts, side] = k.split('|');
        dump.big.push({ t: ts + 'Z', ticker: t, side, contracts: Math.round(o.n), usd: Math.round(o.usd), price: o.p });
      }
      dump.taker[t] = Object.fromEntries(Object.entries(day).map(([d, v]) => [d, v.map(Math.round)]));
    } catch (e) { errs.push(t + ': ' + (e.message || e)); }
  }
  // hourly closes for the last 72 hours, so moves between morning pulls are captured hour by hour
  const RACE = { 'CONTROLS-2026': 'control', 'SENATETX-26': 'TX', 'SENATEOHS-26': 'OH', 'SENATEME-26': 'ME', 'SENATEMI-26': 'MI',
    'SENATEIA-26': 'IA', 'SENATEAK-26': 'AK', 'SENATENE-26': 'NE', 'SENATENC-26': 'NC', 'SENATEGA-26': 'GA', 'SENATENH-26': 'NH', 'SENATEMN-26': 'MN' };
  const H0 = Math.floor((now - 72 * 3600) / 3600) * 3600 + 3600, HN = Math.floor((now - H0) / 3600) + 1;
  dump.hourly = { start: H0, step: 3600, price: {}, vol: {} };
  for (const [series, t] of MARKETS) {
    try {
      const j = await get(`${API}/series/${series}/markets/${t}/candlesticks?start_ts=${H0 - 3600}&end_ts=${now}&period_interval=60`);
      const c = Array(HN).fill(null), v = Array(HN).fill(0);
      for (const x of j.candlesticks || []) {
        const i = Math.round((x.end_period_ts - H0) / 3600); if (i < 0 || i >= HN) continue;
        const p = x.price && x.price.close_dollars; if (p != null) c[i] = Math.round(parseFloat(p) * 1000);
        v[i] = parseFloat(x.volume_fp || 0);
      }
      dump.hourly.price[t] = c;
      const race = RACE[t.replace(/-(D|R|DOSB)$/, '')];
      const acc = dump.hourly.vol[race] || (dump.hourly.vol[race] = Array(HN).fill(0));
      v.forEach((x, i) => { acc[i] += x; });
      await sleep(120);
    } catch (e) { errs.push(t + ' hourly: ' + (e.message || e)); }
  }
  for (const k of Object.keys(dump.hourly.vol)) dump.hourly.vol[k] = dump.hourly.vol[k].map(x => Math.round(x / 1000));
  const s = JSON.stringify(dump);
  window.__kalshiDump = s;
  window.__kalshiChunk = i => s.slice(i * 900, (i + 1) * 900);
  // also put the dump on the page itself so it can be read in one go with the page-text tool
  document.body.innerHTML = '<main><pre id="kalshi-dump"></pre></main>';
  document.getElementById('kalshi-dump').textContent = s;
  return `kalshi dump ready: ${s.length} chars (read it with the page-text tool, or in ${Math.ceil(s.length / 900)} chunks), ${Object.keys(dump.live).length} markets, ${dump.big.length} big orders, errors: ${errs.length ? errs.slice(0, 6).join(' / ') : 'none'}`;
})()

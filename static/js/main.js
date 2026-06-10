// ── Mobile nav ───────────────────────────────────────────────
document.querySelector('.nav-toggle')?.addEventListener('click', () => {
  document.querySelector('.nav-links')?.classList.toggle('open');
});

// ── Animated counters ────────────────────────────────────────
const easeOut = t => 1 - Math.pow(1 - t, 3);
function animateCounter(el) {
  const target = +el.dataset.count || 0;
  const dur = 1400; const start = performance.now();
  function frame(t) {
    const p = Math.min((t - start) / dur, 1);
    el.textContent = Math.floor(easeOut(p) * target).toLocaleString();
    if (p < 1) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}
const io = new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting) { animateCounter(e.target); io.unobserve(e.target); } });
}, { threshold: 0.4 });
document.querySelectorAll('[data-count]').forEach(el => io.observe(el));

// ── Tabs ─────────────────────────────────────────────────────
document.querySelectorAll('.tab-bar').forEach(bar => {
  const tabs = bar.querySelectorAll('.tab');
  const panels = bar.parentElement.querySelectorAll('.tab-panel');
  tabs.forEach(t => t.addEventListener('click', () => {
    tabs.forEach(x => x.classList.remove('active'));
    panels.forEach(p => p.classList.remove('active'));
    t.classList.add('active');
    bar.parentElement.querySelector(`[data-panel="${t.dataset.tab}"]`)?.classList.add('active');
  }));
});

// ── Player live search ───────────────────────────────────────
const search = document.getElementById('player-search');
const results = document.getElementById('search-results');
let tHandle;
search?.addEventListener('input', e => {
  clearTimeout(tHandle);
  const q = e.target.value.trim();
  if (!q) { results.innerHTML = ''; return; }
  tHandle = setTimeout(async () => {
    const r = await fetch(`/api/players/search?q=${encodeURIComponent(q)}`);
    const d = await r.json();
    let html = '';
    d.batters.forEach(b => html += `<div class="res"><b>${b.batsman}</b> · ${b.team}<br><small>${b.runs} runs · SR ${b.strike_rate?.toFixed(1)} · Avg ${b.average?.toFixed(2)}</small></div>`);
    d.bowlers.forEach(b => html += `<div class="res"><b>${b.bowler}</b> · ${b.team}<br><small>${b.wickets} wkts · Eco ${b.economy?.toFixed(2)} · Avg ${b.avg?.toFixed(2)}</small></div>`);
    results.innerHTML = html || '<div class="res muted">No players found.</div>';
  }, 200);
});

// ── Matches filter ───────────────────────────────────────────
function filterMatches() {
  const q = (document.getElementById('m-search')?.value || '').toLowerCase();
  const v = document.getElementById('m-venue')?.value || '';
  const t = document.getElementById('m-team')?.value || '';
  document.querySelectorAll('#matches-table tbody tr').forEach(row => {
    const txt = row.textContent.toLowerCase();
    const okQ = !q || txt.includes(q);
    const okV = !v || row.dataset.venue === v;
    const okT = !t || row.dataset.team1 === t || row.dataset.team2 === t;
    row.style.display = (okQ && okV && okT) ? '' : 'none';
  });
}
['m-search','m-venue','m-team'].forEach(id => document.getElementById(id)?.addEventListener('input', filterMatches));

// ── Head-to-Head ─────────────────────────────────────────────
document.getElementById('h2h-go')?.addEventListener('click', async () => {
  const t1 = document.getElementById('h2h-t1').value;
  const t2 = document.getElementById('h2h-t2').value;
  const out = document.getElementById('h2h-result');
  if (t1 === t2) { out.innerHTML = '<div class="muted">Pick two different teams.</div>'; return; }
  const r = await fetch(`/api/h2h?t1=${t1}&t2=${t2}`);
  const d = await r.json();
  if (!d.length) { out.innerHTML = '<div class="muted">No completed matches between these teams this season.</div>'; return; }
  out.innerHTML = d.map(x => `<div class="row"><span><b>${x.match_winner}</b> wins</span><span>${x.cnt}</span></div>`).join('');
});

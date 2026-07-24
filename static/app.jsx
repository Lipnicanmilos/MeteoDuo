const { useState, useEffect, useMemo } = React;

const DEFAULT_CITY = "32463"; // Babin
const IS_ANDROID = /Android/i.test(navigator.userAgent || ""); // widget je len pre Android

const EMOJI = [
  ["clearsky", "☀️"], ["fair", "🌤️"], ["partlycloudy", "⛅"], ["cloudy", "☁️"],
  ["fog", "🌫️"], ["heavyrainandthunder", "⛈️"], ["rainandthunder", "⛈️"],
  ["thunder", "⛈️"], ["heavyrain", "🌧️"], ["rain", "🌧️"], ["lightrain", "🌦️"],
  ["rainshowers", "🌦️"], ["heavyrainshowers", "🌧️"], ["lightrainshowers", "🌦️"],
  ["sleet", "🌨️"], ["snow", "❄️"], ["lightsnow", "🌨️"], ["heavysnow", "❄️"],
];
function symbolEmoji(code) {
  if (!code) return "·";
  const base = code.replace(/_(day|night|polartwilight)$/, "");
  for (const [k, v] of EMOJI) if (base.includes(k)) return v;
  return "🌡️";
}

// WMO weather code (Open-Meteo) -> emoji
function wmoEmoji(code) {
  if (code == null) return "·";
  if (code === 0) return "☀️";
  if (code === 1) return "🌤️";
  if (code === 2) return "⛅";
  if (code === 3) return "☁️";
  if (code === 45 || code === 48) return "🌫️";
  if (code >= 51 && code <= 57) return "🌦️";
  if (code >= 61 && code <= 65) return "🌧️";
  if (code === 66 || code === 67) return "🌨️";
  if (code >= 71 && code <= 77) return "❄️";
  if (code >= 80 && code <= 82) return "🌦️";
  if (code === 85 || code === 86) return "🌨️";
  if (code >= 95) return "⛈️";
  return "🌡️";
}

const DAY_NAMES = ["nedeľa","pondelok","utorok","streda","štvrtok","piatok","sobota"];
function dayLabel(dateStr, idx) {
  if (idx === 0) return "dnes";
  if (idx === 1) return "zajtra";
  return DAY_NAMES[new Date(dateStr + "T12:00:00").getDay()];
}
function fmtDate(dateStr) {
  const d = new Date(dateStr + "T12:00:00");
  return d.getDate() + ". " + (d.getMonth() + 1) + ".";
}
function windArrow(deg) {
  if (deg == null) return "";
  const arrows = ["↓","↙","←","↖","↑","↗","→","↘"];
  return arrows[Math.round(deg / 45) % 8];
}
function fmtTime(iso) { return iso ? iso.slice(11, 16) : "–"; }
// UV index -> farba podľa škály WHO
function uvColor(uv) {
  if (uv == null) return "var(--muted)";
  if (uv < 3) return "#22c55e";
  if (uv < 6) return "#eab308";
  if (uv < 8) return "#f97316";
  if (uv < 11) return "#ef4444";
  return "#a855f7";
}

function CityPicker({ cities, value, onChange, children }) {
  const byName = useMemo(() => new Map(cities.map(c => [c.name.toLowerCase(), c.id])), [cities]);
  const current = cities.find(c => c.id === value);
  const [text, setText] = useState("");
  useEffect(() => { setText(current ? current.name : ""); }, [current]);

  function commit(t) {
    const id = byName.get(t.trim().toLowerCase());
    if (id) onChange(id);
  }
  return (
    <div className="city-picker">
      <label htmlFor="city">📍</label>
      <input id="city" list="citylist" value={text}
             placeholder="Vyber obec…"
             onChange={e => { setText(e.target.value); commit(e.target.value); }}
             onFocus={e => e.target.select()} />
      <datalist id="citylist">
        {cities.map(c => <option key={c.id} value={c.name} />)}
      </datalist>
      {children}
    </div>
  );
}

function DayCards({ days, daily }) {
  const sunByDate = useMemo(() => {
    const m = new Map();
    (daily || []).forEach(d => m.set(d.date, d));
    return m;
  }, [daily]);

  return (
    <div className="day-cards">
      {days.map((d, i) => {
        const sun = sunByDate.get(d.date);
        return (
          <div className="day-card" key={d.date}>
            <div className="row">
              <div className="dayname">{dayLabel(d.date, i)}<small>{fmtDate(d.date)}</small></div>
              <div className="emoji">{symbolEmoji(d.symbol)}</div>
              <div className="temps">{Math.round(d.temp_max)}° <span className="min">/ {Math.round(d.temp_min)}°</span></div>
              <div className="precip">💧 {d.precip} mm</div>
            </div>
            {sun && (sun.sunrise || sun.uv_max != null) && (
              <div className="sun">
                {sun.sunrise && <span title="Východ slnka">🌅 {fmtTime(sun.sunrise)}</span>}
                {sun.sunset && <span title="Západ slnka">🌇 {fmtTime(sun.sunset)}</span>}
                {sun.uv_max != null && (
                  <span className="uv" title="Maximálny UV index">
                    UV <span className="uv-pill" style={{ background: uvColor(sun.uv_max) }}>{sun.uv_max}</span>
                  </span>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// farebný prúžok s výstrahami pre okres (bod 4)
function fmtWhen(iso) {
  // CAP negarantuje onset/expires — chýbajúci čas nesmie zhodiť render
  return iso ? fmtDate(iso.slice(0, 10)) + " " + fmtTime(iso) : "?";
}

// Vek dát. Server cachuje predpovede 15 min a service worker pri výpadku siete
// servuje poslednú uloženú — bez tohto by používateľ nerozoznal čerstvé dáta od
// včerajších. Čas sa prepočítava každú minútu, aby zostarol aj v otvorenej karte.
const STALE_AFTER_MIN = 35;

function Freshness({ fetchedAt }) {
  const [now, setNow] = React.useState(() => Date.now());
  const [offline, setOffline] = React.useState(() => !navigator.onLine);

  React.useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 60000);
    const on = () => setOffline(false);
    const off = () => setOffline(true);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    return () => {
      clearInterval(t);
      window.removeEventListener("online", on);
      window.removeEventListener("offline", off);
    };
  }, []);

  if (!fetchedAt) return null;
  const then = new Date(fetchedAt).getTime();
  if (isNaN(then)) return null;

  const minutes = Math.max(0, Math.round((now - then) / 60000));
  const stale = offline || minutes >= STALE_AFTER_MIN;
  const time = new Date(then).toLocaleTimeString("sk-SK", { hour: "2-digit", minute: "2-digit" });

  let age;
  if (minutes < 1) age = "pred chvíľou";
  else if (minutes < 60) age = "pred " + minutes + " min";
  else {
    const h = Math.floor(minutes / 60);
    age = "pred " + h + (h === 1 ? " hodinou" : " hodinami");
  }

  return (
    <div className={"freshness" + (stale ? " stale" : "")}
         title={"Dáta stiahnuté zo zdrojov " + new Date(then).toLocaleString("sk-SK")}>
      {offline ? "⚠ offline · " : stale ? "⚠ " : ""}
      aktualizované {time} <span className="age">({age})</span>
    </div>
  );
}

function WarnBar({ warnings }) {
  if (!warnings || !warnings.length) return null;
  return (
    <div className="warn-bar">
      {warnings.map((w, i) => (
        <div className="warn" key={i} style={{ "--wc": w.color }}>
          <span className="wi">{w.icon}</span>
          <span className="wt">
            <b>{w.event || ("Výstraha – " + w.type)}</b>
            {w.headline && <span className="wmeta">{w.headline}</span>}
            <span className="wmeta">
              {w.level} úroveň · {fmtWhen(w.onset)} – {fmtWhen(w.expires)}
            </span>
          </span>
        </div>
      ))}
    </div>
  );
}

function HourlyPanel({ hourly, daysCount }) {
  const byDay = useMemo(() => {
    const m = new Map();
    for (const h of hourly) {
      const day = h.time.slice(0, 10);
      if (!m.has(day)) m.set(day, []);
      m.get(day).push(h);
    }
    return [...m.entries()].slice(0, daysCount);
  }, [hourly, daysCount]);

  // pri jednom dni každú hodinu, pri troch každú tretiu, pri desiatich šiestu
  // (MET Norway po ~60 h aj tak dáva už len 6-hodinové kroky)
  const step = daysCount === 1 ? 1 : daysCount === 10 ? 6 : 3;

  return (
    <div>
      {byDay.map(([day, rows], i) => (
        <div className="day-block" key={day}>
          <h3>{dayLabel(day, i)} {fmtDate(day)}</h3>
          <table className="hours"><tbody>
            {rows.filter(h => parseInt(h.time.slice(11, 13)) % step === 0).map(h => (
              <tr key={h.time}>
                <td className="h">{h.time.slice(11, 16)}</td>
                <td className="e">{symbolEmoji(h.symbol)}</td>
                <td className="t">{h.temp != null ? Math.round(h.temp) + "°" : "–"}</td>
                <td className="p">{h.precip ? h.precip.toFixed(1) + " mm" : ""}</td>
                <td className="w">{h.wind != null ? h.wind.toFixed(0) + " m/s " + windArrow(h.wind_dir) : ""}</td>
              </tr>
            ))}
          </tbody></table>
        </div>
      ))}
    </div>
  );
}

// typy SHMÚ meteogramov (id -> API ?type=, label pre čipy, popis)
const MG_TYPES = [
  { id: "aladin",  label: "ALADIN · 3 dni",  caption: "Automatická predpoveď modelu ALADIN, aktualizovaná 4× denne." },
  { id: "laef",    label: "A-LAEF · 3 dni",  caption: "Ansámblová predpoveď A-LAEF (epsgram) na 3 dni." },
  { id: "egram8",  label: "EPS · 8 dní",     caption: "Ansámblová predpoveď ECMWF (epsgram) na 8 dní." },
  { id: "mgram10", label: "ECMWF · 10 dní",  caption: "Meteogram ECMWF na 10 dní." },
];

const ZOOM = 2.5;

function Meteogram({ src, alt, caption }) {
  const [lens, setLens] = useState(null);   // {x, y, bgX, bgY, bgW, bgH}
  const [failed, setFailed] = useState(false);
  const [open, setOpen] = useState(false);  // lightbox
  useEffect(() => { setFailed(false); setLens(null); setOpen(false); }, [src]);

  useEffect(() => {
    if (!open) return;
    const onKey = e => { if (e.key === "Escape") setOpen(false); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  function onMove(e) {
    const img = e.currentTarget;
    const rect = img.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    if (x < 0 || y < 0 || x > rect.width || y > rect.height) { setLens(null); return; }
    const half = 170; // polovica priemeru lupy
    setLens({
      x: img.offsetLeft + x - half,
      y: img.offsetTop + y - half,
      bgX: -(x * ZOOM - half),
      bgY: -(y * ZOOM - half),
      bgW: rect.width * ZOOM,
      bgH: rect.height * ZOOM,
    });
  }

  return (
    <div className="meteogram-wrap">
      <div className="meteogram-scroll">
        {!failed && (
          <img src={src} alt={alt}
               onMouseMove={onMove} onMouseLeave={() => setLens(null)}
               onClick={() => setOpen(true)}
               onError={() => setFailed(true)} />
        )}
        {failed && <div className="error">Meteogram sa nepodarilo načítať.</div>}
        {lens && !failed && (
          <div className="zoom-lens" style={{
            left: lens.x + "px", top: lens.y + "px",
            backgroundImage: "url(" + src + ")",
            backgroundSize: lens.bgW + "px " + lens.bgH + "px",
            backgroundPosition: lens.bgX + "px " + lens.bgY + "px",
          }} />
        )}
      </div>
      <div className="note">{caption} Prejdením myšou sa zobrazí lupa, kliknutím sa meteogram zväčší.</div>
      {open && !failed && (
        <div className="lightbox" onClick={() => setOpen(false)}>
          <img src={src} alt={alt} />
        </div>
      )}
    </div>
  );
}

function fmtWind(v) { return v != null ? v.toFixed(1) + " m/s" : "–"; }

// zdroje v porovnávacej tabuľke; ECMWF = model, ktorý predvolene zobrazuje
// Windy aj 10-dňový meteogram SHMÚ (ALADIN čísla SHMÚ nezverejňuje)
const SOURCES = [
  { id: "yr",    label: "🇳🇴 yr.no",  sub: "MET Norway",        color: "#2563eb" },
  { id: "ecmwf", label: "🌍 ECMWF",   sub: "Windy · SHMÚ 10 d", color: "#0f766e" },
  { id: "icon",  label: "🇩🇪 ICON",   sub: "DWD",               color: "#7c3aed" },
  { id: "gfs",   label: "🇺🇸 GFS",    sub: "NOAA",              color: "#b45309" },
];

// mini SVG graf: čiara (teplota) alebo stĺpce (zrážky) cez dni
function Sparkline({ values, domainMin, domainMax, color, type }) {
  const W = 100, H = 30, pad = 3;
  const pts = values.filter(v => v != null);
  if (pts.length < 1) return <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" />;
  const span = (domainMax - domainMin) || 1;
  const x = i => pad + (values.length === 1 ? W / 2 : (i * (W - 2 * pad)) / (values.length - 1));
  const y = v => H - pad - ((v - domainMin) / span) * (H - 2 * pad);

  if (type === "bar") {
    const bw = Math.max(2, (W - 2 * pad) / values.length - 2);
    return (
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
        {values.map((v, i) => v == null ? null : (
          <rect key={i} x={x(i) - bw / 2} width={bw}
                y={Math.min(y(v), H - pad - 0.5)} height={Math.max(0.5, H - pad - y(v))}
                fill={color} rx="1" opacity="0.85" />
        ))}
      </svg>
    );
  }
  const line = values.map((v, i) => v == null ? null : `${x(i).toFixed(1)},${y(v).toFixed(1)}`)
                     .filter(Boolean).join(" ");
  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
      <polyline points={line} fill="none" stroke={color} strokeWidth="1.8"
                strokeLinejoin="round" strokeLinecap="round" />
      {values.map((v, i) => v == null ? null : (
        <circle key={i} cx={x(i)} cy={y(v)} r="1.6" fill={color} />
      ))}
    </svg>
  );
}

// súhrn trendov: pre každý zdroj sparkline teploty a zrážok cez zobrazené dni
function SparkSummary({ active, sources, dates }) {
  const dayOf = (id, date) => (sources[id] || []).find(d => d.date === date);
  const tVals = {}, pVals = {};
  let tMin = Infinity, tMax = -Infinity, pMax = 0;
  active.forEach(s => {
    tVals[s.id] = dates.map(dt => { const d = dayOf(s.id, dt); return d ? d.temp_max : null; });
    pVals[s.id] = dates.map(dt => { const d = dayOf(s.id, dt); return d ? d.precip : null; });
    tVals[s.id].forEach(v => { if (v != null) { tMin = Math.min(tMin, v); tMax = Math.max(tMax, v); } });
    pVals[s.id].forEach(v => { if (v != null) pMax = Math.max(pMax, v); });
  });
  if (tMin === Infinity) return null;

  return (
    <div className="spark-summary">
      {active.map(s => {
        const tv = tVals[s.id].filter(v => v != null);
        const pv = pVals[s.id].filter(v => v != null);
        const tLast = tv.length ? Math.round(tv[tv.length - 1]) : "–";
        const pSum = pv.reduce((a, b) => a + b, 0);
        return (
          <div className="spark-card" key={s.id}>
            <div className="sh" style={{ color: s.color }}>{s.label} <small>{s.sub}</small></div>
            <div className="spark-row">
              <span className="lbl">🌡️ max</span>
              <Sparkline values={tVals[s.id]} domainMin={tMin} domainMax={tMax}
                         color={s.color} type="line" />
              <span className="val">{tLast}°</span>
            </div>
            <div className="spark-row">
              <span className="lbl">💧 zrážky</span>
              <Sparkline values={pVals[s.id]} domainMin={0} domainMax={pMax || 1}
                         color={s.color} type="bar" />
              <span className="val">{pSum.toFixed(0)} mm</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// spoločná tabuľka: všetky zdroje pod sebou, deň po dni
function CompareTable({ sources, yrError, omError, daysCount }) {
  const active = SOURCES.filter(s => sources[s.id] && sources[s.id].length);

  const dates = useMemo(() => {
    const set = new Set();
    active.forEach(s => sources[s.id].forEach(d => set.add(d.date)));
    return [...set].sort().slice(0, daysCount);
  }, [sources, daysCount]);

  if (!dates.length) {
    return <div className="error">{yrError || omError || "Dáta na porovnanie nie sú dostupné."}</div>;
  }

  const dayOf = (srcId, date) => (sources[srcId] || []).find(d => d.date === date);
  const spreadOf = (date, field) => {
    const vals = active.map(s => { const d = dayOf(s.id, date); return d && d[field]; })
                       .filter(v => v != null);
    return vals.length > 1 ? Math.max(...vals) - Math.min(...vals) : 0;
  };

  return (
    <div>
      <SparkSummary active={active} sources={sources} dates={dates} />
      <div className="compare-scroll">
      <table className="compare-table">
        <thead>
          <tr>
            <th className="c-day">Deň</th>
            <th>Zdroj</th>
            <th></th>
            <th>Max</th>
            <th>Min</th>
            <th>Zrážky</th>
            <th>Vietor</th>
          </tr>
        </thead>
        <tbody>
          {dates.map((date, i) => {
            const tSpread = spreadOf(date, "temp_max");
            const pSpread = spreadOf(date, "precip");
            return (
              <React.Fragment key={date}>
                {active.map((s, j) => {
                  const d = dayOf(s.id, date);
                  return (
                    <tr key={s.id} className={j === 0 ? "day-top" : ""}>
                      {j === 0 && (
                        <td className="c-day" rowSpan={active.length}>
                          <span className="dn">{dayLabel(date, i)}</span>
                          <small>{fmtDate(date)}</small>
                          {tSpread >= 2 && <span className="delta" title="Rozptyl max. teploty medzi modelmi">Δ {tSpread.toFixed(1)}°</span>}
                          {pSpread >= 3 && <span className="delta" title="Rozptyl zrážok medzi modelmi">Δ {pSpread.toFixed(1)} mm</span>}
                        </td>
                      )}
                      <td className="src" style={{ color: s.color }}>
                        {s.label} <small className="sub">{s.sub}</small>
                      </td>
                      <td className="sym">{d ? (s.id === "yr" ? symbolEmoji(d.symbol) : wmoEmoji(d.wmo)) : ""}</td>
                      <td className="tmax">{d ? Math.round(d.temp_max) + "°" : "–"}</td>
                      <td className="tmin">{d ? Math.round(d.temp_min) + "°" : "–"}</td>
                      <td className="prec">{d ? "💧 " + d.precip + " mm" : "–"}</td>
                      <td className="wind">{d ? fmtWind(d.wind_max) : "–"}</td>
                    </tr>
                  );
                })}
              </React.Fragment>
            );
          })}
        </tbody>
      </table>
      </div>
      <div className="note">
        ECMWF je model, ktorý predvolene zobrazuje Windy aj 10-dňový meteogram SHMÚ.
        ALADIN (SHMÚ, 3 dni) čísla nezverejňuje — je len v obrázkovom meteograme vyššie.
        {yrError && <div>⚠️ yr.no: {yrError}</div>}
        {omError && <div>⚠️ Open-Meteo: {omError}</div>}
      </div>
    </div>
  );
}

function loadFavs() {
  try { return JSON.parse(localStorage.getItem("meteoduo_favs")) || []; }
  catch (e) { return []; }
}

function FavBar({ favs, cities, cityId, onSelect, onRemove }) {
  if (!favs.length || !cities.length) return null;
  return (
    <div className="fav-bar">
      {favs.map(id => {
        const c = cities.find(c => c.id === id);
        if (!c) return null;
        return (
          <span key={id} className={"fav-chip" + (id === cityId ? " active" : "")}
                role="button" tabIndex={0}
                onClick={() => onSelect(id)}
                onKeyDown={e => {
                  if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onSelect(id); }
                }}
                title={"Zobraziť " + c.name}>
            {c.name}
            <button className="x" title="Odobrať z obľúbených"
                    onClick={e => { e.stopPropagation(); onRemove(id); }}>✕</button>
          </span>
        );
      })}
    </div>
  );
}

// počiatočný stav zo zdieľateľnej URL (?obec=32463&dni=10), inak localStorage
function initialCity() {
  const p = new URLSearchParams(location.search).get("obec");
  return p || localStorage.getItem("meteoduo_city") || DEFAULT_CITY;
}
function initialDays() {
  const p = new URLSearchParams(location.search).get("dni");
  const v = p || localStorage.getItem("meteoduo_days");
  return v === "1" ? 1 : v === "10" ? 10 : 3;
}
function initialTheme() {
  return localStorage.getItem("meteoduo_theme") || "auto"; // auto | light | dark
}

function App() {
  const [cities, setCities] = useState([]);
  const [cityId, setCityId] = useState(initialCity);
  const [favs, setFavs] = useState(loadFavs);
  const [daysCount, setDaysCount] = useState(initialDays);
  const [theme, setTheme] = useState(initialTheme);
  const [mgType, setMgType] = useState("aladin");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => { localStorage.setItem("meteoduo_favs", JSON.stringify(favs)); }, [favs]);
  useEffect(() => { localStorage.setItem("meteoduo_days", String(daysCount)); }, [daysCount]);
  // rozsah dní automaticky prepne aj zodpovedajúci meteogram (ručne sa dá zmeniť čipmi)
  useEffect(() => { setMgType(daysCount === 10 ? "mgram10" : "aladin"); }, [daysCount]);

  // tmavý režim (bod 6c): auto = podľa systému (žiadny atribút), inak vynútené
  useEffect(() => {
    const root = document.documentElement;
    if (theme === "auto") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", theme);
    localStorage.setItem("meteoduo_theme", theme);
  }, [theme]);
  const cycleTheme = () => setTheme(t => t === "auto" ? "light" : t === "light" ? "dark" : "auto");
  const themeIcon = theme === "dark" ? "🌙" : theme === "light" ? "☀️" : "🌗";

  // zdieľateľná URL (bod 6b): drž ?obec&dni v adrese bez reloadu
  useEffect(() => {
    const p = new URLSearchParams(location.search);
    p.set("obec", cityId);
    p.set("dni", String(daysCount));
    history.replaceState(null, "", location.pathname + "?" + p.toString());
  }, [cityId, daysCount]);
  const isFav = favs.includes(cityId);
  const toggleFav = () => setFavs(f => f.includes(cityId) ? f.filter(x => x !== cityId) : [...f, cityId]);
  const removeFav = id => setFavs(f => f.filter(x => x !== id));

  useEffect(() => {
    fetch("/api/cities").then(r => r.json()).then(setCities)
      .catch(() => setError("Nepodarilo sa načítať zoznam obcí."));
  }, []);

  // neplatné ID z URL (?obec=...) alebo zo starého localStorage -> default
  useEffect(() => {
    if (cities.length && !cities.some(c => c.id === cityId)) {
      setCityId(DEFAULT_CITY);
    }
  }, [cities, cityId]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true); setError(null);
    localStorage.setItem("meteoduo_city", cityId);
    fetch("/api/forecast/" + cityId)
      .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(d => { if (!cancelled) { setData(d); setLoading(false); } })
      .catch(() => { if (!cancelled) { setError("Predpoveď sa nepodarilo načítať."); setLoading(false); } });
    return () => { cancelled = true; };
  }, [cityId]);

  return (
    <React.Fragment>
      <header>
        <div>
          <h1>⛅ MeteoDuo</h1>
          <div className="tagline">dve predpovede vedľa seba · {daysCount === 1 ? "dnes" : daysCount === 3 ? "na 3 dni" : "na 10 dní"}</div>
        </div>
        <div className="view-toggle" role="group" aria-label="Rozsah predpovede">
          <button className={daysCount === 1 ? "active" : ""}
                  onClick={() => setDaysCount(1)}>1 deň</button>
          <button className={daysCount === 3 ? "active" : ""}
                  onClick={() => setDaysCount(3)}>3 dni</button>
          <button className={daysCount === 10 ? "active" : ""}
                  onClick={() => setDaysCount(10)}>10 dní</button>
        </div>
        <div className="map-links">
          {[{ href: "/radar", label: "🌧️ Radar" },
            { href: "/windy", label: "🌀 Windy" },
            { href: "/blesky", label: "⚡ Blesky" }].map((m) => (
            <a key={m.href} className="map-link"
               href={data && data.city.lat != null
                     ? m.href + "?lat=" + data.city.lat + "&lon=" + data.city.lon
                     : m.href}>{m.label}</a>
          ))}
          {IS_ANDROID && (
          <a className="map-link" href="/widget"
             title="Natívny Android widget so živou predpoveďou na plochu">📲 Widget</a>
          )}
        </div>
        <CityPicker cities={cities} value={cityId} onChange={setCityId}>
          <button className="fav-btn" onClick={toggleFav}
                  title={isFav ? "Odobrať z obľúbených" : "Uložiť medzi obľúbené"}>
            {isFav ? "★" : "☆"}
          </button>
          <button className="theme-btn" onClick={cycleTheme}
                  title={"Motív: " + (theme === "auto" ? "automatický" : theme === "light" ? "svetlý" : "tmavý")}>
            {themeIcon}
          </button>
        </CityPicker>
      </header>

      <FavBar favs={favs} cities={cities} cityId={cityId}
              onSelect={setCityId} onRemove={removeFav} />

      <main>
        <section className="panel">
          <h2>🇳🇴 yr.no <span className="src">(MET Norway, hodinová predpoveď)</span></h2>
          {loading && <div className="status">Načítavam…</div>}
          {!loading && data && data.yr && <HourlyPanel hourly={data.yr.hourly} daysCount={daysCount} />}
          {!loading && data && !data.yr && <div className="error">{data.yr_error || "Dáta nie sú dostupné."}</div>}
        </section>

        <section className="panel panel-center">
          {loading && <div className="status">Načítavam…</div>}
          {error && <div className="error">{error}</div>}
          {!loading && data && (
            <React.Fragment>
              <div className="place">
                <div className="name">
                  {data.city.name}
                  {data.warnings && data.warnings.length > 0 &&
                    <span className="warn-badge" title={data.warnings.length + " výstraha/y v okrese " + (data.city.okres || "")}>
                      {data.warnings[0].icon}
                    </span>}
                </div>
                {data.city.okres && <div className="coords">okres {data.city.okres}</div>}
                {data.city.lat && <div className="coords">{data.city.lat.toFixed(3)}°N, {data.city.lon.toFixed(3)}°E</div>}
                <Freshness fetchedAt={data.fetched_at} />
              </div>
              <WarnBar warnings={data.warnings} />
              {data.yr && <DayCards days={data.yr.days.slice(0, daysCount)} daily={data.daily} />}
              {!data.yr && <div className="status">Súhrn nie je dostupný.</div>}
            </React.Fragment>
          )}
        </section>

        <section className="panel">
          <h2>🇸🇰 SHMÚ <span className="src">(meteogramy)</span></h2>
          <div className="mg-tabs" role="group" aria-label="Typ meteogramu">
            {MG_TYPES.map(t => (
              <button key={t.id} className={mgType === t.id ? "active" : ""}
                      onClick={() => setMgType(t.id)}>{t.label}</button>
            ))}
          </div>
          {loading && <div className="status">Načítavam…</div>}
          {!loading && data && (
            <Meteogram src={data.meteogram_url + "?type=" + mgType}
                       alt={"SHMÚ meteogram (" + mgType + ") – " + data.city.name}
                       caption={MG_TYPES.find(t => t.id === mgType).caption} />
          )}
        </section>

        <section className="panel compare">
          <h2>📊 Porovnanie modelov <span className="src">(číselne, deň po dni)</span></h2>
          {loading && <div className="status">Načítavam…</div>}
          {!loading && data && (
            <CompareTable sources={Object.assign({ yr: data.yr && data.yr.days }, data.om_models || {})}
                          yrError={data.yr_error} omError={data.om_error}
                          daysCount={daysCount} />
          )}
        </section>

      </main>

      <footer>
        Meteorologické dáta: <a href="https://www.met.no/en" target="_blank" rel="noreferrer">MET Norway</a> (CC BY 4.0,
        zobrazované aj na <a href="https://www.yr.no/en" target="_blank" rel="noreferrer">yr.no</a>) ·{" "}
        <a href="https://open-meteo.com/" target="_blank" rel="noreferrer">Open-Meteo</a> (modely ECMWF/ICON/GFS, slnko a UV; CC BY 4.0) ·{" "}
        <a href="https://www.shmu.sk" target="_blank" rel="noreferrer">SHMÚ</a> (meteogramy) ·{" "}
        <a href="https://meteoalarm.org" target="_blank" rel="noreferrer">Meteoalarm</a> (výstrahy, CC BY 4.0) ·{" "}
        <a href="https://www.windy.com" target="_blank" rel="noreferrer">Windy</a> (mapa) ·{" "}
        <a href="https://www.blitzortung.org" target="_blank" rel="noreferrer">Blitzortung.org</a> (blesky,
        nekomerčné použitie).
        MeteoDuo dáta iba zobrazuje, nie je ich autorom.
        {" "}Autor: <a href="https://lipnicanmilos.github.io" target="_blank" rel="noreferrer">Miloš Lipničan</a>.
      </footer>
    </React.Fragment>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);

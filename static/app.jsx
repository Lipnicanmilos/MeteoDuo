const { useState, useEffect, useMemo } = React;

const DEFAULT_CITY = "32463"; // Babin

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

function DayCards({ days }) {
  return (
    <div className="day-cards">
      {days.map((d, i) => (
        <div className="day-card" key={d.date}>
          <div className="dayname">{dayLabel(d.date, i)}<small>{fmtDate(d.date)}</small></div>
          <div className="emoji">{symbolEmoji(d.symbol)}</div>
          <div className="temps">{Math.round(d.temp_max)}° <span className="min">/ {Math.round(d.temp_min)}°</span></div>
          <div className="precip">💧 {d.precip} mm</div>
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
                onClick={() => onSelect(id)} title={"Zobraziť " + c.name}>
            {c.name}
            <button className="x" title="Odobrať z obľúbených"
                    onClick={e => { e.stopPropagation(); onRemove(id); }}>✕</button>
          </span>
        );
      })}
    </div>
  );
}

function App() {
  const [cities, setCities] = useState([]);
  const [cityId, setCityId] = useState(localStorage.getItem("meteoduo_city") || DEFAULT_CITY);
  const [favs, setFavs] = useState(loadFavs);
  const [daysCount, setDaysCount] = useState(() => {
    const v = localStorage.getItem("meteoduo_days");
    return v === "1" ? 1 : v === "10" ? 10 : 3;
  });
  const [mgType, setMgType] = useState("aladin");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => { localStorage.setItem("meteoduo_favs", JSON.stringify(favs)); }, [favs]);
  useEffect(() => { localStorage.setItem("meteoduo_days", String(daysCount)); }, [daysCount]);
  // rozsah dní automaticky prepne aj zodpovedajúci meteogram (ručne sa dá zmeniť čipmi)
  useEffect(() => { setMgType(daysCount === 10 ? "mgram10" : "aladin"); }, [daysCount]);
  const isFav = favs.includes(cityId);
  const toggleFav = () => setFavs(f => f.includes(cityId) ? f.filter(x => x !== cityId) : [...f, cityId]);
  const removeFav = id => setFavs(f => f.filter(x => x !== id));

  useEffect(() => {
    fetch("/api/cities").then(r => r.json()).then(setCities)
      .catch(() => setError("Nepodarilo sa načítať zoznam obcí."));
  }, []);

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
        <a className="radar-link"
           href={data && data.city.lat != null
                 ? "/radar?lat=" + data.city.lat + "&lon=" + data.city.lon
                 : "/radar"}>🌧️ Radar</a>
        <CityPicker cities={cities} value={cityId} onChange={setCityId}>
          <button className="fav-btn" onClick={toggleFav}
                  title={isFav ? "Odobrať z obľúbených" : "Uložiť medzi obľúbené"}>
            {isFav ? "★" : "☆"}
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
                <div className="name">{data.city.name}</div>
                {data.city.lat && <div className="coords">{data.city.lat.toFixed(3)}°N, {data.city.lon.toFixed(3)}°E</div>}
              </div>
              {data.yr && <DayCards days={data.yr.days.slice(0, daysCount)} />}
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

        <section className="panel windy">
          <h2>🌀 Windy <span className="src">(interaktívna mapa a predpoveď)</span></h2>
          {loading && <div className="status">Načítavam…</div>}
          {!loading && data && data.city.lat != null && (
            <React.Fragment>
              <iframe title={"Windy – " + data.city.name}
                      loading="lazy"
                      src={"https://embed.windy.com/embed.html?type=map&location=coordinates" +
                           "&metricWind=m%2Fs&metricTemp=%C2%B0C&metricRain=mm" +
                           "&zoom=9&overlay=rain&product=ecmwf&level=surface" +
                           "&lat=" + data.city.lat + "&lon=" + data.city.lon +
                           "&detailLat=" + data.city.lat + "&detailLon=" + data.city.lon +
                           "&detail=true&marker=true&message=true"} />
              <div className="note">Interaktívna mapa windy.com (model ECMWF) so značkou na vybranej obci
                — v spodnej časti bodová predpoveď na 10+ dní.</div>
            </React.Fragment>
          )}
          {!loading && data && data.city.lat == null && (
            <div className="error">Bez súradníc obce sa Windy mapa nedá zobraziť.</div>
          )}
        </section>
      </main>

      <footer>
        Meteorologické dáta: <a href="https://www.met.no/en" target="_blank" rel="noreferrer">MET Norway</a> (CC BY 4.0,
        zobrazované aj na <a href="https://www.yr.no/en" target="_blank" rel="noreferrer">yr.no</a>) ·
        <a href="https://www.shmu.sk" target="_blank" rel="noreferrer"> SHMÚ</a> (meteogram ALADIN).
        MeteoDuo dáta iba zobrazuje, nie je ich autorom.
      </footer>
    </React.Fragment>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);

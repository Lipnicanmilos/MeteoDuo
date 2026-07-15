# TODO

## Optimalizácie (poradie = priorita)

- [ ] **1. Súradnice priamo v cities.json** — každá obec sa teraz geokóduje
      cez Open-Meteo API za behu; predpočítať jednorazovým skriptom
      → rýchlejšie načítanie, o jednu závislosť menej
- [ ] **2. Predkompilovať JSX** — Babel standalone kompiluje v prehliadači
      pri každom načítaní (~1 s); jednorazová kompilácia do plain JS
      (bez Node/Vite)
- [ ] **3. PWA** — manifest + service worker; inštalácia na mobil,
      posledná predpoveď dostupná offline

## Funkcie

- [ ] **4. Výstrahy SHMÚ / Meteoalarm** ⚠️ — farebný prúžok pri obci, keď
      platí výstraha (vietor, búrky, poľadovica)
- [ ] **5. Východ/západ slnka + UV index** — Open-Meteo daily, do denného
      súhrnu
- [ ] **6a.** Sparkline grafy (teplota/zrážky) v porovnávacej tabuľke
- [ ] **6b.** Zdieľateľná URL s obcou a rozsahom (?obec=32463&dni=10)
- [ ] **6c.** Tmavý režim

## Ostatné

- [ ] **Nasadenie** — Cloud Run alebo AWS; Dockerfile je hotový, appka zatiaľ
      beží len lokálne. Po nasadení skontrolovať User-Agent limity API
      (MET Norway vyžaduje identifikáciu) a prípadne pridať rate-limit.
- [ ] **Migrácia na Vite** (voliteľné) — frontend zámerne beží cez React CDN
      + Babel standalone bez Node; pri raste appky zvážiť build krok.

## Hotové

- [x] Fullscreen radar na /radar (Windy embed, overlay=radar, centrovaný na obec)
- [x] Prepínač rozsahu 1 / 3 / 10 dní
- [x] Porovnanie 4 modelov (yr.no, ECMWF, ICON, GFS) v spoločnej tabuľke
- [x] 4 typy SHMÚ meteogramov (ALADIN, A-LAEF, EPS 8 d, ECMWF 10 d)
- [x] Windy panel (embed widget)
- [x] Obľúbené obce (localStorage)
- [x] Lupa + lightbox na meteograme
- [x] Responzívne mobilné zobrazenie

# TODO

## Otvorené

- [ ] **Nasadenie** — Cloud Run alebo AWS; Dockerfile je hotový, appka zatiaľ
      beží len lokálne. Po nasadení skontrolovať User-Agent limity API
      (MET Norway vyžaduje identifikáciu) a prípadne pridať rate-limit.
- [ ] **Migrácia na Vite** (voliteľné) — frontend zámerne beží cez React CDN
      + Babel standalone bez Node; pri raste appky zvážiť build krok.

## Nápady

- [ ] Grafy priamo z čísel (teplota/zrážky ako sparkline v porovnávacej
      tabuľke) namiesto/popri PNG meteogramoch
- [ ] Zdieľateľná URL s obcou a rozsahom (?obec=32463&dni=10)
- [ ] Tmavý režim

## Hotové

- [x] Prepínač rozsahu 1 / 3 / 10 dní
- [x] Porovnanie 4 modelov (yr.no, ECMWF, ICON, GFS) v spoločnej tabuľke
- [x] 4 typy SHMÚ meteogramov (ALADIN, A-LAEF, EPS 8 d, ECMWF 10 d)
- [x] Windy panel (embed widget)
- [x] Obľúbené obce (localStorage)
- [x] Lupa + lightbox na meteograme
- [x] Responzívne mobilné zobrazenie

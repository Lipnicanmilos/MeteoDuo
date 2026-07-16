# TODO

## Otvorené

- [ ] **AWS: vymeniť root access key za IAM usera** — CLI kľúč je vytvorený
      pre root účet (a bol viditeľný na screenshote) → vytvoriť IAM usera
      (napr. `milos-cli`, AdministratorAccess), `aws configure` s novým kľúčom,
      root kľúč deaktivovať a zmazať. GitHub Actions sa to netýka (OIDC rola).
- [ ] **Vlastná doména** — API Gateway custom domain + certifikát (ACM),
      teraz beží na execute-api URL.
- [ ] **Skontrolovať User-Agent pre MET Norway** — API vyžaduje identifikáciu
      aplikácie; overiť, že yr.py posiela zmysluplný User-Agent aj z Lambdy.
- [ ] **Testy** — pytest pre digest funkcie (yr._digest, openmeteo._digest_model,
      warnings._digest) s uloženými JSON fixture — ochrana pri zmene formátu API.
- [ ] **Logging** — chyby externých zdrojov v /api/forecast sa teraz zahadzujú
      potichu (zámerne pre UX); logovať ich do CloudWatch pre diagnostiku.
- [ ] **Migrácia na Vite** (voliteľné) — frontend zámerne beží cez React CDN
      a JSX kompiluje server (dukpy), bez Node/build kroku; zvážiť pri raste appky.

## Hotové

- [x] **Nasadenie na AWS** — Lambda (container image) + API Gateway HTTP API,
      https://h3r2z4x75k.execute-api.eu-central-1.amazonaws.com; CI/CD cez
      GitHub Actions (OIDC) → ECR → update-function-code; uvicorn
      `--proxy-headers`; JSX predkompilované pri builde (read-only FS)
- [x] **Súradnice + okres v cities.json** — scripts/geocode_cities.py (súradnice),
      scripts/assign_okres.py (okres pre výstrahy); API geokódovanie je len fallback
- [x] **Serverová kompilácia JSX** — JSX v static/app.jsx, kompiluje server cez
      dukpy (Babel v Pythone) na /app.js s auto-rekompiláciou; Babel z prehliadača preč
- [x] **PWA** — manifest.webmanifest + sw.js (network-first, posledná predpoveď
      offline; CDN cache-first), ikony cez Pillow (scripts/make_icons.py)
- [x] **Výstrahy SHMÚ / Meteoalarm** ⚠️ — warnings.py (JSON feed, na úrovni okresu),
      farebný prúžok + badge pri obci
- [x] **Východ/západ slnka + UV index** — openmeteo.fetch_daily, v denných kartách
      🌅/🌇 + farebný UV pill (škála WHO)
- [x] **Sparkline grafy** — SVG trend teploty a zrážok pre každý model nad tabuľkou
- [x] **Zdieľateľná URL** — ?obec=&dni= (init z URL + sync cez history.replaceState)
- [x] **Tmavý režim** — prepínač auto/svetlý/tmavý, CSS premenné + prefers-color-scheme
- [x] **Opravy z code review** — neúplné posledné dni modelov sa vynechávajú;
      opravené typy výstrah (7/12/13); CAP bez onset/expires nezhodí render;
      gzip; PNG cache meteogramov; evikcia cache; validácia ?obec=;
      klávesnica pre obľúbené čipy; väčšie dotykové ciele na mobile;
      atribúcia všetkých zdrojov vo footeri (CC BY 4.0)
- [x] Fullscreen radar na /radar (Windy embed, overlay=radar, centrovaný na obec)
- [x] Prepínač rozsahu 1 / 3 / 10 dní
- [x] Porovnanie 4 modelov (yr.no, ECMWF, ICON, GFS) v spoločnej tabuľke
- [x] 4 typy SHMÚ meteogramov (ALADIN, A-LAEF, EPS 8 d, ECMWF 10 d)
- [x] Windy panel (embed widget)
- [x] Obľúbené obce (localStorage)
- [x] Lupa + lightbox na meteograme
- [x] Responzívne mobilné zobrazenie

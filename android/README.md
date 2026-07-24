# MeteoDuo — natívny Android widget

Domovský widget s **živou predpoveďou počasia** z MeteoDuo API. Na rozdiel od
webového PNG riešenia sa obnovuje **sám** (Android widget update, bez KWGT/Tasker)
a renderuje sa **natívne** (RemoteViews, emoji ikona) — nie je to obrázok.

## Čo robí

- Ťahá dáta z `GET /api/forecast/{cityId}` (živá predpoveď yr.no cez MeteoDuo).
- Zobrazuje: mesto, ikonu počasia (emoji), aktuálnu teplotu, popis, max/min a čas obnovy.
- Android ho obnovuje každých ~30 min (`updatePeriodMillis`); **ťuknutím** sa obnoví hneď.
- Pri pridaní widgetu sa spýta na **mesto** (SHMÚ id) — predvolene Bratislava (centrum) `32737`.

## Ako zistiť `cityId`

V appke MeteoDuo vyber mesto a otvor stránku **„🖼️ Tapeta"** — v adrese je `?city=<číslo>`.
(Alebo priamo na webe je mesto v URL ako `?obec=<číslo>`.)

## Build (potrebuješ Android Studio)

> ⚠️ Tento projekt **nebol zbuildený ani otestovaný automaticky** — je to scaffold.
> Skompilovať a nainštalovať APK treba na vlastnom stroji.

1. Otvor priečinok `android/` v **Android Studio** (Giraffe alebo novší).
   Android Studio si dogeneruje Gradle wrapper a stiahne závislosti.
2. Priprav zariadenie: fyzický telefón s **USB debugging**, alebo emulátor.
3. **Run ▶** (alebo *Build → Build APK(s)*), APK bude v
   `app/build/outputs/apk/`.
4. Na telefóne: podrž plochu → **Widgety** → *MeteoDuo Widget* → pretiahni na plochu →
   zadaj mesto → **Uložiť**.

### Alternatívne z príkazového riadka
```bash
cd android
gradle wrapper            # jednorazovo, ak nemáš ./gradlew
./gradlew assembleDebug   # APK: app/build/outputs/apk/debug/app-debug.apk
```

## Distribúcia užívateľom (podpísaný APK → GitHub Releases)

Web appka má stránku `/widget` s tlačidlom, ktoré ukazuje na
`https://github.com/Lipnicanmilos/MeteoDuo/releases/latest/download/meteoduo-widget.apk`.
Aby fungovalo, nahraj podpísaný APK **presne s týmto názvom** do GitHub Releases:

**A) Podpísaný release APK (Android Studio)**
1. *Build → Generate Signed Bundle / APK…* → **APK** → Next.
2. *Key store path* → **Create new…** → ulož `.jks` (napr. `meteoduo-widget.jks`),
   zadaj heslá + alias. **Zálohuj `.jks` a heslá** — bez nich nevydáš žiadny update!
3. Build variant **release** → Finish. APK je v `android/app/release/app-release.apk`.

**B) Premenuj** `app-release.apk` → **`meteoduo-widget.apk`** (názov musí sedieť s webom).

**C) GitHub Releases (cez web, netreba gh CLI)**
1. Repo MeteoDuo → **Releases** → **Draft a new release**.
2. *Choose a tag* → napíš napr. `widget-v1` → *Create new tag*.
3. Title napr. „MeteoDuo Widget v1", do *Attach binaries* pretiahni `meteoduo-widget.apk`.
4. **Publish release**. Tlačidlo na `/widget` odteraz stiahne tento APK.

> Pri ďalších verziách vytvor nový release, ale **asset pomenuj vždy** `meteoduo-widget.apk`,
> aby „latest/download" link ostal platný.

**Rýchly self-test bez podpisu:** `./gradlew assembleDebug` → nainštaluj
`app/build/outputs/apk/debug/app-debug.apk` cez USB (na distribúciu ale použi podpísaný release).

## Konfigurácia

- **Endpoint** a **predvolené mesto** sú v
  `app/src/main/java/sk/meteoduo/widget/WeatherWidgetProvider.kt`
  (`BASE`, `DEFAULT_CITY`).
- Interval obnovy: `app/src/main/res/xml/weather_widget_info.xml`
  (`updatePeriodMillis`; Android ignoruje hodnoty pod 30 min). Pre spoľahlivejšiu
  a častejšiu obnovu sa dá neskôr doplniť `WorkManager`.

## Prečo natívne a nie PWA

PWA/web nemá na Androide žiadny spôsob, ako poskytnúť vlastný samo-aktualizujúci
sa widget na domovskej obrazovke — to vie iba natívna appka. Preto je toto
samostatný Kotlin projekt, ktorý len konzumuje existujúce MeteoDuo API.

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

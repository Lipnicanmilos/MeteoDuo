# MeteoDuo — natívna Android appka a widgety

Kotlin projekt s **domovskými widgetmi** so živou predpoveďou počasia z MeteoDuo
API + jednoduchou **appkou (WebView)**. Renderuje sa **natívne** (RemoteViews,
emoji ikony) a obnovuje **sám** (Android widget update) — bez KWGT/Tasker.

## Čo obsahuje

- **Dva widgety** (v zozname widgetov pod „MeteoDuo — počasie" / „MeteoDuo — 24 h"):
  - **Aktuálne počasie** — mesto, ikona, teplota, popis, dnešné max/min, čas obnovy.
  - **24-hodinová hodinovka** — 8 stĺpcov po 3 h (čas / ikona / teplota).
- **Nastavenia widgetu** (⚙ v rohu, dostupné hocikedy — nielen pri pridaní):
  - **Vyhľadávanie obce** — našepkávač zo všetkých obcí (`GET /api/cities`),
    netreba poznať SHMÚ id.
  - **Obľúbené mestá** — pridať / vybrať / odobrať (uložené v telefóne, zdieľané).
  - **Priehľadnosť pozadia** — posuvník 0–100 %.
- **Appka (WebView)** — ikona v zásuvke aplikácií otvorí webové MeteoDuo;
  **klik na widget** ju tiež otvorí. Pri otvorení obnoví widgety.
- Android obnovuje widgety každých ~30 min (`updatePeriodMillis`).
- Predvolené mesto: Bratislava (centrum) `32737`.

## Build a distribúcia — automaticky cez GitHub Actions

Nepotrebuješ Android Studio ani lokálny toolchain. Workflow
[`.github/workflows/android.yml`](../.github/workflows/android.yml) pri každej
zmene v `android/**` (alebo ručne cez *Run workflow*):

1. na runneri (Android SDK) zbuildí **podpísaný release APK**,
2. nahrá ho ako `meteoduo-widget.apk` do releasu **`widget-latest`**.

Web stránka `/widget` ho ponúka na stiahnutie cez
`/download/meteoduo-widget.apk` (server ho proxuje z GitHubu → vlastná doména,
obchádza CDN, ktorý niektorým mobilom zamŕzal).

### Stabilný podpis (updaty bez odinštalovania)

Aby mal každý build **rovnaký podpis** (a nová verzia sa nainštalovala „cez"
starú), CI pri prvom builde vygeneruje `app/meteoduo-release.jks` (`keytool`)
a **commitne ho do repa**; ďalšie buildy ním podpisujú release. Heslo je
v `app/build.gradle.kts` (`signingConfigs.release`).

> ⚠️ Keystore aj heslo sú vo verejnom repe — vedomý kompromis pre hobby
> sideload appku. Ak by projekt išiel na **Google Play**, vygeneruj nový,
> privátny kľúč (do GitHub Secrets) a tento nepoužívaj.

## Lokálny build (voliteľné, Android Studio)

Otvor priečinok `android/` v Android Studio → **Run ▶** na telefón (USB
debugging) alebo emulátor. Z CLI: `gradle wrapper && ./gradlew assembleDebug`
(debug APK v `app/build/outputs/apk/debug/`). Release build lokálne potrebuje
`app/meteoduo-release.jks` (po prvom CI builde je už v repe).

## Konfigurácia v kóde

- **Endpoint** a **predvolené mesto**: `WeatherWidgetProvider.kt` (`BASE`,
  `DEFAULT_CITY`).
- **Interval obnovy**: `res/xml/weather_widget_info.xml` a `hourly_widget_info.xml`
  (`updatePeriodMillis`; Android ignoruje hodnoty pod 30 min).
- **Hodiny v 24 h widgete**: `HourlyWidgetProvider.STEPS`.

## Prečo natívne a nie PWA

PWA/web nemá na Androide žiadny spôsob, ako poskytnúť vlastný samo-aktualizujúci
sa widget na domovskej obrazovke — to vie iba natívna appka. Preto je toto
samostatný Kotlin projekt, ktorý len konzumuje existujúce MeteoDuo API.

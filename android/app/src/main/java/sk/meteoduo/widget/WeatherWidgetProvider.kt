package sk.meteoduo.widget

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.Context
import android.content.Intent
import android.widget.RemoteViews
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlin.math.roundToInt

/**
 * Domovský widget s aktuálnym počasím z MeteoDuo API.
 *
 * Dáta ťahá z `/api/forecast/{cityId}` (živá predpoveď yr.no). Android widget
 * obnovuje sám podľa `updatePeriodMillis` (30 min); ťuknutím sa obnoví hneď.
 * Renderuje sa natívne cez RemoteViews (žiadny PNG), emoji ikona počasia.
 */
class WeatherWidgetProvider : AppWidgetProvider() {

    override fun onUpdate(context: Context, mgr: AppWidgetManager, ids: IntArray) {
        // goAsync + vlákno: onUpdate beží na hlavnom vlákne, sieť tam nesmie
        val pending = goAsync()
        Thread {
            try {
                for (id in ids) refresh(context, mgr, id)
            } finally {
                pending.finish()
            }
        }.start()
    }

    override fun onReceive(context: Context, intent: Intent) {
        super.onReceive(context, intent)
        if (intent.action == ACTION_REFRESH) {
            val id = intent.getIntExtra(
                AppWidgetManager.EXTRA_APPWIDGET_ID,
                AppWidgetManager.INVALID_APPWIDGET_ID
            )
            if (id == AppWidgetManager.INVALID_APPWIDGET_ID) return
            val mgr = AppWidgetManager.getInstance(context)
            val pending = goAsync()
            Thread {
                try {
                    refresh(context, mgr, id)
                } finally {
                    pending.finish()
                }
            }.start()
        }
    }

    override fun onDeleted(context: Context, ids: IntArray) {
        val p = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
        for (id in ids) {
            p.remove(keyCity(id))
            p.remove(keyAlpha(id))
        }
        p.apply()
    }

    companion object {
        const val ACTION_REFRESH = "sk.meteoduo.widget.REFRESH"
        const val BASE = "https://h3r2z4x75k.execute-api.eu-central-1.amazonaws.com"
        const val DEFAULT_CITY = "32737"     // Bratislava (centrum)
        const val PREFS = "meteoduo_widget"

        const val FAVS_KEY = "favs"

        fun keyCity(id: Int) = "city_$id"
        fun keyAlpha(id: Int) = "alpha_$id"

        private fun prefs(context: Context) =
            context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

        fun prefsEdit(context: Context) = prefs(context).edit()

        fun cityFor(context: Context, id: Int): String =
            prefs(context).getString(keyCity(id), DEFAULT_CITY) ?: DEFAULT_CITY

        /** Priehľadnosť pozadia v % (0 = priehľadné, 100 = plné). */
        fun alphaFor(context: Context, id: Int): Int =
            prefs(context).getInt(keyAlpha(id), 100)

        /** Obľúbené mestá (zdieľané naprieč widgetmi), zoznam SHMÚ id. */
        fun getFavs(context: Context): List<String> =
            (prefs(context).getString(FAVS_KEY, "") ?: "")
                .split(",").filter { it.isNotBlank() }

        fun setFavs(context: Context, ids: List<String>) =
            prefs(context).edit().putString(FAVS_KEY, ids.joinToString(",")).apply()

        /** Naplní jeden widget aktuálnymi dátami. Volá sa z pozadia (nie main). */
        fun refresh(context: Context, mgr: AppWidgetManager, id: Int) {
            val views = RemoteViews(context.packageName, R.layout.widget_weather)
            val piFlags = PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE

            // ťuknutie na telo widgetu = otvor appku (WebView s MeteoDuo)
            val openApp = Intent(context, MainActivity::class.java)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            views.setOnClickPendingIntent(
                R.id.widget_root,
                PendingIntent.getActivity(context, id * 2, openApp, piFlags)
            )

            // ťuknutie na ⚙ = uprav mesto / obľúbené / priehľadnosť hocikedy
            val openCfg = Intent(context, WidgetConfigActivity::class.java)
                .putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, id)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            views.setOnClickPendingIntent(
                R.id.w_settings,
                PendingIntent.getActivity(context, id * 2 + 1, openCfg, piFlags)
            )

            // priehľadnosť pozadia (0–100 % → 0–255 alpha na ImageView)
            views.setInt(R.id.widget_bg, "setImageAlpha", alphaFor(context, id) * 255 / 100)

            try {
                val city = cityFor(context, id)
                val json = JSONObject(httpGet("$BASE/api/forecast/$city"))

                val name = json.getJSONObject("city").optString("name", "—")
                val yr = json.optJSONObject("yr")
                val hourly = yr?.optJSONArray("hourly")
                val days = yr?.optJSONArray("days")

                val now = hourly?.optJSONObject(0)
                val temp = now?.optDouble("temp", Double.NaN)
                val symbol = now?.optString("symbol")

                views.setTextViewText(R.id.w_city, name)
                views.setTextViewText(R.id.w_emoji, symbolEmoji(symbol))
                views.setTextViewText(
                    R.id.w_temp,
                    if (temp != null && !temp.isNaN()) "${temp.roundToInt()}°" else "–"
                )
                views.setTextViewText(R.id.w_condition, conditionLabel(symbol))

                val today = days?.optJSONObject(0)
                if (today != null) {
                    val hi = today.optDouble("temp_max", Double.NaN)
                    val lo = today.optDouble("temp_min", Double.NaN)
                    views.setTextViewText(
                        R.id.w_hilo,
                        "↑ ${fmt(hi)}   ↓ ${fmt(lo)}"
                    )
                } else {
                    views.setTextViewText(R.id.w_hilo, "")
                }

                val time = SimpleDateFormat("HH:mm", Locale.getDefault()).format(Date())
                views.setTextViewText(R.id.w_updated, "aktualizované $time")
            } catch (e: Exception) {
                views.setTextViewText(R.id.w_condition, "Dáta nedostupné")
                views.setTextViewText(R.id.w_updated, "ťuknutím skús znova")
            }

            mgr.updateAppWidget(id, views)
        }

        private fun fmt(t: Double): String =
            if (t.isNaN()) "–" else "${t.roundToInt()}°"

        private fun httpGet(urlStr: String): String {
            val conn = (URL(urlStr).openConnection() as HttpURLConnection).apply {
                requestMethod = "GET"
                connectTimeout = 8000
                readTimeout = 8000
                setRequestProperty("Accept", "application/json")
            }
            try {
                if (conn.responseCode !in 200..299) {
                    throw RuntimeException("HTTP ${conn.responseCode}")
                }
                return conn.inputStream.bufferedReader().use { it.readText() }
            } finally {
                conn.disconnect()
            }
        }

        /** MET Norway symbol_code -> emoji (rovnaké mapovanie ako web appka). */
        fun symbolEmoji(code: String?): String {
            if (code.isNullOrEmpty()) return "🌡️"
            val base = code.replace(Regex("_(day|night|polartwilight)$"), "")
            val pairs = listOf(
                "clearsky" to "☀️", "fair" to "🌤️", "partlycloudy" to "⛅",
                "cloudy" to "☁️", "fog" to "🌫️",
                "rainandthunder" to "⛈️", "thunder" to "⛈️",
                "sleet" to "🌨️", "snow" to "❄️",
                "rainshowers" to "🌦️", "lightrain" to "🌦️",
                "heavyrain" to "🌧️", "rain" to "🌧️"
            )
            for ((k, v) in pairs) if (base.contains(k)) return v
            return "🌡️"
        }

        /** MET Norway symbol_code -> slovenský popis. */
        fun conditionLabel(code: String?): String {
            if (code.isNullOrEmpty()) return "—"
            val base = code.replace(Regex("_(day|night|polartwilight)$"), "")
            val checks = listOf(
                "thunder" to "Búrky", "sleet" to "Dážď so snehom", "snow" to "Sneženie",
                "rainshowers" to "Prehánky", "showers" to "Prehánky", "rain" to "Dážď",
                "fog" to "Hmla", "partlycloudy" to "Polojasno", "cloudy" to "Zamračené",
                "fair" to "Skoro jasno", "clearsky" to "Jasno"
            )
            for ((k, v) in checks) if (base.contains(k)) return v
            return "—"
        }
    }
}

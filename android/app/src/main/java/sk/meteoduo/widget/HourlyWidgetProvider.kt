package sk.meteoduo.widget

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.Context
import android.content.Intent
import android.widget.RemoteViews
import org.json.JSONObject
import java.time.Instant
import java.time.ZoneId
import kotlin.math.roundToInt

/**
 * Druhý typ widgetu: predpoveď na ~24 hodín (8 stĺpcov po 3 h).
 * Zdieľa mesto / obľúbené / priehľadnosť s [WeatherWidgetProvider] (rovnaké prefs).
 */
class HourlyWidgetProvider : AppWidgetProvider() {

    override fun onUpdate(context: Context, mgr: AppWidgetManager, ids: IntArray) {
        val pending = goAsync()
        Thread {
            try {
                for (id in ids) refreshHourly(context, mgr, id)
            } finally {
                pending.finish()
            }
        }.start()
    }

    override fun onDeleted(context: Context, ids: IntArray) {
        val p = WeatherWidgetProvider.prefsEdit(context)
        for (id in ids) {
            p.remove(WeatherWidgetProvider.keyCity(id))
            p.remove(WeatherWidgetProvider.keyAlpha(id))
        }
        p.apply()
    }

    companion object {
        // hodiny od teraz, ktoré zobrazíme (3-hodinové kroky ≈ 24 h)
        private val STEPS = intArrayOf(0, 3, 6, 9, 12, 15, 18, 21)

        fun refreshHourly(context: Context, mgr: AppWidgetManager, id: Int) {
            val views = RemoteViews(context.packageName, R.layout.widget_hourly)
            val flags = PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE

            val openApp = Intent(context, MainActivity::class.java)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            views.setOnClickPendingIntent(
                R.id.widget_root, PendingIntent.getActivity(context, id * 2, openApp, flags)
            )
            val openCfg = Intent(context, WidgetConfigActivity::class.java)
                .putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, id)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            views.setOnClickPendingIntent(
                R.id.w_settings, PendingIntent.getActivity(context, id * 2 + 1, openCfg, flags)
            )
            views.setInt(
                R.id.widget_bg, "setImageAlpha",
                WeatherWidgetProvider.alphaFor(context, id) * 255 / 100
            )

            val timeIds = intArrayOf(
                R.id.wh0_time, R.id.wh1_time, R.id.wh2_time, R.id.wh3_time,
                R.id.wh4_time, R.id.wh5_time, R.id.wh6_time, R.id.wh7_time
            )
            val emojiIds = intArrayOf(
                R.id.wh0_emoji, R.id.wh1_emoji, R.id.wh2_emoji, R.id.wh3_emoji,
                R.id.wh4_emoji, R.id.wh5_emoji, R.id.wh6_emoji, R.id.wh7_emoji
            )
            val tempIds = intArrayOf(
                R.id.wh0_temp, R.id.wh1_temp, R.id.wh2_temp, R.id.wh3_temp,
                R.id.wh4_temp, R.id.wh5_temp, R.id.wh6_temp, R.id.wh7_temp
            )

            try {
                val city = WeatherWidgetProvider.cityFor(context, id)
                val json = JSONObject(
                    WeatherWidgetProvider.httpGet("${WeatherWidgetProvider.BASE}/api/forecast/$city")
                )
                views.setTextViewText(
                    R.id.wh_city, json.getJSONObject("city").optString("name", "—")
                )
                val hourly = json.optJSONObject("yr")?.optJSONArray("hourly")
                for (col in STEPS.indices) {
                    val h = hourly?.optJSONObject(STEPS[col])
                    views.setTextViewText(timeIds[col], timeLabel(h?.optString("time")))
                    views.setTextViewText(
                        emojiIds[col], WeatherWidgetProvider.symbolEmoji(h?.optString("symbol"))
                    )
                    val t = h?.optDouble("temp", Double.NaN)
                    views.setTextViewText(
                        tempIds[col],
                        if (t != null && !t.isNaN()) "${t.roundToInt()}°" else "–"
                    )
                }
            } catch (e: Exception) {
                views.setTextViewText(R.id.wh_city, "Dáta nedostupné")
            }

            mgr.updateAppWidget(id, views)
        }

        /** ISO UTC čas → lokálna hodina "HH". */
        private fun timeLabel(iso: String?): String {
            if (iso.isNullOrEmpty()) return ""
            return try {
                val h = Instant.parse(iso).atZone(ZoneId.systemDefault()).hour
                "%02d".format(h)
            } catch (e: Exception) {
                ""
            }
        }
    }
}

package sk.meteoduo.widget

import android.app.Activity
import android.appwidget.AppWidgetManager
import android.content.Context
import android.os.Bundle
import android.widget.Button
import android.widget.EditText

/**
 * Zobrazí sa pri pridaní widgetu na plochu. Používateľ zadá SHMÚ id mesta
 * (predvolene Bratislava centrum). Id sa nájde v appke MeteoDuo — na stránke
 * „Tapeta" v URL `?city=<číslo>`, alebo v adrese webu `?obec=<číslo>`.
 */
class WidgetConfigActivity : Activity() {

    private var widgetId = AppWidgetManager.INVALID_APPWIDGET_ID

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // ak používateľ odíde bez uloženia, widget sa nepridá
        setResult(RESULT_CANCELED)

        widgetId = intent?.extras?.getInt(
            AppWidgetManager.EXTRA_APPWIDGET_ID,
            AppWidgetManager.INVALID_APPWIDGET_ID
        ) ?: AppWidgetManager.INVALID_APPWIDGET_ID
        if (widgetId == AppWidgetManager.INVALID_APPWIDGET_ID) {
            finish()
            return
        }

        setContentView(R.layout.activity_config)
        val input = findViewById<EditText>(R.id.cfg_city)
        input.setText(WeatherWidgetProvider.cityFor(this, widgetId))

        findViewById<Button>(R.id.cfg_save).setOnClickListener {
            val city = input.text.toString().trim().ifEmpty {
                WeatherWidgetProvider.DEFAULT_CITY
            }
            getSharedPreferences(WeatherWidgetProvider.PREFS, Context.MODE_PRIVATE)
                .edit()
                .putString(WeatherWidgetProvider.keyCity(widgetId), city)
                .apply()

            val mgr = AppWidgetManager.getInstance(this)
            // prvé naplnenie na pozadí (sieť nesmie na hlavnom vlákne)
            Thread { WeatherWidgetProvider.refresh(this, mgr, widgetId) }.start()

            val result = android.content.Intent()
                .putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, widgetId)
            setResult(RESULT_OK, result)
            finish()
        }
    }
}

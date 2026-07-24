package sk.meteoduo.widget

import android.annotation.SuppressLint
import android.app.Activity
import android.appwidget.AppWidgetManager
import android.content.ComponentName
import android.os.Bundle
import android.webkit.WebView
import android.webkit.WebViewClient

/**
 * Appka: WebView s webovým MeteoDuo. Je to spúšťacia aktivita (ikona v zásuvke)
 * aj cieľ po ťuknutí na widget. Pri otvorení zároveň obnoví widgety.
 */
class MainActivity : Activity() {

    private lateinit var web: WebView

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        web = WebView(this)
        setContentView(web)
        with(web.settings) {
            javaScriptEnabled = true        // React SPA
            domStorageEnabled = true        // localStorage (obľúbené, téma, obec)
            cacheMode = android.webkit.WebSettings.LOAD_DEFAULT
        }
        web.webViewClient = WebViewClient() // navigáciu drž vnútri appky
        if (savedInstanceState == null) {
            web.loadUrl(WeatherWidgetProvider.BASE)
        }
    }

    override fun onResume() {
        super.onResume()
        // otvorenie appky = dobrá chvíľa obnoviť aj widgety na ploche
        val mgr = AppWidgetManager.getInstance(this)
        val currentIds = mgr.getAppWidgetIds(
            ComponentName(this, WeatherWidgetProvider::class.java)
        )
        val hourlyIds = mgr.getAppWidgetIds(
            ComponentName(this, HourlyWidgetProvider::class.java)
        )
        if (currentIds.isNotEmpty() || hourlyIds.isNotEmpty()) {
            Thread {
                for (id in currentIds) WeatherWidgetProvider.refresh(this, mgr, id)
                for (id in hourlyIds) HourlyWidgetProvider.refreshHourly(this, mgr, id)
            }.start()
        }
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (web.canGoBack()) web.goBack() else super.onBackPressed()
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        web.saveState(outState)
    }

    override fun onRestoreInstanceState(state: Bundle) {
        super.onRestoreInstanceState(state)
        web.restoreState(state)
    }
}

package sk.meteoduo.widget

import android.app.Activity
import android.appwidget.AppWidgetManager
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.ArrayAdapter
import android.widget.AutoCompleteTextView
import android.widget.Button
import android.widget.LinearLayout
import android.widget.SeekBar
import android.widget.TextView
import android.widget.Toast
import org.json.JSONArray
import java.net.HttpURLConnection
import java.net.URL

/**
 * Nastavenie widgetu pri jeho pridaní: vyhľadanie mesta/obce (zoznam z
 * `/api/cities`), obľúbené mestá (pridať/vybrať/odobrať) a priehľadnosť pozadia.
 */
class WidgetConfigActivity : Activity() {

    private var widgetId = AppWidgetManager.INVALID_APPWIDGET_ID

    private val nameToId = LinkedHashMap<String, String>()
    private val idToName = HashMap<String, String>()

    private var selectedId = WeatherWidgetProvider.DEFAULT_CITY

    private lateinit var search: AutoCompleteTextView
    private lateinit var selectedLabel: TextView
    private lateinit var favsBox: LinearLayout
    private lateinit var favsEmpty: TextView
    private lateinit var alphaBar: SeekBar
    private lateinit var alphaLabel: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setResult(RESULT_CANCELED)   // odchod bez uloženia = widget sa nepridá

        widgetId = intent?.extras?.getInt(
            AppWidgetManager.EXTRA_APPWIDGET_ID,
            AppWidgetManager.INVALID_APPWIDGET_ID
        ) ?: AppWidgetManager.INVALID_APPWIDGET_ID
        if (widgetId == AppWidgetManager.INVALID_APPWIDGET_ID) {
            finish()
            return
        }

        setContentView(R.layout.activity_config)
        search = findViewById(R.id.cfg_search)
        selectedLabel = findViewById(R.id.cfg_selected)
        favsBox = findViewById(R.id.cfg_favs)
        favsEmpty = findViewById(R.id.cfg_favs_empty)
        alphaBar = findViewById(R.id.cfg_alpha)
        alphaLabel = findViewById(R.id.cfg_alpha_label)

        selectedId = WeatherWidgetProvider.cityFor(this, widgetId)
        selectedLabel.text = getString(R.string.config_loading)

        // priehľadnosť
        alphaBar.progress = WeatherWidgetProvider.alphaFor(this, widgetId)
        updateAlphaLabel(alphaBar.progress)
        alphaBar.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(s: SeekBar?, p: Int, fromUser: Boolean) =
                updateAlphaLabel(p)
            override fun onStartTrackingTouch(s: SeekBar?) {}
            override fun onStopTrackingTouch(s: SeekBar?) {}
        })

        // výber zo šepkára
        search.setOnItemClickListener { parent, _, pos, _ ->
            val name = parent.getItemAtPosition(pos) as String
            nameToId[name]?.let { select(it, name) }
        }

        findViewById<Button>(R.id.cfg_addfav).setOnClickListener { addCurrentToFavs() }
        findViewById<Button>(R.id.cfg_save).setOnClickListener { save() }

        loadCities()
        renderFavs()   // zatiaľ z prefs (mená doplní loadCities)
    }

    private fun updateAlphaLabel(p: Int) {
        alphaLabel.text = getString(R.string.config_alpha_label) + ": $p %"
    }

    private fun select(id: String, name: String?) {
        selectedId = id
        val label = name ?: idToName[id] ?: id
        selectedLabel.text = "✓ $label"
    }

    private fun loadCities() {
        Thread {
            try {
                val body = httpGet("${WeatherWidgetProvider.BASE}/api/cities")
                val arr = JSONArray(body)
                val names = ArrayList<String>(arr.length())
                for (i in 0 until arr.length()) {
                    val o = arr.getJSONObject(i)
                    val id = o.optString("id")
                    val name = o.optString("name")
                    if (id.isEmpty() || name.isEmpty()) continue
                    nameToId[name] = id
                    idToName[id] = name
                    names.add(name)
                }
                runOnUiThread {
                    search.setAdapter(
                        ArrayAdapter(this, android.R.layout.simple_dropdown_item_1line, names)
                    )
                    select(selectedId, idToName[selectedId])
                    renderFavs()
                }
            } catch (e: Exception) {
                runOnUiThread {
                    selectedLabel.text = "✓ " + (idToName[selectedId] ?: selectedId)
                }
            }
        }.start()
    }

    private fun addCurrentToFavs() {
        val favs = WeatherWidgetProvider.getFavs(this).toMutableList()
        if (!favs.contains(selectedId)) {
            favs.add(selectedId)
            WeatherWidgetProvider.setFavs(this, favs)
            renderFavs()
        } else {
            Toast.makeText(this, "Už je medzi obľúbenými", Toast.LENGTH_SHORT).show()
        }
    }

    private fun removeFav(id: String) {
        val favs = WeatherWidgetProvider.getFavs(this).toMutableList()
        favs.remove(id)
        WeatherWidgetProvider.setFavs(this, favs)
        renderFavs()
    }

    private fun renderFavs() {
        favsBox.removeAllViews()
        val favs = WeatherWidgetProvider.getFavs(this)
        favsEmpty.visibility = if (favs.isEmpty()) View.VISIBLE else View.GONE
        val m = (8 * resources.displayMetrics.density).toInt()
        for (id in favs) {
            val row = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
            val pick = Button(this).apply {
                text = idToName[id] ?: id
                setOnClickListener { select(id, idToName[id]) }
            }
            val del = Button(this).apply {
                text = "✕"
                setOnClickListener { removeFav(id) }
            }
            row.addView(pick)
            row.addView(del)
            val lp = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            lp.marginEnd = m
            favsBox.addView(row, lp)
        }
    }

    private fun save() {
        WeatherWidgetProvider.prefsEdit(this)
            .putString(WeatherWidgetProvider.keyCity(widgetId), selectedId)
            .putInt(WeatherWidgetProvider.keyAlpha(widgetId), alphaBar.progress)
            .apply()

        val mgr = AppWidgetManager.getInstance(this)
        Thread { WeatherWidgetProvider.refresh(this, mgr, widgetId) }.start()

        setResult(RESULT_OK, Intent().putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, widgetId))
        finish()
    }

    private fun httpGet(urlStr: String): String {
        val conn = (URL(urlStr).openConnection() as HttpURLConnection).apply {
            requestMethod = "GET"
            connectTimeout = 8000
            readTimeout = 8000
        }
        try {
            return conn.inputStream.bufferedReader().use { it.readText() }
        } finally {
            conn.disconnect()
        }
    }
}

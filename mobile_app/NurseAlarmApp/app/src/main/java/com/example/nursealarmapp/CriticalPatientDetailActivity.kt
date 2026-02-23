package com.example.nursealarmapp

import android.graphics.BitmapFactory
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.speech.tts.TextToSpeech
import android.util.Log
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.example.nursealarmapp.utils.NetworkPreferences
import com.google.gson.JsonParser
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.net.HttpURLConnection
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Critical Ward patient detail screen.
 * - Camera feed always visible at top (native ImageView JPEG polling).
 * - All 6 vitals displayed live, updated every 3 s.
 * - Red alert banner + TTS voice when any vital crosses threshold.
 * - No fall-detected gate, no proximity logic.
 */
class CriticalPatientDetailActivity : AppCompatActivity() {

    companion object {
        const val EXTRA_PATIENT_ID   = "crit_patient_id"   // BAND_01 display string
        const val EXTRA_PATIENT_NAME = "crit_patient_name"
        private const val TAG = "CritWardDetail"
        private const val TTS_COOLDOWN_MS = 30_000L        // speak at most every 30 s
    }

    // Views
    private lateinit var tvName      : TextView
    private lateinit var tvId        : TextView
    private lateinit var tvLive      : TextView
    private lateinit var imgCamera   : ImageView
    private lateinit var pbCamera    : ProgressBar
    private lateinit var tvCamStatus : TextView
    private lateinit var layoutAlert : LinearLayout
    private lateinit var tvAlertMsg  : TextView
    private lateinit var tvUpdated   : TextView
    private lateinit var tvHR        : TextView
    private lateinit var tvSpO2      : TextView
    private lateinit var tvBP        : TextView
    private lateinit var tvTemp      : TextView
    private lateinit var tvRR        : TextView
    private lateinit var tvGlucose   : TextView
    // Staff
    private lateinit var tvDoctor    : TextView
    private lateinit var tvNurse     : TextView
    private lateinit var tvAssistant : TextView
    // Attended log
    private lateinit var btnAttended       : Button
    private lateinit var tvNoAttended      : TextView
    private lateinit var layoutAttHistory  : LinearLayout

    private lateinit var networkPrefs: NetworkPreferences
    private var patientBandId: String = "BAND_01"   // used as SharedPrefs key
    private var cameraJob  : Job? = null
    private var vitalsJob  : Job? = null
    private var tts        : TextToSpeech? = null
    private var ttsReady   = false
    private var lastTtsMs  = 0L
    private var backendPatientId: Int = -1       // filled from /api/patient/active
    private var frameCount = 0
    private val sdf = SimpleDateFormat("HH:mm:ss", Locale.getDefault())

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_critical_patient_detail)

        networkPrefs = NetworkPreferences.getInstance(this)

        val displayId   = intent.getStringExtra(EXTRA_PATIENT_ID)   ?: "BAND_01"
        val displayName = intent.getStringExtra(EXTRA_PATIENT_NAME) ?: "Critical Patient"
        patientBandId  = displayId

        bindViews()
        tvName.text = displayName
        tvId.text   = "Band: $displayId"

        // Init TTS
        tts = TextToSpeech(this) { status ->
            if (status == TextToSpeech.SUCCESS) {
                tts?.language = Locale.US
                ttsReady = true
            }
        }

        findViewById<Button>(R.id.btnCritBack).setOnClickListener { finish() }

        // Mark attended button
        btnAttended.setOnClickListener { markAttended() }
        // Restore any saved timestamps for this patient
        loadAttendedTimestamps()

        // Resolve numeric backend ID, then start polling
        resolveBackendId()
    }

    private fun bindViews() {
        tvName      = findViewById(R.id.tvCritName)
        tvId        = findViewById(R.id.tvCritId)
        tvLive      = findViewById(R.id.tvCritLiveBadge)
        imgCamera   = findViewById(R.id.imgCritCamera)
        pbCamera    = findViewById(R.id.pbCritCam)
        tvCamStatus = findViewById(R.id.tvCritCamStatus)
        layoutAlert = findViewById(R.id.layoutCritAlert)
        tvAlertMsg  = findViewById(R.id.tvCritAlertMsg)
        tvUpdated   = findViewById(R.id.tvCritUpdated)
        tvHR        = findViewById(R.id.tvCritHR)
        tvSpO2      = findViewById(R.id.tvCritSpO2)
        tvBP        = findViewById(R.id.tvCritBP)
        tvTemp      = findViewById(R.id.tvCritTemp)
        tvRR        = findViewById(R.id.tvCritRR)
        tvGlucose   = findViewById(R.id.tvCritGlucose)
        tvDoctor    = findViewById(R.id.tvCritDoctor)
        tvNurse     = findViewById(R.id.tvCritNurse)
        tvAssistant = findViewById(R.id.tvCritAssistant)
        btnAttended      = findViewById(R.id.btnCritAttended)
        tvNoAttended     = findViewById(R.id.tvCritNoAttended)
        layoutAttHistory = findViewById(R.id.layoutAttendedHistory)
    }

    // ── Resolve the numeric patient ID from /api/patient/active ──────────────

    private fun resolveBackendId() {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val base = networkPrefs.getBaseUrl()
                val conn = (URL("$base/api/patient/active").openConnection() as HttpURLConnection).apply {
                    connectTimeout = 4000; readTimeout = 4000
                }
                val body = conn.inputStream.bufferedReader().readText()
                conn.disconnect()
                val obj = JsonParser.parseString(body).asJsonObject
                backendPatientId = obj.get("id")?.asInt ?: -1
                val nameFromServer = obj.get("name")?.asString ?: ""
                // Parse staff assignment from emergency_contact JSON
                val emergencyRaw = obj.get("emergency_contact")?.asString ?: ""
                withContext(Dispatchers.Main) {
                    if (nameFromServer.isNotBlank()) tvName.text = nameFromServer
                    tvLive.visibility = View.VISIBLE
                    // Show staff if available
                    if (emergencyRaw.startsWith("{")) {
                        try {
                            val staffObj = JsonParser.parseString(emergencyRaw).asJsonObject
                            val doc  = staffObj.get("doctor_primary")?.asString
                            val nurse = staffObj.get("nurse_assigned")?.asString
                            val asst = staffObj.get("doctor_assistant")?.asString
                            if (!doc.isNullOrBlank())  tvDoctor.text  = "\uD83D\uDC68\u200D\u2695\uFE0F Primary Doctor: $doc"
                            if (!nurse.isNullOrBlank()) tvNurse.text  = "\uD83D\uDC69\u200D\u2695\uFE0F Assigned Nurse: $nurse"
                            if (!asst.isNullOrBlank()) {
                                tvAssistant.text = "\uD83E\uDE7A Assistant Doctor: $asst"
                                tvAssistant.visibility = View.VISIBLE
                            }
                        } catch (_: Exception) {}
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "resolveBackendId failed: ${e.message}")
            }
            withContext(Dispatchers.Main) {
                startCameraStream()
                startVitalsPolling()
            }
        }
    }

    // ── Camera ────────────────────────────────────────────────────────────────

    private fun startCameraStream() {
        val snapshotUrl = "${networkPrefs.getBaseUrl()}/snapshot"
        cameraJob = CoroutineScope(Dispatchers.IO).launch {
            var errors = 0
            while (isActive) {
                try {
                    val conn = (URL(snapshotUrl).openConnection() as HttpURLConnection).apply {
                        connectTimeout = 3000; readTimeout = 3000
                        setRequestProperty("Cache-Control", "no-cache")
                    }
                    val bytes = conn.inputStream.readBytes()
                    conn.disconnect()
                    val bmp = BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
                    if (bmp != null) {
                        errors = 0; frameCount++
                        withContext(Dispatchers.Main) {
                            imgCamera.setImageBitmap(bmp)
                            pbCamera.visibility = View.GONE
                            tvCamStatus.text = "📷 Live ● (frame $frameCount)"
                        }
                    }
                } catch (e: Exception) {
                    errors++
                    withContext(Dispatchers.Main) {
                        tvCamStatus.text = "📷 Reconnecting... ($errors)"
                    }
                    delay(1000); continue
                }
                delay(330)   // ~3 fps from cached backend frame
            }
        }
    }

    // ── Vitals ────────────────────────────────────────────────────────────────

    private fun startVitalsPolling() {
        vitalsJob = CoroutineScope(Dispatchers.IO).launch {
            while (isActive) {
                if (backendPatientId > 0) fetchAndDisplayVitals()
                delay(3000)
            }
        }
    }

    private suspend fun fetchAndDisplayVitals() {
        try {
            val base = networkPrefs.getBaseUrl()
            val conn = (URL("$base/api/patient/$backendPatientId/vitals/latest")
                .openConnection() as HttpURLConnection).apply {
                connectTimeout = 4000; readTimeout = 4000
            }
            val body = conn.inputStream.bufferedReader().readText()
            conn.disconnect()

            val v = JsonParser.parseString(body).asJsonObject
            val hr    = v.get("heart_rate")?.asDouble      ?: return
            val spo2  = v.get("spo2")?.asDouble            ?: return
            val temp  = v.get("temperature")?.asDouble     ?: return
            val bpSys = v.get("bp_systolic")?.asDouble     ?: return
            val bpDia = v.get("bp_diastolic")?.asDouble    ?: return
            val rr    = v.get("respiratory_rate")?.asDouble ?: 0.0
            val gluc  = v.get("blood_glucose")?.asDouble   ?: 0.0

            withContext(Dispatchers.Main) {
                updateVitalsUI(hr, spo2, temp, bpSys, bpDia, rr, gluc)
            }
        } catch (e: Exception) {
            Log.w(TAG, "Vitals fetch failed: ${e.message}")
        }
    }

    private fun updateVitalsUI(
        hr: Double, spo2: Double, temp: Double,
        bpSys: Double, bpDia: Double, rr: Double, gluc: Double
    ) {
        tvUpdated.text = "Updated: ${sdf.format(Date())}"
        tvHR.text      = "❤  HR: ${"%.0f".format(hr)} bpm"
        tvSpO2.text    = "🫁 SpO₂: ${"%.0f".format(spo2)} %"
        tvBP.text      = "💉 BP: ${"%.0f".format(bpSys)}/${"%.0f".format(bpDia)} mmHg"
        tvTemp.text    = "🌡 Temp: ${"%.1f".format(temp)} °C"
        tvRR.text      = "〰 RR: ${"%.0f".format(rr)} rpm"
        tvGlucose.text = "🩸 Glucose: ${"%.0f".format(gluc)} mg/dL"

        // Colour abnormal values red
        tvHR.setTextColor(
            if (hr > 100 || hr < 50) 0xFFE53935.toInt() else 0xFFEF5350.toInt()
        )
        tvSpO2.setTextColor(
            if (spo2 < 92) 0xFFE53935.toInt() else 0xFF42A5F5.toInt()
        )
        tvTemp.setTextColor(
            if (temp > 38.0 || temp < 35.0) 0xFFE53935.toInt() else 0xFFFFA726.toInt()
        )

        // Build alert message
        val alerts = mutableListOf<String>()
        if (hr > 100) alerts.add("High HR: ${"%.0f".format(hr)} bpm")
        if (hr < 50)  alerts.add("Low HR: ${"%.0f".format(hr)} bpm")
        if (spo2 < 92) alerts.add("Low SpO₂: ${"%.0f".format(spo2)}%")
        if (temp > 38.0) alerts.add("Fever: ${"%.1f".format(temp)}°C")
        if (bpSys > 140) alerts.add("High BP: ${"%.0f".format(bpSys)}/${"%.0f".format(bpDia)}")

        if (alerts.isNotEmpty()) {
            layoutAlert.visibility = View.VISIBLE
            tvAlertMsg.text = alerts.joinToString("  •  ")
            speakAlertIfCooled(tvName.text.toString(), alerts)
        } else {
            layoutAlert.visibility = View.GONE
        }
    }

    // ── TTS ───────────────────────────────────────────────────────────────────

    private fun speakAlertIfCooled(patientName: String, alerts: List<String>) {
        val now = System.currentTimeMillis()
        if (!ttsReady || now - lastTtsMs < TTS_COOLDOWN_MS) return
        lastTtsMs = now
        val msg = "Critical alert. Patient $patientName. ${alerts.joinToString(". ")}"
        tts?.speak(msg, TextToSpeech.QUEUE_FLUSH, null, "crit_alert")
    }
    // ── Attended log ─────────────────────────────────────────────────────────────

    private val attendedTimestamps = mutableListOf<String>()
    private val dateSdf = SimpleDateFormat("dd MMM yyyy  HH:mm:ss", Locale.getDefault())
    private val PREFS_NAME = "attended_log"

    private fun loadAttendedTimestamps() {
        val prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
        val saved = prefs.getString("ts_$patientBandId", "") ?: ""
        if (saved.isBlank()) return
        val items = saved.split("\n").filter { it.isNotBlank() }
        attendedTimestamps.addAll(items)
        tvNoAttended.visibility = View.GONE
        items.forEach { ts ->
            val row = TextView(this).apply {
                text = "\u2022  $ts"
                textSize = 13f
                setTextColor(0xFFCCBBFF.toInt())
                setPadding(0, 6, 0, 6)
            }
            layoutAttHistory.addView(row)   // already in correct order (newest first from save)
        }
    }

    private fun saveAttendedTimestamps() {
        val prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
        prefs.edit().putString("ts_$patientBandId", attendedTimestamps.joinToString("\n")).apply()
    }

    private fun markAttended() {
        val ts = dateSdf.format(Date())
        attendedTimestamps.add(0, ts)  // newest first
        saveAttendedTimestamps()
        tvNoAttended.visibility = View.GONE

        val row = TextView(this).apply {
            text = "\u2022  $ts"
            textSize = 13f
            setTextColor(0xFFCCBBFF.toInt())
            setPadding(0, 6, 0, 6)
        }
        layoutAttHistory.addView(row, 0)   // prepend so newest is on top
    }
    // ── Lifecycle ─────────────────────────────────────────────────────────────

    override fun onDestroy() {
        super.onDestroy()
        cameraJob?.cancel()
        vitalsJob?.cancel()
        tts?.shutdown()
    }
}

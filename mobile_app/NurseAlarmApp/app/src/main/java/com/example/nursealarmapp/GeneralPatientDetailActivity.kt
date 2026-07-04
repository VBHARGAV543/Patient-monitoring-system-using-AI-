package com.example.nursealarmapp

import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.View
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.cardview.widget.CardView
import com.example.nursealarmapp.models.GeneralPatient
import java.text.SimpleDateFormat
import java.util.*

/**
 * Shows live vitals for a General Ward patient.
 *  - Real patient: vitals come from GeneralWardManager (updated by WebSocket from backend).
 *  - Dummy patient: vitals shown from GeneralWardManager snapshot, refreshed every 2s.
 * If the patient is ALERTED, an "Attended" button is shown which clears the alert.
 */
class GeneralPatientDetailActivity : AppCompatActivity() {

    companion object {
        const val EXTRA_PATIENT_ID = "gwd_patient_id"
    }

    private lateinit var tvName: TextView
    private lateinit var tvDisease: TextView
    private lateinit var tvId: TextView
    private lateinit var tvGwdRisk: TextView
    private lateinit var tvGwdLiveBadge: TextView
    private lateinit var layoutAlertBanner: View
    private lateinit var tvHR: TextView
    private lateinit var tvSpO2: TextView
    private lateinit var tvBP: TextView
    private lateinit var tvTemp: TextView
    private lateinit var tvRR: TextView
    private lateinit var tvGlucose: TextView
    private lateinit var tvUpdated: TextView
    private lateinit var btnAttended: Button
    private lateinit var cardHistory: CardView
    private lateinit var tvHistory: TextView

    private val sdf = SimpleDateFormat("HH:mm:ss", Locale.getDefault())
    private val handler = Handler(Looper.getMainLooper())
    private lateinit var patientId: String

    private val refreshRunnable = object : Runnable {
        override fun run() {
            val p = GeneralWardManager.allPatients.find { it.id == patientId }
            if (p != null) refreshUI(p)
            handler.postDelayed(this, 2000L)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_general_patient_detail)

        patientId = intent.getStringExtra(EXTRA_PATIENT_ID) ?: run { finish(); return }

        bindViews()

        val p = GeneralWardManager.allPatients.find { it.id == patientId }
        if (p == null) { finish(); return }

        refreshUI(p)

        // Start periodic UI refresh
        handler.post(refreshRunnable)
    }

    private fun bindViews() {
        tvName          = findViewById(R.id.tvGwdName)
        tvDisease       = findViewById(R.id.tvGwdDisease)
        tvId            = findViewById(R.id.tvGwdId)
        tvGwdRisk       = findViewById(R.id.tvGwdRisk)
        tvGwdLiveBadge  = findViewById(R.id.tvGwdLiveBadge)
        layoutAlertBanner = findViewById(R.id.layoutGwdAlertBanner)
        tvHR            = findViewById(R.id.tvGwdHR)
        tvSpO2          = findViewById(R.id.tvGwdSpO2)
        tvBP            = findViewById(R.id.tvGwdBP)
        tvTemp          = findViewById(R.id.tvGwdTemp)
        tvRR            = findViewById(R.id.tvGwdRR)
        tvGlucose       = findViewById(R.id.tvGwdGlucose)
        tvUpdated       = findViewById(R.id.tvGwdUpdated)
        btnAttended     = findViewById(R.id.btnGwdAttended)
        cardHistory     = findViewById(R.id.cardGwdHistory)
        tvHistory       = findViewById(R.id.tvGwdHistory)

        findViewById<Button>(R.id.btnGwdBack).setOnClickListener { finish() }

        // Remote camera buttons — open fullscreen camera activity
        val openCamera = View.OnClickListener {
            val p = GeneralWardManager.allPatients.find { it.id == patientId }
            val intent = Intent(this, CameraStreamActivity::class.java).apply {
                putExtra("PATIENT_NAME", p?.name ?: patientId)
                putExtra("PATIENT_ID", patientId)
            }
            startActivity(intent)
        }
        findViewById<Button>(R.id.btnGwdCamera).setOnClickListener(openCamera)

        btnAttended.setOnClickListener {
            GeneralWardManager.markAttended(patientId)
            val p = GeneralWardManager.allPatients.find { it.id == patientId }
            if (p != null) refreshUI(p)
        }
    }

    private fun refreshUI(p: GeneralPatient) {
        tvName.text    = p.name
        tvDisease.text = "Condition: ${p.disease}"
        tvId.text      = "ID: ${p.id}"

        // Live badge for real patient
        tvGwdLiveBadge.visibility = if (p.isReal) View.VISIBLE else View.GONE

        // Vitals
        tvHR.text      = "❤  HR: ${p.heartRate} bpm"
        tvSpO2.text    = "🫁 SpO₂: ${p.spO2}%"
        tvBP.text      = "💉 BP: ${p.bpSystolic}/${p.bpDiastolic} mmHg"
        tvTemp.text    = "🌡 Temp: ${"%.1f".format(p.temperature)} °C"
        tvRR.text      = "〰 RR: ${p.respRate} rpm"
        tvGlucose.text = "🩸 Glucose: ${p.glucose} mg/dL"
        tvUpdated.text = "Updated: ${sdf.format(Date())}"

        // Alert state
        if (p.isAlerted) {
            layoutAlertBanner.visibility = View.VISIBLE
            tvGwdRisk.text = p.riskLevel
            tvGwdRisk.setBackgroundColor(
                if (p.riskLevel == "HIGH") 0xFFF44336.toInt() else 0xFFFF9800.toInt()
            )
            btnAttended.visibility = View.VISIBLE

            // Colour abnormal vitals red
            tvHR.setTextColor(
                if (p.heartRate > 100 || p.heartRate < 50) 0xFFE74C3C.toInt()
                else 0xFF2C3E50.toInt()
            )
            tvSpO2.setTextColor(
                if (p.spO2 < 92) 0xFFE74C3C.toInt() else 0xFF2C3E50.toInt()
            )
            tvTemp.setTextColor(
                if (p.temperature > 38.0) 0xFFE74C3C.toInt() else 0xFF2C3E50.toInt()
            )
        } else {
            layoutAlertBanner.visibility = View.GONE
            btnAttended.visibility = View.GONE
            tvHR.setTextColor(0xFF2C3E50.toInt())
            tvSpO2.setTextColor(0xFF2C3E50.toInt())
            tvTemp.setTextColor(0xFF2C3E50.toInt())
        }

        // Attendance history
        if (p.attendedTimestamps.isNotEmpty()) {
            cardHistory.visibility = View.VISIBLE
            tvHistory.text = p.attendedTimestamps
                .mapIndexed { i, ts -> "${i + 1}.  $ts" }
                .joinToString("\n")
        } else {
            cardHistory.visibility = View.GONE
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        handler.removeCallbacks(refreshRunnable)
    }
}

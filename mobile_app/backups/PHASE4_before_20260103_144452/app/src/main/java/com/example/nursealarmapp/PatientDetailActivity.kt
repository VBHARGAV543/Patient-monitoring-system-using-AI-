package com.example.nursealarmapp

import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.example.nursealarmapp.models.Patient

class PatientDetailActivity : AppCompatActivity() {

    private lateinit var tvPatientName: TextView
    private lateinit var tvPatientId: TextView
    private lateinit var tvStatus: TextView
    private lateinit var tvTimestamp: TextView
    private lateinit var tvFallStatus: TextView
    private lateinit var tvHeartRate: TextView
    private lateinit var tvSpO2: TextView
    private lateinit var tvTemperature: TextView
    private lateinit var tvBloodPressure: TextView
    private lateinit var btnCamera: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_patient_detail)

        // Initialize views
        tvPatientName = findViewById(R.id.tvDetailPatientName)
        tvPatientId = findViewById(R.id.tvDetailPatientId)
        tvStatus = findViewById(R.id.tvDetailStatus)
        tvTimestamp = findViewById(R.id.tvDetailTimestamp)
        tvFallStatus = findViewById(R.id.tvDetailFallStatus)
        tvHeartRate = findViewById(R.id.tvHeartRate)
        tvSpO2 = findViewById(R.id.tvSpO2)
        tvTemperature = findViewById(R.id.tvTemperature)
        tvBloodPressure = findViewById(R.id.tvBloodPressure)
        btnCamera = findViewById(R.id.btnCamera)

        // Get patient data from intent
        val patientId = intent.getStringExtra("PATIENT_ID") ?: ""
        val patientName = intent.getStringExtra("PATIENT_NAME") ?: ""
        val status = intent.getStringExtra("STATUS") ?: ""
        val timestamp = intent.getStringExtra("TIMESTAMP") ?: ""
        val fallDetected = intent.getBooleanExtra("FALL_DETECTED", false)
        val heartRate = intent.getIntExtra("HEART_RATE", 0)
        val spO2 = intent.getIntExtra("SPO2", 0)
        val temperature = intent.getDoubleExtra("TEMPERATURE", 0.0)
        val bpSystolic = intent.getIntExtra("BP_SYSTOLIC", 0)
        val bpDiastolic = intent.getIntExtra("BP_DIASTOLIC", 0)

        // Display patient data
        tvPatientName.text = patientName
        tvPatientId.text = "ID: $patientId"
        tvStatus.text = status
        tvTimestamp.text = "Last Update: $timestamp"
        
        if (fallDetected) {
            tvFallStatus.text = "⚠️ FALL DETECTED"
            tvFallStatus.setTextColor(getColor(R.color.gold))
            // Show camera button ONLY for alerted patients
            btnCamera.visibility = View.VISIBLE
        } else {
            tvFallStatus.text = "✓ No Fall Detected"
            tvFallStatus.setTextColor(getColor(android.R.color.holo_green_dark))
            // Hide camera button for stable/dummy patients
            btnCamera.visibility = View.GONE
        }

        // Display vitals
        tvHeartRate.text = "Heart Rate: $heartRate bpm"
        tvSpO2.text = "SpO2: $spO2 %"
        tvTemperature.text = "Temperature: ${"%.1f".format(temperature)} °C"
        tvBloodPressure.text = "Blood Pressure: $bpSystolic / $bpDiastolic mmHg"

        // Camera button - Phase 4 (laptop webcam live stream)
        btnCamera.setOnClickListener {
            Toast.makeText(this, "Opening laptop camera feed...", Toast.LENGTH_SHORT).show()
            // TODO Phase 4: Launch camera stream activity
        }

        // Back button
        findViewById<Button>(R.id.btnBack).setOnClickListener {
            finish()
        }
    }
}

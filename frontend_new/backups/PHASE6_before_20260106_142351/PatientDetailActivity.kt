package com.example.nursealarmapp

import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.View
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.cardview.widget.CardView
import com.example.nursealarmapp.utils.Constants
import kotlin.random.Random

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
    
    // Camera views
    private lateinit var cardCameraSection: CardView
    private lateinit var layoutCameraHeader: LinearLayout
    private lateinit var layoutCameraContent: LinearLayout
    private lateinit var tvCameraToggle: TextView
    private lateinit var btnExpandCamera: Button
    private lateinit var webViewCamera: WebView
    private lateinit var progressBarCamera: ProgressBar
    private lateinit var tvCameraStatus: TextView
    
    private var isCameraExpanded = false
    private var cameraLoaded = false
    private var patientName = ""
    private var patientId = ""
    
    // Auto-update vitals
    private val updateHandler = Handler(Looper.getMainLooper())
    private var currentHeartRate = 0
    private var currentSpO2 = 0
    private var currentTemperature = 0.0
    private var currentBpSystolic = 0
    private var currentBpDiastolic = 0

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
        
        // Camera views
        cardCameraSection = findViewById(R.id.cardCameraSection)
        layoutCameraHeader = findViewById(R.id.layoutCameraHeader)
        layoutCameraContent = findViewById(R.id.layoutCameraContent)
        tvCameraToggle = findViewById(R.id.tvCameraToggle)
        btnExpandCamera = findViewById(R.id.btnExpandCamera)
        webViewCamera = findViewById(R.id.webViewCamera)
        progressBarCamera = findViewById(R.id.progressBarCamera)
        tvCameraStatus = findViewById(R.id.tvCameraStatus)

        // Get patient data from intent
        patientId = intent.getStringExtra("PATIENT_ID") ?: ""
        patientName = intent.getStringExtra("PATIENT_NAME") ?: ""
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
            tvFallStatus.setTextColor(getColor(R.color.coral))
            // Show camera section ONLY for alerted patients
            cardCameraSection.visibility = View.VISIBLE
        } else {
            tvFallStatus.text = "✓ No Fall Detected"
            tvFallStatus.setTextColor(getColor(android.R.color.holo_green_dark))
            // Hide camera section for stable/dummy patients
            cardCameraSection.visibility = View.GONE
        }

        // Store initial vitals
        currentHeartRate = heartRate
        currentSpO2 = spO2
        currentTemperature = temperature
        currentBpSystolic = bpSystolic
        currentBpDiastolic = bpDiastolic
        
        // Display vitals
        updateVitalsDisplay()
        
        // Start auto-updating vitals every second
        startVitalsUpdate()

        // Setup expandable camera
        setupCamera()

        // Back button
        findViewById<Button>(R.id.btnBack).setOnClickListener {
            finish()
        }
    }
    
    private fun setupCamera() {
        // Camera header click to expand/collapse
        layoutCameraHeader.setOnClickListener {
            toggleCamera()
        }
        
        // Fullscreen camera button
        btnExpandCamera.setOnClickListener {
            val intent = Intent(this, CameraStreamActivity::class.java).apply {
                putExtra("PATIENT_NAME", patientName)
                putExtra("PATIENT_ID", patientId)
            }
            startActivity(intent)
        }
    }
    
    private fun toggleCamera() {
        isCameraExpanded = !isCameraExpanded
        
        if (isCameraExpanded) {
            // Expand camera
            layoutCameraContent.visibility = View.VISIBLE
            tvCameraToggle.text = "▲"
            
            // Load camera stream only once
            if (!cameraLoaded) {
                loadCameraStream()
                cameraLoaded = true
            }
        } else {
            // Collapse camera
            layoutCameraContent.visibility = View.GONE
            tvCameraToggle.text = "▼"
        }
    }
    
    private fun loadCameraStream() {
        progressBarCamera.visibility = View.VISIBLE
        tvCameraStatus.visibility = View.VISIBLE
        tvCameraStatus.text = "Connecting to camera..."
        
        // Configure WebView for video streaming
        webViewCamera.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            loadWithOverviewMode = true
            useWideViewPort = false
            builtInZoomControls = false
            displayZoomControls = false
            setSupportZoom(false)
            cacheMode = WebSettings.LOAD_NO_CACHE
            mediaPlaybackRequiresUserGesture = false
            mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
        }
        
        webViewCamera.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                // Hide loading after 2 seconds (stream should start loading)
                Handler(Looper.getMainLooper()).postDelayed({
                    progressBarCamera.visibility = View.GONE
                    tvCameraStatus.visibility = View.GONE
                }, 2000)
            }
            
            override fun onReceivedError(
                view: WebView?,
                errorCode: Int,
                description: String?,
                failingUrl: String?
            ) {
                super.onReceivedError(view, errorCode, description, failingUrl)
                progressBarCamera.visibility = View.GONE
                tvCameraStatus.visibility = View.VISIBLE
                tvCameraStatus.text = "Camera connection failed\n⟳ Tap to retry"
                tvCameraStatus.setOnClickListener {
                    cameraLoaded = false
                    loadCameraStream()
                }
            }
        }
        
        webViewCamera.webChromeClient = WebChromeClient()
        
        // Load the camera stream with HTML wrapper for better compatibility
        val streamUrl = "${Constants.BASE_URL}/stream"
        val htmlData = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body { margin: 0; padding: 0; background: #000; display: flex; justify-content: center; align-items: center; }
                    img { max-width: 100%; height: auto; }
                </style>
            </head>
            <body>
                <img src="$streamUrl" alt="Camera Stream" />
            </body>
            </html>
        """.trimIndent()
        
        webViewCamera.loadDataWithBaseURL(Constants.BASE_URL, htmlData, "text/html", "UTF-8", null)
    }
    
    private fun startVitalsUpdate() {
        val updateRunnable = object : Runnable {
            override fun run() {
                // Simulate realistic vital changes
                currentHeartRate += Random.nextInt(-2, 3) // ±2 bpm variation
                currentHeartRate = currentHeartRate.coerceIn(60, 100)
                
                currentSpO2 += Random.nextInt(-1, 2) // ±1% variation
                currentSpO2 = currentSpO2.coerceIn(95, 100)
                
                currentTemperature += Random.nextDouble(-0.1, 0.1) // ±0.1°C variation
                currentTemperature = currentTemperature.coerceIn(36.5, 37.5)
                
                currentBpSystolic += Random.nextInt(-2, 3)
                currentBpSystolic = currentBpSystolic.coerceIn(110, 130)
                
                currentBpDiastolic += Random.nextInt(-1, 2)
                currentBpDiastolic = currentBpDiastolic.coerceIn(70, 85)
                
                // Update UI
                updateVitalsDisplay()
                
                // Schedule next update in 1 second
                updateHandler.postDelayed(this, 1000)
            }
        }
        
        // Start the update cycle
        updateHandler.postDelayed(updateRunnable, 1000)
    }
    
    private fun updateVitalsDisplay() {
        tvHeartRate.text = "Heart Rate: $currentHeartRate bpm"
        tvSpO2.text = "SpO2: $currentSpO2 %"
        tvTemperature.text = "Temperature: ${"%.1f".format(currentTemperature)} °C"
        tvBloodPressure.text = "Blood Pressure: $currentBpSystolic / $currentBpDiastolic mmHg"
    }
    
    override fun onDestroy() {
        super.onDestroy()
        // Stop vitals updates
        updateHandler.removeCallbacksAndMessages(null)
        // Clean up WebView
        webViewCamera.destroy()
    }
}

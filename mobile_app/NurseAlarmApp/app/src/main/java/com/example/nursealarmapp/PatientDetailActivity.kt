package com.example.nursealarmapp

import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
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
import com.example.nursealarmapp.network.ApiService
import com.example.nursealarmapp.utils.NetworkPreferences
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

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
    private lateinit var apiService: ApiService
    private lateinit var networkPrefs: NetworkPreferences
    private var currentHeartRate = 0.0
    private var currentSpO2 = 0.0
    private var currentTemperature = 0.0
    private var currentBpSystolic = 0.0
    private var currentBpDiastolic = 0.0
    private var currentRespRate = 0.0
    private var currentGlucose = 0.0

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_patient_detail)

        // Initialize API Service
        apiService = ApiService(this)
        networkPrefs = NetworkPreferences.getInstance(this)
        
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
        } else {
            tvFallStatus.text = "✓ No Fall Detected"
            tvFallStatus.setTextColor(getColor(android.R.color.holo_green_dark))
        }
        // Camera always visible — nurse monitors patient remotely when not in proximity
        cardCameraSection.visibility = View.VISIBLE

        // Store initial vitals
        currentHeartRate = heartRate.toDouble()
        currentSpO2 = spO2.toDouble()
        currentTemperature = temperature
        currentBpSystolic = bpSystolic.toDouble()
        currentBpDiastolic = bpDiastolic.toDouble()
        
        // Display vitals
        updateVitalsDisplay()
        
        // Start auto-updating vitals from API every 3 seconds
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
        
        // Auto-expand camera immediately for remote monitoring demo
        toggleCamera()
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
        
        // Load the backend JS-polling camera page.
        // Android WebView cannot render MJPEG (multipart/x-mixed-replace) streams.
        // /camera serves an HTML page that polls /snapshot every 300 ms instead.
        val cameraPageUrl = "${networkPrefs.getBaseUrl()}/camera"
        webViewCamera.loadUrl(cameraPageUrl)
    }
    
    private fun startVitalsUpdate() {
        val updateRunnable = object : Runnable {
            override fun run() {
                // Fetch real vitals from API
                fetchLatestVitals()
                
                // Schedule next update in 3 seconds
                updateHandler.postDelayed(this, 3000)
            }
        }
        
        // Start the update cycle
        updateHandler.postDelayed(updateRunnable, 3000)
    }
    
    private fun fetchLatestVitals() {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val result = apiService.getLatestVitals(patientId)
                result.onSuccess { vitalsJson ->
                    // Extract vitals from JSON
                    val vitals = vitalsJson.getAsJsonObject("vitals")
                    
                    currentHeartRate = vitals.get("HR")?.asDouble ?: currentHeartRate
                    currentSpO2 = vitals.get("SpO2")?.asDouble ?: currentSpO2
                    currentTemperature = vitals.get("Temp")?.asDouble ?: currentTemperature
                    currentBpSystolic = vitals.get("BP_sys")?.asDouble ?: currentBpSystolic
                    currentBpDiastolic = vitals.get("BP_dia")?.asDouble ?: currentBpDiastolic
                    currentRespRate = vitals.get("RR")?.asDouble ?: currentRespRate
                    currentGlucose = vitals.get("Glucose")?.asDouble ?: currentGlucose
                    
                    // Update UI on main thread
                    withContext(Dispatchers.Main) {
                        updateVitalsDisplay()
                    }
                }.onFailure { error ->
                    Log.e("PatientDetail", "Failed to fetch vitals: ${error.message}")
                }
            } catch (e: Exception) {
                Log.e("PatientDetail", "Error fetching vitals: ${e.message}")
            }
        }
    }
    
    private fun updateVitalsDisplay() {
        tvHeartRate.text = "Heart Rate: ${"%.0f".format(currentHeartRate)} bpm"
        tvSpO2.text = "SpO2: ${"%.0f".format(currentSpO2)} %"
        tvTemperature.text = "Temperature: ${"%.1f".format(currentTemperature)} °C"
        tvBloodPressure.text = "Blood Pressure: ${"%.0f".format(currentBpSystolic)} / ${"%.0f".format(currentBpDiastolic)} mmHg"
    }
    
    override fun onDestroy() {
        super.onDestroy()
        // Stop vitals updates
        updateHandler.removeCallbacksAndMessages(null)
        // Clean up WebView
        webViewCamera.destroy()
    }
}

package com.example.nursealarmapp

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.speech.tts.TextToSpeech
import android.view.MenuItem
import android.widget.ImageButton
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.widget.SwitchCompat
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.core.view.GravityCompat
import androidx.drawerlayout.widget.DrawerLayout
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.example.nursealarmapp.adapters.PatientAdapter
import com.example.nursealarmapp.models.GeneralWardEvent
import com.example.nursealarmapp.models.Patient
import com.example.nursealarmapp.network.ApiService
import com.example.nursealarmapp.network.WebSocketManager
import com.example.nursealarmapp.services.AlertNotificationService
import com.example.nursealarmapp.utils.NetworkPreferences
import com.example.nursealarmapp.utils.NotificationHelper
import com.example.nursealarmapp.utils.VibrationHelper
import com.google.android.material.navigation.NavigationView
import com.google.gson.JsonParser
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.net.HttpURLConnection
import java.net.URL
import java.text.SimpleDateFormat
import java.util.*
import android.widget.LinearLayout
import com.example.nursealarmapp.adapters.AdmittedPatientAdapter
import com.example.nursealarmapp.adapters.AlertedPatientAdapter

class MainActivity : AppCompatActivity(), NavigationView.OnNavigationItemSelectedListener {

    private val PERMISSION_REQUEST_CODE = 123
    private lateinit var drawerLayout: DrawerLayout
    private lateinit var navigationView: NavigationView
    private lateinit var recyclerView: RecyclerView
    private lateinit var patientAdapter: PatientAdapter
    private lateinit var webSocketManager: WebSocketManager
    private lateinit var apiService: ApiService
    private lateinit var vibrationHelper: VibrationHelper
    private lateinit var notificationHelper: NotificationHelper
    private lateinit var tvProximityStatus: TextView
    private lateinit var switchProximity: SwitchCompat

    private val patients = mutableListOf<Patient>()
    private var currentWardType = "RECORDS" // RECORDS, GENERAL_ADMITTED, GENERAL_ALERTED, CRITICAL

    // Critical ward background alert engine
    private var critAlertJob: Job? = null
    private var critTts: TextToSpeech? = null
    private var critTtsReady = false
    private var critTtsLastMs = 0L
    private val CRIT_TTS_COOLDOWN = 30_000L

    // Proximity / nurse session state
    private var nurseSessionId: String? = null
    private var isNearPatient = false
    private var proximityJob: Job? = null

    // Auto-update timestamps
    private val updateHandler = Handler(Looper.getMainLooper())
    private val sdf = SimpleDateFormat("HH:mm:ss", Locale.getDefault())

    private val refreshRunnable = Runnable {
        if (currentWardType == "RECORDS") {
            loadDischargedPatients()
        }
    }
    
    // General ward adapters & proximity bar layout
    private lateinit var admittedAdapter: AdmittedPatientAdapter
    private lateinit var alertedAdapter: AlertedPatientAdapter
    private lateinit var criticalAdapter: AdmittedPatientAdapter
    private val criticalPatients: MutableList<com.example.nursealarmapp.models.GeneralPatient> = mutableListOf()
    private lateinit var proximityBarLayout: LinearLayout

    // Alert notification service
    private lateinit var alertService: AlertNotificationService

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Request permissions
        requestPermissions()

        // Initialize WebSocket
        webSocketManager = WebSocketManager(this)
        
        // Initialize API Service
        apiService = ApiService(this)
        
        // Initialize Alert Service
        alertService = AlertNotificationService(this)

        // Initialize views
        drawerLayout = findViewById(R.id.drawerLayout)
        navigationView = findViewById(R.id.navigationView)
        recyclerView = findViewById(R.id.recyclerViewPatients)
        
        // Setup navigation drawer
        navigationView.setNavigationItemSelectedListener(this)
        
        // Setup menu button
        findViewById<ImageButton>(R.id.btnMenu).setOnClickListener {
            drawerLayout.openDrawer(GravityCompat.START)
        }

        // Proximity UI
        tvProximityStatus = findViewById(R.id.tvProximityStatus)
        switchProximity = findViewById(R.id.switchProximity)
        switchProximity.setOnCheckedChangeListener { _, checked ->
            isNearPatient = checked
            updateProximityUI()
            if (checked) startProximityReporting() else stopProximityReporting()
        }

        // Helpers
        vibrationHelper = VibrationHelper(this)
        notificationHelper = NotificationHelper(this)

        // Setup RecyclerView
        recyclerView.layoutManager = LinearLayoutManager(this)
        patientAdapter = PatientAdapter(patients) { patient ->
            onPatientClick(patient)
        }
        recyclerView.adapter = patientAdapter

        // ── General ward setup ────────────────────────────────────────────
        admittedAdapter = AdmittedPatientAdapter(emptyList()) { p -> openGeneralPatientDetail(p) }
        alertedAdapter = AlertedPatientAdapter(
            emptyList(),
            { p -> openGeneralPatientDetail(p) },
            { p -> onPatientAttended(p) },
            { p -> openCameraStream(p.name) }
        )
        criticalAdapter = AdmittedPatientAdapter(emptyList()) { p -> openCriticalPatientDetail(p) }
        proximityBarLayout = findViewById(R.id.proximityBar)
        // Wire list-change callback so WebSocket updates refresh the visible list
        GeneralWardManager.onListChanged = { runOnUiThread { refreshCurrentView() } }
        updateProximityBarVisibility()

        // Load records by default
        loadDischargedPatients()

        // Start auto-updating timestamps
        startTimestampUpdate()

        // Init TTS for critical ward background alerts
        critTts = TextToSpeech(this) { status ->
            if (status == TextToSpeech.SUCCESS) {
                critTts?.language = Locale.US
                critTtsReady = true
            }
        }

        // Register nurse session and connect WebSocket
        registerNurseAndConnect()
    }

    // ── Proximity ──────────────────────────────────────────────────────────

    private fun registerNurseAndConnect() {
        lifecycleScope.launch {
            val result = apiService.registerNurse("${Build.MANUFACTURER} ${Build.MODEL}")
            result.onSuccess { id ->
                nurseSessionId = id
                webSocketManager.connectGeneral(id)
                observeAlarmEvents()
            }
            // Silent failure — proximity just won't work until reconnect
        }
    }

    private fun observeAlarmEvents() {
        lifecycleScope.launch {
            webSocketManager.generalWardEventFlow.collect { event ->
                when (event) {
                    is GeneralWardEvent.AlarmTriggered -> handleAlarm(event)
                    is GeneralWardEvent.VitalsUpdate -> handleVitalsUpdate(event)
                    else -> {}
                }
            }
        }
    }

    private fun handleAlarm(event: GeneralWardEvent.AlarmTriggered) {
        runOnUiThread {
            // Critical ward alarms handled by CriticalPatientDetailActivity — skip here
            if (event.patient_type == "CRITICAL") return@runOnUiThread

            if (event.vitals != null) {
                GeneralWardManager.onAlarmTriggered(
                    backendPatientId = event.patient_id,
                    patientName = event.patient_name,
                    hr = event.vitals.HR?.toInt() ?: 72,
                    spo2 = event.vitals.SpO2?.toInt() ?: 98,
                    temp = event.vitals.Temp ?: 36.8,
                    bpSys = event.vitals.BP_sys?.toInt() ?: 120,
                    bpDia = event.vitals.BP_dia?.toInt() ?: 80,
                    rr = event.vitals.RR?.toInt() ?: 16,
                    glucose = event.vitals.Glucose?.toInt() ?: 100,
                    risk = "HIGH"
                )
            }
            if (isNearPatient) {
                vibrationHelper.vibrateGeneral()
                tvProximityStatus.text = "⚡ ALERT: ${event.patient_name} — vibrating (nurse nearby)"
                updateHandler.postDelayed({ updateProximityUI() }, 5000)
            } else {
                vibrationHelper.vibrateAlarm()
                notificationHelper.showGeneralWardAlarm(event.patient_name)
            }
        }
    }

    private fun startProximityReporting() {
        proximityJob?.cancel()
        proximityJob = lifecycleScope.launch {
            while (isNearPatient) {
                nurseSessionId?.let { id ->
                    apiService.sendProximityUpdate(id, listOf("BAND_01"))
                }
                delay(5000)
            }
        }
    }

    private fun stopProximityReporting() {
        proximityJob?.cancel()
        nurseSessionId?.let { id ->
            lifecycleScope.launch {
                apiService.sendProximityUpdate(id, emptyList())
            }
        }
    }

    private fun updateProximityUI() {
        if (isNearPatient) {
            tvProximityStatus.text = "● Nurse Mode: Near patient (vibrate only)"
            tvProximityStatus.setTextColor(0xFF4CAF50.toInt()) // green
        } else {
            tvProximityStatus.text = "○ Nurse Mode: Away from patient"
            tvProximityStatus.setTextColor(0xFFFFCC00.toInt()) // yellow
        }
    }

    private fun loadMockPatients() {
        val currentTime = sdf.format(Date())
        
        patients.clear()
        // Band patient - CRITICAL WARD - starts STABLE, will become ALERT after 5 seconds
        patients.add(Patient("BAND_001", "Patient 1 (Band)", "STABLE", currentTime, false, 
            heartRate = 75, spO2 = 97, temperature = 36.8, bpSystolic = 120, bpDiastolic = 80))
        
        // Dummy patients - GENERAL WARD - NEVER alerted, always STABLE with normal vitals
        patients.add(Patient("P002", "Patient 2 (Dummy)", "STABLE", currentTime, false,
            heartRate = 72, spO2 = 98, temperature = 36.8, bpSystolic = 120, bpDiastolic = 80))
        patients.add(Patient("P003", "Patient 3 (Dummy)", "STABLE", currentTime, false,
            heartRate = 68, spO2 = 97, temperature = 36.5, bpSystolic = 118, bpDiastolic = 78))
        patients.add(Patient("P004", "Patient 4 (Dummy)", "STABLE", currentTime, false,
            heartRate = 75, spO2 = 99, temperature = 36.9, bpSystolic = 122, bpDiastolic = 82))
        patients.add(Patient("P005", "Patient 5 (Dummy)", "STABLE", currentTime, false,
            heartRate = 70, spO2 = 98, temperature = 36.6, bpSystolic = 115, bpDiastolic = 75))
        patients.add(Patient("P006", "Patient 6 (Dummy)", "STABLE", currentTime, false,
            heartRate = 78, spO2 = 96, temperature = 37.0, bpSystolic = 125, bpDiastolic = 85))
        patients.add(Patient("P007", "Patient 7 (Dummy)", "STABLE", currentTime, false,
            heartRate = 65, spO2 = 99, temperature = 36.7, bpSystolic = 110, bpDiastolic = 72))
        patients.add(Patient("P008", "Patient 8 (Dummy)", "STABLE", currentTime, false,
            heartRate = 73, spO2 = 97, temperature = 36.8, bpSystolic = 119, bpDiastolic = 79))
        patients.add(Patient("P009", "Patient 9 (Dummy)", "STABLE", currentTime, false,
            heartRate = 69, spO2 = 98, temperature = 36.5, bpSystolic = 116, bpDiastolic = 76))
        patients.add(Patient("P010", "Patient 10 (Dummy)", "STABLE", currentTime, false,
            heartRate = 76, spO2 = 99, temperature = 36.9, bpSystolic = 123, bpDiastolic = 81))
        
        patientAdapter.updatePatients(patients)
    }
    
    private fun startTimestampUpdate() {
        val updateRunnable = object : Runnable {
            override fun run() {
                // Update timestamps for all patients
                val currentTime = sdf.format(Date())
                patients.forEach { patient ->
                    patient.timestamp = currentTime
                }
                
                // Notify adapter of changes
                patientAdapter.notifyDataSetChanged()
                
                // Schedule next update in 1 second
                updateHandler.postDelayed(this, 1000)
            }
        }
        
        // Start the update cycle
        updateHandler.postDelayed(updateRunnable, 1000)
    }
    

    
    private fun observeWebSocket() {
        // Placeholder for WebSocket observation
        // Will be connected to backend in future when backend provides patient list endpoint
        lifecycleScope.launch {
            // webSocketManager.generalWardEventFlow.collect { event ->
            //     // Update patient list based on real-time events
            // }
        }
    }

    // ── General Ward helpers ──────────────────────────────────────────────

    private fun openGeneralPatientDetail(patient: com.example.nursealarmapp.models.GeneralPatient) {
        val intent = Intent(this, GeneralPatientDetailActivity::class.java).apply {
            putExtra(GeneralPatientDetailActivity.EXTRA_PATIENT_ID, patient.id)
        }
        startActivity(intent)
    }

    private fun openCriticalPatientDetail(patient: com.example.nursealarmapp.models.GeneralPatient) {
        val intent = Intent(this, CriticalPatientDetailActivity::class.java).apply {
            putExtra(CriticalPatientDetailActivity.EXTRA_PATIENT_ID, patient.id)
            putExtra(CriticalPatientDetailActivity.EXTRA_PATIENT_NAME, patient.name)
        }
        startActivity(intent)
    }

    private fun openCameraStream(patientName: String) {
        val intent = Intent(this, CameraStreamActivity::class.java).apply {
            putExtra("PATIENT_NAME", patientName)
        }
        startActivity(intent)
    }

    private fun onPatientAttended(patient: com.example.nursealarmapp.models.GeneralPatient) {
        GeneralWardManager.markAttended(patient.id)
        refreshCurrentView()
    }

    private fun handleVitalsUpdate(event: GeneralWardEvent.VitalsUpdate) {
        GeneralWardManager.onVitalsUpdate(
            backendPatientId = event.patient_id,
            hr = event.vitals.HR?.toInt() ?: 72,
            spo2 = event.vitals.SpO2?.toInt() ?: 98,
            temp = event.vitals.Temp ?: 36.8,
            bpSys = event.vitals.BP_sys?.toInt() ?: 120,
            bpDia = event.vitals.BP_dia?.toInt() ?: 80,
            rr = event.vitals.RR?.toInt() ?: 16,
            glucose = event.vitals.Glucose?.toInt() ?: 100
        )
    }

    private fun refreshCurrentView() {
        when (currentWardType) {
            "GENERAL_ADMITTED" -> admittedAdapter.update(GeneralWardManager.admittedList())
            "GENERAL_ALERTED"  -> alertedAdapter.update(GeneralWardManager.alertedList())
            "CRITICAL"         -> criticalAdapter.update(criticalPatients.toList())
        }
    }

    private fun updateProximityBarVisibility() {
        val inGeneralWard = currentWardType.startsWith("GENERAL")
        proximityBarLayout.visibility =
            if (inGeneralWard) android.view.View.VISIBLE else android.view.View.GONE
    }

    override fun onDestroy() {
        super.onDestroy()
        updateHandler.removeCallbacksAndMessages(null)
        proximityJob?.cancel()
        critAlertJob?.cancel()
        critTts?.shutdown()
        stopProximityReporting()
        webSocketManager.disconnect()
    }

    private fun onPatientClick(patient: Patient) {
        // Critical ward patients (BAND_) → dedicated screen with camera + vitals
        if (patient.patientId.startsWith("BAND_") || currentWardType == "CRITICAL") {
            val intent = Intent(this, CriticalPatientDetailActivity::class.java).apply {
                putExtra(CriticalPatientDetailActivity.EXTRA_PATIENT_ID, patient.patientId)
                putExtra(CriticalPatientDetailActivity.EXTRA_PATIENT_NAME, patient.name)
            }
            startActivity(intent)
            return
        }
        val intent = Intent(this, PatientDetailActivity::class.java).apply {
            putExtra("PATIENT_ID", patient.patientId)
            putExtra("PATIENT_NAME", patient.name)
            putExtra("STATUS", patient.status)
            putExtra("TIMESTAMP", patient.timestamp)
            putExtra("FALL_DETECTED", patient.fallDetected)
            putExtra("HEART_RATE", patient.heartRate)
            putExtra("SPO2", patient.spO2)
            putExtra("TEMPERATURE", patient.temperature)
            putExtra("BP_SYSTOLIC", patient.bpSystolic)
            putExtra("BP_DIASTOLIC", patient.bpDiastolic)
        }
        startActivity(intent)
    }

    override fun onNavigationItemSelected(item: MenuItem): Boolean {
        // Cancel critical alert polling whenever we navigate away
        critAlertJob?.cancel()
        when (item.itemId) {
            R.id.nav_records -> {
                currentWardType = "RECORDS"
                loadDischargedPatients()
            }
            R.id.nav_general_admitted -> {
                currentWardType = "GENERAL_ADMITTED"
                filterGeneralWardPatients()
            }
            R.id.nav_general_alerted -> {
                currentWardType = "GENERAL_ALERTED"
                filterAlertedPatients()
            }
            R.id.nav_critical_patients -> {
                currentWardType = "CRITICAL"
                filterCriticalWardPatients()
            }
            R.id.nav_network_settings -> {
                startActivity(Intent(this, NetworkSettingsActivity::class.java))
            }
        }
        
        updateProximityBarVisibility()
        drawerLayout.closeDrawer(GravityCompat.START)
        return true
    }
    
    private fun loadDischargedPatients() {
        lifecycleScope.launch {
            try {
                val result = apiService.getDischargedPatients()
                val currentTime = sdf.format(Date())
                
                result.onSuccess { patientsList ->
                    patients.clear()
                    
                    patientsList.forEach { patientJson ->
                        val id = patientJson.get("id")?.asInt?.toString() ?: "Unknown"
                        val name = patientJson.get("name")?.asString ?: "Unknown"
                        val problem = patientJson.get("problem")?.asString ?: "Unknown"
                        
                        patients.add(Patient(
                            id, name, "DISCHARGED - $problem", currentTime, false,
                            heartRate = 0, spO2 = 0, temperature = 0.0,
                            bpSystolic = 0, bpDiastolic = 0
                        ))
                    }
                    
                    runOnUiThread {
                        patientAdapter.updatePatients(patients)
                        // Re-attach patientAdapter in case we switched away to General Ward adapters
                        recyclerView.adapter = patientAdapter
                    }
                }
                
                result.onFailure {
                    runOnUiThread {
                        patients.clear()
                        patientAdapter.updatePatients(patients)
                        recyclerView.adapter = patientAdapter
                    }
                }
            } catch (e: Exception) {
                // silently ignore load errors
            }
        }
        
        // Auto-refresh every 10 seconds (only while on RECORDS tab)
        updateHandler.removeCallbacks(refreshRunnable)
        updateHandler.postDelayed(refreshRunnable, 10000)
    }
    
    private fun filterGeneralWardPatients() {
        // Fetch admitted GENERAL patients from backend, then show in admitted adapter
        GeneralWardManager.loadFromBackend(
            apiService = apiService,
            scope = lifecycleScope,
            onDone = {
                runOnUiThread {
                    admittedAdapter.update(GeneralWardManager.admittedList())
                    recyclerView.adapter = admittedAdapter
                }
            }
        )
        // Show current cached list immediately while fetch is in progress
        admittedAdapter.update(GeneralWardManager.admittedList())
        recyclerView.adapter = admittedAdapter
    }
    
    private fun filterCriticalWardPatients() {
        // Fetch admitted CRITICAL patients from backend
        criticalPatients.clear()
        criticalAdapter.update(emptyList())
        recyclerView.adapter = criticalAdapter

        lifecycleScope.launch {
            try {
                val result = apiService.getAdmittedPatients(patientType = "CRITICAL")
                result.onSuccess { jsonList ->
                    criticalPatients.clear()
                    jsonList.forEachIndexed { idx, obj ->
                        val id      = obj.get("id")?.asInt?.toString() ?: "?"
                        val name    = obj.get("name")?.asString    ?: "Unknown"
                        val problem = obj.get("problem")?.asString ?: "Critical condition"
                        val bandId  = obj.get("band_id")?.asString ?: "BAND_01"
                        val roomNum = idx + 1
                        criticalPatients.add(
                            com.example.nursealarmapp.models.GeneralPatient(
                                id      = bandId,
                                name    = name,
                                disease = "\uD83D\uDD34 ICU Ward  \u2022  Critical Room $roomNum  |  $problem",
                                isReal  = true
                            )
                        )
                    }
                    runOnUiThread { criticalAdapter.update(criticalPatients.toList()) }
                }
            } catch (e: Exception) { /* silent */ }
        }

        // Start background TTS alert polling while on this screen
        startCriticalAlertPolling()
    }

    private fun startCriticalAlertPolling() {
        critAlertJob?.cancel()
        critAlertJob = lifecycleScope.launch {
            val prefs = NetworkPreferences.getInstance(this@MainActivity)
            while (true) {
                try {
                    // 1. Get active patient id
                    val conn1 = (URL("${prefs.getBaseUrl()}/api/patient/active")
                        .openConnection() as HttpURLConnection).apply {
                        connectTimeout = 4000; readTimeout = 4000 }
                    val body1 = withContext(Dispatchers.IO) { conn1.inputStream.bufferedReader().readText() }
                    conn1.disconnect()
                    val obj1  = JsonParser.parseString(body1).asJsonObject
                    val pid   = obj1.get("id")?.asInt ?: -1
                    val pname = obj1.get("name")?.asString ?: "Patient"
                    val ptype = obj1.get("patient_type")?.asString ?: ""
                    if (pid > 0 && ptype == "CRITICAL") {
                        // 2. Get latest vitals
                        val conn2 = (URL("${prefs.getBaseUrl()}/api/patient/$pid/vitals/latest")
                            .openConnection() as HttpURLConnection).apply {
                            connectTimeout = 4000; readTimeout = 4000 }
                        val body2 = withContext(Dispatchers.IO) { conn2.inputStream.bufferedReader().readText() }
                        conn2.disconnect()
                        val v = JsonParser.parseString(body2).asJsonObject
                        val hr    = v.get("heart_rate")?.asDouble  ?: 72.0
                        val spo2  = v.get("spo2")?.asDouble        ?: 98.0
                        val temp  = v.get("temperature")?.asDouble ?: 36.8
                        val bpSys = v.get("bp_systolic")?.asDouble ?: 120.0
                        // 3. Check thresholds and speak
                        val alerts = mutableListOf<String>()
                        if (hr > 100) alerts.add("High heart rate ${"%,.0f".format(hr)} bpm")
                        if (hr < 50)  alerts.add("Low heart rate ${"%,.0f".format(hr)} bpm")
                        if (spo2 < 92) alerts.add("Low SpO 2 ${"%,.0f".format(spo2)} percent")
                        if (temp > 38.0) alerts.add("Fever ${"%,.1f".format(temp)} degrees")
                        if (bpSys > 140) alerts.add("High blood pressure")
                        if (alerts.isNotEmpty()) {
                            val now = System.currentTimeMillis()
                            if (critTtsReady && now - critTtsLastMs >= CRIT_TTS_COOLDOWN) {
                                critTtsLastMs = now
                                val msg = "Critical alert. Patient $pname. ${alerts.joinToString(". ")}"
                                withContext(Dispatchers.Main) {
                                    critTts?.speak(msg, TextToSpeech.QUEUE_FLUSH, null, "crit_list")
                                }
                            }
                        }
                    }
                } catch (_: Exception) {}
                delay(15_000)
            }
        }
    }
    
    private fun filterAlertedPatients() {
        alertedAdapter.update(GeneralWardManager.alertedList())
        recyclerView.adapter = alertedAdapter
    }

    private fun requestPermissions() {
        val permissions = mutableListOf<String>()

        // Bluetooth permissions
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            permissions.add(Manifest.permission.BLUETOOTH_SCAN)
            permissions.add(Manifest.permission.BLUETOOTH_CONNECT)
        }

        // Location permissions (required for BLE)
        permissions.add(Manifest.permission.ACCESS_FINE_LOCATION)
        permissions.add(Manifest.permission.ACCESS_COARSE_LOCATION)

        // Notification permission (Android 13+)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions.add(Manifest.permission.POST_NOTIFICATIONS)
        }

        // Check which permissions are not granted
        val permissionsToRequest = permissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }

        if (permissionsToRequest.isNotEmpty()) {
            ActivityCompat.requestPermissions(
                this,
                permissionsToRequest.toTypedArray(),
                PERMISSION_REQUEST_CODE
            )
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)

        if (requestCode == PERMISSION_REQUEST_CODE) {
            val allGranted = grantResults.all { it == PackageManager.PERMISSION_GRANTED }
            if (!allGranted) {
                Toast.makeText(this, "Some permissions denied. App may not work properly.", Toast.LENGTH_LONG).show()
            }
        }
    }

    override fun onBackPressed() {
        if (drawerLayout.isDrawerOpen(GravityCompat.START)) {
            drawerLayout.closeDrawer(GravityCompat.START)
        } else {
            super.onBackPressed()
        }
    }
}

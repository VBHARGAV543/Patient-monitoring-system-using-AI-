package com.example.nursealarmapp

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.MenuItem
import android.widget.ImageButton
import android.widget.Toast
import androidx.appcompat.app.ActionBarDrawerToggle
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.core.view.GravityCompat
import androidx.drawerlayout.widget.DrawerLayout
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.example.nursealarmapp.adapters.PatientAdapter
import com.example.nursealarmapp.models.Patient
import com.example.nursealarmapp.network.WebSocketManager
import com.example.nursealarmapp.services.AlertNotificationService
import com.google.android.material.navigation.NavigationView
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.*

class MainActivity : AppCompatActivity(), NavigationView.OnNavigationItemSelectedListener {

    private val PERMISSION_REQUEST_CODE = 123
    private lateinit var drawerLayout: DrawerLayout
    private lateinit var navigationView: NavigationView
    private lateinit var recyclerView: RecyclerView
    private lateinit var patientAdapter: PatientAdapter
    private lateinit var webSocketManager: WebSocketManager
    
    private val patients = mutableListOf<Patient>()
    private var currentWardType = "RECORDS" // RECORDS, GENERAL_ADMITTED, GENERAL_ALERTED, CRITICAL
    
    // Auto-update timestamps
    private val updateHandler = Handler(Looper.getMainLooper())
    private val sdf = SimpleDateFormat("HH:mm:ss", Locale.getDefault())
    
    // Alert notification service
    private lateinit var alertService: AlertNotificationService

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Request permissions
        requestPermissions()

        // Initialize WebSocket
        webSocketManager = WebSocketManager()
        
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

        // Setup RecyclerView
        recyclerView.layoutManager = LinearLayoutManager(this)
        patientAdapter = PatientAdapter(patients) { patient ->
            onPatientClick(patient)
        }
        recyclerView.adapter = patientAdapter

        // Load mock data
        loadMockPatients()
        
        // Start auto-updating timestamps
        startTimestampUpdate()
        
        // Trigger alert after 5 seconds for critical patient
        triggerDelayedAlert()
        
        // Observe WebSocket connection (for future real data)
        observeWebSocket()
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
    
    private fun triggerDelayedAlert() {
        // Trigger alert after 5 seconds for BAND_001 patient
        Handler(Looper.getMainLooper()).postDelayed({
            val criticalPatient = patients.find { it.patientId == "BAND_001" }
            criticalPatient?.let { patient ->
                // Update patient to critical condition
                patient.status = "CRITICAL ALERT"
                patient.fallDetected = true
                patient.heartRate = 145
                patient.spO2 = 85
                patient.temperature = 39.2
                patient.bpSystolic = 160
                patient.bpDiastolic = 100
                
        // Release alert service
        alertService.release()
                // Refresh the list
                patientAdapter.notifyDataSetChanged()
                
                // Play alert with voice announcement
                alertService.playAlertWithVoice(
                    patientName = patient.name,
                    condition = "Critical",
                    heartRate = patient.heartRate,
                    spO2 = patient.spO2,
                    temperature = patient.temperature
                )
                
                // Show toast notification
                Toast.makeText(
                    this,
                    "🚨 CRITICAL ALERT: ${patient.name} - Heart Rate ${patient.heartRate} BPM!",
                    Toast.LENGTH_LONG
                ).show()
            }
        }, 5000) // 5 seconds delay
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

    override fun onDestroy() {
        super.onDestroy()
        // Stop timestamp updates
        updateHandler.removeCallbacksAndMessages(null)
        webSocketManager.disconnect()
    }

    private fun onPatientClick(patient: Patient) {
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
        when (item.itemId) {
            R.id.nav_records -> {
                Toast.makeText(this, "All Patients", Toast.LENGTH_SHORT).show()
                loadMockPatients()
            }
            R.id.nav_general_admitted -> {
                Toast.makeText(this, "General Ward - Dummy Patients", Toast.LENGTH_SHORT).show()
                filterGeneralWardPatients()
            }
            R.id.nav_general_alerted -> {
                Toast.makeText(this, "General Ward - Alerted", Toast.LENGTH_SHORT).show()
                filterAlertedPatients()
            }
            R.id.nav_critical_patients -> {
                Toast.makeText(this, "Critical Ward - Band Patient", Toast.LENGTH_SHORT).show()
                filterCriticalWardPatients()
            }
        }
        
        drawerLayout.closeDrawer(GravityCompat.START)
        return true
    }
    
    private fun filterGeneralWardPatients() {
        // Show only dummy patients (General Ward)
        val generalPatients = patients.filter { it.patientId.startsWith("P") }
        patientAdapter.updatePatients(generalPatients)
    }
    
    private fun filterCriticalWardPatients() {
        // Show only band patients (Critical Ward)
        val criticalPatients = patients.filter { it.patientId.startsWith("BAND_") }
        patientAdapter.updatePatients(criticalPatients)
    }
    
    private fun filterAlertedPatients() {
        // Show only alerted patients
        val alertedPatients = patients.filter { it.fallDetected }
        patientAdapter.updatePatients(alertedPatients)
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
            if (allGranted) {
                Toast.makeText(this, "All permissions granted!", Toast.LENGTH_SHORT).show()
            } else {
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

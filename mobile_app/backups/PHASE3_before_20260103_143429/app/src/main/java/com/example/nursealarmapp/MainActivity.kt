package com.example.nursealarmapp

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.view.MenuItem
import android.widget.ImageButton
import android.widget.Toast
import androidx.appcompat.app.ActionBarDrawerToggle
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.core.view.GravityCompat
import androidx.drawerlayout.widget.DrawerLayout
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.example.nursealarmapp.adapters.PatientAdapter
import com.example.nursealarmapp.models.Patient
import com.google.android.material.navigation.NavigationView
import java.text.SimpleDateFormat
import java.util.*

class MainActivity : AppCompatActivity(), NavigationView.OnNavigationItemSelectedListener {

    private val PERMISSION_REQUEST_CODE = 123
    private lateinit var drawerLayout: DrawerLayout
    private lateinit var navigationView: NavigationView
    private lateinit var recyclerView: RecyclerView
    private lateinit var patientAdapter: PatientAdapter
    
    private val patients = mutableListOf<Patient>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Request permissions
        requestPermissions()

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
    }

    private fun loadMockPatients() {
        val sdf = SimpleDateFormat("HH:mm:ss", Locale.getDefault())
        val currentTime = sdf.format(Date())
        
        patients.clear()
        // Real patient - can have alerts
        patients.add(Patient("P001", "Patient 1", "ALERT", currentTime, true))
        
        // Dummy patients - NEVER alerted, always STABLE
        patients.add(Patient("P002", "Patient 2 (Dummy)", "STABLE", currentTime, false))
        patients.add(Patient("P003", "Patient 3 (Dummy)", "STABLE", currentTime, false))
        patients.add(Patient("P004", "Patient 4 (Dummy)", "STABLE", currentTime, false))
        patients.add(Patient("P005", "Patient 5 (Dummy)", "STABLE", currentTime, false))
        patients.add(Patient("P006", "Patient 6 (Dummy)", "STABLE", currentTime, false))
        patients.add(Patient("P007", "Patient 7 (Dummy)", "STABLE", currentTime, false))
        patients.add(Patient("P008", "Patient 8 (Dummy)", "STABLE", currentTime, false))
        patients.add(Patient("P009", "Patient 9 (Dummy)", "STABLE", currentTime, false))
        patients.add(Patient("P010", "Patient 10 (Dummy)", "STABLE", currentTime, false))
        
        patientAdapter.updatePatients(patients)
    }

    private fun onPatientClick(patient: Patient) {
        Toast.makeText(this, "Clicked: ${patient.name}", Toast.LENGTH_SHORT).show()
        // TODO: Open patient details activity in Phase 3
    }

    override fun onNavigationItemSelected(item: MenuItem): Boolean {
        when (item.itemId) {
            R.id.nav_records -> {
                Toast.makeText(this, "Records selected", Toast.LENGTH_SHORT).show()
                loadMockPatients()
            }
            R.id.nav_general_admitted -> {
                Toast.makeText(this, "General Ward - Admitted", Toast.LENGTH_SHORT).show()
                // TODO: Filter and display admitted patients
            }
            R.id.nav_general_alerted -> {
                Toast.makeText(this, "General Ward - Alerted", Toast.LENGTH_SHORT).show()
                // TODO: Filter and display alerted patients only
            }
            R.id.nav_critical_patients -> {
                Toast.makeText(this, "Critical Ward - Patients", Toast.LENGTH_SHORT).show()
                // TODO: Filter and display critical ward patients
            }
        }
        
        drawerLayout.closeDrawer(GravityCompat.START)
        return true
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
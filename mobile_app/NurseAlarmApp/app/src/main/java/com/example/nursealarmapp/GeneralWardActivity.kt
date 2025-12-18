package com.example.nursealarmapp

import android.Manifest
import android.bluetooth.BluetoothManager
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.widget.Button
import android.widget.Switch
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.lifecycle.lifecycleScope
import com.example.nursealarmapp.models.GeneralWardEvent
import com.example.nursealarmapp.network.ApiService
import com.example.nursealarmapp.network.WebSocketManager
import com.example.nursealarmapp.utils.NotificationHelper
import com.example.nursealarmapp.utils.VibrationHelper
import com.google.gson.Gson
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class GeneralWardActivity : AppCompatActivity() {

    private lateinit var tvStatus: TextView
    private lateinit var tvNearbyDevices: TextView
    private lateinit var tvRecentAlerts: TextView
    private lateinit var btnToggleScanning: Button
    private lateinit var btnTestVibration: Button
    private lateinit var switchSimulateBand: Switch

    private val apiService = ApiService()
    private val wsManager = WebSocketManager()
    private lateinit var vibrationHelper: VibrationHelper
    private lateinit var notificationHelper: NotificationHelper

    private var sessionId: String? = null
    private var isScanning = false
    private var scanJob: Job? = null
    private val nearbyDevices = mutableSetOf<String>()
    private val gson = Gson()
    private val logHistory = mutableListOf<String>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_general_ward)

        tvStatus = findViewById(R.id.tvStatus)
        tvNearbyDevices = findViewById(R.id.tvNearbyDevices)
        tvRecentAlerts = findViewById(R.id.tvRecentAlerts)
        btnToggleScanning = findViewById(R.id.btnToggleScanning)
        btnTestVibration = findViewById(R.id.btnTestVibration)
        switchSimulateBand = findViewById(R.id.switchSimulateBand)

        vibrationHelper = VibrationHelper(this)
        notificationHelper = NotificationHelper(this)

        btnToggleScanning.setOnClickListener { toggleScanning() }
        btnTestVibration.setOnClickListener {
            logToScreen("[UI] >> Manually testing vibration...")
            vibrationHelper.vibrateAlarm()
        }

        registerNurse()
        observeConnectionStatus()
        observeWebSocketEvents()
    }

    private fun registerNurse() {
        logToScreen("[API] >> Registering nurse...")
        lifecycleScope.launch {
            tvStatus.text = "Status: Registering..."
            val result = apiService.registerNurse("${Build.MANUFACTURER} ${Build.MODEL}")
            result.onSuccess { id ->
                sessionId = id
                tvStatus.text = "Status: Registered. Connecting..."
                logToScreen("[API] ✅ Nurse registered with session ID: ${id.substring(0, 8)}...")
                wsManager.connectGeneral(id)
            }.onFailure { error ->
                tvStatus.text = "Status: ○ Registration failed"
                logToScreen("[API] ❌ Registration failed: ${error.message}")
            }
        }
    }

    private fun observeConnectionStatus() {
        lifecycleScope.launch {
            wsManager.connectionStatus.collect { isConnected ->
                if (isConnected) {
                    tvStatus.text = "Status: ● Connected"
                    logToScreen("[WS] ✅ WebSocket Connected.")
                } else {
                    if (sessionId != null) {
                        tvStatus.text = "Status: ○ Disconnected"
                        logToScreen("[WS] ❌ WebSocket Disconnected.")
                    }
                }
            }
        }
    }

    private fun observeWebSocketEvents() {
        lifecycleScope.launch {
            wsManager.generalWardEventFlow.collect { event ->
                handleGeneralWardEvent(event)
            }
        }
    }

    private fun handleGeneralWardEvent(event: GeneralWardEvent) {
        logToScreen("[WS] << Received event: ${event.javaClass.simpleName}")
        when (event) {
            is GeneralWardEvent.AlarmTriggered -> {
                logToScreen("[ALARM] 🚨 ALARM: Patient ${event.patient_name} (${event.band_id})")
                logToScreen("[ALARM]    Nearby Devices: $nearbyDevices")

                if (event.band_id in nearbyDevices) {
                    logToScreen("[ALARM]    ✅ Proximity Match! Triggering alert.")
                    vibrationHelper.vibrateAlarm()
                    notificationHelper.showGeneralWardAlarm(event.patient_name)
                } else {
                    logToScreen("[ALARM]    ❌ No Proximity. Ignoring.")
                }
            }
            is GeneralWardEvent.VitalsUpdate -> {
                logToScreen("[Vitals] Vitals for patient ${event.patient_id}")
            }
            is GeneralWardEvent.Heartbeat -> {
                logToScreen("[Heartbeat] ❤️")
            }
            is GeneralWardEvent.Unknown -> {
                logToScreen("[Unknown] Received unknown event: ${event.raw.take(100)}...")
            }
            else -> {}
        }
    }

    private fun logToScreen(message: String) {
        runOnUiThread {
            // Use a Toast for guaranteed visibility
            Toast.makeText(this, message, Toast.LENGTH_SHORT).show()

            // Also log to Logcat for a persistent record
            Log.d("OnScreenDebug", message)

            // We'll still try to update the TextView, just in case.
            val timeFormat = SimpleDateFormat("HH:mm:ss", Locale.getDefault())
            val currentTime = timeFormat.format(Date())
            logHistory.add(0, "$currentTime - $message")
            if (logHistory.size > 20) {
                logHistory.removeAt(logHistory.size - 1)
            }
            tvRecentAlerts.text = logHistory.joinToString("\n")
        }
    }

    private fun toggleScanning() {
        if (isScanning) {
            stopScanning()
        } else {
            startScanning()
        }
    }

    private fun startScanning() {
        isScanning = true
        btnToggleScanning.text = "Stop Scanning"
        logToScreen("[SCAN] >> Started proximity simulation.")

        if (switchSimulateBand.isChecked) {
            scanJob = lifecycleScope.launch {
                while (isScanning) {
                    nearbyDevices.add("BAND_01")
                    updateNearbyDevices()
                    sendProximityUpdate()
                    delay(5000)
                }
            }
        } else {
             if (checkBluetoothPermissions()) {
                startBluetoothScan()
            } else {
                Toast.makeText(this, "Bluetooth permissions required", Toast.LENGTH_SHORT).show()
                stopScanning()
            }
        }
    }

    private fun stopScanning() {
        isScanning = false
        btnToggleScanning.text = "Start Scanning"
        logToScreen("[SCAN] >> Stopped proximity simulation.")
        scanJob?.cancel()
        nearbyDevices.clear()
        updateNearbyDevices()
    }

    private fun sendProximityUpdate() {
        sessionId?.let { id ->
            lifecycleScope.launch {
                apiService.sendProximityUpdate(id, nearbyDevices.toList())
            }
        }
    }

    private fun updateNearbyDevices() {
        runOnUiThread {
            if (nearbyDevices.isEmpty()) {
                tvNearbyDevices.text = "Nearby Patients:\nNo devices detected"
            } else {
                tvNearbyDevices.text = "Nearby Patients:\n" +
                        nearbyDevices.joinToString("\n") { "• $it" }
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        stopScanning()
        wsManager.disconnect()
    }

    private fun checkBluetoothPermissions(): Boolean {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            return ActivityCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_SCAN) == PackageManager.PERMISSION_GRANTED
        }
        return true
    }

    private fun startBluetoothScan() {
        val bluetoothManager = getSystemService(BLUETOOTH_SERVICE) as BluetoothManager
        val bluetoothAdapter = bluetoothManager.adapter
        if (bluetoothAdapter?.isEnabled == true) {
            scanJob = lifecycleScope.launch {
                while (isScanning) {
                    Toast.makeText(this@GeneralWardActivity, "Real BLE scanning not implemented", Toast.LENGTH_SHORT).show()
                    delay(5000)
                }
            }
        } else {
            Toast.makeText(this, "Please enable Bluetooth", Toast.LENGTH_SHORT).show()
            stopScanning()
        }
    }
}
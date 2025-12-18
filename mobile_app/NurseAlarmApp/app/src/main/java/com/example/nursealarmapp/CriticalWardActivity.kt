package com.example.nursealarmapp

import android.os.Bundle
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.example.nursealarmapp.models.AlarmData
import com.example.nursealarmapp.network.WebSocketManager
import com.example.nursealarmapp.utils.NotificationHelper
import com.example.nursealarmapp.utils.VibrationHelper
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class CriticalWardActivity : AppCompatActivity() {

    private lateinit var tvStatus: TextView
    private lateinit var tvActiveAlerts: TextView
    private lateinit var tvAlarmCount: TextView

    private val wsManager = WebSocketManager()
    private lateinit var vibrationHelper: VibrationHelper
    private lateinit var notificationHelper: NotificationHelper

    private val alertsList = mutableListOf<String>()
    private var alarmCount = 0

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_critical_ward)

        // Initialize views
        tvStatus = findViewById(R.id.tvStatus)
        tvActiveAlerts = findViewById(R.id.tvActiveAlerts)
        tvAlarmCount = findViewById(R.id.tvAlarmCount)

        vibrationHelper = VibrationHelper(this)
        notificationHelper = NotificationHelper(this)

        // Connect to WebSocket
        connectToCriticalWard()
        observeAlarms()
        observeConnection()
    }

    private fun connectToCriticalWard() {
        tvStatus.text = getString(R.string.status_connecting_critical_ward)
        wsManager.connectCritical()
        Toast.makeText(this, getString(R.string.monitoring_all_critical_patients), Toast.LENGTH_SHORT).show()
    }

    private fun observeConnection() {
        lifecycleScope.launch {
            wsManager.connectionStatus.collect { isConnected ->
                tvStatus.text = if (isConnected) {
                    getString(R.string.status_connected_monitoring_active)
                } else {
                    getString(R.string.status_disconnected)
                }
            }
        }
    }

    private fun observeAlarms() {
        lifecycleScope.launch {
            wsManager.criticalAlarmFlow.collect { alarm ->
                handleCriticalAlarm(alarm)
            }
        }
    }

    private fun handleCriticalAlarm(alarm: AlarmData) {
        // Vibrate strongly for critical alerts
        vibrationHelper.vibrateCritical()

        // Format vitals
        val vitals = getString(
            R.string.vitals_hr_spo2_temp_bp,
            alarm.vitals.HR?.toInt()?.toString() ?: "--",
            alarm.vitals.SpO2?.toInt()?.toString() ?: "--",
            String.format(Locale.ROOT, "%.1f", alarm.vitals.Temp ?: 0.0),
            alarm.vitals.BP_sys?.toInt()?.toString() ?: "--",
            alarm.vitals.BP_dia?.toInt()?.toString() ?: "--"
        )

        // Show notification
        notificationHelper.showCriticalAlert(alarm.patient_name, vitals)

        // Update alarm count
        alarmCount++
        tvAlarmCount.text = getString(R.string.total_alarms_today, alarmCount)

        // Add to alerts list
        val timeFormat = SimpleDateFormat("HH:mm:ss", Locale.getDefault())
        val currentTime = timeFormat.format(Date())

        val alertText = getString(
            R.string.critical_alert_details,
            currentTime,
            alarm.patient_name,
            alarm.alarm_decision.message,
            vitals,
            getString(R.string.risk_level, alarm.prediction.risk_level ?: getString(R.string.unknown)) + 
            if (alarm.prediction.risk_factors?.isNotEmpty() == true) "\n" + getString(R.string.risk_factors, alarm.prediction.risk_factors.joinToString(", ")) else ""
        )


        alertsList.add(0, alertText) // Add to beginning

        // Keep only last 20 alerts
        if (alertsList.size > 20) {
            alertsList.removeAt(alertsList.size - 1)
        }

        // Update UI
        updateAlertsDisplay()
    }

    private fun updateAlertsDisplay() {
        if (alertsList.isEmpty()) {
            tvActiveAlerts.text = getString(R.string.active_alerts_none)
        } else {
            tvActiveAlerts.text = getString(R.string.active_alerts_header) + "\n\n" + alertsList.joinToString("\n")
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        wsManager.disconnect()
    }
}

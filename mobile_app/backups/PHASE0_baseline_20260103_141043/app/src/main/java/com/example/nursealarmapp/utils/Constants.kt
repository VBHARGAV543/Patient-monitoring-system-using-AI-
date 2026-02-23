package com.example.nursealarmapp.utils

object Constants {
    // Your laptop's IP address
    const val BASE_URL = "http://10.205.77.101:8000"
    const val WS_URL = "ws://10.205.77.101:8000"

    // BLE Scan settings
    const val BLE_SCAN_INTERVAL_MS = 5000L
    const val BLE_DEVICE_PREFIX = "BAND_"

    // Notification settings
    const val CHANNEL_ID = "nurse_alerts"
    const val CHANNEL_NAME = "Patient Alerts"
    const val CHANNEL_DESCRIPTION = "Alerts for patient vital sign abnormalities"

    // Vibration patterns
    val VIBRATION_PATTERN_GENERAL = longArrayOf(0, 500, 200, 500)
    val VIBRATION_PATTERN_CRITICAL = longArrayOf(0, 1000, 500, 1000, 500, 1000)
    val VIBRATION_PATTERN_ALARM = longArrayOf(0, 1000, 500, 1000)
}
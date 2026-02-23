package com.example.nursealarmapp.models

/**
 * Represents a patient in the General Ward.
 * isReal = true → the one real backend patient.
 * isReal = false → one of the 20 simulated dummy patients.
 */
data class GeneralPatient(
    val id: String,
    val name: String,
    val disease: String,
    val isReal: Boolean = false,

    // Live / simulated vitals
    var heartRate: Int = 72,
    var spO2: Int = 98,
    var temperature: Double = 36.8,
    var bpSystolic: Int = 120,
    var bpDiastolic: Int = 80,
    var respRate: Int = 16,
    var glucose: Int = 100,

    // Alarm state
    var isAlerted: Boolean = false,
    var alertTimestamp: String = "",   // when the current alarm fired
    var riskLevel: String = "LOW",

    // Attended history: each entry is a formatted timestamp string
    val attendedTimestamps: MutableList<String> = mutableListOf()
)

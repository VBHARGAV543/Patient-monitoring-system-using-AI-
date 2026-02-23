package com.example.nursealarmapp.models

data class Patient(
    val patientId: String,
    val name: String,
    var status: String, // Mutable for alert updates
    var timestamp: String, // Mutable for auto-update
    var fallDetected: Boolean = false, // Mutable for alert trigger
    var heartRate: Int = 0, // Mutable for alert
    var spO2: Int = 0, // Mutable for alert
    var temperature: Double = 0.0, // Mutable for alert
    var bpSystolic: Int = 0, // Mutable for alert
    var bpDiastolic: Int = 0 // Mutable for alert
)

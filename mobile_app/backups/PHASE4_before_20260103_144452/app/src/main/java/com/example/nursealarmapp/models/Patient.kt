package com.example.nursealarmapp.models

data class Patient(
    val patientId: String,
    val name: String,
    val status: String, // "STABLE" or "ALERT"
    val timestamp: String,
    val fallDetected: Boolean = false,
    val heartRate: Int = 0,
    val spO2: Int = 0,
    val temperature: Double = 0.0,
    val bpSystolic: Int = 0,
    val bpDiastolic: Int = 0
)

package com.example.nursealarmapp.models

data class Patient(
    val patientId: String,
    val name: String,
    val status: String, // "STABLE" or "ALERT"
    val timestamp: String,
    val fallDetected: Boolean = false
)

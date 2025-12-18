package com.example.nursealarmapp.models

data class AlarmData(
    val event: String,
    val patient_id: Int,
    val patient_name: String,
    val patient_type: String,
    val vitals: VitalsData,
    val prediction: PredictionData,
    val alarm_decision: AlarmDecision,
    val timestamp: String
)

data class PredictionData(
    val prediction: Int,
    val confidence: Double?,
    val risk_level: String?,
    val risk_factors: List<String>?,
    val recommendations: List<String>?
)

data class AlarmDecision(
    val action: String,
    val alarm_active: Boolean,
    val message: String,
    val route_to_nurse: Boolean,
    val route_to_dashboard: Boolean
)

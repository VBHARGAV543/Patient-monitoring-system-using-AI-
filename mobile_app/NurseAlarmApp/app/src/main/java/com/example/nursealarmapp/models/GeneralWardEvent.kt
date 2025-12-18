package com.example.nursealarmapp.models

import com.google.gson.annotations.SerializedName

sealed class GeneralWardEvent {
    data class Connected(val session_id: String, val message: String) : GeneralWardEvent()
    data class VitalsUpdate(val patient_id: Int, val vitals: VitalsData, @SerializedName("ml_prediction") val mlPrediction: PredictionData) : GeneralWardEvent()
    data class AlarmTriggered(
        val patient_id: Int,
        val patient_name: String,
        val band_id: String,
        val vitals: VitalsData
    ) : GeneralWardEvent()
    data class Heartbeat(val timestamp: String) : GeneralWardEvent()
    data class Unknown(val raw: String) : GeneralWardEvent()
}
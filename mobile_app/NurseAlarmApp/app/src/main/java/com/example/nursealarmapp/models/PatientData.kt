package com.example.nursealarmapp.models

data class PatientData(
    val id: Int,
    val name: String,
    val age: Int,
    val problem: String,
    val patient_type: String,
    val band_id: String?,
    val vitals: VitalsData?
)

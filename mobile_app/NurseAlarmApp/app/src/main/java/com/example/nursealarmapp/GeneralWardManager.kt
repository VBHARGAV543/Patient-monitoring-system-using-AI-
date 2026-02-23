package com.example.nursealarmapp

import com.example.nursealarmapp.models.GeneralPatient
import com.example.nursealarmapp.network.ApiService
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.*

/**
 * Singleton that owns the General Ward patient list.
 *
 * Patients come ONLY from the backend (/api/patients/admitted?patient_type=GENERAL).
 * The list is empty until loadFromBackend() is called.
 * Alarm state is updated by MainActivity when a WebSocket AlarmTriggered event arrives.
 */
object GeneralWardManager {

    private val sdf     = SimpleDateFormat("HH:mm:ss", Locale.getDefault())
    private val dateSdf = SimpleDateFormat("dd MMM HH:mm", Locale.getDefault())

    // All currently admitted GENERAL patients (fetched from backend)
    val allPatients: MutableList<GeneralPatient> = mutableListOf()

    /** Callback set by MainActivity whenever the list changes */
    var onListChanged: (() -> Unit)? = null

    // ── Backend fetch ─────────────────────────────────────────────────────

    /**
     * Fetches admitted GENERAL patients from the backend and refreshes [allPatients].
     * Preserves existing alarm / attended state for patients already in the list.
     */
    fun loadFromBackend(
        apiService: ApiService,
        scope: CoroutineScope,
        onDone: (() -> Unit)? = null
    ) {
        scope.launch {
            val result = apiService.getAdmittedPatients(patientType = "GENERAL")
            result.onSuccess { jsonList ->
                // Keep existing state (alerted, attendedTimestamps, vitals)
                val existingById = allPatients.associateBy { it.id }

                val fetched = jsonList.map { obj ->
                    val id      = obj.get("id")?.asInt?.toString() ?: "?"
                    val name    = obj.get("name")?.asString    ?: "Unknown"
                    val disease = obj.get("problem")?.asString ?: "General"

                    val existing = existingById[id]
                    GeneralPatient(
                        id = id,
                        name = name,
                        disease = disease,
                        isReal = true,
                        isAlerted      = existing?.isAlerted      ?: false,
                        alertTimestamp = existing?.alertTimestamp  ?: "",
                        riskLevel      = existing?.riskLevel       ?: "LOW",
                        heartRate      = existing?.heartRate       ?: 72,
                        spO2           = existing?.spO2            ?: 98,
                        temperature    = existing?.temperature     ?: 36.8,
                        bpSystolic     = existing?.bpSystolic      ?: 120,
                        bpDiastolic    = existing?.bpDiastolic     ?: 80,
                        respRate       = existing?.respRate        ?: 16,
                        glucose        = existing?.glucose         ?: 100,
                        attendedTimestamps = existing?.attendedTimestamps ?: mutableListOf()
                    )
                }

                allPatients.clear()
                allPatients.addAll(fetched)

                // Append 20 static dummy ward patients so the ward looks populated.
                // IDs start at DUMMY_ so WebSocket events (int IDs) never match them.
                val dummyData = listOf(
                    Triple("Arjun Sharma",     "UTI (Urinary Tract Infection)",   Triple(74, 98, 36.6)),
                    Triple("Priya Patel",      "Mild Pneumonia",                  Triple(88, 95, 37.8)),
                    Triple("Ravi Kumar",       "Gastroenteritis",                 Triple(80, 97, 37.1)),
                    Triple("Sneha Reddy",      "Hypertension",                    Triple(70, 99, 36.5)),
                    Triple("Amit Verma",       "Diabetes Type 2",                 Triple(76, 98, 36.9)),
                    Triple("Kavya Nair",       "Asthma (Mild Attack)",            Triple(84, 96, 37.0)),
                    Triple("Rohit Singh",      "Fever (Unknown Origin)",          Triple(90, 97, 38.2)),
                    Triple("Meena Joshi",      "UTI (Urinary Tract Infection)",   Triple(68, 99, 36.4)),
                    Triple("Suresh Iyer",      "Gastroenteritis",                 Triple(82, 97, 37.3)),
                    Triple("Ananya Das",       "Hypertension",                    Triple(72, 98, 36.7)),
                    Triple("Vikram Gupta",     "Mild Pneumonia",                  Triple(86, 94, 37.6)),
                    Triple("Deepa Menon",      "Diabetes Type 2",                 Triple(78, 98, 36.8)),
                    Triple("Rajesh Rao",       "Fever (Unknown Origin)",          Triple(92, 96, 38.0)),
                    Triple("Nisha Kapoor",     "Asthma (Mild Attack)",            Triple(85, 95, 37.2)),
                    Triple("Arun Pillai",      "UTI (Urinary Tract Infection)",   Triple(66, 99, 36.3)),
                    Triple("Pooja Desai",      "Gastroenteritis",                 Triple(79, 97, 37.0)),
                    Triple("Sanjay Mishra",    "Hypertension",                    Triple(73, 98, 36.6)),
                    Triple("Lakshmi Subramaniam", "Mild Pneumonia",              Triple(88, 95, 37.5)),
                    Triple("Tarun Bose",       "Diabetes Type 2",                 Triple(75, 99, 36.8)),
                    Triple("Geeta Choudhury",  "Fever (Unknown Origin)",          Triple(91, 96, 38.1))
                )
                dummyData.forEachIndexed { i, (name, disease, vitals) ->
                    val dummyId = "DUMMY_%02d".format(i + 1)
                    if (allPatients.none { it.id == dummyId }) {
                        allPatients.add(
                            GeneralPatient(
                                id = dummyId,
                                name = name,
                                disease = disease,
                                isReal = false,
                                heartRate   = vitals.first,
                                spO2        = vitals.second,
                                temperature = vitals.third,
                                bpSystolic  = (110..130).random(),
                                bpDiastolic = (70..85).random(),
                                respRate    = (14..18).random(),
                                glucose     = (85..115).random()
                            )
                        )
                    }
                }

                onDone?.invoke()
                onListChanged?.invoke()
            }
            result.onFailure { onDone?.invoke() }
        }
    }

    // ── Alarm state ───────────────────────────────────────────────────────

    /**
     * Called when WebSocket fires an AlarmTriggered for a GENERAL patient.
     * Finds the patient by backend id, marks as alerted.
     * If not in the list yet, adds them transiently until next refresh.
     */
    fun onAlarmTriggered(
        backendPatientId: Int,
        patientName: String,
        hr: Int, spo2: Int, temp: Double,
        bpSys: Int, bpDia: Int, rr: Int, glucose: Int,
        risk: String = "HIGH"
    ) {
        val idStr = backendPatientId.toString()
        var p = allPatients.find { it.id == idStr }
        if (p == null) {
            p = GeneralPatient(id = idStr, name = patientName, disease = "General", isReal = true)
            allPatients.add(0, p)
        }
        p.isAlerted      = true
        p.alertTimestamp = sdf.format(Date())
        p.riskLevel      = risk
        p.heartRate = hr;  p.spO2 = spo2;  p.temperature = temp
        p.bpSystolic = bpSys; p.bpDiastolic = bpDia
        p.respRate = rr;  p.glucose = glucose
        onListChanged?.invoke()
    }

    // ── Vitals update (non-alarm) ─────────────────────────────────────────

    fun onVitalsUpdate(
        backendPatientId: Int,
        hr: Int, spo2: Int, temp: Double,
        bpSys: Int, bpDia: Int, rr: Int, glucose: Int
    ) {
        val p = allPatients.find { it.id == backendPatientId.toString() } ?: return
        p.heartRate = hr;  p.spO2 = spo2;  p.temperature = temp
        p.bpSystolic = bpSys; p.bpDiastolic = bpDia
        p.respRate = rr;  p.glucose = glucose
        onListChanged?.invoke()
    }

    // ── Attended ──────────────────────────────────────────────────────────

    fun markAttended(patientId: String) {
        val p = allPatients.find { it.id == patientId } ?: return
        p.isAlerted      = false
        p.alertTimestamp = ""
        p.riskLevel      = "LOW"
        p.attendedTimestamps.add(0, dateSdf.format(Date()))
        onListChanged?.invoke()
    }

    // ── Helpers ───────────────────────────────────────────────────────────

    fun admittedList(): List<GeneralPatient> = allPatients.toList()

    fun alertedList(): List<GeneralPatient> = allPatients.filter { it.isAlerted }

    fun clear() {
        allPatients.clear()
        onListChanged = null
    }
}

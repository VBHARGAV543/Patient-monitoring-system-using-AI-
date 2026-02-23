package com.example.nursealarmapp.network

import android.content.Context
import com.google.gson.Gson
import com.google.gson.JsonObject
import com.example.nursealarmapp.utils.NetworkPreferences
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.util.UUID
import java.util.concurrent.TimeUnit

class ApiService(context: Context) {

    private val networkPrefs = NetworkPreferences.getInstance(context)
    
    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(10, TimeUnit.SECONDS)
        .writeTimeout(10, TimeUnit.SECONDS)
        .build()

    private val gson = Gson()

    suspend fun registerNurse(deviceInfo: String): Result<String> = withContext(Dispatchers.IO) {
        try {
            val sessionId = UUID.randomUUID().toString()
            val json = JsonObject().apply {
                addProperty("session_id", sessionId)
                addProperty("device_info", deviceInfo)
            }

            val body = json.toString().toRequestBody("application/json".toMediaType())
            val request = Request.Builder()
                .url("${networkPrefs.getBaseUrl()}/api/nurse/register")
                .post(body)
                .build()

            val response = client.newCall(request).execute()

            if (response.isSuccessful) {
                Result.success(sessionId)
            } else {
                Result.failure(Exception("Failed to register: ${response.code}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun sendProximityUpdate(
        sessionId: String,
        bleDevices: List<String>
    ): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val json = JsonObject().apply {
                addProperty("session_id", sessionId)
                add("ble_devices_nearby", gson.toJsonTree(bleDevices))
            }

            val body = json.toString().toRequestBody("application/json".toMediaType())
            val request = Request.Builder()
                .url("${networkPrefs.getBaseUrl()}/api/nurse/proximity")
                .post(body)
                .build()

            val response = client.newCall(request).execute()

            if (response.isSuccessful) {
                Result.success(Unit)
            } else {
                Result.failure(Exception("Failed to update proximity: ${response.code}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun getDischargedPatients(): Result<List<JsonObject>> = withContext(Dispatchers.IO) {
        try {
            val request = Request.Builder()
                .url("${networkPrefs.getBaseUrl()}/api/patients/discharged")
                .get()
                .build()

            val response = client.newCall(request).execute()

            if (response.isSuccessful) {
                val body = response.body?.string()
                val jsonArray = gson.fromJson(body, com.google.gson.JsonArray::class.java)
                val list = mutableListOf<JsonObject>()
                for (element in jsonArray) {
                    list.add(element.asJsonObject)
                }
                Result.success(list)
            } else {
                Result.failure(Exception("Failed to get discharged patients: ${response.code}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /** Fetch all currently admitted patients from the backend.
     *  Each JsonObject has: id, name, age, problem, patient_type, status, admission_time */
    suspend fun getAdmittedPatients(patientType: String? = null): Result<List<JsonObject>> =
        withContext(Dispatchers.IO) {
            try {
                val url = buildString {
                    append("${networkPrefs.getBaseUrl()}/api/patients/admitted")
                    if (patientType != null) append("?patient_type=$patientType")
                }
                val request = Request.Builder().url(url).get().build()
                val response = client.newCall(request).execute()
                if (response.isSuccessful) {
                    val body = response.body?.string()
                    val arr = gson.fromJson(body, com.google.gson.JsonArray::class.java)
                    val list = mutableListOf<JsonObject>()
                    for (el in arr) list.add(el.asJsonObject)
                    Result.success(list)
                } else {
                    Result.failure(Exception("HTTP ${response.code}"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }

    suspend fun getLatestVitals(patientId: String): Result<JsonObject> = withContext(Dispatchers.IO) {
        try {
            val request = Request.Builder()
                .url("${networkPrefs.getBaseUrl()}/api/patient/$patientId/vitals/latest")
                .get()
                .build()

            val response = client.newCall(request).execute()

            if (response.isSuccessful) {
                val body = response.body?.string()
                val jsonObject = gson.fromJson(body, JsonObject::class.java)
                Result.success(jsonObject)
            } else {
                Result.failure(Exception("Failed to get vitals: ${response.code}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
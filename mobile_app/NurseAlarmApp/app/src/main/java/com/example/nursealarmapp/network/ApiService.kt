package com.example.nursealarmapp.network

import com.google.gson.Gson
import com.google.gson.JsonObject
import com.example.nursealarmapp.utils.Constants
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.util.UUID
import java.util.concurrent.TimeUnit

class ApiService {

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
                .url("${Constants.BASE_URL}/api/nurse/register")
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
                .url("${Constants.BASE_URL}/api/nurse/proximity")
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
}
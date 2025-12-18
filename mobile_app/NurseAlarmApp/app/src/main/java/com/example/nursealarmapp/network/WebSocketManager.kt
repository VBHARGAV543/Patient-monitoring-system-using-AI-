package com.example.nursealarmapp.network

import android.util.Log
import com.example.nursealarmapp.models.AlarmData
import com.example.nursealarmapp.models.GeneralWardEvent
import com.example.nursealarmapp.parser.GeneralWardEventParser
import com.example.nursealarmapp.utils.Constants
import com.google.gson.Gson
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import java.util.concurrent.TimeUnit

class WebSocketManager {

    private var webSocket: WebSocket? = null
    private val client = OkHttpClient.Builder()
        .pingInterval(30, TimeUnit.SECONDS)
        .build()

    private val gson = Gson()
    private val eventParser = GeneralWardEventParser()
    private val scope = CoroutineScope(Dispatchers.IO)

    // CRITICAL FIX: Add a replay cache of 1. This ensures the last event is always available to new subscribers.
    private val _generalWardEventFlow = MutableSharedFlow<GeneralWardEvent>(replay = 1)
    val generalWardEventFlow = _generalWardEventFlow.asSharedFlow()

    private val _criticalAlarmFlow = MutableSharedFlow<AlarmData>(replay = 1)
    val criticalAlarmFlow = _criticalAlarmFlow.asSharedFlow()

    private val _connectionStatus = MutableStateFlow(false)
    val connectionStatus = _connectionStatus.asStateFlow()

    fun connectGeneral(sessionId: String) {
        val request = Request.Builder()
            .url("${Constants.WS_URL}/ws/nurse/$sessionId")
            .build()
        webSocket = client.newWebSocket(request, GeneralWardListener())
    }

    fun connectCritical() {
        val request = Request.Builder()
            .url("${Constants.WS_URL}/ws")
            .build()
        webSocket = client.newWebSocket(request, CriticalWardListener())
    }

    fun disconnect() {
        webSocket?.close(1000, "User disconnected")
    }

    private inner class GeneralWardListener : WebSocketListener() {
        override fun onOpen(webSocket: WebSocket, response: Response) {
            _connectionStatus.value = true
        }

        override fun onMessage(webSocket: WebSocket, text: String) {
            val event = eventParser.parse(text)
            // CRITICAL FIX: Use the suspending emit() in a coroutine scope for reliability.
            scope.launch {
                _generalWardEventFlow.emit(event)
            }
        }

        override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
            _connectionStatus.value = false
        }

        override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
            _connectionStatus.value = false
        }
    }

    private inner class CriticalWardListener : WebSocketListener() {
        override fun onOpen(webSocket: WebSocket, response: Response) {
            _connectionStatus.value = true
        }

        override fun onMessage(webSocket: WebSocket, text: String) {
            try {
                val alarm = gson.fromJson(text, AlarmData::class.java)
                if (alarm.patient_type == "CRITICAL") {
                    scope.launch {
                        _criticalAlarmFlow.emit(alarm)
                    }
                }
            } catch (e: Exception) {
                Log.e("WebSocket", "Failed to parse critical alarm data", e)
            }
        }

        override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
            _connectionStatus.value = false
        }

        override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
            _connectionStatus.value = false
        }
    }
}
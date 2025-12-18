package com.example.nursealarmapp.parser

import android.util.Log
import com.example.nursealarmapp.models.GeneralWardEvent
import com.google.gson.Gson
import com.google.gson.JsonObject
import com.google.gson.JsonSyntaxException

class GeneralWardEventParser {

    private val gson = Gson()

    fun parse(json: String): GeneralWardEvent {
        return try {
            val jsonObject = gson.fromJson(json, JsonObject::class.java)
            val eventType = jsonObject.get("event")?.asString ?: "unknown"

            when (eventType) {
                "connected" -> gson.fromJson(json, GeneralWardEvent.Connected::class.java)
                "vital_signs_update" -> gson.fromJson(json, GeneralWardEvent.VitalsUpdate::class.java)
                "heartbeat" -> gson.fromJson(json, GeneralWardEvent.Heartbeat::class.java)
                "alarm_triggered" -> {
                    try {
                        Log.d("EventParser", "Attempting to parse 'alarm_triggered': $json")
                        val alarm = gson.fromJson(json, GeneralWardEvent.AlarmTriggered::class.java)
                        if (alarm.band_id == null) {
                            Log.e("EventParser", "'band_id' is null in the received alarm event.")
                            return GeneralWardEvent.Unknown("Parsed alarm with null band_id: $json")
                        }
                        Log.d("EventParser", "Successfully parsed 'alarm_triggered' with band_id: ${alarm.band_id}")
                        alarm
                    } catch (e: JsonSyntaxException) {
                        Log.e("EventParser", "Failed to parse 'alarm_triggered' event.", e)
                        GeneralWardEvent.Unknown("Failed to parse alarm: $json")
                    }
                }
                else -> GeneralWardEvent.Unknown(json)
            }
        } catch (e: Exception) {
            Log.e("EventParser", "Generic parsing error.", e)
            GeneralWardEvent.Unknown("Error parsing general event: $json")
        }
    }
}
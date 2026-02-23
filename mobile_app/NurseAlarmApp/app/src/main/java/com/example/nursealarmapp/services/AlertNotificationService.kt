package com.example.nursealarmapp.services

import android.content.Context
import android.media.AudioAttributes
import android.media.MediaPlayer
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.speech.tts.TextToSpeech
import android.util.Log
import com.example.nursealarmapp.R
import java.util.*

class AlertNotificationService(private val context: Context) {

    private var mediaPlayer: MediaPlayer? = null
    private var textToSpeech: TextToSpeech? = null
    private var ttsInitialized = false

    init {
        // Initialize Text-to-Speech
        textToSpeech = TextToSpeech(context) { status ->
            if (status == TextToSpeech.SUCCESS) {
                textToSpeech?.language = Locale.US
                ttsInitialized = true
                Log.d("AlertService", "TTS initialized successfully")
            } else {
                Log.e("AlertService", "TTS initialization failed")
            }
        }
    }

    fun playAlertWithVoice(patientName: String, condition: String, heartRate: Int, spO2: Int, temperature: Double) {
        // Play alarm sound first
        playAlarmSound()
        
        // Vibrate phone
        vibratePhone()
        
        // Speak the alert message
        val message = "Alert! $patientName. Critical condition. Heart rate $heartRate BPM. Oxygen $spO2 percent. Temperature $temperature degrees."
        speakAlert(message)
    }

    private fun playAlarmSound() {
        try {
            // Release any existing MediaPlayer
            mediaPlayer?.release()
            
            // Create new MediaPlayer with alarm sound
            mediaPlayer = MediaPlayer.create(context, R.raw.alert_sound)
            mediaPlayer?.setAudioAttributes(
                AudioAttributes.Builder()
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                    .setUsage(AudioAttributes.USAGE_ALARM)
                    .build()
            )
            mediaPlayer?.isLooping = false
            mediaPlayer?.start()
            
            Log.d("AlertService", "Playing alarm sound")
        } catch (e: Exception) {
            Log.e("AlertService", "Error playing alarm sound: ${e.message}")
        }
    }

    private fun speakAlert(message: String) {
        if (ttsInitialized) {
            // Wait for alarm sound to finish (approx 2 seconds), then speak
            android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
                textToSpeech?.speak(message, TextToSpeech.QUEUE_FLUSH, null, "alert")
                Log.d("AlertService", "Speaking: $message")
            }, 2000)
        } else {
            Log.w("AlertService", "TTS not initialized yet")
        }
    }

    private fun vibratePhone() {
        try {
            val vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                val vibratorManager = context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager
                vibratorManager.defaultVibrator
            } else {
                @Suppress("DEPRECATION")
                context.getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
            }

            // Create vibration pattern: wait 0ms, vibrate 1000ms, wait 500ms, vibrate 1000ms
            val pattern = longArrayOf(0, 1000, 500, 1000, 500, 1000)
            
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator.vibrate(VibrationEffect.createWaveform(pattern, -1))
            } else {
                @Suppress("DEPRECATION")
                vibrator.vibrate(pattern, -1)
            }
            
            Log.d("AlertService", "Vibrating phone")
        } catch (e: Exception) {
            Log.e("AlertService", "Error vibrating phone: ${e.message}")
        }
    }

    fun stopAll() {
        mediaPlayer?.stop()
        mediaPlayer?.release()
        mediaPlayer = null
        
        textToSpeech?.stop()
    }

    fun release() {
        stopAll()
        textToSpeech?.shutdown()
        textToSpeech = null
    }
}

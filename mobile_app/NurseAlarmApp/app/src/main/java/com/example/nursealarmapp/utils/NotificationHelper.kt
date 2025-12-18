package com.example.nursealarmapp.utils

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.media.RingtoneManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat

class NotificationHelper(private val context: Context) {

    private val notificationManager = NotificationManagerCompat.from(context)

    init {
        createNotificationChannel()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                Constants.CHANNEL_ID,
                Constants.CHANNEL_NAME,
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = Constants.CHANNEL_DESCRIPTION
                enableVibration(true)
                vibrationPattern = Constants.VIBRATION_PATTERN_ALARM
                setSound(RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM), null)
            }

            val manager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            manager.createNotificationChannel(channel)
        }
    }

    fun showGeneralWardAlarm(patientName: String) {
        val notification = NotificationCompat.Builder(context, Constants.CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_alert)
            .setContentTitle("ALARM: Patient $patientName needs attention!")
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setSound(RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM))
            .setAutoCancel(true)
            .build()

        try {
            notificationManager.notify(patientName.hashCode(), notification)
        } catch (e: SecurityException) {
            // Permission not granted
        }
    }

    fun showCriticalAlert(patientName: String, vitals: String) {
        val notification = NotificationCompat.Builder(context, Constants.CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_alert)
            .setContentTitle("🆘 CRITICAL ALERT: $patientName")
            .setContentText("Immediate attention required!")
            .setStyle(NotificationCompat.BigTextStyle().bigText("CRITICAL PATIENT: $patientName\n$vitals"))
            .setPriority(NotificationCompat.PRIORITY_MAX)
            .setAutoCancel(true)
            .build()

        try {
            notificationManager.notify(patientName.hashCode(), notification)
        } catch (e: SecurityException) {
            // Permission not granted
        }
    }
}
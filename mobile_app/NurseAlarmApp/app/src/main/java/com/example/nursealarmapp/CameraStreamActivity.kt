package com.example.nursealarmapp

import android.graphics.BitmapFactory
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.ImageView
import android.widget.ProgressBar
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.example.nursealarmapp.utils.NetworkPreferences
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.net.HttpURLConnection
import java.net.URL

class CameraStreamActivity : AppCompatActivity() {

    private lateinit var imageView: ImageView
    private lateinit var progressBar: ProgressBar
    private lateinit var tvStatus: TextView
    private lateinit var btnBack: Button
    private lateinit var networkPrefs: NetworkPreferences
    private var streamJob: Job? = null
    private var frameCount = 0

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_camera_stream)

        networkPrefs = NetworkPreferences.getInstance(this)
        val patientName = intent.getStringExtra("PATIENT_NAME") ?: "Unknown"

        imageView   = findViewById(R.id.imageViewCamera)
        progressBar = findViewById(R.id.progressBarCamera)
        tvStatus    = findViewById(R.id.tvCameraStatus)
        btnBack     = findViewById(R.id.btnBackFromCamera)

        findViewById<TextView>(R.id.tvCameraTitle).text = "Live Feed - $patientName"

        btnBack.setOnClickListener { finish() }

        startStreaming()
    }

    private fun startStreaming() {
        tvStatus.text = "Connecting..."
        progressBar.visibility = View.VISIBLE

        val snapshotUrl = "${networkPrefs.getBaseUrl()}/snapshot"

        streamJob = CoroutineScope(Dispatchers.IO).launch {
            var consecutiveErrors = 0
            while (isActive) {
                try {
                    val conn = (URL(snapshotUrl).openConnection() as HttpURLConnection).apply {
                        connectTimeout = 3000
                        readTimeout    = 3000
                        setRequestProperty("Cache-Control", "no-cache")
                    }
                    val bytes = conn.inputStream.readBytes()
                    conn.disconnect()

                    val bmp = BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
                    if (bmp != null) {
                        consecutiveErrors = 0
                        frameCount++
                        withContext(Dispatchers.Main) {
                            imageView.setImageBitmap(bmp)
                            progressBar.visibility = View.GONE
                            tvStatus.text = "Live ● (frame $frameCount)"
                            tvStatus.setTextColor(getColor(android.R.color.holo_green_dark))
                        }
                    }
                } catch (e: Exception) {
                    consecutiveErrors++
                    withContext(Dispatchers.Main) {
                        if (frameCount == 0) {
                            tvStatus.text = "Opening camera... (retry $consecutiveErrors)"
                        } else {
                            tvStatus.text = "Reconnecting... ($consecutiveErrors errors)"
                        }
                        tvStatus.setTextColor(getColor(android.R.color.holo_orange_light))
                    }
                    delay(1000)
                    continue
                }
                // ~3 fps — camera hardware captures at 1 fps, extra polls served from cache
                delay(330)
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        streamJob?.cancel()
    }
}

package com.example.nursealarmapp.utils

import android.content.Context
import android.content.SharedPreferences

/**
 * Network Preferences Manager
 * Handles storing and retrieving backend server configuration
 */
class NetworkPreferences(context: Context) {
    
    companion object {
        private const val PREFS_NAME = "network_preferences"
        private const val KEY_BASE_URL = "base_url"
        private const val KEY_WS_URL = "ws_url"
        
        // Default values (fallback if not configured)
        const val DEFAULT_BASE_URL = "http://10.138.1.240:8000"
        const val DEFAULT_WS_URL = "ws://10.138.1.240:8000"
        
        @Volatile
        private var INSTANCE: NetworkPreferences? = null
        
        fun getInstance(context: Context): NetworkPreferences {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: NetworkPreferences(context.applicationContext).also { INSTANCE = it }
            }
        }
    }
    
    private val prefs: SharedPreferences = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    
    /**
     * Get the configured backend base URL
     */
    fun getBaseUrl(): String {
        return prefs.getString(KEY_BASE_URL, Constants.BASE_URL) ?: Constants.BASE_URL
    }
    
    /**
     * Get the configured WebSocket URL
     */
    fun getWsUrl(): String {
        return prefs.getString(KEY_WS_URL, Constants.WS_URL) ?: Constants.WS_URL
    }
    
    /**
     * Save backend configuration
     * Automatically generates WS URL from HTTP URL if not provided
     */
    fun saveConfiguration(baseUrl: String, wsUrl: String? = null) {
        val normalizedBaseUrl = normalizeUrl(baseUrl)
        val normalizedWsUrl = wsUrl?.let { normalizeUrl(it, isWebSocket = true) }
            ?: convertHttpToWs(normalizedBaseUrl)
        
        prefs.edit().apply {
            putString(KEY_BASE_URL, normalizedBaseUrl)
            putString(KEY_WS_URL, normalizedWsUrl)
            apply()
        }
    }
    
    /**
     * Save backend configuration from URL only (auto-generates WS URL)
     */
    fun saveBackendUrl(url: String) {
        val normalizedUrl = normalizeUrl(url)
        saveConfiguration(normalizedUrl)
    }
    
    /**
     * Reset to default configuration
     */
    fun resetToDefault() {
        prefs.edit().apply {
            putString(KEY_BASE_URL, Constants.BASE_URL)
            putString(KEY_WS_URL, Constants.WS_URL)
            apply()
        }
    }
    
    /**
     * Check if custom configuration is set (different from defaults)
     */
    fun hasCustomConfiguration(): Boolean {
        return getBaseUrl() != Constants.BASE_URL || getWsUrl() != Constants.WS_URL
    }
    
    /**
     * Clear all preferences
     */
    fun clear() {
        prefs.edit().clear().apply()
    }
    
    /**
     * Get stream URL for camera
     */
    fun getStreamUrl(): String {
        return "${getBaseUrl()}/stream"
    }
    
    /**
     * Normalize URL - ensure it has http:// or ws:// prefix and no trailing slash
     */
    private fun normalizeUrl(url: String, isWebSocket: Boolean = false): String {
        var normalized = url.trim()
        
        // Remove trailing slash
        if (normalized.endsWith("/")) {
            normalized = normalized.dropLast(1)
        }
        
        // Add protocol if missing
        if (!normalized.startsWith("http://") && !normalized.startsWith("https://") && 
            !normalized.startsWith("ws://") && !normalized.startsWith("wss://")) {
            normalized = if (isWebSocket) "ws://$normalized" else "http://$normalized"
        }
        
        return normalized
    }
    
    /**
     * Convert HTTP URL to WebSocket URL
     */
    private fun convertHttpToWs(httpUrl: String): String {
        return when {
            httpUrl.startsWith("https://") -> httpUrl.replace("https://", "wss://")
            httpUrl.startsWith("http://") -> httpUrl.replace("http://", "ws://")
            else -> "ws://$httpUrl"
        }
    }
    
    /**
     * Extract host and port from URL
     */
    fun getHostAndPort(): Pair<String, Int> {
        val baseUrl = getBaseUrl()
        val withoutProtocol = baseUrl.replace("http://", "").replace("https://", "")
        val parts = withoutProtocol.split(":")
        
        return if (parts.size >= 2) {
            val host = parts[0]
            val port = parts[1].toIntOrNull() ?: 8000
            Pair(host, port)
        } else {
            Pair(parts[0], 8000)
        }
    }
    
    /**
     * Get display-friendly configuration info
     */
    fun getConfigurationInfo(): Map<String, String> {
        val (host, port) = getHostAndPort()
        return mapOf(
            "baseUrl" to getBaseUrl(),
            "wsUrl" to getWsUrl(),
            "streamUrl" to getStreamUrl(),
            "host" to host,
            "port" to port.toString(),
            "isCustom" to hasCustomConfiguration().toString()
        )
    }
}

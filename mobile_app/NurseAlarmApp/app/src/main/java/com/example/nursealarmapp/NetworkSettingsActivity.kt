package com.example.nursealarmapp

import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.example.nursealarmapp.ui.theme.NurseAlarmAppTheme
import com.example.nursealarmapp.utils.NetworkPreferences
import com.journeyapps.barcodescanner.ScanContract
import com.journeyapps.barcodescanner.ScanOptions
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.util.concurrent.TimeUnit

class NetworkSettingsActivity : ComponentActivity() {
    
    private lateinit var networkPrefs: NetworkPreferences
    
    // QR Code Scanner launcher
    private val barcodeLauncher = registerForActivityResult(ScanContract()) { result ->
        result.contents?.let { scannedUrl ->
            handleScannedUrl(scannedUrl)
        }
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        networkPrefs = NetworkPreferences.getInstance(this)
        
        setContent {
            NurseAlarmAppTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    NetworkSettingsScreen()
                }
            }
        }
    }
    
    @OptIn(ExperimentalMaterial3Api::class)
    @Composable
    fun NetworkSettingsScreen() {
        var backendUrl by remember { mutableStateOf(networkPrefs.getBaseUrl()) }
        var isTestingConnection by remember { mutableStateOf(false) }
        var connectionStatus by remember { mutableStateOf<ConnectionStatus?>(null) }
        var showResetDialog by remember { mutableStateOf(false) }
        
        val coroutineScope = rememberCoroutineScope()
        
        Scaffold(
            topBar = {
                TopAppBar(
                    title = { Text("Network Settings") },
                    navigationIcon = {
                        IconButton(onClick = { finish() }) {
                            Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(
                        containerColor = MaterialTheme.colorScheme.primary,
                        titleContentColor = MaterialTheme.colorScheme.onPrimary,
                        navigationIconContentColor = MaterialTheme.colorScheme.onPrimary
                    )
                )
            }
        ) { paddingValues ->
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .padding(16.dp)
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // Header Card
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.primaryContainer
                    )
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.Settings,
                            contentDescription = null,
                            modifier = Modifier.size(40.dp),
                            tint = MaterialTheme.colorScheme.onPrimaryContainer
                        )
                        Text(
                            text = "Backend Server Configuration",
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold
                        )
                        Text(
                            text = "Configure the backend server address to connect to the Patient Monitoring System",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
                        )
                    }
                }
                
                // URL Input Section
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Text(
                            text = "Backend URL",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.SemiBold
                        )
                        
                        OutlinedTextField(
                            value = backendUrl,
                            onValueChange = { 
                                backendUrl = it
                                connectionStatus = null  // Reset status when URL changes
                            },
                            label = { Text("Server Address") },
                            placeholder = { Text("http://192.168.1.100:8000") },
                            leadingIcon = {
                                Icon(Icons.Default.Home, contentDescription = null)
                            },
                            modifier = Modifier.fillMaxWidth(),
                            singleLine = true
                        )
                        
                        Text(
                            text = "Example: http://10.138.1.240:8000",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
                
                // Quick Actions
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Text(
                            text = "Quick Actions",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.SemiBold
                        )
                        
                        // Scan QR Code Button
                        Button(
                            onClick = { launchQRScanner() },
                            modifier = Modifier.fillMaxWidth(),
                            colors = ButtonDefaults.buttonColors(
                                containerColor = MaterialTheme.colorScheme.secondary
                            )
                        ) {
                            Icon(
                                imageVector = Icons.Default.QrCodeScanner,
                                contentDescription = null,
                                modifier = Modifier.size(20.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Scan QR Code")
                        }
                        
                        // Test Connection Button
                        Button(
                            onClick = {
                                coroutineScope.launch {
                                    isTestingConnection = true
                                    connectionStatus = testConnection(backendUrl)
                                    isTestingConnection = false
                                }
                            },
                            modifier = Modifier.fillMaxWidth(),
                            enabled = !isTestingConnection && backendUrl.isNotBlank()
                        ) {
                            if (isTestingConnection) {
                                CircularProgressIndicator(
                                    modifier = Modifier.size(20.dp),
                                    color = MaterialTheme.colorScheme.onPrimary,
                                    strokeWidth = 2.dp
                                )
                            } else {
                                Icon(
                                    imageVector = Icons.Default.CheckCircle,
                                    contentDescription = null,
                                    modifier = Modifier.size(20.dp)
                                )
                            }
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(if (isTestingConnection) "Testing..." else "Test Connection")
                        }
                    }
                }
                
                // Connection Status
                connectionStatus?.let { status ->
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(
                            containerColor = if (status.success) 
                                MaterialTheme.colorScheme.tertiaryContainer 
                            else 
                                MaterialTheme.colorScheme.errorContainer
                        )
                    ) {
                        Row(
                            modifier = Modifier.padding(16.dp),
                            horizontalArrangement = Arrangement.spacedBy(12.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                imageVector = if (status.success) Icons.Default.CheckCircle else Icons.Filled.Error,
                                contentDescription = null,
                                tint = if (status.success) 
                                    MaterialTheme.colorScheme.onTertiaryContainer 
                                else 
                                    MaterialTheme.colorScheme.onErrorContainer
                            )
                            Column {
                                Text(
                                    text = if (status.success) "Connection Successful" else "Connection Failed",
                                    style = MaterialTheme.typography.titleSmall,
                                    fontWeight = FontWeight.SemiBold
                                )
                                Text(
                                    text = status.message,
                                    style = MaterialTheme.typography.bodySmall
                                )
                                if (status.success && status.responseTime != null) {
                                    Text(
                                        text = "Response time: ${status.responseTime}ms",
                                        style = MaterialTheme.typography.bodySmall
                                    )
                                }
                            }
                        }
                    }
                }
                
                // Current Configuration Info
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Text(
                            text = "Current Configuration",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.SemiBold
                        )
                        
                        val config = networkPrefs.getConfigurationInfo()
                        ConfigItem("HTTP URL", config["baseUrl"] ?: "Not set")
                        ConfigItem("WebSocket URL", config["wsUrl"] ?: "Not set")
                        ConfigItem("Stream URL", config["streamUrl"] ?: "Not set")
                        ConfigItem("Host", config["host"] ?: "Not set")
                        ConfigItem("Port", config["port"] ?: "Not set")
                    }
                }
                
                Spacer(modifier = Modifier.weight(1f))
                
                // Action Buttons
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    // Reset Button
                    OutlinedButton(
                        onClick = { showResetDialog = true },
                        modifier = Modifier.weight(1f)
                    ) {
                        Icon(Icons.Default.Refresh, contentDescription = null)
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("Reset")
                    }
                    
                    // Save Button
                    Button(
                        onClick = {
                            saveConfiguration(backendUrl)
                        },
                        modifier = Modifier.weight(1f),
                        enabled = backendUrl.isNotBlank()
                    ) {
                        Icon(Icons.Filled.Save, contentDescription = null)
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("Save")
                    }
                }
            }
        }
        
        // Reset Confirmation Dialog
        if (showResetDialog) {
            AlertDialog(
                onDismissRequest = { showResetDialog = false },
                title = { Text("Reset to Default?") },
                text = { Text("This will reset the backend URL to the default value: ${NetworkPreferences.DEFAULT_BASE_URL}") },
                confirmButton = {
                    TextButton(
                        onClick = {
                            networkPrefs.resetToDefault()
                            backendUrl = networkPrefs.getBaseUrl()
                            connectionStatus = null
                            showResetDialog = false
                            Toast.makeText(this@NetworkSettingsActivity, "Reset to default configuration", Toast.LENGTH_SHORT).show()
                        }
                    ) {
                        Text("Reset")
                    }
                },
                dismissButton = {
                    TextButton(onClick = { showResetDialog = false }) {
                        Text("Cancel")
                    }
                }
            )
        }
    }
    
    @Composable
    fun ConfigItem(label: String, value: String) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text(
                text = label,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Text(
                text = value,
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.Medium
            )
        }
    }
    
    private fun launchQRScanner() {
        val options = ScanOptions().apply {
            setDesiredBarcodeFormats(ScanOptions.QR_CODE)
            setPrompt("Scan QR code from backend server")
            setBeepEnabled(true)
            setOrientationLocked(false)
        }
        barcodeLauncher.launch(options)
    }
    
    private fun handleScannedUrl(url: String) {
        // Validate URL format
        if (url.startsWith("http://") || url.startsWith("https://")) {
            networkPrefs.saveBackendUrl(url)
            Toast.makeText(this, "Backend URL updated from QR code", Toast.LENGTH_SHORT).show()
            // Restart activity to refresh UI
            recreate()
        } else {
            Toast.makeText(this, "Invalid URL format in QR code", Toast.LENGTH_LONG).show()
        }
    }
    
    private fun saveConfiguration(url: String) {
        if (url.isBlank()) {
            Toast.makeText(this, "Please enter a valid URL", Toast.LENGTH_SHORT).show()
            return
        }
        
        networkPrefs.saveBackendUrl(url)
        Toast.makeText(this, "Configuration saved successfully", Toast.LENGTH_SHORT).show()
        setResult(RESULT_OK)
        finish()
    }
    
    private suspend fun testConnection(url: String): ConnectionStatus {
        return withContext(Dispatchers.IO) {
            try {
                val client = OkHttpClient.Builder()
                    .connectTimeout(5, TimeUnit.SECONDS)
                    .readTimeout(5, TimeUnit.SECONDS)
                    .build()
                
                val normalizedUrl = if (!url.startsWith("http")) "http://$url" else url
                val testUrl = "$normalizedUrl/api/config"
                
                val request = Request.Builder()
                    .url(testUrl)
                    .build()
                
                val startTime = System.currentTimeMillis()
                val response = client.newCall(request).execute()
                val responseTime = System.currentTimeMillis() - startTime
                
                if (response.isSuccessful) {
                    ConnectionStatus(
                        success = true,
                        message = "Successfully connected to backend server",
                        responseTime = responseTime
                    )
                } else {
                    ConnectionStatus(
                        success = false,
                        message = "Server returned error: ${response.code}",
                        responseTime = null
                    )
                }
            } catch (e: Exception) {
                ConnectionStatus(
                    success = false,
                    message = "Connection failed: ${e.message?.take(50) ?: "Unknown error"}",
                    responseTime = null
                )
            }
        }
    }
    
    data class ConnectionStatus(
        val success: Boolean,
        val message: String,
        val responseTime: Long?
    )
}

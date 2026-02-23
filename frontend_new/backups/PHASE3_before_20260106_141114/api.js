import axios from 'axios';

// Base API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`[API Request] ${config.method.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`[API Response] ${response.config.url}`, response.status);
    return response;
  },
  (error) => {
    console.error('[API Error]', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// ===========================
// PATIENT MANAGEMENT APIs
// ===========================

/**
 * Admit a new patient and bind to BAND_01
 * @param {Object} patientData - Patient information
 * @param {string} patientData.name - Patient name (1-255 chars)
 * @param {number} patientData.age - Patient age (1-149)
 * @param {string} patientData.problem - Patient problem/condition
 * @param {string} patientData.patient_type - 'GENERAL' or 'CRITICAL'
 * @param {boolean} [patientData.demo_mode] - Enable demo mode
 * @param {string} [patientData.demo_scenario] - Demo scenario type
 * @returns {Promise} Patient response with band assignment
 */
export const admitPatient = async (patientData) => {
  const response = await apiClient.post('/api/patient/admit', patientData);
  return response.data;
};

/**
 * Discharge a patient by ID
 * @param {number} patientId - Patient ID to discharge
 * @returns {Promise} Discharge confirmation
 */
export const dischargePatient = async (patientId) => {
  const response = await apiClient.post(`/api/patient/discharge/${patientId}`);
  return response.data;
};

/**
 * Get currently active patient with band assignment
 * @returns {Promise} Active patient data or null
 */
export const getActivePatient = async () => {
  const response = await apiClient.get('/api/patient/active');
  return response.data;
};

/**
 * Get specific patient by ID
 * @param {number} patientId - Patient ID
 * @returns {Promise} Patient data
 */
export const getPatientById = async (patientId) => {
  const response = await apiClient.get(`/api/patient/${patientId}`);
  return response.data;
};

/**
 * Get alarm history for a patient
 * @param {number} patientId - Patient ID
 * @param {number} [limit=50] - Maximum number of records
 * @returns {Promise} Array of alarm events
 */
export const getPatientAlarmHistory = async (patientId, limit = 50) => {
  const response = await apiClient.get(`/api/patient/${patientId}/alarm-history`, {
    params: { limit },
  });
  return response.data;
};

/**
 * Get available diseases for a ward type
 * @param {string} wardType - 'general' or 'critical'
 * @returns {Promise} Array of disease names
 */
export const getDiseases = async (wardType) => {
  const response = await apiClient.get(`/api/diseases/${wardType}`);
  return response.data;
};

/**
 * Get detailed information about a disease
 * @param {string} wardType - 'general' or 'critical'
 * @param {string} diseaseName - Name of the disease
 * @returns {Promise} Disease information including symptoms and medications
 */
export const getDiseaseInfo = async (wardType, diseaseName) => {
  const response = await apiClient.get(`/api/diseases/${wardType}/${encodeURIComponent(diseaseName)}`);
  return response.data;
};

// ===========================
// NURSE PROXIMITY APIs
// ===========================

/**
 * Register a nurse device for proximity monitoring
 * @param {string} [deviceInfo] - Device information
 * @returns {Promise} Nurse session data
 */
export const registerNurse = async (deviceInfo = '') => {
  const response = await apiClient.post('/api/nurse/register', { device_info: deviceInfo });
  return response.data;
};

/**
 * Update nurse proximity with detected BLE devices
 * @param {string} sessionId - Nurse session ID
 * @param {Array<string>} bleDevices - List of detected BLE device IDs
 * @param {Object} [rssiValues] - RSSI values for each device
 * @returns {Promise} Update confirmation
 */
export const updateNurseProximity = async (sessionId, bleDevices, rssiValues = {}) => {
  const response = await apiClient.post('/api/nurse/proximity', {
    session_id: sessionId,
    ble_devices: bleDevices,
    rssi_values: rssiValues,
  });
  return response.data;
};

/**
 * Get nurse session status
 * @param {string} sessionId - Nurse session ID
 * @returns {Promise} Nurse session data
 */
export const getNurseStatus = async (sessionId) => {
  const response = await apiClient.get(`/api/nurse/status/${sessionId}`);
  return response.data;
};

// ===========================
// SENSOR DATA API
// ===========================

/**
 * Send sensor data (typically used by ESP32, but can be used for testing)
 * @param {Object} sensorData - Sensor readings
 * @param {string} [sensorData.band_id='BAND_01'] - Band ID
 * @param {number} sensorData.HR - Heart Rate
 * @param {number} sensorData.SpO2 - Blood Oxygen
 * @param {number} sensorData.Temp - Temperature
 * @param {Array<string>} [sensorData.ble_devices_nearby] - Nearby nurse sessions
 * @param {boolean} [sensorData.demo_mode] - Demo mode flag
 * @returns {Promise} Sensor processing result
 */
export const sendSensorData = async (sensorData) => {
  const response = await apiClient.post('/api/sensor-data', sensorData);
  return response.data;
};

// ===========================
// HEALTH CHECK API
// ===========================

/**
 * Check API health and status
 * @returns {Promise} API status
 */
export const getApiHealth = async () => {
  const response = await apiClient.get('/');
  return response.data;
};

// ===========================
// LEGACY APIs (Backward Compatibility)
// ===========================

/**
 * Predict critical ward alarm (legacy endpoint)
 * @param {Object} vitals - Vital signs
 * @returns {Promise} Alarm prediction
 */
export const predictCritical = async (vitals) => {
  const response = await apiClient.post('/predict_critical', vitals);
  return response.data;
};

/**
 * Predict general ward alarm (legacy endpoint)
 * @param {Object} vitals - Vital signs
 * @returns {Promise} Alarm prediction
 */
export const predictGeneral = async (vitals) => {
  const response = await apiClient.post('/predict_general', vitals);
  return response.data;
};

// ===========================
// PATIENT HISTORY APIs
// ===========================

/**
 * Get discharged patient history (all records by default)
 * @param {number} [limit] - Optional maximum number of records
 * @returns {Promise} Array of discharged patients
 */
export const getDischargedPatients = async (limit = null) => {
  const params = limit ? { limit } : {};
  const response = await apiClient.get('/api/patients/discharged', { params });
  return response.data;
};

/**
 * Get patient statistics
 * @returns {Promise} Patient admission/discharge statistics
 */
export const getPatientStatistics = async () => {
  const response = await apiClient.get('/api/patients/statistics');
  return response.data;
};

// ===========================
// UTILITY FUNCTIONS
// ===========================

/**
 * Check if backend is reachable
 * @returns {Promise<boolean>} True if backend is up
 */
export const checkBackendConnection = async () => {
  try {
    await getApiHealth();
    return true;
  } catch {
    return false;
  }
};

export default apiClient;

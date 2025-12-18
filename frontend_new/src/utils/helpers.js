import { format, formatDistanceToNow } from 'date-fns';

/**
 * Format timestamp to readable date/time
 * @param {string|Date} timestamp - Timestamp to format
 * @param {string} formatStr - Date format string
 * @returns {string} Formatted date string
 */
export const formatTimestamp = (timestamp, formatStr = 'MMM dd, yyyy HH:mm:ss') => {
  if (!timestamp) return 'N/A';
  
  try {
    const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
    return format(date, formatStr);
  } catch (error) {
    console.error('Error formatting timestamp:', error);
    return 'Invalid date';
  }
};

/**
 * Format timestamp as relative time (e.g., "2 minutes ago")
 * @param {string|Date} timestamp - Timestamp to format
 * @returns {string} Relative time string
 */
export const formatRelativeTime = (timestamp) => {
  if (!timestamp) return 'N/A';
  
  try {
    const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
    return formatDistanceToNow(date, { addSuffix: true });
  } catch (error) {
    console.error('Error formatting relative time:', error);
    return 'Unknown';
  }
};

/**
 * Check if vital signs are within normal ranges
 * @param {Object} vitals - Vital signs object
 * @returns {Object} Status for each vital
 */
export const checkVitalsStatus = (vitals) => {
  if (!vitals) return {};
  
  const status = {};
  
  // Heart Rate (60-100 bpm normal)
  if (vitals.HR !== undefined) {
    status.HR = {
      value: vitals.HR,
      normal: vitals.HR >= 60 && vitals.HR <= 100,
      critical: vitals.HR < 40 || vitals.HR > 120,
    };
  }
  
  // SpO2 (95-100% normal)
  if (vitals.SpO2 !== undefined) {
    status.SpO2 = {
      value: vitals.SpO2,
      normal: vitals.SpO2 >= 95,
      critical: vitals.SpO2 < 90,
    };
  }
  
  // Temperature (36.5-37.5°C normal)
  if (vitals.Temp !== undefined) {
    status.Temp = {
      value: vitals.Temp,
      normal: vitals.Temp >= 36.5 && vitals.Temp <= 37.5,
      critical: vitals.Temp < 35 || vitals.Temp > 39,
    };
  }
  
  // Blood Pressure Systolic (90-120 mmHg normal)
  if (vitals.BP_sys !== undefined) {
    status.BP_sys = {
      value: vitals.BP_sys,
      normal: vitals.BP_sys >= 90 && vitals.BP_sys <= 120,
      critical: vitals.BP_sys < 80 || vitals.BP_sys > 160,
    };
  }
  
  // Blood Pressure Diastolic (60-80 mmHg normal)
  if (vitals.BP_dia !== undefined) {
    status.BP_dia = {
      value: vitals.BP_dia,
      normal: vitals.BP_dia >= 60 && vitals.BP_dia <= 80,
      critical: vitals.BP_dia < 50 || vitals.BP_dia > 100,
    };
  }
  
  // Glucose (70-140 mg/dL normal)
  if (vitals.Glucose !== undefined) {
    status.Glucose = {
      value: vitals.Glucose,
      normal: vitals.Glucose >= 70 && vitals.Glucose <= 140,
      critical: vitals.Glucose < 50 || vitals.Glucose > 200,
    };
  }
  
  return status;
};

/**
 * Get color for alarm status
 * @param {string} action - Alarm action (SUPPRESS, PROXIMITY_ALERT, DASHBOARD_ALERT)
 * @returns {string} MUI color name
 */
export const getAlarmColor = (action) => {
  switch (action) {
    case 'SUPPRESS':
      return 'success';
    case 'PROXIMITY_ALERT':
      return 'warning';
    case 'DASHBOARD_ALERT':
      return 'error';
    default:
      return 'default';
  }
};

/**
 * Get color for vital sign status
 * @param {boolean} normal - Is vital normal?
 * @param {boolean} critical - Is vital critical?
 * @returns {string} MUI color name
 */
export const getVitalColor = (normal, critical) => {
  if (critical) return 'error';
  if (!normal) return 'warning';
  return 'success';
};

/**
 * Format vital sign value with unit
 * @param {string} vitalType - Type of vital (HR, SpO2, Temp, etc.)
 * @param {number} value - Vital value
 * @returns {string} Formatted string with unit
 */
export const formatVital = (vitalType, value) => {
  if (value === null || value === undefined) return 'N/A';
  
  const units = {
    HR: 'bpm',
    SpO2: '%',
    Temp: '°C',
    BP_sys: 'mmHg',
    BP_dia: 'mmHg',
    Glucose: 'mg/dL',
  };
  
  const unit = units[vitalType] || '';
  return `${value}${unit ? ' ' + unit : ''}`;
};

/**
 * Get vital sign name
 * @param {string} vitalType - Type of vital (HR, SpO2, etc.)
 * @returns {string} Full name
 */
export const getVitalName = (vitalType) => {
  const names = {
    HR: 'Heart Rate',
    SpO2: 'Blood Oxygen',
    Temp: 'Temperature',
    BP_sys: 'Blood Pressure (Systolic)',
    BP_dia: 'Blood Pressure (Diastolic)',
    Glucose: 'Blood Glucose',
  };
  
  return names[vitalType] || vitalType;
};

/**
 * Generate demo vitals for testing
 * @param {string} scenario - Demo scenario type
 * @returns {Object} Demo vitals
 */
export const generateDemoVitals = (scenario = 'NORMAL') => {
  const scenarios = {
    NORMAL: {
      HR: 75,
      SpO2: 98,
      Temp: 37.0,
      BP_sys: 115,
      BP_dia: 75,
      Glucose: 100,
    },
    MILD_DETERIORATION: {
      HR: 95,
      SpO2: 93,
      Temp: 37.8,
      BP_sys: 135,
      BP_dia: 85,
      Glucose: 150,
    },
    CRITICAL_EMERGENCY: {
      HR: 125,
      SpO2: 88,
      Temp: 39.5,
      BP_sys: 170,
      BP_dia: 105,
      Glucose: 220,
    },
    FALSE_POSITIVE: {
      HR: 59,
      SpO2: 96,
      Temp: 37.2,
      BP_sys: 141,
      BP_dia: 79,
      Glucose: 98,
    },
  };
  
  return scenarios[scenario] || scenarios.NORMAL;
};

/**
 * Validate patient admission form data
 * @param {Object} data - Form data
 * @returns {Object} Validation result with errors
 */
export const validatePatientForm = (data) => {
  const errors = {};
  
  if (!data.name || data.name.trim().length === 0) {
    errors.name = 'Name is required';
  } else if (data.name.length > 255) {
    errors.name = 'Name must be less than 255 characters';
  }
  
  if (!data.age) {
    errors.age = 'Age is required';
  } else if (data.age < 1 || data.age > 149) {
    errors.age = 'Age must be between 1 and 149';
  }
  
  if (!data.problem || data.problem.trim().length === 0) {
    errors.problem = 'Problem/condition is required';
  }
  
  if (!data.patient_type) {
    errors.patient_type = 'Patient type is required';
  } else if (!['GENERAL', 'CRITICAL'].includes(data.patient_type)) {
    errors.patient_type = 'Invalid patient type';
  }
  
  if (data.demo_mode && !data.demo_scenario) {
    errors.demo_scenario = 'Demo scenario is required when demo mode is enabled';
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
};

export default {
  formatTimestamp,
  formatRelativeTime,
  checkVitalsStatus,
  getAlarmColor,
  getVitalColor,
  formatVital,
  getVitalName,
  generateDemoVitals,
  validatePatientForm,
};

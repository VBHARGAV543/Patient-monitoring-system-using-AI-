import { create } from 'zustand';

/**
 * Patient Store - Global state management for patient data
 */
export const usePatientStore = create((set, get) => ({
  // Current active patient
  activePatient: null,
  
  // Patient vitals (latest readings)
  currentVitals: null,
  
  // Alarm status
  alarmStatus: {
    active: false,
    action: null,
    message: '',
    timestamp: null,
  },
  
  // Ward type
  wardType: 'GENERAL', // 'GENERAL' or 'CRITICAL'
  
  // Connection status
  backendConnected: false,
  wsConnected: false,
  
  // Alarm history cache
  alarmHistory: [],
  
  // Loading states
  isLoading: false,
  error: null,

  // Actions
  setActivePatient: (patient) => set({ activePatient: patient, error: null }),
  
  setCurrentVitals: (vitals) => set({ currentVitals: vitals }),
  
  setAlarmStatus: (status) => set({ alarmStatus: status }),
  
  setWardType: (wardType) => {
    set({ wardType });
    // Clear patient when switching wards (optional)
    // set({ activePatient: null, currentVitals: null });
  },
  
  setBackendConnected: (connected) => set({ backendConnected: connected }),
  
  setWsConnected: (connected) => set({ wsConnected: connected }),
  
  setAlarmHistory: (history) => set({ alarmHistory: history }),
  
  addAlarmEvent: (event) => set((state) => ({
    alarmHistory: [event, ...state.alarmHistory].slice(0, 100), // Keep last 100
  })),
  
  setLoading: (isLoading) => set({ isLoading }),
  
  setError: (error) => set({ error }),
  
  clearError: () => set({ error: null }),
  
  clearPatient: () => set({
    activePatient: null,
    currentVitals: null,
    alarmStatus: {
      active: false,
      action: null,
      message: '',
      timestamp: null,
    },
    alarmHistory: [],
  }),
  
  // Update from WebSocket sensor data
  updateFromSensorData: (data) => {
    const { result } = data;
    
    if (result) {
      set({
        currentVitals: result.vitals,
        alarmStatus: {
          active: result.alarm_decision?.alarm_active || false,
          action: result.alarm_decision?.action || null,
          message: result.alarm_decision?.message || '',
          timestamp: result.timestamp,
        },
      });
      
      // Add to history
      const event = {
        id: result.alarm_event_id || Date.now(),
        timestamp: result.timestamp,
        vitals: result.vitals,
        alarm_status: result.alarm_decision?.action || 'UNKNOWN',
        nurse_in_proximity: result.nurse_in_proximity || false,
      };
      
      get().addAlarmEvent(event);
    }
  },
}));

export default usePatientStore;

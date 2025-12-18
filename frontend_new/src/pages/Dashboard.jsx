import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Grid,
  Paper,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Chip,
  Card,
  CardContent,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Favorite,
  Opacity,
  Thermostat,
  MonitorHeart,
  LocalHospital,
  Sensors,
  Person,
  ExitToApp,
  History,
  Refresh,
  MedicalServices,
  LocalPharmacy,
  Warning,
  ContactPhone,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import { usePatientStore } from '../stores/patientStore';
import { useDashboardWebSocket } from '../hooks/useWebSocket';
import { getActivePatient, dischargePatient, checkBackendConnection } from '../services/api';
import {
  formatTimestamp,
  formatRelativeTime,
  checkVitalsStatus,
  getAlarmColor,
  getVitalColor,
} from '../utils/helpers';
import AlarmHistoryModal from '../components/AlarmHistoryModal';
import ConnectionStatus from '../components/ConnectionStatus';

const Dashboard = () => {
  const navigate = useNavigate();
  
  const {
    activePatient,
    currentVitals,
    alarmStatus,
    setActivePatient,
    updateFromSensorData,
    setWsConnected,
    setBackendConnected,
    clearPatient,
  } = usePatientStore();

  const [loading, setLoading] = useState(true);
  const [discharging, setDischarging] = useState(false);
  const [showDischargeDialog, setShowDischargeDialog] = useState(false);
  const [showAlarmHistory, setShowAlarmHistory] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);

  // WebSocket connection for real-time updates
  const { isConnected: wsConnected } = useDashboardWebSocket({
    onMessage: (data) => {
      console.log('Dashboard received WebSocket message:', data);
      
      // Handle different event types
      if (data.event === 'patient_admitted') {
        setActivePatient(data.patient);
        toast.success(`New patient admitted: ${data.patient.name}`);
      } else if (data.event === 'patient_discharged') {
        clearPatient();
        toast.info('Patient has been discharged');
      } else if (data.event === 'vital_signs_update') {
        // Update vitals from mock data system
        updateFromSensorData({
          result: {
            vitals: data.vitals,
            alarm_decision: {
              alarm_active: data.ml_prediction?.prediction === 1,
              action: data.ml_prediction?.prediction === 1 ? 'ALARM' : 'NORMAL',
              message: data.ml_prediction?.recommendation || 'Normal status',
            },
            timestamp: data.timestamp,
          }
        });
      } else if (data.event === 'alarm_triggered') {
        // Handle alarm trigger
        updateFromSensorData({
          result: {
            vitals: data.vitals,
            alarm_decision: {
              alarm_active: true,
              action: 'ALARM',
              message: data.prediction?.recommendation || 'Alarm triggered',
            },
            timestamp: data.timestamp,
          }
        });
      } else {
        // Legacy sensor data update
        updateFromSensorData(data);
      }
    },
    onConnect: () => {
      console.log('Dashboard WebSocket connected');
      setWsConnected(true);
      toast.success('Connected to monitoring system', { id: 'ws-connection' });
    },
    onDisconnect: () => {
      console.log('Dashboard WebSocket disconnected');
      setWsConnected(false);
      // Only show disconnect message once using toast ID
      toast.error('Disconnected from monitoring system', { id: 'ws-disconnect', duration: 3000 });
    },
  });

  // Load active patient on mount
  useEffect(() => {
    const loadActivePatient = async () => {
      try {
        setLoading(true);
        const patient = await getActivePatient();
        setActivePatient(patient);
      } catch (error) {
        console.error('Error loading active patient:', error);
        toast.error('Failed to load patient data');
      } finally {
        setLoading(false);
      }
    };

    loadActivePatient();
  }, [setActivePatient]);

  // Check backend connection periodically
  useEffect(() => {
    const checkConnection = async () => {
      const isOnline = await checkBackendConnection();
      setBackendOnline(isOnline);
      setBackendConnected(isOnline);
    };

    checkConnection();
    const interval = setInterval(checkConnection, 10000); // Check every 10 seconds

    return () => clearInterval(interval);
  }, [setBackendConnected]);

  // Handle patient discharge
  const handleDischarge = async () => {
    if (!activePatient) return;

    setDischarging(true);

    try {
      await dischargePatient(activePatient.id);
      toast.success(`Patient ${activePatient.name} discharged successfully`);
      clearPatient();
      setShowDischargeDialog(false);
    } catch (error) {
      console.error('Error discharging patient:', error);
      toast.error('Failed to discharge patient');
    } finally {
      setDischarging(false);
    }
  };

  // Navigate to admission page
  const handleAdmitPatient = () => {
    navigate('/admit');
  };

  // Get vital status indicators
  const vitalStatuses = currentVitals ? checkVitalsStatus(currentVitals) : {};

  // Loading state
  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
        <CircularProgress size={60} />
      </Container>
    );
  }

  // No active patient
  if (!activePatient) {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          <Paper elevation={3} sx={{ p: 6, textAlign: 'center' }}>
            <LocalHospital sx={{ fontSize: 80, color: 'primary.main', mb: 2 }} />
            <Typography variant="h4" gutterBottom>
              No Active Patient
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
              There is currently no patient assigned to the monitoring band.
            </Typography>
            <Button
              variant="contained"
              size="large"
              startIcon={<Person />}
              onClick={handleAdmitPatient}
            >
              Admit New Patient
            </Button>
          </Paper>
        </motion.div>
      </Container>
    );
  }

  const MotionPaper = motion(Paper);

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Connection Status */}
      <ConnectionStatus backendConnected={backendOnline} wsConnected={wsConnected} />

      <Container maxWidth="xl" sx={{ py: 3 }}>
        {/* Header */}
        <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
            <Box>
              <Typography variant="h4" gutterBottom>
                Patient Monitoring Dashboard
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
                <Chip
                  icon={<Person />}
                  label={activePatient.name}
                  color="primary"
                  variant="outlined"
                />
                <Chip
                  label={`${activePatient.age} years old`}
                  variant="outlined"
                />
                <Chip
                  label={activePatient.patient_type === 'CRITICAL' ? 'Critical Ward' : 'General Ward'}
                  color={activePatient.patient_type === 'CRITICAL' ? 'error' : 'success'}
                />
                {activePatient.demo_mode && (
                  <Chip
                    label={`Demo: ${activePatient.demo_scenario || 'NORMAL'}`}
                    color="warning"
                  />
                )}
              </Box>
            </Box>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="outlined"
                startIcon={<History />}
                onClick={() => setShowAlarmHistory(true)}
              >
                Alarm History
              </Button>
              <Button
                variant="contained"
                color="error"
                startIcon={<ExitToApp />}
                onClick={() => setShowDischargeDialog(true)}
              >
                Discharge Patient
              </Button>
            </Box>
          </Box>
        </Paper>

        {/* Patient Info */}
        <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Patient Information
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="text.secondary">
                Problem/Condition:
              </Typography>
              <Typography variant="body1">{activePatient.problem}</Typography>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography variant="body2" color="text.secondary">
                Admission Time:
              </Typography>
              <Typography variant="body1">
                {formatTimestamp(activePatient.admission_time)}
              </Typography>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography variant="body2" color="text.secondary">
                Band ID:
              </Typography>
              <Typography variant="body1">{activePatient.band_id}</Typography>
            </Grid>
            
            {/* Medical Details if available */}
            {activePatient.gender && (
              <>
                <Grid item xs={12} md={3}>
                  <Typography variant="body2" color="text.secondary">
                    Gender:
                  </Typography>
                  <Typography variant="body1">{activePatient.gender}</Typography>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Typography variant="body2" color="text.secondary">
                    Blood Type:
                  </Typography>
                  <Typography variant="body1">{activePatient.blood_type || 'N/A'}</Typography>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Typography variant="body2" color="text.secondary">
                    Weight:
                  </Typography>
                  <Typography variant="body1">{activePatient.weight ? `${activePatient.weight} kg` : 'N/A'}</Typography>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Typography variant="body2" color="text.secondary">
                    Height:
                  </Typography>
                  <Typography variant="body1">{activePatient.height ? `${activePatient.height} cm` : 'N/A'}</Typography>
                </Grid>
              </>
            )}
            
            {/* Emergency Contact */}
            {activePatient.emergency_contact && (
              <>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="text.secondary">
                    Emergency Contact:
                  </Typography>
                  <Typography variant="body1">{activePatient.emergency_contact}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="text.secondary">
                    Emergency Phone:
                  </Typography>
                  <Typography variant="body1">{activePatient.emergency_phone || 'N/A'}</Typography>
                </Grid>
              </>
            )}
          </Grid>
        </Paper>

        {/* Medical History Section */}
        {(activePatient.medical_history || activePatient.allergies || activePatient.current_medications) && (
          <Grid container spacing={3} sx={{ mb: 3 }}>
            {/* Medical History */}
            {activePatient.medical_history && activePatient.medical_history.length > 0 && (
              <Grid item xs={12} md={4}>
                <Paper elevation={2} sx={{ p: 3, height: '100%' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <MedicalServices sx={{ mr: 1, color: 'primary.main' }} />
                    <Typography variant="h6">Medical History</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {activePatient.medical_history.map((condition, index) => (
                      <Chip
                        key={index}
                        label={condition}
                        color="primary"
                        variant="outlined"
                        size="small"
                      />
                    ))}
                  </Box>
                </Paper>
              </Grid>
            )}

            {/* Allergies */}
            {activePatient.allergies && activePatient.allergies.length > 0 && (
              <Grid item xs={12} md={4}>
                <Paper elevation={2} sx={{ p: 3, height: '100%', bgcolor: 'error.light', color: 'error.contrastText' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Warning sx={{ mr: 1 }} />
                    <Typography variant="h6">⚠️ Allergies</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {activePatient.allergies.map((allergy, index) => (
                      <Chip
                        key={index}
                        label={allergy}
                        color="error"
                        size="small"
                      />
                    ))}
                  </Box>
                </Paper>
              </Grid>
            )}

            {/* Current Medications */}
            {activePatient.current_medications && activePatient.current_medications.length > 0 && (
              <Grid item xs={12} md={4}>
                <Paper elevation={2} sx={{ p: 3, height: '100%' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <LocalPharmacy sx={{ mr: 1, color: 'success.main' }} />
                    <Typography variant="h6">Current Medications</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    {activePatient.current_medications.map((medication, index) => (
                      <Box key={index}>
                        <Typography variant="body2" fontWeight="bold">
                          {medication.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {medication.dosage} - {medication.frequency}
                        </Typography>
                      </Box>
                    ))}
                  </Box>
                </Paper>
              </Grid>
            )}
          </Grid>
        )}

        {/* Alarm Status */}
        <AnimatePresence>
          {alarmStatus.action && (
            <MotionPaper
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              elevation={3}
              sx={{
                p: 3,
                mb: 3,
                bgcolor: alarmStatus.active ? 'error.main' : 'success.main',
                color: 'white',
                animation: alarmStatus.active ? 'gentle-pulse 2s ease-in-out infinite, soft-glow 3s ease-in-out infinite' : 'none',
                transition: 'all 0.3s ease-in-out',
                border: alarmStatus.active ? '2px solid rgba(255, 255, 255, 0.3)' : 'none',
                background: alarmStatus.active 
                  ? 'linear-gradient(135deg, #f44336 0%, #d32f2f 100%)' 
                  : 'linear-gradient(135deg, #4caf50 0%, #388e3c 100%)',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Sensors sx={{ fontSize: 40 }} />
                <Box sx={{ flex: 1 }}>
                  <Typography variant="h5" gutterBottom>
                    {alarmStatus.active ? '⚠️ ALARM ACTIVE' : '✅ Normal Status'}
                  </Typography>
                  <Typography variant="body1">{alarmStatus.message}</Typography>
                  {alarmStatus.timestamp && (
                    <Typography variant="caption">
                      {formatRelativeTime(alarmStatus.timestamp)}
                    </Typography>
                  )}
                </Box>
                <Chip
                  label={alarmStatus.action}
                  color={getAlarmColor(alarmStatus.action)}
                  sx={{ fontWeight: 'bold' }}
                />
              </Box>
            </MotionPaper>
          )}
        </AnimatePresence>

        {/* Vital Signs */}
        <Typography variant="h5" gutterBottom sx={{ mt: 3, mb: 2 }}>
          Vital Signs
        </Typography>

        {!currentVitals && (
          <Alert severity="info" sx={{ mb: 3 }}>
            Waiting for sensor data... Make sure the monitoring device is active.
          </Alert>
        )}

        <Grid container spacing={3}>
          {/* Heart Rate */}
          <Grid item xs={12} sm={6} md={4}>
            <VitalCard
              icon={<Favorite />}
              title="Heart Rate"
              value={currentVitals?.HR}
              unit="bpm"
              status={vitalStatuses.HR}
            />
          </Grid>

          {/* Blood Oxygen */}
          <Grid item xs={12} sm={6} md={4}>
            <VitalCard
              icon={<Opacity />}
              title="Blood Oxygen (SpO2)"
              value={currentVitals?.SpO2}
              unit="%"
              status={vitalStatuses.SpO2}
            />
          </Grid>

          {/* Temperature */}
          <Grid item xs={12} sm={6} md={4}>
            <VitalCard
              icon={<Thermostat />}
              title="Temperature"
              value={currentVitals?.Temp}
              unit="°C"
              status={vitalStatuses.Temp}
            />
          </Grid>

          {/* Blood Pressure Systolic */}
          <Grid item xs={12} sm={6} md={4}>
            <VitalCard
              icon={<MonitorHeart />}
              title="BP (Systolic)"
              value={currentVitals?.BP_sys}
              unit="mmHg"
              status={vitalStatuses.BP_sys}
            />
          </Grid>

          {/* Blood Pressure Diastolic */}
          <Grid item xs={12} sm={6} md={4}>
            <VitalCard
              icon={<MonitorHeart />}
              title="BP (Diastolic)"
              value={currentVitals?.BP_dia}
              unit="mmHg"
              status={vitalStatuses.BP_dia}
            />
          </Grid>

          {/* Blood Glucose */}
          <Grid item xs={12} sm={6} md={4}>
            <VitalCard
              icon={<LocalHospital />}
              title="Blood Glucose"
              value={currentVitals?.Glucose}
              unit="mg/dL"
              status={vitalStatuses.Glucose}
            />
          </Grid>
        </Grid>
      </Container>

      {/* Discharge Confirmation Dialog */}
      <Dialog open={showDischargeDialog} onClose={() => setShowDischargeDialog(false)}>
        <DialogTitle>Confirm Discharge</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to discharge patient <strong>{activePatient.name}</strong>?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            This will release the monitoring band and stop all data collection for this patient.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowDischargeDialog(false)} disabled={discharging}>
            Cancel
          </Button>
          <Button
            onClick={handleDischarge}
            variant="contained"
            color="error"
            disabled={discharging}
            startIcon={discharging && <CircularProgress size={20} />}
          >
            {discharging ? 'Discharging...' : 'Discharge Patient'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Alarm History Modal */}
      {showAlarmHistory && (
        <AlarmHistoryModal
          open={showAlarmHistory}
          onClose={() => setShowAlarmHistory(false)}
          patientId={activePatient.id}
        />
      )}
    </Box>
  );
};

// Vital Sign Card Component
const VitalCard = ({ icon, title, value, unit, status }) => {
  const color = status
    ? getVitalColor(status.normal, status.critical)
    : 'default';

  return (
    <Card
      elevation={3}
      sx={{
        height: '100%',
        transition: 'transform 0.2s',
        '&:hover': { transform: 'scale(1.02)' },
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Box sx={{ mr: 2, color: `${color}.main` }}>{icon}</Box>
          <Typography variant="h6" component="div">
            {title}
          </Typography>
        </Box>
        <Typography variant="h3" component="div" color={`${color}.main`}>
          {value !== null && value !== undefined ? value : '--'}
          <Typography variant="h6" component="span" sx={{ ml: 1 }}>
            {unit}
          </Typography>
        </Typography>
        {status && (
          <Chip
            label={status.critical ? 'Critical' : status.normal ? 'Normal' : 'Warning'}
            color={color}
            size="small"
            sx={{ mt: 1 }}
          />
        )}
      </CardContent>
    </Card>
  );
};

export default Dashboard;

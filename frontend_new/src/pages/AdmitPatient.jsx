import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  TextField,
  RadioGroup,
  FormControlLabel,
  Radio,
  FormControl,
  FormLabel,
  Button,
  Checkbox,
  Select,
  MenuItem,
  InputLabel,
  Alert,
  CircularProgress,
  Box,
  Chip,
  Grid,
  Divider,
} from '@mui/material';
import { motion } from 'framer-motion';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import toast from 'react-hot-toast';
import { admitPatient, getActivePatient, getDiseases, getDiseaseInfo } from '../services/api';
import { usePatientStore } from '../stores/patientStore';

// Validation schema
const patientSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255, 'Name must be less than 255 characters'),
  age: z.coerce.number().min(1, 'Age must be at least 1').max(149, 'Age must be at most 149'),
  problem: z.string().min(1, 'Problem/condition is required'),
  patient_type: z.enum(['GENERAL', 'CRITICAL'], { required_error: 'Patient type is required' }),
  demo_mode: z.boolean().optional(),
  demo_scenario: z.enum(['NORMAL', 'MILD_DETERIORATION', 'CRITICAL_EMERGENCY', 'FALSE_POSITIVE']).optional(),
  disease: z.string().optional(),
  body_strength: z.enum(['strong', 'average', 'weak']).optional(),
  genetic_condition: z.enum(['healthy', 'hypertension_prone', 'diabetes_prone']).optional(),
  allergies: z.array(z.string()).optional(),
});

const AdmitPatient = () => {
  const navigate = useNavigate();
  const setActivePatient = usePatientStore((state) => state.setActivePatient);
  
  const [bandStatus, setBandStatus] = useState({ available: false, checking: true });
  const [submitting, setSubmitting] = useState(false);
  const [diseases, setDiseases] = useState([]);
  const [diseaseInfo, setDiseaseInfo] = useState(null);
  const [loadingDiseases, setLoadingDiseases] = useState(false);

  const {
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(patientSchema),
    defaultValues: {
      name: '',
      age: '',
      problem: '',
      patient_type: 'GENERAL',
      demo_mode: false,
      demo_scenario: 'NORMAL',
      disease: '',
      body_strength: 'average',
      genetic_condition: 'healthy',
      allergies: [],
    },
  });

  const demoMode = watch('demo_mode');
  const patientType = watch('patient_type');
  const selectedDisease = watch('disease');

  // Load diseases when patient type changes
  useEffect(() => {
    const loadDiseases = async () => {
      if (!patientType) return;
      
      setLoadingDiseases(true);
      try {
        const wardType = patientType === 'CRITICAL' ? 'critical' : 'general';
        const diseaseList = await getDiseases(wardType);
        setDiseases(diseaseList);
      } catch (error) {
        console.error('Error loading diseases:', error);
        toast.error('Failed to load diseases');
      } finally {
        setLoadingDiseases(false);
      }
    };

    loadDiseases();
  }, [patientType]);

  // Load disease info when disease is selected
  useEffect(() => {
    const loadDiseaseInfo = async () => {
      if (!selectedDisease || !patientType) return;
      
      try {
        const wardType = patientType === 'CRITICAL' ? 'critical' : 'general';
        const info = await getDiseaseInfo(wardType, selectedDisease);
        setDiseaseInfo(info);
      } catch (error) {
        console.error('Error loading disease info:', error);
      }
    };

    loadDiseaseInfo();
  }, [selectedDisease, patientType]);

  // Check band availability
  useEffect(() => {
    const checkBandAvailability = async () => {
      try {
        const activePatient = await getActivePatient();
        setBandStatus({
          available: !activePatient,
          checking: false,
          currentPatient: activePatient,
        });
      } catch (error) {
        console.error('Error checking band availability:', error);
        setBandStatus({
          available: false,
          checking: false,
          error: 'Failed to check band status',
        });
      }
    };

    checkBandAvailability();
    
    // Poll every 5 seconds
    const interval = setInterval(checkBandAvailability, 5000);
    
    return () => clearInterval(interval);
  }, []);

  // Handle form submission
  const onSubmit = async (data) => {
    if (!bandStatus.available) {
      toast.error('Cannot admit patient - Band is occupied');
      return;
    }

    setSubmitting(true);

    try {
      // Prepare patient data
      const patientData = { ...data };

      // Remove demo_scenario if demo_mode is false
      if (!patientData.demo_mode) {
        delete patientData.demo_scenario;
      }

      const result = await admitPatient(patientData);
      
      setActivePatient(result);
      
      toast.success(`Patient ${result.name} admitted successfully!`);
      
      // Navigate to dashboard after 1 second
      setTimeout(() => {
        navigate('/dashboard');
      }, 1000);
    } catch (error) {
      console.error('Error admitting patient:', error);
      
      const errorMessage = error.response?.data?.detail || 'Failed to admit patient';
      toast.error(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  const MotionDiv = motion.div;

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <MotionDiv
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Paper elevation={3} sx={{ p: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom align="center" color="primary">
            Patient Admission
          </Typography>
          
          <Typography variant="subtitle1" gutterBottom align="center" color="text.secondary" sx={{ mb: 3 }}>
            Hospital Alarm Fatigue Monitoring System
          </Typography>

          {/* Band Status */}
          <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 2 }}>
            <Typography variant="body1" fontWeight="bold">
              Band Status:
            </Typography>
            {bandStatus.checking ? (
              <Chip label="Checking..." icon={<CircularProgress size={16} />} />
            ) : bandStatus.available ? (
              <Chip label="Available" color="success" />
            ) : (
              <Chip label="Occupied" color="error" />
            )}
          </Box>

          {bandStatus.currentPatient && (
            <Alert severity="warning" sx={{ mb: 3 }}>
              Band is currently assigned to patient: <strong>{bandStatus.currentPatient.name}</strong>.
              Please discharge the current patient before admitting a new one.
            </Alert>
          )}

          {bandStatus.error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {bandStatus.error}
            </Alert>
          )}

          {/* Admission Form */}
          <form onSubmit={handleSubmit(onSubmit)}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              {/* Name Field */}
              <Controller
                name="name"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Patient Name"
                    fullWidth
                    required
                    error={!!errors.name}
                    helperText={errors.name?.message}
                    disabled={submitting || !bandStatus.available}
                  />
                )}
              />

              {/* Age Field */}
              <Controller
                name="age"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Age"
                    type="number"
                    fullWidth
                    required
                    error={!!errors.age}
                    helperText={errors.age?.message}
                    disabled={submitting || !bandStatus.available}
                    InputProps={{
                      inputProps: { min: 1, max: 149 },
                    }}
                  />
                )}
              />

              {/* Problem Field */}
              <Controller
                name="problem"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Problem/Condition"
                    fullWidth
                    required
                    multiline
                    rows={3}
                    error={!!errors.problem}
                    helperText={errors.problem?.message}
                    disabled={submitting || !bandStatus.available}
                  />
                )}
              />

              {/* Patient Type */}
              <FormControl component="fieldset" error={!!errors.patient_type}>
                <FormLabel component="legend">Patient Type *</FormLabel>
                <Controller
                  name="patient_type"
                  control={control}
                  render={({ field }) => (
                    <RadioGroup {...field} row>
                      <FormControlLabel
                        value="GENERAL"
                        control={<Radio />}
                        label="General Ward"
                        disabled={submitting || !bandStatus.available}
                      />
                      <FormControlLabel
                        value="CRITICAL"
                        control={<Radio />}
                        label="Critical Ward"
                        disabled={submitting || !bandStatus.available}
                      />
                    </RadioGroup>
                  )}
                />
                {errors.patient_type && (
                  <Typography variant="caption" color="error">
                    {errors.patient_type.message}
                  </Typography>
                )}
              </FormControl>

              <Divider sx={{ my: 2 }}>
                <Chip label="Disease Profile (Optional)" size="small" />
              </Divider>

              {/* Disease Selection */}
              <FormControl fullWidth>
                <InputLabel>Disease/Condition</InputLabel>
                <Controller
                  name="disease"
                  control={control}
                  render={({ field }) => (
                    <Select
                      {...field}
                      label="Disease/Condition"
                      disabled={submitting || !bandStatus.available || loadingDiseases}
                    >
                      <MenuItem value="">
                        <em>None (Use demo mode instead)</em>
                      </MenuItem>
                      {diseases.map((disease) => (
                        <MenuItem key={disease} value={disease}>
                          {disease}
                        </MenuItem>
                      ))}
                    </Select>
                  )}
                />
                {loadingDiseases && (
                  <Typography variant="caption" color="text.secondary">
                    Loading diseases...
                  </Typography>
                )}
              </FormControl>

              {/* Disease Info Display */}
              {diseaseInfo && selectedDisease && (
                <Alert severity="info" sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    {selectedDisease}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Symptoms:</strong> {diseaseInfo.symptoms?.join(', ')}
                  </Typography>
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    <strong>Medications:</strong> {diseaseInfo.medications?.length || 0} prescribed
                  </Typography>
                </Alert>
              )}

              {/* Body Strength */}
              {selectedDisease && (
                <FormControl fullWidth>
                  <InputLabel>Body Strength</InputLabel>
                  <Controller
                    name="body_strength"
                    control={control}
                    render={({ field }) => (
                      <Select
                        {...field}
                        label="Body Strength"
                        disabled={submitting || !bandStatus.available}
                      >
                        <MenuItem value="strong">Strong</MenuItem>
                        <MenuItem value="average">Average</MenuItem>
                        <MenuItem value="weak">Weak</MenuItem>
                      </Select>
                    )}
                  />
                </FormControl>
              )}

              {/* Genetic Condition */}
              {selectedDisease && (
                <FormControl fullWidth>
                  <InputLabel>Genetic Condition</InputLabel>
                  <Controller
                    name="genetic_condition"
                    control={control}
                    render={({ field }) => (
                      <Select
                        {...field}
                        label="Genetic Condition"
                        disabled={submitting || !bandStatus.available}
                      >
                        <MenuItem value="healthy">Healthy</MenuItem>
                        <MenuItem value="hypertension_prone">Hypertension Prone</MenuItem>
                        <MenuItem value="diabetes_prone">Diabetes Prone</MenuItem>
                      </Select>
                    )}
                  />
                </FormControl>
              )}

              {/* Allergies */}
              {selectedDisease && (
                <FormControl component="fieldset">
                  <FormLabel component="legend">Known Allergies</FormLabel>
                  <Controller
                    name="allergies"
                    control={control}
                    render={({ field }) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                        {['Penicillin', 'Sulfa drugs', 'NSAIDs', 'Cephalosporins'].map((allergy) => (
                          <FormControlLabel
                            key={allergy}
                            control={
                              <Checkbox
                                checked={field.value?.includes(allergy)}
                                onChange={(e) => {
                                  const newValue = e.target.checked
                                    ? [...(field.value || []), allergy]
                                    : (field.value || []).filter((a) => a !== allergy);
                                  field.onChange(newValue);
                                }}
                                disabled={submitting || !bandStatus.available}
                              />
                            }
                            label={allergy}
                          />
                        ))}
                      </Box>
                    )}
                  />
                </FormControl>
              )}

              {/* Demo Mode */}
              <Box>
                <Controller
                  name="demo_mode"
                  control={control}
                  render={({ field }) => (
                    <FormControlLabel
                      control={
                        <Checkbox
                          {...field}
                          checked={field.value}
                          disabled={submitting || !bandStatus.available}
                        />
                      }
                      label="Enable Demo Mode (for testing without real sensors)"
                    />
                  )}
                />
              </Box>

              {/* Demo Scenario (conditional) */}
              {demoMode && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                >
                  <FormControl fullWidth error={!!errors.demo_scenario}>
                    <InputLabel>Demo Scenario</InputLabel>
                    <Controller
                      name="demo_scenario"
                      control={control}
                      render={({ field }) => (
                        <Select
                          {...field}
                          label="Demo Scenario"
                          disabled={submitting || !bandStatus.available}
                        >
                          <MenuItem value="NORMAL">Normal Vitals</MenuItem>
                          <MenuItem value="MILD_DETERIORATION">Mild Deterioration</MenuItem>
                          <MenuItem value="CRITICAL_EMERGENCY">Critical Emergency</MenuItem>
                          <MenuItem value="FALSE_POSITIVE">False Positive</MenuItem>
                        </Select>
                      )}
                    />
                    {errors.demo_scenario && (
                      <Typography variant="caption" color="error">
                        {errors.demo_scenario.message}
                      </Typography>
                    )}
                  </FormControl>
                </motion.div>
              )}

              {/* Submit Button */}
              <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                <Button
                  type="submit"
                  variant="contained"
                  size="large"
                  fullWidth
                  disabled={submitting || !bandStatus.available || bandStatus.checking}
                  startIcon={submitting && <CircularProgress size={20} />}
                >
                  {submitting ? 'Admitting Patient...' : 'Admit Patient'}
                </Button>
                
                <Button
                  variant="outlined"
                  size="large"
                  onClick={() => navigate('/')}
                  disabled={submitting}
                >
                  Cancel
                </Button>
              </Box>
            </Box>
          </form>
        </Paper>
      </MotionDiv>
    </Container>
  );
};

export default AdmitPatient;

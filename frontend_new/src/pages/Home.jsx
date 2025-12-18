import { useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
} from '@mui/material';
import { LocalHospital, PersonAdd, Dashboard as DashboardIcon, Folder } from '@mui/icons-material';
import { motion } from 'framer-motion';

const MotionCard = motion(Card);

const Home = () => {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        alignItems: 'center',
        py: 4,
      }}
    >
      <Container maxWidth="lg">
        <motion.div
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <Paper elevation={10} sx={{ p: 6, borderRadius: 4, textAlign: 'center', mb: 6 }}>
            <LocalHospital sx={{ fontSize: 80, color: 'primary.main', mb: 2 }} />
            <Typography variant="h2" component="h1" gutterBottom fontWeight="bold">
              Hospital Alarm Fatigue Monitoring System
            </Typography>
            <Typography variant="h5" color="text.secondary" sx={{ mb: 2 }}>
              Patient-Centric Real-Time Vital Monitoring with ML-Powered Alarm Routing
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 800, mx: 'auto' }}>
              Advanced patient monitoring system that reduces alarm fatigue by intelligently routing
              alerts based on patient type, nurse proximity, and machine learning predictions.
            </Typography>
          </Paper>
        </motion.div>

        <Grid container spacing={4}>
          <Grid item xs={12} md={3}>
            <MotionCard
              elevation={5}
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              sx={{ height: '100%' }}
            >
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                <PersonAdd sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
                <Typography variant="h5" component="h2" gutterBottom>
                  Admit Patient
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Register a new patient and bind them to the monitoring band.
                </Typography>
              </CardContent>
              <CardActions sx={{ justifyContent: 'center', pb: 3 }}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={() => navigate('/admit')}
                  startIcon={<PersonAdd />}
                >
                  Admit
                </Button>
              </CardActions>
            </MotionCard>
          </Grid>

          <Grid item xs={12} md={3}>
            <MotionCard
              elevation={5}
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              sx={{ height: '100%' }}
            >
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                <DashboardIcon sx={{ fontSize: 60, color: 'success.main', mb: 2 }} />
                <Typography variant="h5" component="h2" gutterBottom>
                  Dashboard
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Monitor active patient vital signs in real-time with live updates.
                </Typography>
              </CardContent>
              <CardActions sx={{ justifyContent: 'center', pb: 3 }}>
                <Button
                  variant="contained"
                  size="large"
                  color="success"
                  onClick={() => navigate('/dashboard')}
                  startIcon={<DashboardIcon />}
                >
                  Dashboard
                </Button>
              </CardActions>
            </MotionCard>
          </Grid>

          <Grid item xs={12} md={3}>
            <MotionCard
              elevation={5}
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              sx={{ height: '100%' }}
            >
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                <Folder sx={{ fontSize: 60, color: 'warning.main', mb: 2 }} />
                <Typography variant="h5" component="h2" gutterBottom>
                  Records
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  View complete history of all discharged patients and statistics.
                </Typography>
              </CardContent>
              <CardActions sx={{ justifyContent: 'center', pb: 3 }}>
                <Button
                  variant="contained"
                  size="large"
                  color="warning"
                  onClick={() => navigate('/records')}
                  startIcon={<Folder />}
                >
                  View Records
                </Button>
              </CardActions>
            </MotionCard>
          </Grid>

          <Grid item xs={12} md={3}>
            <MotionCard
              elevation={5}
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              sx={{ height: '100%' }}
            >
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                <LocalHospital sx={{ fontSize: 60, color: 'info.main', mb: 2 }} />
                <Typography variant="h5" component="h2" gutterBottom>
                  System Info
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  ML-based alarms, BLE proximity, intelligent routing & more.
                </Typography>
              </CardContent>
              <CardActions sx={{ justifyContent: 'center', pb: 3 }}>
                <Button
                  variant="outlined"
                  size="large"
                  color="info"
                  disabled
                >
                  Learn More
                </Button>
              </CardActions>
            </MotionCard>
          </Grid>
        </Grid>

        <Box sx={{ textAlign: 'center', mt: 6 }}>
          <Typography variant="body2" color="white" sx={{ opacity: 0.8 }}>
            © 2025 Hospital Alarm Fatigue Monitoring System | Patient-monitoring-system-using-AI
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default Home;

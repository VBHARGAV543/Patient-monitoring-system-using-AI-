import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Typography,
  CircularProgress,
  Alert,
  Box,
} from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getPatientAlarmHistory } from '../services/api';
import { formatTimestamp, getAlarmColor } from '../utils/helpers';
import toast from 'react-hot-toast';

const AlarmHistoryModal = ({ open, onClose, patientId }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'chart'

  useEffect(() => {
    const loadHistory = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await getPatientAlarmHistory(patientId, 100);
        setHistory(data);
      } catch (err) {
        console.error('Error loading alarm history:', err);
        setError('Failed to load alarm history');
        toast.error('Failed to load alarm history');
      } finally {
        setLoading(false);
      }
    };

    if (open && patientId) {
      loadHistory();
    }
  }, [open, patientId]);

  const refreshHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getPatientAlarmHistory(patientId, 100);
      setHistory(data);
    } catch (err) {
      console.error('Error loading alarm history:', err);
      setError('Failed to load alarm history');
      toast.error('Failed to load alarm history');
    } finally {
      setLoading(false);
    }
  };

  // Prepare chart data
  const chartData = history
    .slice(0, 50) // Last 50 readings
    .reverse()
    .map((event, index) => ({
      index,
      HR: event.vitals?.HR || 0,
      SpO2: event.vitals?.SpO2 || 0,
      Temp: event.vitals?.Temp || 0,
      BP_sys: event.vitals?.BP_sys || 0,
      timestamp: formatTimestamp(event.timestamp, 'HH:mm'),
    }));

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h5">Alarm History</Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant={viewMode === 'table' ? 'contained' : 'outlined'}
              size="small"
              onClick={() => setViewMode('table')}
            >
              Table
            </Button>
            <Button
              variant={viewMode === 'chart' ? 'contained' : 'outlined'}
              size="small"
              onClick={() => setViewMode('chart')}
            >
              Chart
            </Button>
          </Box>
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {error && <Alert severity="error">{error}</Alert>}

        {!loading && !error && history.length === 0 && (
          <Alert severity="info">No alarm history available yet.</Alert>
        )}

        {!loading && !error && history.length > 0 && viewMode === 'table' && (
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Timestamp</TableCell>
                  <TableCell>HR</TableCell>
                  <TableCell>SpO2</TableCell>
                  <TableCell>Temp</TableCell>
                  <TableCell>BP (S/D)</TableCell>
                  <TableCell>Glucose</TableCell>
                  <TableCell>Alarm Status</TableCell>
                  <TableCell>Nurse Nearby</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {history.map((event) => (
                  <TableRow key={event.id} hover>
                    <TableCell>
                      <Typography variant="caption">
                        {formatTimestamp(event.timestamp)}
                      </Typography>
                    </TableCell>
                    <TableCell>{event.vitals?.HR || '--'}</TableCell>
                    <TableCell>{event.vitals?.SpO2 || '--'}</TableCell>
                    <TableCell>{event.vitals?.Temp || '--'}</TableCell>
                    <TableCell>
                      {event.vitals?.BP_sys || '--'} / {event.vitals?.BP_dia || '--'}
                    </TableCell>
                    <TableCell>{event.vitals?.Glucose || '--'}</TableCell>
                    <TableCell>
                      <Chip
                        label={event.alarm_status}
                        color={getAlarmColor(event.alarm_status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={event.nurse_in_proximity ? 'Yes' : 'No'}
                        color={event.nurse_in_proximity ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}

        {!loading && !error && history.length > 0 && viewMode === 'chart' && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Vital Signs Trends (Last 50 Readings)
            </Typography>

            {/* Heart Rate Chart */}
            <Box sx={{ mb: 4 }}>
              <Typography variant="subtitle2" gutterBottom>
                Heart Rate (bpm)
              </Typography>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis domain={[40, 140]} />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="HR"
                    stroke="#f44336"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>

            {/* SpO2 Chart */}
            <Box sx={{ mb: 4 }}>
              <Typography variant="subtitle2" gutterBottom>
                Blood Oxygen (%)
              </Typography>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis domain={[85, 100]} />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="SpO2"
                    stroke="#2196f3"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>

            {/* Temperature Chart */}
            <Box sx={{ mb: 4 }}>
              <Typography variant="subtitle2" gutterBottom>
                Temperature (°C)
              </Typography>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis domain={[35, 40]} />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="Temp"
                    stroke="#ff9800"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>

            {/* Blood Pressure Chart */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Blood Pressure (Systolic, mmHg)
              </Typography>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis domain={[80, 180]} />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="BP_sys"
                    stroke="#4caf50"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={refreshHistory} disabled={loading}>
          Refresh
        </Button>
        <Button onClick={onClose} variant="contained">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AlarmHistoryModal;

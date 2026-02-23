import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  CircularProgress,
  Alert,
  Button,
  TextField,
  InputAdornment,
} from '@mui/material';
import {
  ArrowBack,
  Search,
  Person,
  LocalHospital,
  CalendarToday,
  Timer,
} from '@mui/icons-material';
import toast from 'react-hot-toast';
import { getDischargedPatients, getPatientStatistics } from '../services/api';
import { formatTimestamp } from '../utils/helpers';

const Records = () => {
  const navigate = useNavigate();
  
  const [records, setRecords] = useState([]);
  const [filteredRecords, setFilteredRecords] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Load all discharged patients
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [patientsData, statsData] = await Promise.all([
          getDischargedPatients(),
          getPatientStatistics(),
        ]);
        
        setRecords(patientsData);
        setFilteredRecords(patientsData);
        setStatistics(statsData);
      } catch (error) {
        console.error('Error loading records:', error);
        toast.error('Failed to load patient records');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Filter records based on search query
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredRecords(records);
      return;
    }

    const query = searchQuery.toLowerCase();
    const filtered = records.filter((record) => {
      return (
        record.name.toLowerCase().includes(query) ||
        record.problem.toLowerCase().includes(query) ||
        record.patient_type.toLowerCase().includes(query) ||
        record.id.toString().includes(query)
      );
    });

    setFilteredRecords(filtered);
    setPage(0); // Reset to first page when filtering
  }, [searchQuery, records]);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const calculateStayDuration = (admissionTime, dischargeTime) => {
    const admission = new Date(admissionTime);
    const discharge = new Date(dischargeTime);
    const diffMs = discharge - admission;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);
    const remainingHours = diffHours % 24;

    if (diffDays > 0) {
      return `${diffDays}d ${remainingHours}h`;
    }
    return `${diffHours}h`;
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress size={60} />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Button
            startIcon={<ArrowBack />}
            onClick={() => navigate('/')}
            variant="outlined"
          >
            Back
          </Button>
          <Typography variant="h4" component="h1" fontWeight="bold">
            Patient Records
          </Typography>
        </Box>
      </Box>

      {/* Statistics Cards */}
      {statistics && (
        <Box sx={{ mb: 3, display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 2 }}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="body2" color="text.secondary">Total Admitted</Typography>
            <Typography variant="h4" fontWeight="bold">{statistics.total_admitted}</Typography>
          </Paper>
          <Paper sx={{ p: 2 }}>
            <Typography variant="body2" color="text.secondary">Active Patients</Typography>
            <Typography variant="h4" fontWeight="bold" color="primary">{statistics.active_patients}</Typography>
          </Paper>
          <Paper sx={{ p: 2 }}>
            <Typography variant="body2" color="text.secondary">Discharged</Typography>
            <Typography variant="h4" fontWeight="bold" color="success.main">{statistics.discharged_patients}</Typography>
          </Paper>
          <Paper sx={{ p: 2 }}>
            <Typography variant="body2" color="text.secondary">Avg. Stay</Typography>
            <Typography variant="h4" fontWeight="bold">{statistics.average_stay_hours.toFixed(1)}h</Typography>
          </Paper>
        </Box>
      )}

      {/* Search Bar */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <TextField
          fullWidth
          placeholder="Search by name, problem, type, or ID..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search />
              </InputAdornment>
            ),
          }}
        />
      </Paper>

      {/* Records Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell><strong>ID</strong></TableCell>
                <TableCell><strong>Patient Name</strong></TableCell>
                <TableCell><strong>Age</strong></TableCell>
                <TableCell><strong>Type</strong></TableCell>
                <TableCell><strong>Problem</strong></TableCell>
                <TableCell><strong>Admitted</strong></TableCell>
                <TableCell><strong>Discharged</strong></TableCell>
                <TableCell><strong>Stay Duration</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredRecords.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    <Typography variant="body1" color="text.secondary" sx={{ py: 4 }}>
                      {searchQuery ? 'No records found matching your search' : 'No discharged patients yet'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredRecords
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((record) => (
                    <TableRow key={record.id} hover>
                      <TableCell>{record.id}</TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Person fontSize="small" />
                          <strong>{record.name}</strong>
                        </Box>
                      </TableCell>
                      <TableCell>{record.age}</TableCell>
                      <TableCell>
                        <Chip
                          label={record.patient_type}
                          color={record.patient_type === 'CRITICAL' ? 'error' : 'success'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{record.problem}</TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatTimestamp(record.admission_time)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatTimestamp(record.discharge_time)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          icon={<Timer />}
                          label={calculateStayDuration(record.admission_time, record.discharge_time)}
                          variant="outlined"
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                  ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25, 50, 100]}
          component="div"
          count={filteredRecords.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Paper>

      {/* Summary */}
      <Box sx={{ mt: 3 }}>
        <Alert severity="info">
          Showing {filteredRecords.length} total record(s). All discharged patient data is permanently stored.
        </Alert>
      </Box>
    </Container>
  );
};

export default Records;

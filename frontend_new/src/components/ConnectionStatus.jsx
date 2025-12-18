import { Box, Chip, Tooltip } from '@mui/material';
import { Wifi, WifiOff, CloudDone, CloudOff } from '@mui/icons-material';

const ConnectionStatus = ({ backendConnected, wsConnected }) => {
  return (
    <Box
      sx={{
        position: 'fixed',
        top: 16,
        right: 16,
        zIndex: 1000,
        display: 'flex',
        gap: 1,
        flexDirection: 'column',
      }}
    >
      {/* Backend Connection */}
      <Tooltip title={backendConnected ? 'Backend Connected' : 'Backend Disconnected'}>
        <Chip
          icon={backendConnected ? <CloudDone /> : <CloudOff />}
          label="Backend"
          color={backendConnected ? 'success' : 'error'}
          size="small"
          sx={{ fontWeight: 'bold' }}
        />
      </Tooltip>

      {/* WebSocket Connection */}
      <Tooltip title={wsConnected ? 'WebSocket Connected' : 'WebSocket Disconnected'}>
        <Chip
          icon={wsConnected ? <Wifi /> : <WifiOff />}
          label="WebSocket"
          color={wsConnected ? 'success' : 'error'}
          size="small"
          sx={{ fontWeight: 'bold' }}
        />
      </Tooltip>
    </Box>
  );
};

export default ConnectionStatus;

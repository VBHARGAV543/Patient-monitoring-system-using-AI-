/**
 * CameraViewerPage  — opened on the mobile device.
 * URL: http://<laptop-ip>:3000/camera
 *
 * Automatically starts as a WebRTC *viewer* and receives the
 * stream broadcasted from the dashboard/laptop.
 */
import { Box, Typography, Container } from '@mui/material';
import CameraView from '../components/CameraView';

const CameraViewerPage = () => {
  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#111', pt: 2, pb: 4 }}>
      <Container maxWidth="md">
        <Typography
          variant="h5"
          align="center"
          sx={{ color: 'white', mb: 2, fontWeight: 600 }}
        >
          Patient Room Camera
        </Typography>

        {/* Viewer mode — auto-connects to the broadcaster */}
        <CameraView mode="viewer" autoStart={true} wardType="GENERAL" />

        <Typography
          variant="caption"
          display="block"
          align="center"
          sx={{ color: 'grey.500', mt: 2 }}
        >
          This stream is relayed via WebRTC. Keep this page open to watch.
        </Typography>
      </Container>
    </Box>
  );
};

export default CameraViewerPage;

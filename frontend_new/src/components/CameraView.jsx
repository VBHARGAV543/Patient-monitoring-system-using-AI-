import { useState, useRef, useEffect } from 'react';
import {
  Box,
  Button,
  Paper,
  Typography,
  Alert,
  IconButton,
} from '@mui/material';
import { Videocam, VideocamOff, Refresh } from '@mui/icons-material';
import toast from 'react-hot-toast';

const CameraView = ({ autoStart = false, wardType = 'GENERAL' }) => {
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState(null);
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  const startCamera = async () => {
    try {
      setError(null);
      
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720 },
        audio: false,
      });

      streamRef.current = stream;
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }

      setIsActive(true);
      toast.success('Camera activated');
    } catch (err) {
      console.error('Error accessing camera:', err);
      setError('Failed to access camera. Please check permissions.');
      toast.error('Failed to access camera');
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsActive(false);
    toast.info('Camera deactivated');
  };

  const toggleCamera = () => {
    if (isActive) {
      stopCamera();
    } else {
      startCamera();
    }
  };

  // Auto-start camera for critical ward
  useEffect(() => {
    let mounted = true;

    const initCamera = async () => {
      if (autoStart && wardType === 'CRITICAL' && mounted) {
        await startCamera();
      }
    };

    initCamera();

    // Cleanup on unmount
    return () => {
      mounted = false;
      stopCamera();
    };
  }, [autoStart, wardType]);

  return (
    <Paper elevation={3} sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Patient Camera Monitor</Typography>
        <Box>
          {wardType === 'GENERAL' && (
            <Button
              variant={isActive ? 'contained' : 'outlined'}
              color={isActive ? 'error' : 'primary'}
              startIcon={isActive ? <VideocamOff /> : <Videocam />}
              onClick={toggleCamera}
              sx={{ mr: 1 }}
            >
              {isActive ? 'Stop Camera' : 'Start Camera'}
            </Button>
          )}
          {isActive && (
            <IconButton onClick={startCamera} color="primary" title="Refresh Camera">
              <Refresh />
            </IconButton>
          )}
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {wardType === 'CRITICAL' && !isActive && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Camera will auto-start for Critical Ward patients
        </Alert>
      )}

      <Box
        sx={{
          position: 'relative',
          width: '100%',
          paddingTop: '56.25%', // 16:9 aspect ratio
          bgcolor: 'black',
          borderRadius: 1,
          overflow: 'hidden',
        }}
      >
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        
        {!isActive && (
          <Box
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              textAlign: 'center',
              color: 'white',
            }}
          >
            <VideocamOff sx={{ fontSize: 60, mb: 2 }} />
            <Typography variant="h6">Camera Inactive</Typography>
          </Box>
        )}
      </Box>
    </Paper>
  );
};

export default CameraView;

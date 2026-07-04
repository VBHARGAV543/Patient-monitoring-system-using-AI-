import { useState, useRef, useEffect, useCallback } from 'react';
import {
  Box,
  Button,
  Paper,
  Typography,
  Alert,
  Chip,
} from '@mui/material';
import { Videocam, VideocamOff, Tv } from '@mui/icons-material';
import toast from 'react-hot-toast';

/**
 * CameraView — WebRTC-based camera streaming.
 *
 * mode="broadcaster"  (default on Dashboard / laptop)
 *   → Captures the local webcam and streams it to all connected viewers
 *     via a WebRTC peer connection negotiated through the backend signaling relay.
 *
 * mode="viewer"  (mobile / any remote browser)
 *   → Opens the stream sent by the broadcaster.
 *     Navigate to: http://<laptop-ip>:3000/camera  (or use the viewer URL shown below)
 *
 * room  = arbitrary room name (default "patient-room-1")
 * autoStart = true → immediately starts on mount (used for CRITICAL ward)
 */

const STUN = { iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] };
const ROOM = 'patient-room-1';

// Build signaling WebSocket URL dynamically so it works on any IP
const signalingUrl = (role) => {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const host = window.location.hostname;
  // Always talk directly to the backend port (8000), not the Vite dev-server
  return `${proto}://${host}:8000/ws/webrtc/${ROOM}/${role}`;
};

const CameraView = ({ autoStart = false, wardType = 'GENERAL', mode = 'broadcaster' }) => {
  const [isActive, setIsActive] = useState(false);
  const [status, setStatus] = useState('idle'); // idle | connecting | streaming | error
  const [error, setError] = useState(null);

  const videoRef = useRef(null);
  // broadcaster refs
  const localStreamRef = useRef(null);
  const peersRef = useRef({}); // viewer_index -> RTCPeerConnection
  const sigWsRef = useRef(null);

  // ─── cleanup helper ─────────────────────────────────────────────────────────
  const cleanup = useCallback(() => {
    // Close all peer connections
    Object.values(peersRef.current).forEach((pc) => pc.close());
    peersRef.current = {};

    // Stop local tracks (broadcaster)
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach((t) => t.stop());
      localStreamRef.current = null;
    }

    // Close signaling WS
    if (sigWsRef.current) {
      sigWsRef.current.close();
      sigWsRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsActive(false);
    setStatus('idle');
  }, []);

  // ─── BROADCASTER logic ───────────────────────────────────────────────────────
  const startBroadcaster = useCallback(async () => {
    setError(null);
    setStatus('connecting');

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      localStreamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }

      const ws = new WebSocket(signalingUrl('broadcaster'));
      sigWsRef.current = ws;

      ws.onopen = () => {
        setStatus('streaming');
        setIsActive(true);
        toast.success('Camera streaming started');
      };

      ws.onerror = () => {
        setError('Signaling connection failed. Is the backend running?');
        setStatus('error');
      };

      ws.onclose = () => {
        if (status !== 'idle') setStatus('idle');
      };

      ws.onmessage = async (evt) => {
        const msg = JSON.parse(evt.data);

        if (msg.type === 'viewer_joined') {
          // New viewer connected — create a new peer connection for it
          const id = Date.now();
          const pc = new RTCPeerConnection(STUN);
          peersRef.current[id] = pc;

          // Add all local tracks
          stream.getTracks().forEach((track) => pc.addTrack(track, stream));

          pc.onicecandidate = (e) => {
            if (e.candidate && ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ type: 'ice', candidate: e.candidate }));
            }
          };

          const offer = await pc.createOffer();
          await pc.setLocalDescription(offer);
          ws.send(JSON.stringify({ type: 'offer', sdp: pc.localDescription }));

        } else if (msg.type === 'answer') {
          // Find the most recently created peer (simplistic single-viewer model)
          const ids = Object.keys(peersRef.current);
          if (ids.length) {
            const pc = peersRef.current[ids[ids.length - 1]];
            if (pc.signalingState !== 'stable') {
              await pc.setRemoteDescription(new RTCSessionDescription(msg.sdp));
            }
          }

        } else if (msg.type === 'ice') {
          // Forward ICE to the last peer
          const ids = Object.keys(peersRef.current);
          if (ids.length) {
            const pc = peersRef.current[ids[ids.length - 1]];
            try { await pc.addIceCandidate(new RTCIceCandidate(msg.candidate)); } catch {}
          }
        }
      };

    } catch (err) {
      console.error('Broadcaster error:', err);
      setError('Could not access camera. Check browser permissions.');
      setStatus('error');
      toast.error('Camera access denied');
    }
  }, []);

  // ─── VIEWER logic ────────────────────────────────────────────────────────────
  const startViewer = useCallback(() => {
    setError(null);
    setStatus('connecting');

    const pc = new RTCPeerConnection(STUN);
    peersRef.current['viewer'] = pc;

    pc.ontrack = (e) => {
      if (videoRef.current && e.streams[0]) {
        videoRef.current.srcObject = e.streams[0];
        setIsActive(true);
        setStatus('streaming');
        toast.success('Receiving camera stream');
      }
    };

    const ws = new WebSocket(signalingUrl('viewer'));
    sigWsRef.current = ws;

    ws.onerror = () => {
      setError('Signaling connection failed.');
      setStatus('error');
    };

    ws.onclose = () => setStatus('idle');

    ws.onmessage = async (evt) => {
      const msg = JSON.parse(evt.data);

      if (msg.type === 'offer') {
        await pc.setRemoteDescription(new RTCSessionDescription(msg.sdp));
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);
        ws.send(JSON.stringify({ type: 'answer', sdp: pc.localDescription }));

      } else if (msg.type === 'ice') {
        try { await pc.addIceCandidate(new RTCIceCandidate(msg.candidate)); } catch {}

      } else if (msg.type === 'broadcaster_left') {
        setIsActive(false);
        setStatus('idle');
        if (videoRef.current) videoRef.current.srcObject = null;
        toast.info('Camera stream ended');
      }
    };

    pc.onicecandidate = (e) => {
      if (e.candidate && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ice', candidate: e.candidate }));
      }
    };
  }, []);

  // ─── Start / Stop ─────────────────────────────────────────────────────────
  const start = useCallback(() => {
    if (mode === 'broadcaster') startBroadcaster();
    else startViewer();
  }, [mode, startBroadcaster, startViewer]);

  const stop = useCallback(() => {
    cleanup();
    toast.info('Camera stopped');
  }, [cleanup]);

  // Auto-start for CRITICAL ward or viewer mode
  useEffect(() => {
    if (autoStart && (wardType === 'CRITICAL' || mode === 'viewer')) {
      start();
    }
    return () => cleanup();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ─── Viewer URL helper (shown to broadcaster so they can share it) ──────────
  const viewerUrl = `${window.location.protocol}//${window.location.hostname}:${window.location.port}/camera`;

  const statusColor = { idle: 'default', connecting: 'warning', streaming: 'success', error: 'error' };
  const statusLabel = { idle: 'Idle', connecting: 'Connecting…', streaming: 'Live', error: 'Error' };

  return (
    <Paper elevation={3} sx={{ p: 2 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {mode === 'broadcaster' ? <Videocam color="primary" /> : <Tv color="secondary" />}
          <Typography variant="h6">
            {mode === 'broadcaster' ? 'Patient Camera (Broadcaster)' : 'Remote Camera View'}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Chip
            label={statusLabel[status]}
            color={statusColor[status]}
            size="small"
          />
          <Button
            variant={isActive ? 'outlined' : 'contained'}
            color={isActive ? 'error' : 'primary'}
            size="small"
            startIcon={isActive ? <VideocamOff /> : <Videocam />}
            onClick={isActive ? stop : start}
          >
            {isActive ? 'Stop' : mode === 'broadcaster' ? 'Start Stream' : 'Connect'}
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 1.5 }}>
          {error}
        </Alert>
      )}

      {/* Share link for broadcaster */}
      {mode === 'broadcaster' && isActive && (
        <Alert severity="info" sx={{ mb: 1.5, wordBreak: 'break-all' }}>
          <strong>Mobile viewer URL:</strong> {viewerUrl}
        </Alert>
      )}

      {mode === 'viewer' && status === 'connecting' && (
        <Alert severity="info" sx={{ mb: 1.5 }}>
          Waiting for broadcaster to start streaming…
        </Alert>
      )}

      {/* Video element */}
      <Box
        sx={{
          position: 'relative',
          width: '100%',
          paddingTop: '56.25%', // 16:9
          bgcolor: '#000',
          borderRadius: 1,
          overflow: 'hidden',
        }}
      >
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted={mode === 'broadcaster'} // don't mute viewer (future: add audio)
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
            <Typography variant="body2" color="grey.400">
              {mode === 'broadcaster'
                ? 'Press "Start Stream" to begin'
                : 'Press "Connect" to view the stream'}
            </Typography>
          </Box>
        )}
      </Box>
    </Paper>
  );
};

export default CameraView;

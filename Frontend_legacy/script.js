// WebSocket connection for real-time updates
let ws = null;
let reconnectInterval = null;

// Patient data with real-time vitals
const patients = {
  general: [
    { name: 'John Doe', age: 45, drug: 'Drug A', id: 'gen_001', vitals: {} },
    { name: 'Mary Ann', age: 60, drug: 'Drug B', id: 'gen_002', vitals: {} },
    { name: 'Alex Smith', age: 32, drug: 'Drug C', id: 'gen_003', vitals: {} },
  ],
  critical: [
    { name: 'Anna Lee', age: 70, drug: 'Drug X', id: 'crit_001', vitals: {} },
    { name: 'Robert Brown', age: 65, drug: 'Drug Y', id: 'crit_002', vitals: {} },
  ],
};

// WebSocket connection management
function connectWebSocket() {
  try {
    ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onopen = function(event) {
      console.log('WebSocket connected');
      updateConnectionStatus(true);
      if (reconnectInterval) {
        clearInterval(reconnectInterval);
        reconnectInterval = null;
      }
    };
    
    ws.onmessage = function(event) {
      const data = JSON.parse(event.data);
      handleRealtimeUpdate(data);
    };
    
    ws.onclose = function(event) {
      console.log('WebSocket disconnected');
      updateConnectionStatus(false);
      // Attempt to reconnect every 5 seconds
      if (!reconnectInterval) {
        reconnectInterval = setInterval(connectWebSocket, 5000);
      }
    };
    
    ws.onerror = function(error) {
      console.error('WebSocket error:', error);
      updateConnectionStatus(false);
    };
  } catch (error) {
    console.error('Failed to connect WebSocket:', error);
    updateConnectionStatus(false);
  }
}

function updateConnectionStatus(connected) {
  const statusElement = document.getElementById('connection-status');
  if (statusElement) {
    statusElement.textContent = connected ? 'Connected' : 'Disconnected';
    statusElement.className = connected ? 'status-connected' : 'status-disconnected';
  }
}

function handleRealtimeUpdate(data) {
  // Update patient vitals based on incoming data
  if (data.type === 'sensor_data') {
    updatePatientVitals(data.patient_id, data.vitals);
  } else if (data.type === 'alarm_status') {
    updateAlarmStatus(data.ward, data.status);
  } else if (data.type === 'ml_prediction') {
    updateMLPrediction(data);
  }
}

function updatePatientVitals(patientId, vitals) {
  // Find patient and update vitals
  for (const ward in patients) {
    const patient = patients[ward].find(p => p.id === patientId);
    if (patient) {
      patient.vitals = { ...vitals, timestamp: new Date().toLocaleTimeString() };
      // Update display if this patient is currently selected
      if (selectedPatientIdx !== null && getCurrentPatient().id === patientId) {
        displayVitals(patient);
      }
      break;
    }
  }
}

const wardBtns = document.querySelectorAll('.ward-btn');
const patientListDiv = document.getElementById('patient-list');
const patientTitle = document.getElementById('patient-title');
const wardDesc = document.getElementById('ward-desc');
const patientDetails = document.getElementById('patient-details');

let currentWard = 'general';
let selectedPatientIdx = null;
let stream = null; // global stream variable to manage webcam access

function renderPatientList(ward) {
  patientListDiv.innerHTML = '';
  const titleDiv = document.createElement('div');
  titleDiv.className = 'patient-title';
  titleDiv.textContent = ward === 'general' ? 'General Ward' : 'Critical Patients';
  patientListDiv.appendChild(titleDiv);
  patients[ward].forEach((patient, idx) => {
    const card = document.createElement('div');
    card.className = 'patient-card' + (selectedPatientIdx === idx ? ' selected' : '');
    card.textContent = patient.name;
    card.addEventListener('click', () => {
      selectedPatientIdx = idx;
      showPatientDetails(patient);
      updateSelections();
    });
    patientListDiv.appendChild(card);
  });
}

function updateSelections() {
  document.querySelectorAll('.patient-card').forEach((c, idx) => {
    c.classList.toggle('selected', idx === selectedPatientIdx);
  });
}

function showPatientDetails(patient) {
  // Stop any active stream if switching patients to avoid multiple cameras
  if (stream) {
    stream.getTracks().forEach(t => t.stop());
    stream = null;
  }

  // Clear previous details content
  patientDetails.innerHTML = `
    <strong>${patient.name}</strong><br>
    Age: ${patient.age}<br>
    Medication: ${patient.drug}<br>
    Patient ID: ${patient.id}<br><br>
    
    <div id="vitals-display">
      <h4>Real-time Vitals:</h4>
      <div id="vitals-data">
        <div class="vital-item">Heart Rate: <span id="hr-value">--</span> BPM</div>
        <div class="vital-item">SpO2: <span id="spo2-value">--</span>%</div>
        <div class="vital-item">Temperature: <span id="temp-value">--</span>°C</div>
        <div class="vital-item">Nurse Nearby: <span id="nurse-value">--</span></div>
        <div class="vital-timestamp">Last Update: <span id="vitals-timestamp">--</span></div>
      </div>
    </div>
    
    <div id="alarm-status">
      <h4>Alarm Status:</h4>
      <div id="alarm-indicator" class="alarm-normal">Normal</div>
    </div>
    
    <div id="camera-controls"></div>
    <div id="camera-container"></div>
  `;
  
  // Display current vitals if available
  displayVitals(patient);

  const cameraControls = document.getElementById('camera-controls');
  const cameraContainer = document.getElementById('camera-container');

  function startCamera() {
    if (stream) return; // Already streaming

    const video = document.createElement('video');
    video.id = 'patient-video';
    video.autoplay = true;
    video.style.width = '320px';
    video.style.height = '240px';
    video.style.marginTop = '15px';

    cameraContainer.appendChild(video);

    navigator.mediaDevices.getUserMedia({ video: true, audio: false })
      .then(mediaStream => {
        stream = mediaStream;
        video.srcObject = stream;
        createDeactivateButton();
      })
      .catch(err => {
        cameraContainer.innerHTML = 'Unable to access camera: ' + err.message;
      });
  }

  function createDeactivateButton() {
    cameraControls.innerHTML = '';
    const deactivateBtn = document.createElement('button');
    deactivateBtn.textContent = 'Deactivate Cam';
    deactivateBtn.style.marginLeft = '10px';

    deactivateBtn.addEventListener('click', () => {
      if (stream) {
        stream.getTracks().forEach(t => t.stop());
        stream = null;
      }
      const video = document.getElementById('patient-video');
      if (video) video.remove();

      cameraControls.innerHTML = '';
      if (currentWard === 'general') {
        createActivateButton();
      }
    });

    cameraControls.appendChild(deactivateBtn);
  }

  function createActivateButton() {
    cameraControls.innerHTML = '';
    const activateBtn = document.createElement('button');
    activateBtn.textContent = 'Activate Cam';

    activateBtn.addEventListener('click', () => {
      startCamera();
    });

    cameraControls.appendChild(activateBtn);
  }

  // Logic based on ward type
  if (currentWard === 'general') {
    createActivateButton(); // Camera off initially for general ward patients
  } else if (currentWard === 'critical') {
    startCamera(); // Camera on by default for critical ward patients
  }
}

wardBtns.forEach((btn) => {
  btn.addEventListener('click', () => {
    wardBtns.forEach((b) => b.classList.remove('active'));
    btn.classList.add('active');
    currentWard = btn.dataset.ward;
    selectedPatientIdx = null;
    // Stop any active camera stream when switching ward
    if (stream) {
      stream.getTracks().forEach(t => t.stop());
      stream = null;
    }
    renderPatientList(currentWard);
    patientTitle.textContent =
      currentWard === 'general' ? 'General Ward Patients' : 'Critical Ward Patients';
    wardDesc.textContent = 'Patient details and medication updates will appear here.';
    patientDetails.textContent = 'Select a patient from the left to view more information.';
  });
});

function displayVitals(patient) {
  if (!patient.vitals || Object.keys(patient.vitals).length === 0) {
    return;
  }
  
  const hrElement = document.getElementById('hr-value');
  const spo2Element = document.getElementById('spo2-value');
  const tempElement = document.getElementById('temp-value');
  const nurseElement = document.getElementById('nurse-value');
  const timestampElement = document.getElementById('vitals-timestamp');
  
  if (hrElement) hrElement.textContent = patient.vitals.HR || '--';
  if (spo2Element) spo2Element.textContent = patient.vitals.SpO2 || '--';
  if (tempElement) tempElement.textContent = patient.vitals.Temp || '--';
  if (nurseElement) nurseElement.textContent = patient.vitals.nurse_nearby ? 'Yes' : 'No';
  if (timestampElement) timestampElement.textContent = patient.vitals.timestamp || '--';
}

function updateAlarmStatus(ward, status) {
  const alarmElement = document.getElementById('alarm-indicator');
  if (alarmElement && currentWard === ward) {
    alarmElement.textContent = status;
    alarmElement.className = status === 'Normal' ? 'alarm-normal' : 'alarm-critical';
  }
}

function updateMLPrediction(data) {
  console.log('ML Prediction received:', data);
  // Handle ML prediction results
  if (data.prediction && data.patient_id) {
    // Update UI based on ML prediction
    updateAlarmStatus(data.ward, data.prediction === 1 ? 'CRITICAL ALARM' : 'Normal');
  }
}

function getCurrentPatient() {
  if (selectedPatientIdx === null) return null;
  return patients[currentWard][selectedPatientIdx];
}

// Generate random patient profile for testing
function generateRandomProfile() {
  fetch('http://localhost:8000/api/generate-patient', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ ward: currentWard })
  })
  .then(response => response.json())
  .then(data => {
    console.log('Generated patient profile:', data);
  })
  .catch(error => {
    console.error('Error generating profile:', error);
  });
}

// Initial render and WebSocket connection
renderPatientList(currentWard);
connectWebSocket();

// Add connection status to page
window.addEventListener('load', function() {
  const statusDiv = document.createElement('div');
  statusDiv.innerHTML = 'Connection Status: <span id="connection-status" class="status-disconnected">Disconnected</span>';
  statusDiv.style.position = 'fixed';
  statusDiv.style.top = '10px';
  statusDiv.style.right = '10px';
  statusDiv.style.background = '#f0f0f0';
  statusDiv.style.padding = '5px 10px';
  statusDiv.style.borderRadius = '5px';
  statusDiv.style.fontSize = '12px';
  document.body.appendChild(statusDiv);
});

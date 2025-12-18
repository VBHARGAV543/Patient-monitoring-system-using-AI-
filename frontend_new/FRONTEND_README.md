# Hospital Alarm Fatigue Monitoring System - Frontend

Modern React-based patient monitoring dashboard with real-time vital signs monitoring, ML-powered alarm routing, and nurse proximity detection.

## 🚀 Features

- **Patient Management**: Admit and discharge patients with band assignment
- **Real-Time Monitoring**: WebSocket-based live vital signs updates
- **Intelligent Alarms**: ML-predicted alarm routing (suppress, proximity alert, dashboard alert)
- **Ward Support**: Separate policies for General and Critical wards
- **Alarm History**: View patient alarm events with table and chart visualization
- **Camera Integration**: Ward-specific camera activation (manual for General, auto for Critical)
- **Demo Mode**: Test without real sensors using simulated data scenarios
- **Connection Status**: Real-time backend and WebSocket connection indicators

## 🛠️ Tech Stack

- **React 19** with Vite for fast development
- **Material-UI (MUI)** for professional healthcare UI components
- **Framer Motion** for smooth animations
- **Zustand** for lightweight state management
- **React Router** for navigation
- **React Query** for server state management
- **Recharts** for data visualization
- **React Hook Form** with Zod validation
- **Axios** for HTTP requests
- **WebSocket** for real-time updates
- **date-fns** for date formatting

## 📋 Prerequisites

- Node.js 18+ and npm
- Backend server running on `http://localhost:8000`
- ML models trained (critical_model.pkl and general_model.pkl)

## 🎯 Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

The frontend will run on `http://localhost:3000`

## 🌐 Environment Configuration

`.env` file:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## 📁 Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── AlarmHistoryModal.jsx
│   ├── CameraView.jsx
│   └── ConnectionStatus.jsx
├── pages/              # Route pages
│   ├── Home.jsx
│   ├── AdmitPatient.jsx
│   └── Dashboard.jsx
├── services/           # API and external services
│   └── api.js
├── hooks/              # Custom React hooks
│   └── useWebSocket.js
├── stores/             # Zustand state stores
│   └── patientStore.js
├── utils/              # Helper functions
│   └── helpers.js
├── App.jsx             # Main app component with routing
└── main.jsx            # Entry point
```

## 🔌 API Endpoints Connected

### REST Endpoints:
- `POST /api/patient/admit` - Admit new patient
- `POST /api/patient/discharge/{id}` - Discharge patient
- `GET /api/patient/active` - Get active patient
- `GET /api/patient/{id}/alarm-history` - Get alarm history
- `POST /api/nurse/register` - Register nurse session
- `POST /api/nurse/proximity` - Update nurse proximity
- `GET /` - Health check

### WebSocket Connections:
- `ws://localhost:8000/ws` - Main dashboard connection
- `ws://localhost:8000/ws/nurse/{session_id}` - Nurse proximity alerts

## 🎨 Key Pages

### 1. Home (`/`)
Landing page with system overview and navigation

### 2. Patient Admission (`/admit`)
- Patient form with validation
- Band availability checker
- Demo mode configuration
- Auto redirect after admission

### 3. Dashboard (`/dashboard`)
- Real-time vital signs display
- Alarm status with animations
- Patient discharge
- Alarm history modal with charts
- Connection status indicators

## 🏥 Ward-Specific Features

**General Ward:**
- Manual camera activation
- Alarm suppression for low-risk vitals
- Proximity-based routing

**Critical Ward:**
- Auto-start camera
- Minimal alarm suppression
- Always routes to dashboard

## 🔧 Usage

1. **Start Backend**: Ensure backend is running on port 8000
2. **Start Frontend**: Run `npm run dev`
3. **Admit Patient**: Navigate to `/admit` and fill form
4. **Monitor**: Dashboard shows real-time vitals via WebSocket
5. **Discharge**: Click "Discharge Patient" when done

## 📦 Build

```bash
npm run build
# Output in dist/ directory
```

## 🔗 Backend

[Patient-monitoring-system-using-AI-](https://github.com/VBHARGAV543/Patient-monitoring-system-using-AI-)

---

**Built with React 19 + Vite + Material-UI**

import { Routes, Route } from 'react-router-dom'
import UserRole from './pages/UserRole'
import StationLogin from './pages/StationLogin'
import StationDashboard from './pages/StationDashboard'

function App() {
  return (
    <div className="app-container">
      <Routes>
        <Route path="/" element={<UserRole />} />
        <Route path="/report" element={<UserRole />} />
        <Route path="/login" element={<StationLogin />} />
        <Route path="/station/dashboard" element={<StationDashboard />} />
      </Routes>
    </div>
  )
}

export default App

import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, ArrowRight } from 'lucide-react';
import { POLICE_STATION } from '../utils/mappings';

const API_BASE_URL = 'https://gridlock-backend.janbaas.me';

const StationLogin = () => {
  const [stationId, setStationId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/portal/login`, {
        police_station: parseInt(stationId, 10),
        password: password
      });

      if (response.data && response.data.token) {
        localStorage.setItem('ares_token', response.data.token);
        localStorage.setItem('ares_station_id', stationId);
        navigate('/station/dashboard');
      } else {
        setError('Invalid response from server.');
      }
    } catch (err) {
      console.error(err);
      setError('Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-col justify-center align-center h-full w-full" style={{ background: 'radial-gradient(circle at center, var(--bg-surface) 0%, var(--bg-base) 100%)' }}>
      
      <div className="glass-panel animate-slide-in" style={{ padding: 'var(--spacing-6)', width: '100%', maxWidth: '400px' }}>
        <div className="flex-col align-center" style={{ marginBottom: 'var(--spacing-6)' }}>
          <div style={{ backgroundColor: 'var(--primary-light)', padding: '1rem', borderRadius: '50%', marginBottom: '1rem' }}>
            <ShieldCheck size={36} color="var(--primary)" />
          </div>
          <h1 className="text-h2" style={{ textAlign: 'center' }}>Station Portal</h1>
          <p className="text-body" style={{ textAlign: 'center' }}>Secure Access for ARES Command</p>
        </div>

        {error && (
          <div className="badge badge-critical flex-row justify-center w-full" style={{ marginBottom: 'var(--spacing-4)', padding: '0.75rem', borderRadius: 'var(--radius-sm)' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="flex-col gap-4">
          <div className="input-group" style={{ marginBottom: 0 }}>
            <label className="input-label">Select Police Station</label>
            <select 
              className="input-field" 
              value={stationId}
              onChange={(e) => setStationId(e.target.value)}
              required 
            >
              <option value="">Select a Station</option>
              {Object.entries(POLICE_STATION).map(([id, name]) => (
                <option key={id} value={id}>
                  {name} (ID: {id})
                </option>
              ))}
            </select>
          </div>

          <div className="input-group" style={{ marginBottom: 0 }}>
            <label className="input-label">Password</label>
            <input 
              type="password" 
              className="input-field" 
              placeholder="••••••••" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required 
            />
          </div>

          <button type="submit" className="btn btn-primary w-full" disabled={loading} style={{ marginTop: 'var(--spacing-4)' }}>
            {loading ? 'Authenticating...' : 'Access Dashboard'} <ArrowRight size={18} />
          </button>
        </form>
        
        <div className="flex-row justify-center" style={{ marginTop: 'var(--spacing-6)' }}>
          <a href="/" className="text-small" style={{ color: 'var(--text-muted)' }}>&larr; Back to Public Map</a>
        </div>
      </div>
    </div>
  );
};

export default StationLogin;

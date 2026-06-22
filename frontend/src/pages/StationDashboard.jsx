import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { LogOut, Activity, AlertCircle, CheckCircle, Truck } from 'lucide-react';
import { EVENT_CAUSE, POLICE_STATION } from '../utils/mappings';

//const API_BASE_URL = 'https://gridlock-backend.janbaas.me';
const API_BASE_URL = 'http://localhost:8000';



const StationDashboard = () => {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState('time'); // 'time' or 'risk'
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [feedback, setFeedback] = useState({ 
    actual_officers: '', 
    actual_barricades: '', 
    actual_road_closure: false, 
    actual_priority: false, 
    feedback_notes: '' 
  });
  const navigate = useNavigate();

  const stationId = localStorage.getItem('ares_station_id');
  const token = localStorage.getItem('ares_token');

  useEffect(() => {
    if (!stationId || !token) {
      navigate('/login');
      return;
    }
    fetchIncidents();
  }, [stationId, token, navigate]);

  const fetchIncidents = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/portal/incidents/${stationId}?status=ACTIVE`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setIncidents(response.data?.incidents || []);
    } catch (err) {
      console.error('Failed to fetch incidents', err);
      if (err.response && err.response.status === 401) {
        handleLogout();
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('ares_token');
    localStorage.removeItem('ares_station_id');
    navigate('/login');
  };

  const handleResolveClick = (incident) => {
    setSelectedIncident(incident);
  };

  const submitFeedback = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        actual_officers: parseInt(feedback.actual_officers, 10),
        actual_barricades: parseInt(feedback.actual_barricades, 10),
        actual_road_closure: feedback.actual_road_closure ? 1 : 0,
        actual_priority: feedback.actual_priority ? 1 : 0,
        feedback_notes: feedback.feedback_notes || ""
      };

      await axios.post(`${API_BASE_URL}/api/portal/incidents/${selectedIncident.id || selectedIncident.incident_id}/feedback`, payload, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedIncident(null);
      setFeedback({ actual_officers: '', actual_barricades: '', actual_road_closure: false, actual_priority: false, feedback_notes: '' });
      fetchIncidents(); // Refresh queue
    } catch (err) {
      console.error('Failed to submit feedback', err);
      alert('Failed to submit feedback. Please try again.');
    }
  };

  return (
    <div className="flex-col h-full w-full">
      {/* Navbar */}
      <div className="glass-panel flex-row justify-between align-center" style={{ padding: 'var(--spacing-4) var(--spacing-6)', borderRadius: 0, borderBottom: '1px solid var(--border-light)' }}>
        <div className="flex-row align-center gap-4">
          <Activity color="var(--primary)" size={28} />
          <h1 className="text-h3">ARES Command Center</h1>
          <span className="badge badge-success">{POLICE_STATION[stationId] || `Station #${stationId}`}</span>
        </div>
        <button className="btn btn-ghost" onClick={handleLogout}>
          <LogOut size={18} /> Logout
        </button>
      </div>

      {/* Main Board */}
      <div style={{ flex: 1, padding: 'var(--spacing-6)', overflowY: 'auto' }}>
        <div className="flex-row justify-between align-center" style={{ marginBottom: 'var(--spacing-6)' }}>
          <h2 className="text-h2">Active Incidents</h2>
          <div className="flex-row gap-4 align-center">
            <select 
              className="input-field" 
              style={{ width: 'auto', marginBottom: 0, padding: '0.5rem 2rem 0.5rem 1rem' }}
              value={sortBy} 
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="time">Sort by: Time (Newest First)</option>
              <option value="risk">Sort by: Risk (High to Low)</option>
            </select>
            <button className="btn btn-primary" onClick={fetchIncidents}>Refresh Queue</button>
          </div>
        </div>

        {loading ? (
          <div className="flex-row justify-center p-6 text-muted">Loading incidents...</div>
        ) : incidents.length === 0 ? (
          <div className="glass-panel flex-col align-center justify-center p-6 text-muted" style={{ padding: 'var(--spacing-6)', textAlign: 'center' }}>
            <CheckCircle size={48} color="var(--success)" style={{ marginBottom: 'var(--spacing-4)' }} />
            <h3 className="text-h3">All Clear</h3>
            <p>No active incidents requiring response at the moment.</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 'var(--spacing-5)' }}>
            {[...incidents]
              .sort((a, b) => {
                if (sortBy === 'risk') {
                  const riskWeights = { 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1 };
                  const weightA = riskWeights[a.risk_level?.toUpperCase()] || 0;
                  const weightB = riskWeights[b.risk_level?.toUpperCase()] || 0;
                  if (weightA !== weightB) return weightB - weightA;
                  // fallback to score if level is same
                  return (b.risk_score || 0) - (a.risk_score || 0);
                } else {
                  // Sort by time (assuming created_at or id exists)
                  const timeA = new Date(a.created_at || a.timestamp || 0).getTime();
                  const timeB = new Date(b.created_at || b.timestamp || 0).getTime();
                  return timeB - timeA;
                }
              })
              .map((inc, idx) => {
              
              const level = inc.risk_level?.toUpperCase() || 'LOW';
              const riskColor = level === 'HIGH' ? 'var(--accent)' : (level === 'MEDIUM' ? 'var(--warning)' : 'var(--success)');
              const badgeClass = level === 'HIGH' ? 'badge-critical' : (level === 'MEDIUM' ? 'badge-warning' : 'badge-success');
              
              return (
                <div key={idx} className="glass-panel flex-col" style={{ padding: 'var(--spacing-5)', borderTop: `4px solid ${riskColor}` }}>
                  <div className="flex-row justify-between align-center" style={{ marginBottom: 'var(--spacing-3)' }}>
                    <div className="flex-col">
                      <span className="font-bold text-h3">{EVENT_CAUSE[inc.event_cause] || 'Incident'}</span>
                      {inc.description && <span className="text-small text-muted" style={{ marginTop: '2px' }}>{inc.description}</span>}
                    </div>
                    <span className={`badge ${badgeClass}`}>Risk: {inc.risk_level || 'LOW'} ({inc.risk_score || 0})</span>
                  </div>
                  
                  <p className="text-small" style={{ marginBottom: 'var(--spacing-4)' }}>
                    <AlertCircle size={14} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
                    Location: {inc.latitude?.toFixed(4)}, {inc.longitude?.toFixed(4)}
                  </p>

                  <div className="flex-row gap-4" style={{ marginBottom: 'var(--spacing-5)', padding: 'var(--spacing-3)', backgroundColor: 'var(--bg-base)', borderRadius: 'var(--radius-sm)' }}>
                    <div className="flex-col">
                      <span className="text-small">Officers</span>
                      <span className="font-bold">{inc.officers || '2'}</span>
                    </div>
                    <div className="flex-col">
                      <span className="text-small">Barricades</span>
                      <span className="font-bold">{inc.barricades || '0'}</span>
                    </div>
                    {inc.escalation && inc.escalation !== "None" && (
                      <div className="flex-col">
                        <span className="text-small">Escalation</span>
                        <span className="font-bold" style={{color: 'var(--accent)'}}>{inc.escalation}</span>
                      </div>
                    )}
                  </div>

                  <button className="btn btn-success w-full" onClick={() => handleResolveClick(inc)} style={{ backgroundColor: 'var(--success)', color: 'white', marginTop: 'auto' }}>
                    <CheckCircle size={18} /> Mark as Resolved
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Retrospective Feedback Modal */}
      {selectedIncident && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2 className="text-h2" style={{ marginBottom: 'var(--spacing-2)' }}>Incident Resolved</h2>
            <p className="text-body" style={{ marginBottom: 'var(--spacing-5)' }}>Please provide actual resource data to improve ARES predictions.</p>
            
            <form onSubmit={submitFeedback} className="flex-col gap-4">
              <div className="input-group">
                <label className="input-label">Actual Officers Used</label>
                <input 
                  type="number" 
                  className="input-field" 
                  min="0"
                  value={feedback.actual_officers}
                  onChange={(e) => setFeedback({...feedback, actual_officers: e.target.value})}
                  required 
                />
              </div>

              <div className="input-group">
                <label className="input-label">Actual Barricades Used</label>
                <input 
                  type="number" 
                  className="input-field" 
                  min="0"
                  value={feedback.actual_barricades}
                  onChange={(e) => setFeedback({...feedback, actual_barricades: e.target.value})}
                  required 
                />
              </div>

              <div className="flex-row align-center gap-2" style={{ marginBottom: 'var(--spacing-2)' }}>
                <input 
                  type="checkbox" 
                  id="road-closure"
                  checked={feedback.actual_road_closure}
                  onChange={(e) => setFeedback({...feedback, actual_road_closure: e.target.checked})}
                  style={{ width: '1.2rem', height: '1.2rem' }}
                />
                <label htmlFor="road-closure" className="input-label">Road Closure Was Needed</label>
              </div>

              <div className="flex-row align-center gap-2" style={{ marginBottom: 'var(--spacing-4)' }}>
                <input 
                  type="checkbox" 
                  id="high-priority"
                  checked={feedback.actual_priority}
                  onChange={(e) => setFeedback({...feedback, actual_priority: e.target.checked})}
                  style={{ width: '1.2rem', height: '1.2rem' }}
                />
                <label htmlFor="high-priority" className="input-label">It Was High Priority</label>
              </div>
              
              <div className="input-group">
                <label className="input-label">Additional Notes</label>
                <input 
                  type="text" 
                  className="input-field" 
                  placeholder="Any details to help ML learn?"
                  value={feedback.feedback_notes}
                  onChange={(e) => setFeedback({...feedback, feedback_notes: e.target.value})}
                />
              </div>

              <div className="flex-row gap-4">
                <button type="button" className="btn btn-ghost flex-1" onClick={() => setSelectedIncident(null)}>Cancel</button>
                <button type="submit" className="btn btn-primary flex-1">Submit Feedback</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default StationDashboard;

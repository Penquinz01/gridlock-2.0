import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { MapPin, AlertTriangle, Send } from 'lucide-react';
import IncidentMap from '../components/IncidentMap';
import { EVENT_CAUSE, VEHICLE_TYPE } from '../utils/mappings';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://gridlock-backend.janbaas.me');


const UserRole = () => {
  const [reportData, setReportData] = useState({
    latitude: '12.9716',
    longitude: '77.5946',
    cause: '',
    timestamp: '',
    veh_type: '',
    description: ''
  });
  const [hotspots, setHotspots] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [reportStatus, setReportStatus] = useState(null);
  const [mapUrl, setMapUrl] = useState(null);

  const fetchHotspots = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/hotspots?top_n=50`);
      setHotspots(response.data?.hotspots || []);
    } catch (error) {
      console.error("Error fetching hotspots:", error);
    }
  };

  const handleGetCurrentLocation = () => {
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(position => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        if (lat >= 12.7 && lat <= 13.4 && lng >= 77.2 && lng <= 77.9) {
          setReportData(prev => ({
            ...prev,
            latitude: lat,
            longitude: lng
          }));
          setReportStatus(null);
        } else {
          setReportStatus({ type: 'error', message: 'Current location is outside Bengaluru bounds.' });
        }
      }, () => {
        setReportStatus({ type: 'error', message: 'Failed to retrieve location.' });
      });
    } else {
      setReportStatus({ type: 'error', message: 'Geolocation is not supported.' });
    }
  };

  useEffect(() => {
    fetchHotspots();
    
    // Set current time
    const now = new Date().toISOString().slice(0, 16);
    setReportData(prev => ({ ...prev, timestamp: now }));

    // Get Geolocation on load
    handleGetCurrentLocation();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setReportData(prev => ({ ...prev, [name]: value }));
  };

  const handleMapClick = (lat, lng) => {
    setReportData(prev => ({
      ...prev,
      latitude: lat.toFixed(5),
      longitude: lng.toFixed(5)
    }));
  };

  const submitReport = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setReportStatus(null);
    try {
      const lat = parseFloat(reportData.latitude);
      const lng = parseFloat(reportData.longitude);
      
      // Client-side validation matching backend expectations
      if (lat < 12.7 || lat > 13.4 || lng < 77.2 || lng > 77.9) {
        setReportStatus({ type: 'error', message: 'Location must be within Bengaluru district (Lat: 12.7-13.4, Lng: 77.2-77.9)' });
        setSubmitting(false);
        return;
      }

      const payload = {
        latitude: lat,
        longitude: lng,
        event_cause: parseInt(reportData.cause, 10),
        time: reportData.timestamp.length === 16 ? reportData.timestamp + ":00" : reportData.timestamp
      };

      if (reportData.veh_type !== '') {
        payload.veh_type = parseInt(reportData.veh_type, 10);
      }
      
      if (reportData.cause === '17' && reportData.description.trim() !== '') {
        payload.description = reportData.description.trim();
      }

      const response = await axios.post(`${API_BASE_URL}/report`, payload);
      setReportStatus({ type: 'success', message: 'Report submitted successfully. Route generated.' });
      await fetchHotspots();
      
      if (response.data && response.data.diversion_map_url) {
        setMapUrl(`${API_BASE_URL}${response.data.diversion_map_url}`);
      }
    } catch (error) {
      console.error(error);
      setReportStatus({ type: 'error', message: 'Failed to submit report. Please try again.' });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex-row h-full w-full">
      {/* Sidebar - Form & Hotspots */}
      <div className="flex-col glass-panel" style={{ width: '380px', height: '100%', borderRadius: 0, padding: 'var(--spacing-5)', overflowY: 'auto', zIndex: 'var(--z-overlay)', borderRight: '1px solid var(--border-light)' }}>
        <div style={{ marginBottom: 'var(--spacing-6)' }}>
          <h1 className="text-h2" style={{ color: 'var(--primary)', marginBottom: 'var(--spacing-2)' }}>ARES</h1>
          <p className="text-body">AI-Powered Incident Response</p>
        </div>

        {/* Quick Report Form */}
        <div style={{ marginBottom: 'var(--spacing-6)' }}>
          <h2 className="text-h3 flex-row gap-2" style={{ marginBottom: 'var(--spacing-4)' }}>
            <AlertTriangle size={24} color="var(--accent)" /> Report Incident
          </h2>
          <form onSubmit={submitReport} className="flex-col gap-4">
            <div className="input-group" style={{ marginBottom: 0 }}>
              <label className="input-label">Location (Lat, Lng) *</label>
              <div className="flex-row gap-2">
                <input 
                  type="text" 
                  name="latitude"
                  className="input-field" 
                  placeholder="Latitude" 
                  value={reportData.latitude}
                  onChange={handleInputChange}
                  required 
                />
                <input 
                  type="text" 
                  name="longitude"
                  className="input-field" 
                  placeholder="Longitude" 
                  value={reportData.longitude}
                  onChange={handleInputChange}
                  required 
                />
                <button type="button" className="btn btn-ghost" title="Use Current Location" onClick={handleGetCurrentLocation} style={{ padding: '0.75rem' }}>
                  <MapPin size={20} />
                </button>
              </div>
            </div>

            <div className="input-group" style={{ marginBottom: 0 }}>
              <label className="input-label">Cause of Incident *</label>
              <select 
                name="cause" 
                className="input-field" 
                value={reportData.cause} 
                onChange={handleInputChange}
                required
              >
                <option value="">Select a cause</option>
                {Object.entries(EVENT_CAUSE).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            {reportData.cause === '17' && (
              <div className="input-group" style={{ marginBottom: 0 }}>
                <label className="input-label">Description *</label>
                <textarea 
                  name="description" 
                  className="input-field" 
                  value={reportData.description} 
                  onChange={handleInputChange}
                  rows="2"
                  placeholder="Describe the incident..."
                  required
                ></textarea>
              </div>
            )}

            <div className="input-group" style={{ marginBottom: 0 }}>
              <label className="input-label">Select Vehicle</label>
              <select 
                name="veh_type" 
                className="input-field" 
                value={reportData.veh_type} 
                onChange={handleInputChange}
              >
                <option value="">Select Vehicle</option>
                {Object.entries(VEHICLE_TYPE)
                  .filter(([value]) => parseInt(value, 10) <= 9)
                  .map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
              </select>
            </div>

            <div className="input-group" style={{ marginBottom: 0 }}>
              <label className="input-label">Time *</label>
              <input 
                type="datetime-local" 
                name="timestamp" 
                className="input-field" 
                value={reportData.timestamp}
                onChange={handleInputChange}
                required
              />
            </div>

            <button type="submit" className="btn btn-accent w-full" disabled={submitting} style={{ marginTop: 'var(--spacing-2)' }}>
              <Send size={18} /> {submitting ? 'Reporting...' : 'Submit Report'}
            </button>

            {reportStatus && (
              <div className={`text-small ${reportStatus.type === 'success' ? 'text-success' : 'text-accent'}`} style={{ marginTop: '0.5rem', textAlign: 'center' }}>
                {reportStatus.message}
              </div>
            )}
          </form>
        </div>

        <hr style={{ borderColor: 'var(--border-light)', margin: 'var(--spacing-4) 0' }} />

        <hr style={{ borderColor: 'var(--border-light)', margin: 'var(--spacing-4) 0' }} />
        
        <div className="flex-col gap-3">
           <p className="text-muted text-small text-center">Map automatically captures coordinate clicks and displays active hotspots.</p>
        </div>
      </div>

      {/* Main Map Area */}
      <div style={{ flex: 1, position: 'relative', height: '100%' }}>
        <IncidentMap 
          apiBaseUrl={API_BASE_URL}
          useIframe={false} 
          foliumUrl={mapUrl} 
          defaultLat={reportData.latitude} 
          defaultLng={reportData.longitude} 
          hotspots={hotspots}
          onMapClick={handleMapClick}
        />
        <div style={{ position: 'absolute', top: '1rem', right: '1rem', zIndex: 'var(--z-overlay)' }}>
          <a href="/login" className="btn" style={{ backgroundColor: '#000000', color: '#ffffff', border: '1px solid var(--border-light)' }}>Police Station Login</a>
        </div>
      </div>
    </div>
  );
};

export default UserRole;

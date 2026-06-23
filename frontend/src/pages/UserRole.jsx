import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { MapPin, AlertTriangle, Send, Activity, Lock, Unlock, Check, Search } from 'lucide-react';
import IncidentMap from '../components/IncidentMap';
import { EVENT_CAUSE, VEHICLE_TYPE } from '../utils/mappings';

const API_BASE_URL = 'https://gridlock-backend.janbaas.me';
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
    // Fetch Hotspots
    const fetchHotspots = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/hotspots?top_n=50`);
        setHotspots(response.data?.hotspots || []);
      } catch (error) {
        console.error("Error fetching hotspots:", error);
      }
    };
    fetchHotspots();
    
    // Set current time
    const now = new Date().toISOString().slice(0, 16);
    setReportData(prev => ({ ...prev, timestamp: now }));

    // Get Geolocation on load
    handleGetCurrentLocation();
  }, []);

  const [routeParams, setRouteParams] = useState({
    origin: { lat: null, lng: null, name: '', confirmed: false },
    destination: { lat: null, lng: null, name: '', confirmed: false },
  });
  const [originSuggestions, setOriginSuggestions] = useState([]);
  const [destSuggestions, setDestSuggestions] = useState([]);
  const [routeLoading, setRouteLoading] = useState(false);
  const [routeInfo, setRouteInfo] = useState(null);

  const fetchSuggestions = async (query) => {
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/map/search?q=${encodeURIComponent(query)}&limit=5`
      );
      const data = await res.json();
      return data?.suggestions || [];
    } catch (err) {
      console.error('Autocomplete search failed:', err);
      return [];
    }
  };

  useEffect(() => {
    const query = routeParams.origin.name;
    if (!query || query.includes(',') || routeParams.origin.confirmed || (routeParams.origin.lat && routeParams.origin.lng)) {
      setOriginSuggestions([]);
      return;
    }
    const delayDebounce = setTimeout(async () => {
      const results = await fetchSuggestions(query);
      setOriginSuggestions(results);
    }, 300);
    return () => clearTimeout(delayDebounce);
  }, [routeParams.origin.name, routeParams.origin.confirmed, routeParams.origin.lat, routeParams.origin.lng]);

  useEffect(() => {
    const query = routeParams.destination.name;
    if (!query || query.includes(',') || routeParams.destination.confirmed || (routeParams.destination.lat && routeParams.destination.lng)) {
      setDestSuggestions([]);
      return;
    }
    const delayDebounce = setTimeout(async () => {
      const results = await fetchSuggestions(query);
      setDestSuggestions(results);
    }, 300);
    return () => clearTimeout(delayDebounce);
  }, [routeParams.destination.name, routeParams.destination.confirmed, routeParams.destination.lat, routeParams.destination.lng]);

  const handleOriginSearchChange = (e) => {
    const val = e.target.value;
    setRouteParams(prev => ({
      ...prev,
      origin: { ...prev.origin, name: val, lat: null, lng: null }
    }));
  };

  const handleDestSearchChange = (e) => {
    const val = e.target.value;
    setRouteParams(prev => ({
      ...prev,
      destination: { ...prev.destination, name: val, lat: null, lng: null }
    }));
  };

  const selectSuggestion = (type, suggestion) => {
    setRouteParams(prev => ({
      ...prev,
      [type]: {
        lat: suggestion.latitude,
        lng: suggestion.longitude,
        name: suggestion.name,
        confirmed: false
      }
    }));
    if (type === 'origin') {
      setOriginSuggestions([]);
    } else {
      setDestSuggestions([]);
    }
  };

  const confirmField = (type) => {
    setRouteParams(prev => ({
      ...prev,
      [type]: {
        ...prev[type],
        confirmed: true
      }
    }));
  };

  const unlockField = (type) => {
    setRouteParams(prev => ({
      ...prev,
      [type]: {
        ...prev[type],
        confirmed: false
      }
    }));
    setRouteInfo(null);
  };

  const findRoute = async () => {
    if (!routeParams.origin.confirmed || !routeParams.destination.confirmed) return;
    setRouteLoading(true);
    try {
      const payload = {
        origin: {
          latitude: routeParams.origin.lat,
          longitude: routeParams.origin.lng
        },
        destination: {
          latitude: routeParams.destination.lat,
          longitude: routeParams.destination.lng
        }
      };
      const response = await axios.post(`${API_BASE_URL}/route`, payload);
      setRouteInfo(response.data);
    } catch (err) {
      console.error('Failed to calculate route:', err);
      alert('Failed to calculate safest route. Please verify locations and try again.');
    } finally {
      setRouteLoading(false);
    }
  };

  const clearRoute = () => {
    setRouteInfo(null);
    setRouteParams({
      origin: { lat: null, lng: null, name: '', confirmed: false },
      destination: { lat: null, lng: null, name: '', confirmed: false }
    });
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setReportData(prev => ({ ...prev, [name]: value }));
  };

  const handleMapClick = (lat, lng) => {
    const latStr = lat.toFixed(5);
    const lngStr = lng.toFixed(5);

    // 1. Always fill Report Input on the left side
    setReportData(prev => ({
      ...prev,
      latitude: latStr,
      longitude: lngStr
    }));

    // 2. Fill Origin in route planner if not confirmed (unlocked)
    if (!routeParams.origin.confirmed) {
      setRouteParams(prev => ({
        ...prev,
        origin: {
          lat,
          lng,
          name: `${latStr}, ${lngStr}`,
          confirmed: false
        }
      }));
    }

    // 3. Fill Destination in route planner if not confirmed (unlocked)
    if (!routeParams.destination.confirmed) {
      setRouteParams(prev => ({
        ...prev,
        destination: {
          lat,
          lng,
          name: `${latStr}, ${lngStr}`,
          confirmed: false
        }
      }));
    }
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
          routeCoordinates={routeInfo?.route_coordinates}
          originCoords={routeParams.origin.confirmed ? { lat: routeParams.origin.lat, lng: routeParams.origin.lng } : null}
          destCoords={routeParams.destination.confirmed ? { lat: routeParams.destination.lat, lng: routeParams.destination.lng } : null}
        />

        {/* Route Planner floating on the right */}
        <div className="glass-panel flex-col gap-4 animate-slide-in" style={{ 
          position: 'absolute', 
          top: '1rem', 
          right: '1rem', 
          zIndex: 1000, 
          width: '320px', 
          maxHeight: 'calc(100% - 6rem)',
          padding: 'var(--spacing-4)', 
          overflowY: 'auto',
          boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
          backgroundColor: 'rgba(10, 10, 10, 0.92)',
          border: '1px solid var(--border-light)'
        }}>
          <div className="flex-row justify-between align-center">
            <h2 className="text-h3 flex-row gap-2" style={{ margin: 0 }}>
              <Activity size={20} color="var(--primary)" /> Route Planner
            </h2>
          </div>
          
          {/* Origin field */}
          <div className="input-group" style={{ marginBottom: 0 }}>
            <label className="input-label">Origin Location</label>
            <div className="flex-row gap-2" style={{ position: 'relative' }}>
              <input 
                type="text" 
                className="input-field" 
                placeholder="Search or click map..." 
                value={routeParams.origin.name}
                onChange={handleOriginSearchChange}
                disabled={routeParams.origin.confirmed}
                style={{ paddingRight: '2.5rem' }}
              />
              {routeParams.origin.confirmed ? (
                <button 
                  type="button" 
                  className="btn btn-ghost" 
                  onClick={() => unlockField('origin')}
                  title="Unlock origin"
                  style={{ padding: '0.5rem', minWidth: '40px' }}
                >
                  <Lock size={16} color="var(--primary)" />
                </button>
              ) : (
                routeParams.origin.lat && (
                  <button 
                    type="button" 
                    className="btn btn-accent" 
                    onClick={() => confirmField('origin')}
                    title="Confirm origin"
                    style={{ padding: '0.5rem', minWidth: '40px' }}
                  >
                    <Check size={16} />
                  </button>
                )
              )}
              {/* Autocomplete suggestions */}
              {!routeParams.origin.confirmed && originSuggestions.length > 0 && (
                <ul className="suggestions-list" style={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  right: 0,
                  backgroundColor: 'rgba(10, 10, 10, 0.98)',
                  border: '1px solid var(--border-light)',
                  borderRadius: 'var(--radius-md)',
                  listStyle: 'none',
                  padding: '4px 0',
                  margin: '4px 0 0 0',
                  maxHeight: '150px',
                  overflowY: 'auto',
                  zIndex: 1010,
                  boxShadow: '0 4px 12px rgba(0,0,0,0.5)'
                }}>
                  {originSuggestions.map((s, idx) => (
                    <li 
                      key={idx} 
                      onClick={() => selectSuggestion('origin', s)}
                      style={{ padding: '8px 12px', cursor: 'pointer', borderBottom: '1px solid var(--border-light)' }}
                      onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--primary-light)'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}
                    >
                      <strong style={{ fontSize: '0.85rem' }}>{s.name}</strong>
                      {s.address && <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{s.address}</div>}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {/* Destination field */}
          <div className="input-group" style={{ marginBottom: 0 }}>
            <label className="input-label">Destination Location</label>
            <div className="flex-row gap-2" style={{ position: 'relative' }}>
              <input 
                type="text" 
                className="input-field" 
                placeholder="Search or click map..." 
                value={routeParams.destination.name}
                onChange={handleDestSearchChange}
                disabled={routeParams.destination.confirmed}
                style={{ paddingRight: '2.5rem' }}
              />
              {routeParams.destination.confirmed ? (
                <button 
                  type="button" 
                  className="btn btn-ghost" 
                  onClick={() => unlockField('destination')}
                  title="Unlock destination"
                  style={{ padding: '0.5rem', minWidth: '40px' }}
                >
                  <Lock size={16} color="var(--primary)" />
                </button>
              ) : (
                routeParams.destination.lat && (
                  <button 
                    type="button" 
                    className="btn btn-accent" 
                    onClick={() => confirmField('destination')}
                    title="Confirm destination"
                    style={{ padding: '0.5rem', minWidth: '40px' }}
                  >
                    <Check size={16} />
                  </button>
                )
              )}
              {/* Autocomplete suggestions */}
              {!routeParams.destination.confirmed && destSuggestions.length > 0 && (
                <ul className="suggestions-list" style={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  right: 0,
                  backgroundColor: 'rgba(10, 10, 10, 0.98)',
                  border: '1px solid var(--border-light)',
                  borderRadius: 'var(--radius-md)',
                  listStyle: 'none',
                  padding: '4px 0',
                  margin: '4px 0 0 0',
                  maxHeight: '150px',
                  overflowY: 'auto',
                  zIndex: 1010,
                  boxShadow: '0 4px 12px rgba(0,0,0,0.5)'
                }}>
                  {destSuggestions.map((s, idx) => (
                    <li 
                      key={idx} 
                      onClick={() => selectSuggestion('destination', s)}
                      style={{ padding: '8px 12px', cursor: 'pointer', borderBottom: '1px solid var(--border-light)' }}
                      onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--primary-light)'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}
                    >
                      <strong style={{ fontSize: '0.85rem' }}>{s.name}</strong>
                      {s.address && <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{s.address}</div>}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {/* Find Safest Route button */}
          <button 
            className="btn btn-primary w-full" 
            disabled={!routeParams.origin.confirmed || !routeParams.destination.confirmed || routeLoading}
            onClick={findRoute}
          >
            {routeLoading ? 'Calculating Route...' : 'Find Safest Route'}
          </button>

          {/* Display Route Info if available */}
          {routeInfo && (
            <div className="flex-col gap-2 animate-slide-in" style={{ 
              padding: 'var(--spacing-3)', 
              backgroundColor: 'var(--bg-surface)', 
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-light)'
            }}>
              <h4 className="text-body font-bold" style={{ margin: 0 }}>Route Details</h4>
              <div className="flex-row justify-between text-small">
                <span>Distance:</span>
                <span className="font-bold">{routeInfo.distance_km} km</span>
              </div>
              <div className="flex-row justify-between text-small">
                <span>Duration:</span>
                <span className="font-bold">{routeInfo.duration_minutes} mins</span>
              </div>
              {routeInfo.warnings && routeInfo.warnings.length > 0 && (
                <div className="flex-col gap-1" style={{ marginTop: '0.25rem' }}>
                  {routeInfo.warnings.map((w, idx) => (
                    <span key={idx} className="badge badge-warning text-center" style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem', width: '100%' }}>
                      ⚠️ {w}
                    </span>
                  ))}
                </div>
              )}
              <button 
                type="button" 
                className="btn btn-ghost w-full" 
                onClick={clearRoute} 
                style={{ marginTop: '0.5rem', padding: '0.25rem 0.5rem', fontSize: '0.85rem' }}
              >
                Clear Route
              </button>
            </div>
          )}
        </div>

        {/* Police Station Login at bottom right */}
        <div style={{ position: 'absolute', bottom: '1.5rem', right: '1.5rem', zIndex: 1000 }}>
          <a href="/login" className="btn" style={{ backgroundColor: '#000000', color: '#ffffff', border: '1px solid var(--border-light)' }}>Police Station Login</a>
        </div>
      </div>
    </div>
  );
};

export default UserRole;

import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, CircleMarker, Tooltip, useMapEvents, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default Leaflet markers missing icons in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Component to programmatically fly the map to a new location
const MapController = ({ targetCenter }) => {
  const map = useMap();
  useEffect(() => {
    if (targetCenter) {
      map.flyTo(targetCenter, 14, { duration: 1.5 });
    }
  }, [targetCenter, map]);
  return null;
};

// Component to handle clicks on the map
const MapEvents = ({ onMapClick, setClickedPos }) => {
  useMapEvents({
    click(e) {
      if (onMapClick) {
        onMapClick(e.latlng.lat, e.latlng.lng);
        setClickedPos([e.latlng.lat, e.latlng.lng]);
      }
    },
  });
  return null;
};

const IncidentMap = ({ foliumUrl = null, useIframe = false, defaultLat, defaultLng, hotspots = [], onMapClick = null }) => {
  const [clickedPos, setClickedPos] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [targetCenter, setTargetCenter] = useState(null);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    if (!searchQuery.trim()) {
      setSuggestions([]);
      return;
    }

    const delayDebounceFn = setTimeout(async () => {
      setIsSearching(true);
      try {
        // Fetch up to 15 results restricted to the Karnataka bounding box
        const res = await fetch(`https://photon.komoot.io/api/?q=${encodeURIComponent(searchQuery)}&limit=15&lon=77.5946&lat=12.9716&bbox=74.0,11.5,78.6,18.5`);
        const data = await res.json();
        if (data && data.features) {
          setSuggestions(data.features);
        }
      } catch (err) {
        console.error("Search failed:", err);
      } finally {
        setIsSearching(false);
      }
    }, 300); // 300ms debounce for faster automatic appearance

    return () => clearTimeout(delayDebounceFn);
  }, [searchQuery]);

  const handleSelectPlace = (feature) => {
    const [lon, lat] = feature.geometry.coordinates;
    setTargetCenter([lat, lon]);
    setSearchQuery(feature.properties.name || '');
    setSuggestions([]); // Clears dropdown automatically
  };

  // If useIframe is strictly true and there's a folium map (like for diversion routes)
  if (useIframe && foliumUrl) {
    return (
      <div className="map-container" style={{ width: '100%', height: '100%', position: 'relative', minHeight: '400px' }}>
        <iframe
          src={foliumUrl}
          className="map-iframe"
          style={{ width: '100%', height: '100%', border: 'none' }}
          title="Incident Diversion Map"
          sandbox="allow-scripts allow-same-origin"
        ></iframe>
      </div>
    );
  }

  const centerLat = defaultLat || 12.9716;
  const centerLng = defaultLng || 77.5946;

  return (
    <div className="map-container" style={{ width: '100%', height: '100%', position: 'relative', minHeight: '500px', backgroundColor: '#000000', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
      
      {/* Search Bar Overlay */}
      <div style={{ position: 'absolute', top: '15px', left: '50%', transform: 'translateX(-50%)', zIndex: 1000, width: '90%', maxWidth: '400px' }}>
        <div style={{ position: 'relative' }}>
          <input 
            type="text" 
            className="input-field"
            placeholder="Search for a location..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ width: '100%', padding: '12px 40px 12px 20px', borderRadius: '24px', boxShadow: '0 4px 12px rgba(0,0,0,0.5)', backgroundColor: 'var(--bg-surface)' }}
          />
          {searchQuery && (
            <button 
              onClick={() => {
                setSearchQuery('');
                setSuggestions([]);
              }}
              style={{
                position: 'absolute',
                right: '15px',
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'none',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                fontSize: '16px',
                padding: '4px'
              }}
              title="Clear search"
            >
              ✕
            </button>
          )}
          
          {suggestions.length > 0 && (
            <ul style={{ 
              position: 'absolute', top: '100%', left: 0, right: 0, marginTop: '8px',
              backgroundColor: 'var(--bg-surface)', borderRadius: '12px', boxShadow: '0 8px 24px rgba(0,0,0,0.7)',
              listStyle: 'none', padding: '8px 0', margin: '8px 0 0 0', maxHeight: '300px', overflowY: 'auto', border: '1px solid var(--border-light)'
            }}>
              {suggestions.map((f, i) => {
                const props = f.properties;
                const displayName = [props.street, props.city, props.state, props.country].filter(Boolean).join(', ');
                return (
                  <li 
                    key={i} 
                    onClick={() => handleSelectPlace(f)}
                    style={{ padding: '10px 20px', cursor: 'pointer', borderBottom: i < suggestions.length - 1 ? '1px solid var(--border-light)' : 'none', color: 'var(--text-primary)', fontSize: '0.9rem' }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--primary-light)'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    <strong>{props.name}</strong>
                    {displayName && <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{displayName}</div>}
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </div>

      <MapContainer 
        center={[centerLat, centerLng]} 
        zoom={12} 
        style={{ width: '100%', height: '100%', zIndex: 1 }}
      >
        <MapController targetCenter={targetCenter} />
        {/* Highly detailed OSM tiles inverted via CSS to create a rich, path-heavy dark map */}
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          className="dark-map-tiles"
        />
        
        <MapEvents onMapClick={onMapClick} setClickedPos={setClickedPos} />

        {clickedPos && (
          <Marker position={clickedPos}>
            <Tooltip permanent direction="top" offset={[0, -20]}>
              <div style={{ color: '#000', fontWeight: 'bold' }}>Incident Location Logged</div>
            </Tooltip>
          </Marker>
        )}

        {hotspots.map((hs, idx) => (
          <CircleMarker 
            key={idx}
            center={[hs.latitude, hs.longitude]}
            radius={8 + Math.min(hs.incident_count * 1.5, 15)}
            pathOptions={{ color: '#eb9f46', fillColor: '#eb9f46', fillOpacity: 0.6, weight: 2 }}
          >
            {/* Tooltip shows on hover automatically in Leaflet */}
            <Tooltip direction="top" offset={[0, -10]} opacity={1}>
              <div style={{ padding: '2px', color: '#000' }}>
                <strong style={{ fontSize: '14px', marginBottom: '4px', display: 'block', color: '#eb9f46' }}>{hs.corridor_name || 'Corridor ' + hs.corridor}</strong>
                <div style={{ fontSize: '12px', marginBottom: '2px' }}>Incidents: <b>{hs.incident_count}</b></div>
                <div style={{ fontSize: '12px' }}>High Priority: <b>{(hs.high_priority_pct * 100).toFixed(0)}%</b></div>
              </div>
            </Tooltip>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
};

export default IncidentMap;

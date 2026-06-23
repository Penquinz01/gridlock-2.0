import React, { useState, useEffect, useRef, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, CircleMarker, Tooltip, useMapEvents, useMap, Polyline } from 'react-leaflet';
import { mappls, mappls_plugin } from 'mappls-web-maps';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const BANGALORE_CENTER = { lat: 12.9716, lng: 77.5946 };
const MAPPLS_MAP_ID = 'incident-map-mappls';
const mapplsClassObject = new mappls();
const mapplsPluginObject = new mappls_plugin();

const parseCoordinate = (value, fallback) => {
  const parsed = parseFloat(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const hotspotPopupHtml = (hs) => {
  let causesHtml = '';
  if (hs.causes && Object.keys(hs.causes).length > 0) {
    causesHtml = `
      <div style="margin-top:6px;border-top:1px solid #ddd;padding-top:4px;font-size:11px;color:#333;">
        ${Object.entries(hs.causes)
          .map(([cause, count]) => `<div>${cause}: <b>${count}</b></div>`)
          .join('')}
      </div>
    `;
  }
  return `
    <div style="padding:2px;color:#000;min-width:140px;">
      <strong style="font-size:14px;margin-bottom:4px;display:block;color:#eb9f46;">
        ${hs.corridor_name || `Corridor ${hs.corridor}`}
      </strong>
      <div style="font-size:12px;margin-bottom:2px;">Incidents: <b>${hs.incident_count}</b></div>
      <div style="font-size:12px;margin-bottom:2px;">High Priority: <b>${(hs.high_priority_pct * 100).toFixed(0)}%</b></div>
      ${causesHtml}
    </div>
  `;
};

const hotspotRadius = (incidentCount) => 80 + Math.min(incidentCount * 15, 170);

const MapSearchBar = ({ fetchSuggestions, onSelectPlace }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    if (!searchQuery.trim()) {
      setSuggestions([]);
      return undefined;
    }

    const delayDebounceFn = setTimeout(async () => {
      setIsSearching(true);
      try {
        const results = await fetchSuggestions(searchQuery);
        setSuggestions(results || []);
      } catch (err) {
        console.error('Search failed:', err);
        setSuggestions([]);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [fetchSuggestions, searchQuery]);

  const handleSelectPlace = (suggestion) => {
    onSelectPlace(suggestion.latitude, suggestion.longitude, suggestion.name);
    setSearchQuery(suggestion.name || '');
    setSuggestions([]);
  };

  return (
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
              padding: '4px',
            }}
            title="Clear search"
            type="button"
          >
            ✕
          </button>
        )}

        {isSearching && suggestions.length === 0 && searchQuery.trim() && (
          <div style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            marginTop: '8px',
            backgroundColor: 'var(--bg-surface)',
            borderRadius: '12px',
            padding: '10px 20px',
            color: 'var(--text-muted)',
            fontSize: '0.85rem',
          }}
          >
            Searching...
          </div>
        )}

        {suggestions.length > 0 && (
          <ul style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            marginTop: '8px',
            backgroundColor: 'var(--bg-surface)',
            borderRadius: '12px',
            boxShadow: '0 8px 24px rgba(0,0,0,0.7)',
            listStyle: 'none',
            padding: '8px 0',
            margin: '8px 0 0 0',
            maxHeight: '300px',
            overflowY: 'auto',
            border: '1px solid var(--border-light)',
          }}
          >
            {suggestions.map((suggestion, index) => (
              <li
                key={`${suggestion.latitude}-${suggestion.longitude}-${index}`}
                onClick={() => handleSelectPlace(suggestion)}
                style={{
                  padding: '10px 20px',
                  cursor: 'pointer',
                  borderBottom: index < suggestions.length - 1 ? '1px solid var(--border-light)' : 'none',
                  color: 'var(--text-primary)',
                  fontSize: '0.9rem',
                }}
                onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--primary-light)'; }}
                onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}
              >
                <strong>{suggestion.name}</strong>
                {suggestion.address && (
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{suggestion.address}</div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

const MapController = ({ targetCenter, routeBounds }) => {
  const map = useMap();
  useEffect(() => {
    if (targetCenter) {
      map.flyTo(targetCenter, 14, { duration: 1.5 });
    }
  }, [targetCenter, map]);

  useEffect(() => {
    if (routeBounds && routeBounds.length > 0) {
      map.fitBounds(routeBounds, { padding: [50, 50] });
    }
  }, [routeBounds, map]);

  return null;
};

const MapEvents = ({ onMapClick, setClickedPos }) => {
  const onMapClickRef = useRef(onMapClick);
  useEffect(() => {
    onMapClickRef.current = onMapClick;
  }, [onMapClick]);

  useMapEvents({
    click(e) {
      if (onMapClickRef.current) {
        onMapClickRef.current(e.latlng.lat, e.latlng.lng);
        setClickedPos([e.latlng.lat, e.latlng.lng]);
      }
    },
  });
  return null;
};

const OsmIncidentMap = ({
  apiBaseUrl,
  defaultLat,
  defaultLng,
  hotspots,
  onMapClick,
  routeCoordinates = null,
  originCoords = null,
  destCoords = null,
}) => {
  const [clickedPos, setClickedPos] = useState(null);
  const [targetCenter, setTargetCenter] = useState(null);

  const centerLat = parseCoordinate(defaultLat, BANGALORE_CENTER.lat);
  const centerLng = parseCoordinate(defaultLng, BANGALORE_CENTER.lng);

  const fetchSuggestions = useCallback(async (query) => {
    const res = await fetch(
      `${apiBaseUrl}/api/map/search?q=${encodeURIComponent(query)}&limit=15`
    );
    const data = await res.json();
    return data?.suggestions || [];
  }, [apiBaseUrl]);

  const handleSelectPlace = (lat, lng) => {
    setTargetCenter([lat, lng]);
  };

  return (
    <div className="map-container" style={{ width: '100%', height: '100%', position: 'relative', minHeight: '500px', backgroundColor: '#000000', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>

      <MapContainer
        center={[centerLat, centerLng]}
        zoom={12}
        style={{ width: '100%', height: '100%', zIndex: 1 }}
      >
        <MapController targetCenter={targetCenter} routeBounds={routeCoordinates} />
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

        {routeCoordinates && routeCoordinates.length > 0 && (
          <Polyline positions={routeCoordinates} color="#2196F3" weight={5} opacity={0.8} />
        )}

        {originCoords && (
          <Marker position={[originCoords.lat, originCoords.lng]}>
            <Tooltip permanent direction="top" offset={[0, -20]}>
              <div style={{ color: '#2e7d32', fontWeight: 'bold' }}>Origin</div>
            </Tooltip>
          </Marker>
        )}

        {destCoords && (
          <Marker position={[destCoords.lat, destCoords.lng]}>
            <Tooltip permanent direction="top" offset={[0, -20]}>
              <div style={{ color: '#d32f2f', fontWeight: 'bold' }}>Destination</div>
            </Tooltip>
          </Marker>
        )}

        {hotspots.map((hs, idx) => (
          <CircleMarker
            key={`${hs.latitude}-${hs.longitude}-${idx}`}
            center={[hs.latitude, hs.longitude]}
            radius={8 + Math.min(hs.incident_count * 1.5, 15)}
            pathOptions={{ color: '#eb9f46', fillColor: '#eb9f46', fillOpacity: 0.6, weight: 2 }}
          >
            <Tooltip direction="top" offset={[0, -10]} opacity={1}>
              <div dangerouslySetInnerHTML={{ __html: hotspotPopupHtml(hs) }} />
            </Tooltip>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
};

const MapplsIncidentMap = ({
  apiBaseUrl,
  mapConfig,
  defaultLat,
  defaultLng,
  hotspots,
  onMapClick,
  onInitFail,
  routeCoordinates = null,
  originCoords = null,
  destCoords = null,
}) => {
  const mapRef = useRef(null);
  const overlaysRef = useRef([]);
  const incidentMarkerRef = useRef(null);
  const routePolylineRef = useRef(null);
  const originMarkerRef = useRef(null);
  const destMarkerRef = useRef(null);
  const [isMapLoaded, setIsMapLoaded] = useState(false);
  const [clickedPos, setClickedPos] = useState(null);

  const onMapClickRef = useRef(onMapClick);
  useEffect(() => {
    onMapClickRef.current = onMapClick;
  }, [onMapClick]);

  const centerLat = parseCoordinate(defaultLat, BANGALORE_CENTER.lat);
  const centerLng = parseCoordinate(defaultLng, BANGALORE_CENTER.lng);

  const fetchSuggestions = useCallback(async (query) => {
    if (mapRef.current && isMapLoaded) {
      const pluginResults = await new Promise((resolve) => {
        let settled = false;
        const finish = (value) => {
          if (!settled) {
            settled = true;
            resolve(value);
          }
        };

        try {
          mapplsPluginObject.search(query, {
            map: mapRef.current,
            location: BANGALORE_CENTER,
            zoom: 12,
            hyperLocal: true,
          }, (response) => {
            const locations = response?.suggestedLocations || response?.data?.suggestedLocations || [];
            finish(locations.map((item) => ({
              name: item.placeName || item.name || query,
              address: item.placeAddress || item.address || '',
              latitude: parseFloat(item.latitude ?? item.lat),
              longitude: parseFloat(item.longitude ?? item.lng),
            })).filter((item) => Number.isFinite(item.latitude) && Number.isFinite(item.longitude)));
          });
          setTimeout(() => finish([]), 2000);
        } catch (err) {
          console.warn('Mappls plugin search failed:', err);
          finish([]);
        }
      });

      if (pluginResults.length > 0) {
        return pluginResults;
      }
    }

    const res = await fetch(
      `${apiBaseUrl}/api/map/search?q=${encodeURIComponent(query)}&limit=15`
    );
    const data = await res.json();
    return data?.suggestions || [];
  }, [apiBaseUrl, isMapLoaded]);

  const clearOverlays = () => {
    overlaysRef.current.forEach((overlay) => {
      try {
        if (overlay?.remove) {
          overlay.remove();
        } else {
          mapplsClassObject.removeLayer({ map: mapRef.current, layer: overlay });
        }
      } catch (err) {
        console.warn('Failed to remove map overlay:', err);
      }
    });
    overlaysRef.current = [];

    if (incidentMarkerRef.current) {
      try {
        if (incidentMarkerRef.current.remove) {
          incidentMarkerRef.current.remove();
        } else {
          mapplsClassObject.removeLayer({ map: mapRef.current, layer: incidentMarkerRef.current });
        }
      } catch (err) {
        console.warn('Failed to remove incident marker:', err);
      }
      incidentMarkerRef.current = null;
    }
  };

  useEffect(() => {
    if (!mapRef.current || !isMapLoaded) return;

    if (routePolylineRef.current) {
      try {
        if (routePolylineRef.current.remove) {
          routePolylineRef.current.remove();
        } else {
          mapplsClassObject.removeLayer({ map: mapRef.current, layer: routePolylineRef.current });
        }
      } catch (err) {}
      routePolylineRef.current = null;
    }

    if (routeCoordinates && routeCoordinates.length > 0) {
      try {
        const pathCoords = routeCoordinates.map(pt => ({ lat: pt[0], lng: pt[1] }));
        routePolylineRef.current = mapplsClassObject.Polyline({
          map: mapRef.current,
          path: pathCoords,
          strokeColor: '#2196F3',
          strokeOpacity: 0.9,
          strokeWeight: 5,
          fitbounds: true
        });
      } catch (err) {
        console.error('Failed to draw Mappls route polyline:', err);
      }
    }

    if (originMarkerRef.current) {
      try {
        if (originMarkerRef.current.remove) {
          originMarkerRef.current.remove();
        } else {
          mapplsClassObject.removeLayer({ map: mapRef.current, layer: originMarkerRef.current });
        }
      } catch (err) {}
      originMarkerRef.current = null;
    }

    if (originCoords) {
      try {
        originMarkerRef.current = mapplsClassObject.Marker({
          map: mapRef.current,
          position: { lat: originCoords.lat, lng: originCoords.lng },
          fitbounds: false,
          popupHtml: '<div style="color:#2e7d32;font-weight:bold;">Origin</div>',
        });
      } catch (err) {
        console.error('Failed to place Mappls origin marker:', err);
      }
    }

    if (destMarkerRef.current) {
      try {
        if (destMarkerRef.current.remove) {
          destMarkerRef.current.remove();
        } else {
          mapplsClassObject.removeLayer({ map: mapRef.current, layer: destMarkerRef.current });
        }
      } catch (err) {}
      destMarkerRef.current = null;
    }

    if (destCoords) {
      try {
        destMarkerRef.current = mapplsClassObject.Marker({
          map: mapRef.current,
          position: { lat: destCoords.lat, lng: destCoords.lng },
          fitbounds: false,
          popupHtml: '<div style="color:#d32f2f;font-weight:bold;">Destination</div>',
        });
      } catch (err) {
        console.error('Failed to place Mappls destination marker:', err);
      }
    }
  }, [routeCoordinates, originCoords, destCoords, isMapLoaded]);

  const flyTo = (lat, lng) => {
    const map = mapRef.current;
    if (!map) return;

    if (typeof map.flyTo === 'function') {
      map.flyTo({ lat, lng }, 14);
      return;
    }

    if (typeof map.setCenter === 'function') {
      map.setCenter({ lat, lng });
      if (typeof map.setZoom === 'function') {
        map.setZoom(14);
      }
    }
  };

  const placeIncidentMarker = (lat, lng) => {
    if (!mapRef.current) return;

    if (incidentMarkerRef.current) {
      try {
        if (incidentMarkerRef.current.remove) {
          incidentMarkerRef.current.remove();
        } else {
          mapplsClassObject.removeLayer({ map: mapRef.current, layer: incidentMarkerRef.current });
        }
      } catch (err) {
        console.warn('Failed to replace incident marker:', err);
      }
    }

    incidentMarkerRef.current = mapplsClassObject.Marker({
      map: mapRef.current,
      position: { lat, lng },
      fitbounds: false,
      popupHtml: '<div style="color:#000;font-weight:bold;">Incident Location Logged</div>',
      popupOptions: {
        openPopup: true,
        autoPan: false,
      },
    });
  };

  const renderHotspots = () => {
    if (!mapRef.current) return;
    clearOverlays();

    hotspots.forEach((hs) => {
      const circle = mapplsClassObject.Circle({
        map: mapRef.current,
        center: { lat: hs.latitude, lng: hs.longitude },
        radius: hotspotRadius(hs.incident_count),
        fillColor: '#eb9f46',
        fillOpacity: 0.6,
        strokeColor: '#eb9f46',
        strokeOpacity: 0.8,
        strokeWeight: 2,
      });

      if (circle && typeof circle.addListener === 'function') {
        let hoverInfoWindow = null;
        circle.addListener('mouseover', () => {
          try {
            hoverInfoWindow = mapplsClassObject.InfoWindow({
              map: mapRef.current,
              position: { lat: hs.latitude, lng: hs.longitude },
              content: hotspotPopupHtml(hs),
            });
          } catch (err) {
            console.error('Failed to open hover InfoWindow:', err);
          }
        });
        circle.addListener('mouseout', () => {
          if (hoverInfoWindow) {
            try {
              if (hoverInfoWindow.remove) {
                hoverInfoWindow.remove();
              } else {
                mapplsClassObject.removeLayer({ map: mapRef.current, layer: hoverInfoWindow });
              }
            } catch (err) {
              console.warn('Failed to remove hover InfoWindow:', err);
            }
            hoverInfoWindow = null;
          }
        });
      }

      overlaysRef.current.push(circle);
    });

    if (clickedPos) {
      placeIncidentMarker(clickedPos.lat, clickedPos.lng);
    }
  };

  useEffect(() => {
    let cancelled = false;

    const loadObject = {
      map: true,
      version: '3.5',
      style: 'dark-classic',
      plugins: ['search'],
    };

    if (mapConfig.auth_type === 'oauth') {
      loadObject.auth = 'legacy';
    }

    mapplsClassObject.initialize(mapConfig.token, loadObject, () => {
      if (cancelled) return;

      try {
        const map = mapplsClassObject.Map({
          id: MAPPLS_MAP_ID,
          properties: {
            center: [centerLat, centerLng],
            zoom: 12,
            clickTolerance: 5,
          },
        });

        mapRef.current = map;

        const handleReady = () => {
          if (cancelled) return;
          setIsMapLoaded(true);
          renderHotspots();

          const handleClick = (event) => {
            console.log('Mappls click event:', event);
            const lat = event?.lngLat?.lat ?? event?.latlng?.lat ?? event?.latLng?.lat ?? event?.lat;
            const lng = event?.lngLat?.lng ?? event?.latlng?.lng ?? event?.latLng?.lng ?? event?.lng;
            if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;

            setClickedPos({ lat, lng });
            if (onMapClickRef.current) {
              onMapClickRef.current(lat, lng);
            }
            placeIncidentMarker(lat, lng);
          };

          if (typeof map.on === 'function') {
            map.on('click', handleClick);
            map.on('load', () => {});
          } else if (typeof map.addListener === 'function') {
            map.addListener('click', handleClick);
          }
        };

        if (typeof map.on === 'function') {
          map.on('load', handleReady);
        } else if (typeof map.addListener === 'function') {
          map.addListener('load', handleReady);
        } else {
          handleReady();
        }
      } catch (err) {
        console.error('Mappls initialization failed:', err);
        onInitFail();
      }
    });

    return () => {
      cancelled = true;
      clearOverlays();
      if (mapRef.current?.remove) {
        mapRef.current.remove();
      }
      mapRef.current = null;
      setIsMapLoaded(false);
    };
  }, [mapConfig.token, mapConfig.auth_type]);

  useEffect(() => {
    if (!isMapLoaded) return;
    renderHotspots();
  }, [hotspots, isMapLoaded]);

  const handleSelectPlace = (lat, lng) => {
    flyTo(lat, lng);
  };

  return (
    <div className="map-container" style={{ width: '100%', height: '100%', position: 'relative', minHeight: '500px', backgroundColor: '#000000', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>

      {!isMapLoaded && (
        <div style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 2,
          color: 'var(--text-muted)',
          backgroundColor: 'rgba(0,0,0,0.35)',
        }}
        >
          Loading MapMyIndia map...
        </div>
      )}

      <div
        id={MAPPLS_MAP_ID}
        style={{ width: '100%', height: '100%', zIndex: 1 }}
      />
    </div>
  );
};

const IncidentMap = ({
  apiBaseUrl,
  foliumUrl = null,
  useIframe = false,
  defaultLat,
  defaultLng,
  hotspots = [],
  onMapClick = null,
  routeCoordinates = null,
  originCoords = null,
  destCoords = null,
}) => {
  const [mapProvider, setMapProvider] = useState(null);
  const [mapplsConfig, setMapplsConfig] = useState(null);
  const [mapplsFailed, setMapplsFailed] = useState(false);

  useEffect(() => {
    if (!apiBaseUrl) {
      setMapProvider('osm');
      return undefined;
    }

    let cancelled = false;

    const fetchMapConfig = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/api/map/config`);
        const data = await response.json();
        if (cancelled) return;

        if (data.provider === 'mappls' && data.token) {
          setMapplsConfig(data);
          setMapProvider('mappls');
        } else {
          setMapProvider('osm');
        }
      } catch (error) {
        console.error('Failed to load map config:', error);
        if (!cancelled) {
          setMapProvider('osm');
        }
      }
    };

    fetchMapConfig();

    return () => {
      cancelled = true;
    };
  }, [apiBaseUrl]);

  if (useIframe && foliumUrl) {
    return (
      <div className="map-container" style={{ width: '100%', height: '100%', position: 'relative', minHeight: '400px' }}>
        <iframe
          src={foliumUrl}
          className="map-iframe"
          style={{ width: '100%', height: '100%', border: 'none' }}
          title="Incident Diversion Map"
          sandbox="allow-scripts allow-same-origin"
        />
      </div>
    );
  }

  if (mapProvider === null) {
    return (
      <div className="map-container" style={{ width: '100%', height: '100%', position: 'relative', minHeight: '500px', backgroundColor: '#000000', borderRadius: 'var(--radius-lg)', overflow: 'hidden', display: 'flex', alignItems: 'center', justifyIntent: 'center', color: 'var(--text-muted)' }}>
        Loading map...
      </div>
    );
  }

  if (mapProvider === 'mappls' && mapplsConfig && !mapplsFailed) {
    return (
      <MapplsIncidentMap
        apiBaseUrl={apiBaseUrl}
        mapConfig={mapplsConfig}
        defaultLat={defaultLat}
        defaultLng={defaultLng}
        hotspots={hotspots}
        onMapClick={onMapClick}
        onInitFail={() => setMapplsFailed(true)}
        routeCoordinates={routeCoordinates}
        originCoords={originCoords}
        destCoords={destCoords}
      />
    );
  }

  return (
    <OsmIncidentMap
      apiBaseUrl={apiBaseUrl}
      defaultLat={defaultLat}
      defaultLng={defaultLng}
      hotspots={hotspots}
      onMapClick={onMapClick}
      routeCoordinates={routeCoordinates}
      originCoords={originCoords}
      destCoords={destCoords}
    />
  );
};

export default IncidentMap;

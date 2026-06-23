"""
Tests for the routing service — incident-aware route calculation.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.services.routing_service import (
    haversine,
    decode_polyline,
    score_route,
    select_best_route,
    min_distance_to_route_m,
)


# ─── Haversine Tests ─────────────────────────────────────────────

class TestHaversine:
    """Test the haversine distance function."""

    def test_same_point_zero_distance(self):
        """Same point should return 0 distance."""
        assert haversine(13.04, 77.518, 13.04, 77.518) == 0.0

    def test_known_distance(self):
        """Two known Bengaluru points ~2.5km apart."""
        # Peenya to Yeshwanthpura (approximately 2.5km)
        dist = haversine(13.04, 77.518, 13.02, 77.535)
        assert 2000 < dist < 3000  # Should be roughly 2.5km

    def test_short_distance(self):
        """Two very close points should return < 500m."""
        dist = haversine(13.04, 77.518, 13.041, 77.519)
        assert dist < 500

    def test_symmetric(self):
        """Distance A→B should equal B→A."""
        d1 = haversine(13.04, 77.518, 13.02, 77.535)
        d2 = haversine(13.02, 77.535, 13.04, 77.518)
        assert abs(d1 - d2) < 0.01


# ─── Polyline Decode Tests ───────────────────────────────────────

class TestDecodePolyline:
    """Test the Google polyline decoder."""

    def test_simple_decode(self):
        """A known encoded polyline should decode correctly."""
        # This is a simple 2-point encoded polyline
        encoded = "_p~iF~ps|U_ulLnnqC"
        coords = decode_polyline(encoded)
        assert len(coords) == 2
        # First point should be approximately (38.5, -120.2)
        assert abs(coords[0][0] - 38.5) < 0.1
        assert abs(coords[0][1] - (-120.2)) < 0.1

    def test_empty_string(self):
        """Empty string should return empty list."""
        assert decode_polyline("") == []


# ─── Route Scoring Tests ─────────────────────────────────────────

class TestScoreRoute:
    """Test scoring routes against active incidents."""

    def test_clean_route_no_incidents(self):
        """Route with no incidents should score 0."""
        route = [[13.04, 77.518], [13.05, 77.52], [13.06, 77.53]]
        score, crossed = score_route(route, [])
        assert score == 0.0
        assert crossed == []

    def test_clean_route_far_incident(self):
        """Incident far from route should not affect score."""
        route = [[13.04, 77.518], [13.05, 77.52]]
        incidents = [{
            "id": "INC-TEST-001",
            "latitude": 12.90,  # Far away
            "longitude": 77.60,
            "priority": 1,
            "road_closure": 0,
        }]
        score, crossed = score_route(route, incidents)
        assert score == 0.0
        assert crossed == []

    def test_route_near_low_priority_incident(self):
        """Route near a LOW priority incident should get penalty of 5."""
        route = [[13.04, 77.518], [13.041, 77.519]]
        incidents = [{
            "id": "INC-TEST-002",
            "latitude": 13.04,
            "longitude": 77.518,
            "priority": 0,  # LOW
            "road_closure": 0,
        }]
        score, crossed = score_route(route, incidents)
        assert score == 5.0
        assert len(crossed) == 1
        assert crossed[0]["priority"] == "LOW"

    def test_route_near_high_priority_incident(self):
        """Route near a HIGH priority incident should get penalty of 100."""
        route = [[13.04, 77.518], [13.041, 77.519]]
        incidents = [{
            "id": "INC-TEST-003",
            "latitude": 13.04,
            "longitude": 77.518,
            "priority": 1,  # HIGH
            "road_closure": 0,
        }]
        score, crossed = score_route(route, incidents)
        assert score == 100.0
        assert len(crossed) == 1
        assert crossed[0]["priority"] == "HIGH"

    def test_route_near_road_closure(self):
        """Route near a road closure should get penalty of 1000."""
        route = [[13.04, 77.518], [13.041, 77.519]]
        incidents = [{
            "id": "INC-TEST-004",
            "latitude": 13.04,
            "longitude": 77.518,
            "priority": 1,
            "road_closure": 1,
        }]
        score, crossed = score_route(route, incidents)
        assert score == 1000.0

    def test_route_prefers_low_over_high(self):
        """When comparing two routes, one near LOW and one near HIGH, LOW should score lower."""
        route_near_low = [[13.04, 77.518]]
        route_near_high = [[13.06, 77.53]]

        low_incident = [{
            "id": "INC-LOW", "latitude": 13.04, "longitude": 77.518,
            "priority": 0, "road_closure": 0,
        }]
        high_incident = [{
            "id": "INC-HIGH", "latitude": 13.06, "longitude": 77.53,
            "priority": 1, "road_closure": 0,
        }]

        score_low, _ = score_route(route_near_low, low_incident)
        score_high, _ = score_route(route_near_high, high_incident)

        assert score_low < score_high

    def test_route_segment_crossing_incident_is_detected(self):
        """Incident between sparse route points should still count as on-route."""
        route = [[13.04, 77.518], [13.04, 77.528]]
        incidents = [{
            "id": "INC-MIDPOINT",
            "latitude": 13.04,
            "longitude": 77.523,
            "priority": 1,
            "road_closure": 0,
        }]

        min_dist = min_distance_to_route_m(route, 13.04, 77.523)
        score, crossed = score_route(route, incidents)

        assert min_dist < 1
        assert score == 100.0
        assert len(crossed) == 1


# ─── Best Route Selection Tests ─────────────────────────────────

class TestSelectBestRoute:
    """Test route selection priority against incidents and detour size."""

    def test_prefers_clean_route_when_detour_is_reasonable(self):
        """A clean route within the detour threshold should beat a shorter route with incidents."""
        routes = [
            {
                "coordinates": [[13.04, 77.518]],
                "distance_m": 10000,
                "duration_s": 1200,
            },
            {
                "coordinates": [[13.20, 77.70]],
                "distance_m": 12000,
                "duration_s": 1500,
            },
        ]
        incidents = [{
            "id": "INC-LOW",
            "latitude": 13.04,
            "longitude": 77.518,
            "priority": 0,
            "road_closure": 0,
        }]

        route, crossed = select_best_route(routes, incidents)

        assert route["distance_m"] == 12000
        assert crossed == []

    def test_rejects_clean_route_when_detour_is_huge(self):
        """A huge clean detour should not beat a much shorter route with a low-priority incident."""
        routes = [
            {
                "coordinates": [[13.04, 77.518]],
                "distance_m": 10000,
                "duration_s": 1200,
            },
            {
                "coordinates": [[13.20, 77.70]],
                "distance_m": 20000,
                "duration_s": 2400,
            },
        ]
        incidents = [{
            "id": "INC-LOW",
            "latitude": 13.04,
            "longitude": 77.518,
            "priority": 0,
            "road_closure": 0,
        }]

        route, crossed = select_best_route(routes, incidents)

        assert route["distance_m"] == 10000
        assert len(crossed) == 1

    def test_fallback_minimizes_incident_count_before_severity(self):
        """When no acceptable clean route exists, fewer incidents beats lower total penalty."""
        routes = [
            {
                "coordinates": [[13.04, 77.518], [13.041, 77.519]],
                "distance_m": 10000,
                "duration_s": 1200,
            },
            {
                "coordinates": [[13.06, 77.53]],
                "distance_m": 10500,
                "duration_s": 1250,
            },
        ]
        incidents = [
            {
                "id": "INC-LOW-1",
                "latitude": 13.04,
                "longitude": 77.518,
                "priority": 0,
                "road_closure": 0,
            },
            {
                "id": "INC-LOW-2",
                "latitude": 13.041,
                "longitude": 77.519,
                "priority": 0,
                "road_closure": 0,
            },
            {
                "id": "INC-HIGH",
                "latitude": 13.06,
                "longitude": 77.53,
                "priority": 1,
                "road_closure": 0,
            },
        ]

        route, crossed = select_best_route(routes, incidents)

        assert route["distance_m"] == 10500
        assert len(crossed) == 1
        assert crossed[0]["priority"] == "HIGH"

    def test_fallback_prefers_low_priority_when_incident_count_matches(self):
        """For equal incident counts, low-priority incidents beat high-priority incidents."""
        routes = [
            {
                "coordinates": [[13.04, 77.518]],
                "distance_m": 10000,
                "duration_s": 1200,
            },
            {
                "coordinates": [[13.06, 77.53]],
                "distance_m": 10500,
                "duration_s": 1250,
            },
        ]
        incidents = [
            {
                "id": "INC-HIGH",
                "latitude": 13.04,
                "longitude": 77.518,
                "priority": 1,
                "road_closure": 0,
            },
            {
                "id": "INC-LOW",
                "latitude": 13.06,
                "longitude": 77.53,
                "priority": 0,
                "road_closure": 0,
            },
        ]

        route, crossed = select_best_route(routes, incidents)

        assert route["distance_m"] == 10500
        assert len(crossed) == 1
        assert crossed[0]["priority"] == "LOW"

    def test_proximity_penalty_scaling(self):
        """A route passing further from an incident receives a lower score/penalty than a closer route."""
        # Incident at YESHWANTHPURA (13.02, 77.535) - road closure (base penalty 1000)
        incidents = [{
            "id": "INC-CLOSED",
            "latitude": 13.02,
            "longitude": 77.535,
            "priority": 1,
            "road_closure": 1,
        }]
        
        # Route close: passes directly through incident (0m)
        route_close = [[13.02, 77.535]]
        # Route far: passes ~300m away (13.0227, 77.535 -> ~300m away)
        route_far = [[13.0227, 77.535]]
        
        score_close, _ = score_route(route_close, incidents)
        score_far, _ = score_route(route_far, incidents)
        
        assert score_far < score_close
        assert score_close == 1000.0
        assert 0.0 < score_far < 1000.0

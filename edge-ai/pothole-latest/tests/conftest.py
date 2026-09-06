"""Shared fixtures for pothole-detection test suite."""
import sys, os, json, pytest

# Ensure the production module directory is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Pothole_Road_Condition_Model'))

from pothole_pipeline import HealingManager, haversine, validate_gps
from pothole_config import DEDUPLICATION_RADIUS_METERS, HEALING_DISTANCE_RADIUS_METERS, HEALING_FRAME_CONFIDENCE


@pytest.fixture
def tmp_json(tmp_path):
    """Return a helper that writes a list to a temp JSON file and returns its path."""
    def _write(data, filename="known_potholes.json"):
        p = tmp_path / filename
        p.write_text(json.dumps(data, indent=2))
        return str(p)
    return _write


@pytest.fixture
def healing_manager_factory():
    """Factory to build a HealingManager with overridable parameters."""
    def _factory(potholes=None, radius=HEALING_DISTANCE_RADIUS_METERS,
                 frames=HEALING_FRAME_CONFIDENCE, dedup=DEDUPLICATION_RADIUS_METERS):
        return HealingManager(
            known_potholes_list=potholes or [],
            radius_meters=radius,
            frame_confidence=frames,
            deduplication_radius=dedup,
        )
    return _factory

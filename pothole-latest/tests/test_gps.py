"""Tests for GPS validation logic."""
import math
import pytest
from pothole_pipeline import validate_gps


class TestValidGPS:
    """Valid GPS coordinates must be accepted and normalised to floats."""

    def test_normal_coordinates(self):
        lat, lon = validate_gps(28.6139, 77.2090)
        assert lat == pytest.approx(28.6139)
        assert lon == pytest.approx(77.2090)

    def test_negative_coordinates(self):
        lat, lon = validate_gps(-33.8688, 151.2093)
        assert lat == pytest.approx(-33.8688)

    def test_boundary_north_pole(self):
        lat, lon = validate_gps(90, 0)
        assert lat == 90

    def test_boundary_south_pole(self):
        lat, lon = validate_gps(-90, 0)
        assert lat == -90

    def test_boundary_dateline_east(self):
        lat, lon = validate_gps(0, 180)
        assert lon == 180

    def test_boundary_dateline_west(self):
        lat, lon = validate_gps(0, -180)
        assert lon == -180

    def test_all_boundaries(self):
        lat, lon = validate_gps(90, 180)
        assert lat == 90 and lon == 180
        lat, lon = validate_gps(-90, -180)
        assert lat == -90 and lon == -180

    def test_numeric_string_conversion(self):
        lat, lon = validate_gps("28.6139", "77.2090")
        assert lat == pytest.approx(28.6139)
        assert lon == pytest.approx(77.2090)

    def test_zero_coordinates(self):
        lat, lon = validate_gps(0, 0)
        assert lat == 0 and lon == 0


class TestInvalidGPS:
    """Invalid GPS inputs must raise ValueError."""

    def test_latitude_too_high(self):
        with pytest.raises(ValueError):
            validate_gps(91, 0)

    def test_latitude_too_low(self):
        with pytest.raises(ValueError):
            validate_gps(-91, 0)

    def test_longitude_too_high(self):
        with pytest.raises(ValueError):
            validate_gps(0, 181)

    def test_longitude_too_low(self):
        with pytest.raises(ValueError):
            validate_gps(0, -181)

    def test_none_latitude(self):
        with pytest.raises(ValueError):
            validate_gps(None, 77.0)

    def test_none_longitude(self):
        with pytest.raises(ValueError):
            validate_gps(28.0, None)

    def test_both_none(self):
        with pytest.raises(ValueError):
            validate_gps(None, None)

    def test_nan_latitude(self):
        with pytest.raises(ValueError):
            validate_gps(float('nan'), 77.0)

    def test_nan_longitude(self):
        with pytest.raises(ValueError):
            validate_gps(28.0, float('nan'))

    def test_inf_latitude(self):
        with pytest.raises(ValueError):
            validate_gps(float('inf'), 77.0)

    def test_neg_inf_longitude(self):
        with pytest.raises(ValueError):
            validate_gps(28.0, float('-inf'))

    def test_non_numeric_string(self):
        with pytest.raises(ValueError):
            validate_gps("abc", 77.0)

    def test_empty_string(self):
        with pytest.raises(ValueError):
            validate_gps("", 77.0)

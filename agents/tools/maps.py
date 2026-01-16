import os
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from helpers.utils import get_logger

logger = get_logger(__name__)

load_dotenv()

# Common Agri Locations Mock Data (Fallback/Fast-Path)
MOCK_LOCATIONS = {
    # Tamil Nadu
    "chennai": (13.0827, 80.2707),
    "coimbatore": (11.0168, 76.9558),
    "madurai": (9.9252, 78.1198),
    "salem": (11.6643, 78.1460),
    "tiruchirappalli": (10.7905, 78.7047),
    "trichy": (10.7905, 78.7047),
    "thanjavur": (10.7870, 79.1378),
    "puducherry": (11.9139, 79.8145),
    "erode": (11.3410, 77.7172),
    "vellore": (12.9165, 79.1325),
    "tirunelveli": (8.7139, 77.7567),
    "thoothukudi": (8.7642, 78.1348),
    "dindigul": (10.3673, 77.9803),
    # Maharashtra
    "mumbai": (19.0760, 72.8777),
    "pune": (18.5204, 73.8567),
    "nagpur": (21.1458, 79.0882),
    "nashik": (19.9975, 73.7898),
    "aurangabad": (19.8762, 75.3433),
    "solapur": (17.6599, 75.9064),
    "kolhapur": (16.7050, 74.2433),
    "amravati": (20.9374, 77.7796),
    "jalgaon": (21.0077, 75.5626),
    "akola": (20.7002, 77.0082),
    "latur": (18.4088, 76.5604),
    "dhule": (20.9042, 74.7749),
    "ahmednagar": (19.0952, 74.7496),
    "chandrapur": (19.9615, 79.2961),
    "parbhani": (19.2644, 76.6413),
    "jalna": (19.8297, 75.8800),
    "bhusawal": (21.0455, 75.8011),
    "navi mumbai": (19.0330, 73.0297),
    "panvel": (18.9894, 73.1175)
}

# Initialize Nominatim geocoder
# Use public OSM server by default if local config is failing or strict
try:
    geocoder = Nominatim(
        user_agent="oan_agent_dev_testing_" + os.getenv("USER", "dev"), 
        timeout=10
    )
except Exception as e:
    logger.warning(f"Failed to initialize Nominatim: {e}")
    geocoder = None

class Location(BaseModel):
    """Location model for the maps tool."""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    place_name: Optional[str] = None

    @field_validator('latitude', 'longitude')
    @classmethod
    def round_coordinates(cls, v):
        if v is not None:
            return round(float(v), 3)
        return v
    
    def model_post_init(self, __context__) -> None:
        """Called after the model is initialized."""
        super().model_post_init(__context__)
        self.check_place_name()
    
    def check_place_name(self) -> None:
        """If coordinates are provided but not place name, do reverse geocoding."""
        if self.latitude is not None and self.longitude is not None and self.place_name is None:
            # Try mock reverse first (approximate)
            for name, coords in MOCK_LOCATIONS.items():
                if abs(coords[0] - self.latitude) < 0.1 and abs(coords[1] - self.longitude) < 0.1:
                    self.place_name = name.title()
                    return

            if geocoder:
                try:
                    location = geocoder.reverse((self.latitude, self.longitude), exactly_one=True)
                    if location:
                        self.place_name = location.raw['display_name']
                except (GeocoderTimedOut, GeocoderServiceError) as e:
                    logger.error(f"Reverse geocoding error: {e}")

    def _location_string(self):
        if self.latitude and self.longitude:
            return f"{self.place_name} (Latitude: {self.latitude}, Longitude: {self.longitude})"
        else:
            return "Location not available"

    def __str__(self):
        return f"{self.place_name} ({self.latitude}, {self.longitude})"


def forward_geocode(place_name: str) -> Optional[Location]:
    """Forward geocoding using Nominatim with local fallback."""
    # 1. Check Mock Data First
    clean_name = place_name.lower().strip()
    # Simple partial match for multi-word cities (e.g. "Solapur Market" -> "solapur")
    for mock_name, coords in MOCK_LOCATIONS.items():
        if mock_name in clean_name:
            logger.info(f"Using Mock Location for: {place_name} -> {mock_name}")
            return Location(
                place_name=place_name.title(), # Keep original casing if possible, or Title
                latitude=coords[0],
                longitude=coords[1]
            )

    # 2. Try Online Geocoding
    if geocoder:
        try:
            # Removing country_codes='in' restriction for broader testing if needed, 
            # but keeping it helps accuracy.
            response = geocoder.geocode(place_name, exactly_one=True, addressdetails=True, country_codes='in')

            if response:
                return Location(
                    place_name=response.raw['display_name'],
                    latitude=response.latitude,
                    longitude=response.longitude
                )
            else:
                logger.info(f"No results found for {place_name} via Nominatim.")
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Forward geocoding error: {e}")
    
    return None


def reverse_geocode(latitude: float, longitude: float) -> Optional[Location]:
    """Reverse geocoding using Nominatim with local fallback."""
    # 1. Check Mock Data (Approximate)
    for name, coords in MOCK_LOCATIONS.items():
         if abs(coords[0] - latitude) < 0.05 and abs(coords[1] - longitude) < 0.05:
            return Location(
                place_name=name.title(),
                latitude=latitude,
                longitude=longitude
            )

    # 2. Try Online
    if geocoder:
        try:
            location = geocoder.reverse((latitude, longitude), exactly_one=True)
            if location:
                return Location(
                    place_name=location.raw['display_name'],
                    latitude=latitude,
                    longitude=longitude
                )
            else:
                logger.info("No results found.")
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Reverse geocoding error: {e}")
    return None
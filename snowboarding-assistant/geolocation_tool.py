from langchain.tools import Tool
import streamlit as st
from geopy.distance import geodesic
from tool_config import get_tool_version, get_tool_description
import logging

# Configure the logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_user_to_resort_distance(query: str = "") -> str:
    """Get user's location and return relevant information for snowboarding recommendations."""
    print(f"🔧 Using tool: resort_distance_calculator")  # Log tool usage
    
    if 'user_location' not in st.session_state or not st.session_state.user_location:
        return "Location access not granted. Please enable location sharing for personalized resort recommendations."
    
    location_data = st.session_state.user_location
    try:
        lat, lon = location_data['coordinates']
        address = location_data['address']
        
        # Comprehensive database of ski resorts with coordinates
        # This expanded list includes many more resorts across North America
        ski_resorts = {
            # Western US - California, Nevada, Utah
            'Heavenly': (38.9353, -119.9400),
            'Northstar': (39.2746, -120.1211),
            'Palisades Tahoe': (39.1967, -120.2356),
            'Kirkwood': (38.6850, -120.0654),
            'Mammoth Mountain': (37.6308, -119.0326),
            'Sierra-at-Tahoe': (38.8048, -120.0804),
            'Sugar Bowl': (39.3043, -120.3336),
            'Donner Ski Ranch': (39.3172, -120.3306),
            'Boreal': (39.3365, -120.3490),
            'Mt. Rose': (39.3284, -119.8850),
            'Diamond Peak': (39.2546, -119.9310),
            'Homewood': (39.0860, -120.1604),
            'Soda Springs': (39.3211, -120.3802),
            'Dodge Ridge': (38.1888, -119.9558),
            'China Peak': (37.2366, -119.1574),
            'Mountain High': (34.3767, -117.6908),
            'Snow Valley': (34.2250, -117.0375),
            'Snow Summit': (34.2367, -116.8906),
            'Bear Mountain': (34.2286, -116.8600),
            'Mt. Baldy': (34.2700, -117.6588),
            'Brighton': (40.5977, -111.5836),
            'Solitude': (40.6199, -111.5919),
            'Snowbird': (40.5830, -111.6556),
            'Alta': (40.5884, -111.6386),
            'Park City': (40.6461, -111.4980),
            'Deer Valley': (40.6374, -111.4783),
            'Snowbasin': (41.2160, -111.8566),
            'Powder Mountain': (41.3800, -111.7800),
            'Sundance': (40.3924, -111.5788),
            'Brian Head': (37.7024, -112.8498),
            'Eagle Point': (38.3208, -112.3844),
            
            # Western US - Colorado
            'Vail': (39.6433, -106.3781),
            'Breckenridge': (39.4817, -106.0384),
            'Aspen Snowmass': (39.2084, -106.9490),
            'Keystone': (39.6084, -105.9437),
            'Beaver Creek': (39.6042, -106.5165),
            'Copper Mountain': (39.5022, -106.1497),
            'Winter Park': (39.8868, -105.7625),
            'Steamboat': (40.4572, -106.8045),
            'Telluride': (37.9375, -107.8123),
            'Crested Butte': (38.8697, -106.9878),
            'Arapahoe Basin': (39.6425, -105.8719),
            'Loveland': (39.6800, -105.8979),
            'Eldora': (39.9372, -105.5827),
            'Monarch': (38.5121, -106.3320),
            'Purgatory': (37.6303, -107.8140),
            'Wolf Creek': (37.4722, -106.7931),
            
            # Western US - Pacific Northwest
            'Mt. Bachelor': (43.9792, -121.6886),
            'Mt. Hood Meadows': (45.3318, -121.6652),
            'Timberline Lodge': (45.3311, -121.7110),
            'Mt. Baker': (48.7767, -121.8144),
            'Crystal Mountain': (46.9355, -121.4751),
            'Stevens Pass': (47.7448, -121.0890),
            'Snoqualmie Pass': (47.4242, -121.4133),
            'White Pass': (46.6360, -121.3911),
            'Schweitzer': (48.3677, -116.6226),
            'Sun Valley': (43.6962, -114.3525),
            'Grand Targhee': (43.7885, -110.9580),
            'Jackson Hole': (43.5875, -110.8276),
            
            # Eastern US
            'Killington': (43.6045, -72.8201),
            'Stowe': (44.5303, -72.7814),
            'Sugarloaf': (45.0312, -70.3131),
            'Sunday River': (44.4734, -70.8569),
            'Whiteface Mountain': (44.3658, -73.9026),
            'Gore Mountain': (43.6741, -74.0070),
            'Hunter Mountain': (42.2028, -74.2226),
            'Mount Snow': (42.9602, -72.9204),
            'Okemo': (43.4018, -72.7176),
            'Stratton': (43.1134, -72.9081),
            'Sugarbush': (44.1359, -72.8944),
            'Jay Peak': (44.9244, -72.5255),
            'Bretton Woods': (44.2542, -71.4406),
            'Loon Mountain': (44.0360, -71.6214),
            'Cannon Mountain': (44.1773, -71.7003),
            'Attitash': (44.0831, -71.2294),
            'Wildcat Mountain': (44.2590, -71.2401),
            'Waterville Valley': (43.9504, -71.5280),
            
            # Canada
            'Whistler Blackcomb': (50.1163, -122.9574),
            'Banff Sunshine': (51.1152, -115.7631),
            'Lake Louise': (51.4254, -116.1773),
            'Revelstoke': (51.0050, -118.1957),
            'Big White': (49.7352, -118.9433),
            'Sun Peaks': (50.8825, -119.8936),
            'Fernie': (49.4633, -115.0861),
            'Kicking Horse': (51.2979, -117.0419),
            'Mont Tremblant': (46.2095, -74.5855),
            'Blue Mountain': (44.5015, -80.3092),
            'Mont-Sainte-Anne': (47.0756, -70.9033),
            'Le Massif': (47.2792, -70.6314)
        }
        
        # Calculate distances to all resorts
        resort_distances = []
        for resort, coords in ski_resorts.items():
            distance = geodesic(location_data['coordinates'], coords).miles
            resort_distances.append((resort, distance))
        
        # Sort by distance and get the 5 closest
        resort_distances.sort(key=lambda x: x[1])
        closest_resorts = resort_distances[:5]
        
        # Format distances for the 5 closest resorts
        formatted_distances = "\n- ".join([f"{resort}: {int(distance)} miles" for resort, distance in closest_resorts])
        
        # Get the two closest for the summary line
        closest_two = closest_resorts[:2]
        
        return f"""Current location: {address}
        
The 5 closest ski resorts to your location:
- {formatted_distances}

The closest resorts to your location are {closest_two[0][0]} ({int(closest_two[0][1])} miles) and {closest_two[1][0]} ({int(closest_two[1][1])} miles).
"""

    except Exception as e:
        return f"Error processing location data: {str(e)}"

# Define the tool
resort_distance_calculator = Tool(
    name="resort_distance_calculator",
    description=get_tool_description("resort_distance_calculator", get_tool_version("resort_distance_calculator")),
    func=get_user_to_resort_distance
) 
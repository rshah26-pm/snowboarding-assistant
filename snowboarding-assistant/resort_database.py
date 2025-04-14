import sqlite3
import os
from typing import List, Tuple, Dict, Any, Optional
from geopy.distance import geodesic
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'resorts.db')

def init_database():
    """
    Initializes the SQLite database and creates the resorts table if it does not exist.
    
    Returns:
        True if the database and table are successfully initialized, False otherwise.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create the resorts table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS resorts (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            region TEXT,
            state TEXT,
            country TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {DB_PATH}")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False

def populate_resorts():
    """
    Populates the resorts database with a predefined list of ski resorts.
    
    If the database is empty, inserts resort records with geographic and regional data.
    Returns True if the operation succeeds, or False if an error occurs or data already exists.
    """
    # Dictionary of ski resorts with coordinates
    ski_resorts = {
        # Western US - California, Nevada, Utah
        'Heavenly': (38.9353, -119.9400, 'Tahoe', 'CA/NV', 'USA'),
        'Northstar': (39.2746, -120.1211, 'Tahoe', 'CA', 'USA'),
        'Palisades Tahoe': (39.1967, -120.2356, 'Tahoe', 'CA', 'USA'),
        'Kirkwood': (38.6850, -120.0654, 'Tahoe', 'CA', 'USA'),
        'Mammoth Mountain': (37.6308, -119.0326, 'Eastern Sierra', 'CA', 'USA'),
        'Sierra-at-Tahoe': (38.8048, -120.0804, 'Tahoe', 'CA', 'USA'),
        'Sugar Bowl': (39.3043, -120.3336, 'Tahoe', 'CA', 'USA'),
        'Donner Ski Ranch': (39.3172, -120.3306, 'Tahoe', 'CA', 'USA'),
        'Boreal': (39.3365, -120.3490, 'Tahoe', 'CA', 'USA'),
        'Mt. Rose': (39.3284, -119.8850, 'Tahoe', 'NV', 'USA'),
        'Diamond Peak': (39.2546, -119.9310, 'Tahoe', 'NV', 'USA'),
        'Homewood': (39.0860, -120.1604, 'Tahoe', 'CA', 'USA'),
        'Soda Springs': (39.3211, -120.3802, 'Tahoe', 'CA', 'USA'),
        'Dodge Ridge': (38.1888, -119.9558, 'Central Sierra', 'CA', 'USA'),
        'China Peak': (37.2366, -119.1574, 'Central Sierra', 'CA', 'USA'),
        'Mountain High': (34.3767, -117.6908, 'Southern California', 'CA', 'USA'),
        'Snow Valley': (34.2250, -117.0375, 'Southern California', 'CA', 'USA'),
        'Snow Summit': (34.2367, -116.8906, 'Southern California', 'CA', 'USA'),
        'Bear Mountain': (34.2286, -116.8600, 'Southern California', 'CA', 'USA'),
        'Mt. Baldy': (34.2700, -117.6588, 'Southern California', 'CA', 'USA'),
        'Brighton': (40.5977, -111.5836, 'Wasatch', 'UT', 'USA'),
        'Solitude': (40.6199, -111.5919, 'Wasatch', 'UT', 'USA'),
        'Snowbird': (40.5830, -111.6556, 'Wasatch', 'UT', 'USA'),
        'Alta': (40.5884, -111.6386, 'Wasatch', 'UT', 'USA'),
        'Park City': (40.6461, -111.4980, 'Wasatch', 'UT', 'USA'),
        'Deer Valley': (40.6374, -111.4783, 'Wasatch', 'UT', 'USA'),
        'Snowbasin': (41.2160, -111.8566, 'Wasatch', 'UT', 'USA'),
        'Powder Mountain': (41.3800, -111.7800, 'Wasatch', 'UT', 'USA'),
        'Sundance': (40.3924, -111.5788, 'Wasatch', 'UT', 'USA'),
        'Brian Head': (37.7024, -112.8498, 'Southern Utah', 'UT', 'USA'),
        'Eagle Point': (38.3208, -112.3844, 'Southern Utah', 'UT', 'USA'),
        
        # Western US - Colorado
        'Vail': (39.6433, -106.3781, 'Central Rockies', 'CO', 'USA'),
        'Breckenridge': (39.4817, -106.0384, 'Central Rockies', 'CO', 'USA'),
        'Aspen Snowmass': (39.2084, -106.9490, 'Central Rockies', 'CO', 'USA'),
        'Keystone': (39.6084, -105.9437, 'Central Rockies', 'CO', 'USA'),
        'Beaver Creek': (39.6042, -106.5165, 'Central Rockies', 'CO', 'USA'),
        'Copper Mountain': (39.5022, -106.1497, 'Central Rockies', 'CO', 'USA'),
        'Winter Park': (39.8868, -105.7625, 'Central Rockies', 'CO', 'USA'),
        'Steamboat': (40.4572, -106.8045, 'Northern Rockies', 'CO', 'USA'),
        'Telluride': (37.9375, -107.8123, 'San Juan Mountains', 'CO', 'USA'),
        'Crested Butte': (38.8697, -106.9878, 'Central Rockies', 'CO', 'USA'),
        'Arapahoe Basin': (39.6425, -105.8719, 'Central Rockies', 'CO', 'USA'),
        'Loveland': (39.6800, -105.8979, 'Central Rockies', 'CO', 'USA'),
        'Eldora': (39.9372, -105.5827, 'Front Range', 'CO', 'USA'),
        'Monarch': (38.5121, -106.3320, 'Central Rockies', 'CO', 'USA'),
        'Purgatory': (37.6303, -107.8140, 'San Juan Mountains', 'CO', 'USA'),
        'Wolf Creek': (37.4722, -106.7931, 'San Juan Mountains', 'CO', 'USA'),
        
        # Western US - Pacific Northwest
        'Mt. Bachelor': (43.9792, -121.6886, 'Cascade Range', 'OR', 'USA'),
        'Mt. Hood Meadows': (45.3318, -121.6652, 'Cascade Range', 'OR', 'USA'),
        'Timberline Lodge': (45.3311, -121.7110, 'Cascade Range', 'OR', 'USA'),
        'Mt. Baker': (48.7767, -121.8144, 'Cascade Range', 'WA', 'USA'),
        'Crystal Mountain': (46.9355, -121.4751, 'Cascade Range', 'WA', 'USA'),
        'Stevens Pass': (47.7448, -121.0890, 'Cascade Range', 'WA', 'USA'),
        'Snoqualmie Pass': (47.4242, -121.4133, 'Cascade Range', 'WA', 'USA'),
        'White Pass': (46.6360, -121.3911, 'Cascade Range', 'WA', 'USA'),
        'Schweitzer': (48.3677, -116.6226, 'Selkirk Mountains', 'ID', 'USA'),
        'Sun Valley': (43.6962, -114.3525, 'Sawtooth Range', 'ID', 'USA'),
        'Grand Targhee': (43.7885, -110.9580, 'Teton Range', 'WY', 'USA'),
        'Jackson Hole': (43.5875, -110.8276, 'Teton Range', 'WY', 'USA'),
        
        # Eastern US
        'Killington': (43.6045, -72.8201, 'Green Mountains', 'VT', 'USA'),
        'Stowe': (44.5303, -72.7814, 'Green Mountains', 'VT', 'USA'),
        'Sugarloaf': (45.0312, -70.3131, 'Longfellow Mountains', 'ME', 'USA'),
        'Sunday River': (44.4734, -70.8569, 'Mahoosuc Range', 'ME', 'USA'),
        'Whiteface Mountain': (44.3658, -73.9026, 'Adirondack Mountains', 'NY', 'USA'),
        'Gore Mountain': (43.6741, -74.0070, 'Adirondack Mountains', 'NY', 'USA'),
        'Hunter Mountain': (42.2028, -74.2226, 'Catskill Mountains', 'NY', 'USA'),
        'Mount Snow': (42.9602, -72.9204, 'Green Mountains', 'VT', 'USA'),
        'Okemo': (43.4018, -72.7176, 'Green Mountains', 'VT', 'USA'),
        'Stratton': (43.1134, -72.9081, 'Green Mountains', 'VT', 'USA'),
        'Sugarbush': (44.1359, -72.8944, 'Green Mountains', 'VT', 'USA'),
        'Jay Peak': (44.9244, -72.5255, 'Green Mountains', 'VT', 'USA'),
        'Bretton Woods': (44.2542, -71.4406, 'White Mountains', 'NH', 'USA'),
        'Loon Mountain': (44.0360, -71.6214, 'White Mountains', 'NH', 'USA'),
        'Cannon Mountain': (44.1773, -71.7003, 'White Mountains', 'NH', 'USA'),
        'Attitash': (44.0831, -71.2294, 'White Mountains', 'NH', 'USA'),
        'Wildcat Mountain': (44.2590, -71.2401, 'White Mountains', 'NH', 'USA'),
        'Waterville Valley': (43.9504, -71.5280, 'White Mountains', 'NH', 'USA'),
        
        # Canada
        'Whistler Blackcomb': (50.1163, -122.9574, 'Coast Mountains', 'BC', 'Canada'),
        'Banff Sunshine': (51.1152, -115.7631, 'Canadian Rockies', 'AB', 'Canada'),
        'Lake Louise': (51.4254, -116.1773, 'Canadian Rockies', 'AB', 'Canada'),
        'Revelstoke': (51.0050, -118.1957, 'Selkirk Mountains', 'BC', 'Canada'),
        'Big White': (49.7352, -118.9433, 'Monashee Mountains', 'BC', 'Canada'),
        'Sun Peaks': (50.8825, -119.8936, 'Thompson Plateau', 'BC', 'Canada'),
        'Fernie': (49.4633, -115.0861, 'Canadian Rockies', 'BC', 'Canada'),
        'Kicking Horse': (51.2979, -117.0419, 'Purcell Mountains', 'BC', 'Canada'),
        'Mont Tremblant': (46.2095, -74.5855, 'Laurentian Mountains', 'QC', 'Canada'),
        'Blue Mountain': (44.5015, -80.3092, 'Niagara Escarpment', 'ON', 'Canada'),
        'Mont-Sainte-Anne': (47.0756, -70.9033, 'Laurentian Mountains', 'QC', 'Canada'),
        'Le Massif': (47.2792, -70.6314, 'Charlevoix', 'QC', 'Canada')
    }
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if we already have data
        cursor.execute("SELECT COUNT(*) FROM resorts")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Insert resort data
            for name, data in ski_resorts.items():
                if len(data) >= 5:  # Make sure we have all the data
                    lat, lon, region, state, country = data
                    resort_id = name.lower().replace(' ', '_').replace('-', '_').replace('.', '')
                    
                    cursor.execute(
                        "INSERT INTO resorts (id, name, latitude, longitude, region, state, country) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (resort_id, name, lat, lon, region, state, country)
                    )
            
            conn.commit()
            logger.info(f"Populated database with {len(ski_resorts)} resorts")
        else:
            logger.info(f"Database already contains {count} resorts, skipping population")
        
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error populating database: {str(e)}")
        return False

def get_closest_resorts(lat: float, lon: float, query: str = "", limit: int = 5) -> List[Dict[str, Any]]:
    """
    Finds the closest ski resorts to the specified coordinates, optionally filtered by a search query.
    
    Args:
        lat: Latitude of the reference location.
        lon: Longitude of the reference location.
        query: Optional text to filter resorts by name, region, state, or country.
        limit: Maximum number of resorts to return.
    
    Returns:
        A list of dictionaries representing the closest resorts, each including a 'distance' key with the distance in miles.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        cursor = conn.cursor()
        
        # Build the query based on whether we have a search term
        sql_query = "SELECT * FROM resorts"
        params = []
        
        if query:
            # Simple text search - in a real app, you might want to use FTS or a more sophisticated search
            sql_query += " WHERE name LIKE ? OR region LIKE ? OR state LIKE ? OR country LIKE ?"
            search_term = f"%{query}%"
            params = [search_term, search_term, search_term, search_term]
        
        cursor.execute(sql_query, params)
        resorts = cursor.fetchall()
        conn.close()
        
        # Calculate distances
        resort_distances = []
        user_coords = (lat, lon)
        
        for resort in resorts:
            resort_dict = dict(resort)  # Convert Row to dict
            resort_coords = (resort_dict['latitude'], resort_dict['longitude'])
            distance = geodesic(user_coords, resort_coords).miles
            resort_dict['distance'] = round(distance, 1)
            resort_distances.append(resort_dict)
        
        # Sort by distance and limit results
        resort_distances.sort(key=lambda x: x['distance'])
        return resort_distances[:limit]
    
    except Exception as e:
        logger.error(f"Error getting closest resorts: {str(e)}")
        return []

# Initialize the database when the module is imported
init_database()
populate_resorts() 
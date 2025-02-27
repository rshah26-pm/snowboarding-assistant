function getLocation() {
    console.log("getLocation function called");
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                console.log("Got position:", position.coords.latitude, position.coords.longitude);
                const coords = {
                    lat: position.coords.latitude,
                    lon: position.coords.longitude
                };
                // Send coordinates to Streamlit
                window.parent.postMessage({
                    type: "streamlit:setQueryParam",
                    queryParams: { location_data: `${coords.lat},${coords.lon}` }
                }, "*");
                
                console.log("Location data sent to Streamlit");
                
                // Force page reload to apply the query parameter
                setTimeout(function() {
                    console.log("Reloading page to apply query parameter");
                    window.parent.location.reload();
                }, 500);
            },
            function(error) {
                console.error("Error getting location:", error);
                alert("Error getting location: " + error.message);
            },
            { 
                enableHighAccuracy: true,
                timeout: 5000,
                maximumAge: 0
            }
        );
    } else {
        alert("Geolocation is not supported by this browser.");
    }
}
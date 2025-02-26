function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                // Send coordinates directly to Streamlit
                const locationParam = `${position.coords.latitude},${position.coords.longitude}`;
                window.location.search = `?location=${locationParam}`;
            },
            function(error) {
                console.error("Error getting location:", error);
                alert("Error getting location: " + error.message);
            }
        );
    } else {
        alert("Geolocation is not supported by this browser.");
    }
}
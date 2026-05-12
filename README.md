# Querying Google Maps API to find all businesses within a set radius of a company location

_Last updated: August 2024_

For more information, read the [project page](https://www.datascienceportfol.io/christinegarcia/projects/4).

### Requirements

Commands are for Mac 13.5+ with [homebrew](https://brew.sh/).

- Python 3.5+ (I used 3.11 - `brew install python@3.11`)
- Account on [Google Maps Platform](https://mapsplatform.google.com/) with Places API enabled
- [Python client for Google Maps](https://github.com/googlemaps/google-maps-services-python) (`pip3 install googlemaps`) 
- [GeoPy](https://geopy.readthedocs.io/en/stable/#module-geopy.distance) for distance calculation (`pip3 install geopy`)

### Reference links

- [Google Places API documentation](https://developers.google.com/maps/documentation/javascript/places)
- [Python client documentation - see places()](https://googlemaps.github.io/google-maps-services-python/docs/index.html)
- [Python client code for places()](https://github.com/googlemaps/google-maps-services-python/blob/645e07de5a27c4c858b2c0673f0dd6f23ca62d28/googlemaps/places.py#L198)
- [Python client sample test for places()](https://github.com/googlemaps/google-maps-services-python/blob/645e07de5a27c4c858b2c0673f0dd6f23ca62d28/tests/test_places.py#L89)
- [Google Place types](https://developers.google.com/maps/documentation/places/web-service/supported_types)

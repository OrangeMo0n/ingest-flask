import math

class MercatorTools(object):
    def __init__(self, tileSize=256):
        """
        Initialize the TMS Global Mercator pyramid
        :param tileSize:
        """
        self.tileSize = tileSize
        self.initialResolution = 2 * math.pi * 6378137 / self.tileSize
        # 156543.03392804062 for tileSize 256 pixels
        self.originShift = 2 * math.pi * 6378137 / 2.0
        self.MAXZOOMLEVEL = 32

    def LatLonToMeters(self, lat, lon):
        """
        Converts given lat/lon in WGS84 Datum to XY in Spherical Mercator EPSG:3857
        :param lat:
        :param lon:
        :return:
        """
        mx = lon * self.originShift / 180.0
        my = math.log(math.tan((90 + lat) * math.pi / 360.0)) / (math.pi / 180.0)
        my = my * self.originShift / 180.0
        return mx, my

    def MetersToLatLon(self, mx, my):
        """
        Converts XY point from Spherical Mercator EPSG:3857 to lat/lon in WGS84 Datum
        :param mx:
        :param my:
        :return:
        """
        lon = (mx / self.originShift) * 180.0
        lat = (my / self.originShift) * 180.0

        lat = 180 / math.pi * \
              (2 * math.atan(math.exp(lat * math.pi / 180.0)) - math.pi / 2.0)
        return lat, lon

    def PixelsToMeters(self, px, py, zoom):
        """
        Converts pixel coordinates in given zoom level of pyramid to EPSG:3857
        :param px:
        :param py:
        :param zoom:
        :return:
        """
        res = self.Resolution(zoom)
        mx = px * res - self.originShift
        my = py * res - self.originShift
        return mx, my

    def MetersToPixels(self, mx, my, zoom):
        """
        Converts EPSG:3857 to pyramid pixel coordinates in given zoom level
        :param mx:
        :param my:
        :param zoom:
        :return:
        """
        res = self.Resolution(zoom)
        px = (mx + self.originShift) / res
        py = (my + self.originShift) / res
        return px, py

    def PixelsToTile(self, px, py):
        """
        Returns a tile covering region in given pixel coordinates
        :param px:
        :param py:
        :return:
        """
        tx = int(math.ceil(px / float(self.tileSize)) - 1)
        ty = int(math.ceil(py / float(self.tileSize)) - 1)
        return tx, ty

    def PixelsToRaster(self, px, py, zoom):
        """
        Move the origin of pixel coordinates to top-left corner
        :param px:
        :param py:
        :param zoom:
        :return:
        """
        mapSize = self.tileSize << zoom
        return px, mapSize - py

    def MetersToTile(self, mx, my, zoom):
        """
        Returns tile for given mercator coordinates
        :param mx:
        :param my:
        :param zoom:
        :return:
        """
        px, py = self.MetersToPixels(mx, my, zoom)
        return self.PixelsToTile(px, py)
    
    def LatLonToTile(self, lx, ly, zoom):
        mx, my = self.LatLonToMeters(ly, lx)
        return self.MetersToTile(mx, my, zoom)

    def TileBounds(self, tx, ty, zoom):
        """
        Returns bounds of the given tile in EPSG:3857 coordinates
        :param tx:
        :param ty:
        :param zoom:
        :return:
        """
        minx, miny = self.PixelsToMeters(
            tx * self.tileSize, ty * self.tileSize, zoom)
        maxx, maxy = self.PixelsToMeters(
            (tx + 1) * self.tileSize, (ty + 1) * self.tileSize, zoom)
        return minx, miny, maxx, maxy

    def TileLatLonBounds(self, tx, ty, zoom):
        """
        Returns bounds of the given tile in latitude/longitude using WGS84 datum
        :param tx:
        :param ty:
        :param zoom:
        :return:
        """
        bounds = self.TileBounds(tx, ty, zoom)
        minLat, minLon = self.MetersToLatLon(bounds[0], bounds[1])
        maxLat, maxLon = self.MetersToLatLon(bounds[2], bounds[3])
        return minLat, minLon, maxLat, maxLon

    def Resolution(self, zoom):
        """
        Resolution (meters/pixel) for given zoom level (measured at Equator)
        :param zoom:
        :return:
        """
        return self.initialResolution / (2 ** zoom)

    def ZoomForPixelSize(self, pixelSize):
        """
        通过原始像素的分辨率获取最大缩放级别
        :param pixelSize:
        :return:
        """
        _value = 0
        _zoom = 0
        _resolutions = []
        for i in range(self.MAXZOOMLEVEL):
            _resolutions.append(self.Resolution(i))
        _differ = list(map(lambda x: math.fabs(x - pixelSize), _resolutions))
        for i in range(len(_differ)):
            if i == 0:
                _value = _differ[i]
                _zoom = i
            else:
                if _value >= _differ[i]:
                    _value = _differ[i]
                    _zoom = i
        return _zoom
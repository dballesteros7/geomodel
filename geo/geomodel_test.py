"""
The MIT License (MIT)

Copyright (c) 2014 Diego Ballesteros

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
"""Unit tests for geomodel.py."""

from google.appengine.ext import testbed, ndb
import random
import unittest

import geomodel
import geocell
import geotypes


__author__ = 'dballesteros7@gmail.com (Diego Ballesteros)'


class GeoModelTests(unittest.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        #geomodel._DEBUG = True

    def tearDown(self):
        self.testbed.deactivate()

    def test_update_location(self):
        # Geomodel located in zurich
        point = geomodel.GeoModel(location=ndb.GeoPt(47.378194, 8.539236))
        point.put()
        try:
            queried_point = point.query().fetch(1)[0]
        except:
            self.fail()
        self.assertEqual(len(queried_point.location_geocells), 0)
        point.update_location()
        point.put()
        try:
            queried_point = point.query().fetch(1)[0]
        except:
            self.fail()
        self.assertEqual(len(queried_point.location_geocells),
                         geocell.MAX_GEOCELL_RESOLUTION)

    def test_bounding_box_fetch(self):
        # Define a bounding box in lat,long
        south = -20
        east = 20
        west = -20
        north = 20
        # Now partition the world in 9 boxes
        bbox_inside = geotypes.Box(north, east, south, west)
        bbox_more_north = geotypes.Box(90, 180, north + 1, -180)
        bbox_more_east = geotypes.Box(90, 180, -90, east + 1)
        bbox_more_south = geotypes.Box(south - 1, 180, -90, -180)
        bbox_more_west = geotypes.Box(90, west - 1, -90, -180)
        bbox_northeast = geotypes.Box(90, 180, north + 1, east + 1)
        bbox_northwest = geotypes.Box(90, west - 1, north + 1, -180)
        bbox_southeast = geotypes.Box(south - 1, 180, -90, east + 1)
        bbox_southwest = geotypes.Box(south - 1, west - 1, -90, -180)
        # Generate some random points inside and outside the central box
        # Increase these numbers for timing tests
        inside = 6
        more_north = 1
        more_west = 2
        more_east = 4
        more_south = 20
        futures = []
        for _ in xrange(inside):
            point = geomodel.GeoModel(location=ndb.GeoPt(
                                                random.uniform(south, north),
                                                random.uniform(west, east)))
            point.update_location()
            futures.append(point.put_async())
        for _ in xrange(more_north):
            point = geomodel.GeoModel(location=ndb.GeoPt(
                                                random.uniform(north + 1, 90),
                                                random.uniform(-180, 180)))
            point.update_location()
            futures.append(point.put_async())
        for _ in xrange(more_east):
            point = geomodel.GeoModel(location=ndb.GeoPt(
                                                random.uniform(-90, 90),
                                                random.uniform(east + 1, 180)))
            point.update_location()
            futures.append(point.put_async())
        for _ in xrange(more_south):
            point = geomodel.GeoModel(location=ndb.GeoPt(
                                                random.uniform(-90, south - 1),
                                                random.uniform(-180, 180)))
            point.update_location()
            futures.append(point.put_async())
        for _ in xrange(more_west):
            point = geomodel.GeoModel(location=ndb.GeoPt(
                                                random.uniform(-90, 90),
                                                random.uniform(-180, west - 1)))
            point.update_location()
            futures.append(point.put_async())
        ndb.Future.wait_all(futures)
        base_query = geomodel.GeoModel.query()
        results_inside = geomodel.GeoModel.bounding_box_fetch(base_query,
                                                              bbox_inside)
        self.assertEqual(len(results_inside), inside)
        results_north = geomodel.GeoModel.bounding_box_fetch(base_query,
                                                             bbox_more_north)
        results_east = geomodel.GeoModel.bounding_box_fetch(base_query,
                                                            bbox_more_east)
        results_west = geomodel.GeoModel.bounding_box_fetch(base_query,
                                                            bbox_more_west)
        results_south = geomodel.GeoModel.bounding_box_fetch(base_query,
                                                            bbox_more_south)
        results_northeast = geomodel.GeoModel.bounding_box_fetch(base_query,
                                                            bbox_northeast)
        results_northwest = geomodel.GeoModel.bounding_box_fetch(base_query,
                                                            bbox_northwest)
        results_southeast = geomodel.GeoModel.bounding_box_fetch(base_query,
                                                            bbox_southeast)
        results_southwest = geomodel.GeoModel.bounding_box_fetch(base_query,
                                                            bbox_southwest)
        self.assertEqual(len(results_north) + len(results_east) +
                         len(results_west) + len(results_south)
                         - len(results_northeast) - len(results_northwest)
                         - len(results_southeast) - len(results_southwest),
                         more_east + more_north + more_west + more_south)
        results_constrained = geomodel.GeoModel.bounding_box_fetch(base_query,
                                                                   bbox_inside,
                                                                   inside / 2)
        self.assertEqual(len(results_constrained), inside / 2)

if __name__ == '__main__':
    unittest.main()

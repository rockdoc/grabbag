"""
Unit tests for WKT geographic coordinate system definitions.
"""
import unittest
import crswktparser

#---------------------------------------------------------------------------------------------------
class TestGeogCS(unittest.TestCase) :
#---------------------------------------------------------------------------------------------------
   def setUp(self) :
      self.wkt = """GEOGCS [
         "OSGB 1936",
         DATUM [
            "OSGB 1936",
            SPHEROID [
               "Airy 1830",
               6377563.396,
               299.3249646,
               AUTHORITY ["EPSG", "7001"]
            ],
            TOWGS84 [375, -111, 431, 0, 0, 0, 0],
            AUTHORITY ["EPSG", "6277"]
         ],
         PRIMEM [
            "Greenwich",
            0,
            AUTHORITY ["EPSG", "8901"]
         ],
         UNIT [
            "degree",
            0.0174532925199433,
            AUTHORITY ["EPSG", "9108"]
         ],
         AXIS ["latitude", NORTH],
         AXIS ["longitude", EAST],
         AUTHORITY ["EPSG", "4277"]
      ]"""
      parser = crswktparser.CrsWkt1Parser()
      self.geogcs = parser.parse_text(self.wkt)

   def test_geogcs_node(self) :
      self.assertTrue(self.geogcs.node_type == "GEOGCS")
      self.assertTrue(self.geogcs.name == "OSGB 1936")
      self.assertTrue(self.geogcs.authority.name == "EPSG")
      self.assertTrue(self.geogcs.authority.code == "4277")

   def test_datum_node(self) :
      self.assertTrue(self.geogcs.datum.node_type == "DATUM")
      self.assertTrue(self.geogcs.datum.name == "OSGB 1936")
      self.assertTrue(self.geogcs.datum.towgs84.dx == 375.)
      self.assertTrue(self.geogcs.datum.towgs84.dy == -111.)
      self.assertTrue(self.geogcs.datum.towgs84.dz == 431.)

   def test_spheroid_node(self) :
      self.assertTrue(self.geogcs.datum.spheroid.node_type == "SPHEROID")
      self.assertTrue(self.geogcs.datum.spheroid.name == "Airy 1830")
      self.assertTrue(self.geogcs.datum.spheroid.semi_major_axis == 6377563.396)
      self.assertTrue(self.geogcs.datum.spheroid.inverse_flattening == 299.3249646)

   def test_primem_node(self) :
      self.assertTrue(self.geogcs.prime_meridian.node_type == "PRIMEM")
      self.assertTrue(self.geogcs.prime_meridian.name == "Greenwich")
      self.assertTrue(self.geogcs.prime_meridian.longitude == 0)
      self.assertTrue(self.geogcs.prime_meridian.authority.name == "EPSG")
      self.assertTrue(self.geogcs.prime_meridian.authority.code == "8901")

   def test_unit_node(self) :
      self.assertTrue(self.geogcs.angular_unit.node_type == "UNIT")
      self.assertTrue(self.geogcs.angular_unit.name == "degree")
      self.assertTrue(self.geogcs.angular_unit.conversion_factor == 0.0174532925199433)

   def test_axis_nodes(self) :
      self.assertTrue(len(self.geogcs.axis_list) == 2)
      self.assertTrue(self.geogcs.axis_list[0].node_type == "AXIS")
      self.assertTrue(self.geogcs.axis_list[0].name == "latitude")
      self.assertTrue(self.geogcs.axis_list[0].direction == "NORTH")
      self.assertTrue(self.geogcs.axis_list[1].node_type == "AXIS")
      self.assertTrue(self.geogcs.axis_list[1].name == "longitude")
      self.assertTrue(self.geogcs.axis_list[1].direction == "EAST")

#---------------------------------------------------------------------------------------------------
if __name__ == '__main__':
#---------------------------------------------------------------------------------------------------
   unittest.main()

"""
Unit tests for WKT projected coordinate system definitions.
"""
import unittest
import crswktparser

#---------------------------------------------------------------------------------------------------
class TestProjCS(unittest.TestCase) :
#---------------------------------------------------------------------------------------------------
   def setUp(self) :
      self.wkt = """PROJCS [
         "OSGB 1936 / British National Grid",
         GEOGCS ["OSGB 1936",
            DATUM ["OSGB 1936",
               SPHEROID ["Airy 1830", 6377563.396, 299.3249646]
            ],
            PRIMEM ["Greenwich", 0],
            UNIT ["degree", 0.0174532925199433]
         ],
         PROJECTION ["Transverse Mercator"],
         PARAMETER ["False easting", 400000],
         PARAMETER ["False northing", -100000],
         PARAMETER ["Latitude", 49.0],
         PARAMETER ["Longitude", -2.0],
         UNIT ["metre", 1.0, AUTHORITY ["EPSG", "9001"]],
         AXIS ["N", NORTH],
         AXIS ["E", EAST],
         AUTHORITY ["EPSG", "27700"]
      ]"""
      parser = crswktparser.CrsWkt1Parser()
      self.projcs = parser.parse_text(self.wkt)

   def test_projcs_node(self) :
      self.assertTrue(self.projcs.node_type == "PROJCS")
      self.assertTrue(self.projcs.name == "OSGB 1936 / British National Grid")
      self.assertTrue(self.projcs.geographic_cs.node_type == "GEOGCS")
      self.assertTrue(self.projcs.authority.name == "EPSG")
      self.assertTrue(self.projcs.authority.code == "27700")

   def test_parameter_nodes(self) :
      self.assertTrue(len(self.projcs.param_list) == 4)
      self.assertTrue(self.projcs.param_list[0].node_type == "PARAMETER")
      self.assertTrue(self.projcs.param_list[0].name == "False easting")
      self.assertTrue(self.projcs.param_list[0].value == 400000)
      self.assertTrue(self.projcs.param_list[1].name == "False northing")
      self.assertTrue(self.projcs.param_list[1].value == -100000)
      self.assertTrue(self.projcs.param_list[2].name == "Latitude")
      self.assertTrue(self.projcs.param_list[2].value == 49.0)
      self.assertTrue(self.projcs.param_list[3].name == "Longitude")
      self.assertTrue(self.projcs.param_list[3].value == -2.0)

   def test_unit_node(self) :
      self.assertTrue(self.projcs.linear_unit.node_type == "UNIT")
      self.assertTrue(self.projcs.linear_unit.name == "metre")
      self.assertTrue(self.projcs.linear_unit.conversion_factor == 1.0)
      self.assertTrue(self.projcs.linear_unit.authority.name == "EPSG")
      self.assertTrue(self.projcs.linear_unit.authority.code == "9001")

   def test_axis_nodes(self) :
      self.assertTrue(len(self.projcs.axis_list) == 2)
      self.assertTrue(self.projcs.axis_list[0].node_type == "AXIS")
      self.assertTrue(self.projcs.axis_list[0].name == "N")
      self.assertTrue(self.projcs.axis_list[0].direction == "NORTH")
      self.assertTrue(self.projcs.axis_list[1].node_type == "AXIS")
      self.assertTrue(self.projcs.axis_list[1].name == "E")
      self.assertTrue(self.projcs.axis_list[1].direction == "EAST")

#---------------------------------------------------------------------------------------------------
if __name__ == '__main__':
#---------------------------------------------------------------------------------------------------
   unittest.main()

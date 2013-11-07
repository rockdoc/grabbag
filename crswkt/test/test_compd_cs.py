"""
Unit tests for WKT compound coordinate system definitions.
"""
import unittest
import crswktparser

#---------------------------------------------------------------------------------------------------
class TestCompdCS(unittest.TestCase) :
#---------------------------------------------------------------------------------------------------
   def setUp(self) :
      self.wkt = """COMPD_CS [
         "OSGB 1936 / British National Grid + ODN",
         PROJCS [
            "OSGB 1936 / British National Grid",
            GEOGCS ["OSGB 1936",
               DATUM ["OSGB 1936",
                  SPHEROID ["Airy 1830", 6377563.396, 299.3249646]
               ],
               PRIMEM ["Greenwich", 0],
               UNIT ["degree", 0.0174532925199433]
            ],
            PROJECTION ["Transverse Mercator"],
            UNIT ["metre", 1.0],
            AXIS ["N", NORTH],
            AXIS ["E", EAST]
         ],
         VERT_CS ["Newlyn",
            AUTHORITY ["EPSG", "5701"],
            VERT_DATUM ["Ordnance Datum Newlyn",
               2005,
               AUTHORITY ["EPSG", "5101"]
            ],
            UNIT ["metre", 1.0, AUTHORITY ["EPSG", "9001"]],
            AXIS ["Up", UP]
         ],
         AUTHORITY ["EPSG", "7405"]
      ]"""
      parser = crswktparser.CrsWkt1Parser()
      self.compd_cs = parser.parse_text(self.wkt)

   def test_compd_cs_node(self) :
      self.assertTrue(self.compd_cs.node_type == "COMPD_CS")
      self.assertTrue(self.compd_cs.name == "OSGB 1936 / British National Grid + ODN")
      self.assertTrue(self.compd_cs.head_cs.node_type == "PROJCS")
      self.assertTrue(self.compd_cs.head_cs.geographic_cs.node_type == "GEOGCS")
      self.assertTrue(self.compd_cs.authority.name == "EPSG")
      self.assertTrue(self.compd_cs.authority.code == "7405")

   def test_vert_cs_node(self) :
      self.assertTrue(self.compd_cs.tail_cs.node_type == "VERT_CS")
      self.assertTrue(self.compd_cs.tail_cs.name == "Newlyn")
      self.assertTrue(self.compd_cs.tail_cs.authority.name == "EPSG")
      self.assertTrue(self.compd_cs.tail_cs.authority.code == "5701")

   def test_vert_datum_node(self) :
      self.assertTrue(self.compd_cs.tail_cs.vert_datum.node_type == "VERT_DATUM")
      self.assertTrue(self.compd_cs.tail_cs.vert_datum.name == "Ordnance Datum Newlyn")
      self.assertTrue(self.compd_cs.tail_cs.vert_datum.datum_type == 2005)
      self.assertTrue(self.compd_cs.tail_cs.vert_datum.authority.name == "EPSG")
      self.assertTrue(self.compd_cs.tail_cs.vert_datum.authority.code == "5101")

   def test_vert_unit_node(self) :
      self.assertTrue(self.compd_cs.tail_cs.linear_unit.node_type == "UNIT")
      self.assertTrue(self.compd_cs.tail_cs.linear_unit.name == "metre")
      self.assertTrue(self.compd_cs.tail_cs.linear_unit.conversion_factor == 1.0)
      self.assertTrue(self.compd_cs.tail_cs.linear_unit.authority.name == "EPSG")
      self.assertTrue(self.compd_cs.tail_cs.linear_unit.authority.code == "9001")

   def test_vert_axis_nodes(self) :
      self.assertTrue(len(self.compd_cs.tail_cs.axis_list) == 1)
      self.assertTrue(self.compd_cs.tail_cs.axis_list[0].node_type == "AXIS")
      self.assertTrue(self.compd_cs.tail_cs.axis_list[0].name == "Up")
      self.assertTrue(self.compd_cs.tail_cs.axis_list[0].direction == "UP")

#---------------------------------------------------------------------------------------------------
if __name__ == '__main__':
#---------------------------------------------------------------------------------------------------
   unittest.main()

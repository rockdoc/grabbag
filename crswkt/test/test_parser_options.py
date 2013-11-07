"""
Unit tests for CRS WKT parser options.
"""
import unittest
import crswktparser

NO_LOGGING = 99

#---------------------------------------------------------------------------------------------------
class TestParserOptions(unittest.TestCase) :
#---------------------------------------------------------------------------------------------------
   def setUp(self) :
      self.wkt = """GEOGCS [
         # This CRS definition has nodes in non-standard order.
         # Plus this comment, which is also non-standard!
         "OSGB 1936",
         AUTHORITY ["EPSG", "4277"],   # here's an inline comment
         DATUM [
            "OSGB 1936",
            AUTHORITY ["EPSG", "6277"],
            SPHEROID ["Airy 1830", 6377563.396, 299.3249646],
            TOWGS84 [375, -111, 431, 0, 0, 0, 0]
         ],
         PRIMEM ["Greenwich", 0],
         AXIS ["latitude", NORTH],
         AXIS ["longitude", EAST],
         UNIT ["degree", 0.0174532925199433]
      ]"""

   def test_strict_mode(self) :
      parser = crswktparser.CrsWkt1Parser(log_level=NO_LOGGING, strict=True)
      # parsing in strict mode should raise a WktSyntaxError expection
      self.assertRaises(crswktparser.WktSyntaxError, parser.parse_text, self.wkt)

   def test_lax_mode(self) :
      # parsing in lax mode should complete without error
      parser = crswktparser.CrsWkt1Parser(log_level=NO_LOGGING, strict=False)
      geogcs = parser.parse_text(self.wkt)
      self.assertTrue(geogcs.node_type == 'GEOGCS')

#---------------------------------------------------------------------------------------------------
if __name__ == '__main__':
#---------------------------------------------------------------------------------------------------
   unittest.main()

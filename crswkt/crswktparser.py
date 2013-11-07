# Copyright (c) 2013, Philip A.D. Bentley
# All rights reserved.
# This software is made available under a BSD 3-clause license.
# Please refer to the accompanying LICENSE.TXT file.
"""
The crswktparser module includes classes for parsing and instantiating coordinate reference system
descriptions encoded in OGC well-known text format, a.k.a. CRS WKT or OGC WKT.

Package Dependencies
--------------------
The crswktparser module depends upon the following Python packages. If you don't already have these
then you'll need to download and install them.

* PLY - http://www.dabeaz.com/ply/

Basic Usage
-----------
The basic usage idiom for parsing CRS WKT text strings is as follows:

    parser = CrsWkt1Parser(...)
    coord_sys = parser.parse_text(wktext, ...)

If the input WKT string is valid then the parse_text() method will return a CrsWktNode object
representing the top-level coordinate system defined within the string. Inspection of the object's
node_type attribute will reveal the type of the coordinate system, thus:

>>> print coord_sys.node_type
PROJCS

Further properties of the coordinate system are accessible via other attributes of the object,
the attributes being named after the corresponding properties in the OGC CRS WKT 'standard'.
Several of the attributes refer in turn to other CrsWktNode objects (describing, for example,
PROJECTION, PARAMETER, AXIS and AUTHORITY nodes in the WKT string).

Hence, continuing with the above example, and noting that projected coordinate systems contain
a nested geographic coordinate system definition...

>>> print coord_sys.name
OSGB 1936 / British National Grid
>>> print coord_sys.projection
PROJECTION: {'name': 'Transverse Mercator', 'authority': None}
>>> print coord_sys.geographic_cs.name
OSGB 1936
>>> print coord_sys.geographic_cs.authority
AUTHORITY: {'code': '4277', 'name': 'EPSG'}

Projection PARAMETERs, if defined, can be retrieved from the param_list attribute, as follows.
Parameter values are coerced to integers if possible, else floats.

>>> len(coord_sys.param_list)
5
>>> print coord_sys.param_list[0]
PARAMETER: {'authority': None, 'name': 'False easting', 'value': 400000}
>>> coord_sys.param_list[0].value
400000

Similarly, any AXIS definitions can be retrieved from the axis_list attribute:

>>> len(coord_sys.axis_list)
2
>>> print coord_sys.axis_list[0]
AXIS: {'direction': 'NORTH', 'authority': None, 'name': 'N'}
>>> print coord_sys.axis_list[1]
AXIS: {'direction': 'EAST', 'authority': None, 'name': 'E'}

Finally, it's possible to return the value of any CrsWktNode attribute as a dictionary object or
a JSON string as follows.

>>> coord_sys.geographic_cs.prime_meridian.as_dict()
{'PRIMEM': {'longitude': 0.0, 'name': 'Greenwich', 'AUTHORITY': {'code': '8901', 'name': 'EPSG'}}}
>>> coord_sys.geographic_cs.prime_meridian.as_json()
'{"PRIMEM": {"longitude": 0.0, "name": "Greenwich", "AUTHORITY": {"code": "8901", "name": "EPSG"}}}'

Order of Nodes in WKT Strings
-----------------------------
As a rule, the order in which nodes appear in the WKT string should follow the sequence as defined
in the OGC CRS WKT specification. Certainly for those nodes which can optionally include an
AUTHORITY node, that node should appear in the last position. For nodes which permit two or more
optional child nodes, the way in which the parsing rules are defined in the current module means
that those child nodes may appear in any order. Nonetheless, it is recommended that the 'official'
CRS WKT node order is observed, in case future versions of the standard or this module enforce a
more strict ordering.

Error-handling
--------------
Error-handling is fairly simple in the current version of the module. A WktSyntaxError exception is
raised if the WKT input source contains syntax errors. If the syntax is fine but there are errors
in the WKT content, then a WktContentError exception is raised.

The cause of any parsing problems hopefully can be determined by examining the exception text, in
combination with any error messages output by the parser's logging object.
"""
import sys, os, logging
import ply.lex as lex
from ply.lex import TOKEN
import ply.yacc as yacc

__version_info__ = (0, 1, 0, 'beta', 0)
__version__ = "%d.%d.%d-%s" % __version_info__[0:4]

# default logging options
DEFAULT_LOG_LEVEL  = logging.WARNING
DEFAULT_LOG_FORMAT = "[%(levelname)s] %(funcName)s: %(message)s"

class WktSyntaxError(Exception) :
   """Exception class for CRS WKT syntax errors."""
   pass

class WktContentError(Exception) :
   """Exception class for CRS WKT content errors."""
   pass

#---------------------------------------------------------------------------------------------------
class CrsWktNode(object) :
#---------------------------------------------------------------------------------------------------
   """
   A generic class for storing CRS WKT nodes and their properties. The type of the node - GEOGCS,
   DATUM, PRIMEM, and so on - is stored in the node_type attribute. The node's properties are then
   stored in attributes named according to the names defined in the CRS WKT specification, e.g.
   projection, prime_meridian, linear_unit, and so on. Attributes are of type CrsWktNode, list,
   string, or number.

   There are a few corollaries to this pattern as a result of the semi-formal grammar used in the
   CRS WKT specification. These are as follows:

   * The un-named (in WKT, that is) name property is stored, unsurprisingly in the name attribute.
   * Any AXIS definitions are stored as a list accessed via the axis_list attribute. This list may
     be empty.
   * Any PARAMETER definitions are stored as a list accessed via the param_list attribute. This list
     may be empty
   * The datum_type attribute is stored as an integer. Most other numeric properties are stored as
     floats, though you may want to do type-coercion prior to use, just to be on the safe side.
   * All nodes, with the obvious exception of the AUTHORITY node, possess an authority attribute
     which may be (and often is) undefined, i.e. set to None.
   """

   def __init__(self, node_type, **kwargs) :
      self.node_type = node_type
      self.name = "unspecified"
      if node_type != "AUTHORITY" : self.authority = None
      self.__dict__.update(**kwargs)

   def __str__(self) :
      d = vars(self).copy()
      d.pop('node_type')
      return "%s: %s" % (self.node_type, str(d))

   def as_dict(self, depth=0) :
      """Return the CRS node as a Python dictionary."""
      idict = vars(self).copy()
      nt = idict.pop('node_type')
      odict = {}
      for k,v in idict.items() :
         if v is None : continue
         if isinstance(v, CrsWktNode) :
            odict[v.node_type] = v.as_dict(depth+1)
         elif isinstance(v, list) :
            odict[k] = []
            for x in v :
               if isinstance(x, CrsWktNode) :
                  d = {}
                  d[x.node_type] = x.as_dict(depth+1)
                  odict[k].append(d)
         else :
            odict[k] = v
      return (odict if depth else {nt: odict})

   def as_json(self) :
      """Return the CRS node as a JSON string."""
      import json
      return json.dumps(self.as_dict())

#---------------------------------------------------------------------------------------------------
class CrsWkt1Parser(object) :
#---------------------------------------------------------------------------------------------------
   """
   Class for parsing a version 1 CRS WKT string. Currently there is no formal CRS WKT standard, so
   by version 1 we mean the original WKT specification in OGC document 01-009: Coordinate Transform-
   ation Services (where it is referred to as CS WKT). However, there are proposals (as of mid 2012)
   to work up a formal OGC standard for CRS WKT version 2.
   """

   # Keywords used in CRS WKT. Keys represent WKT keywords; values represent token names.
   keywords = {
      'AUTHORITY':  'AUTHORITY',
      'AXIS':       'AXIS',
      'COMPD_CS':   'COMPD_CS',
      'DATUM':      'DATUM',
      'GEOCCS':     'GEOC_CS',      # keyword does not include _ character
      'GEOGCS':     'GEOG_CS',      # ditto
      'LOCAL_CS':   'LOCAL_CS',
      'LOCAL_DATUM':'LOCAL_DATUM',
      'PARAMETER':  'PARAMETER',
      'PRIMEM':     'PRIMEM',
      'PROJCS':     'PROJ_CS',      # keyword does not include _ character
      'PROJECTION': 'PROJECTION',
      'SPHEROID':   'SPHEROID',
      'TOWGS84':    'TOWGS84',
      'UNIT':       'UNIT',
      'VERT_CS':    'VERT_CS',
      'VERT_DATUM': 'VERT_DATUM'
   }

   tokens = ['KEYWORD', 'NAME', 'NUMBER', 'CODE', 'AXIS_DIR', 'LBRACKET', 'RBRACKET'] + \
            keywords.values()

   # quoted text strings
   nonquotes = r'([^"])*'
   textstring = r'\"' + nonquotes + r'\"'

   # decimal and integer numbers
   decimal = r'[+-]?([0-9]+\.[0-9]*|[1-9][0-9]*|0)'

   # literal characters
   literals = [',']

   # ignored characters - whitespace, basically
   t_ignore  = ' \r\t\f'

   def __init__(self, **kwargs) :
      """
      The currently supported keyword arguments, with their default values, are described below. Any
      other keyword argments are passed through as-is to the PLY parser (via the yacc.yacc function).
      For more information about the latter, visit http://www.dabeaz.com/ply/ply.html
      
      log_level: Sets the logging level to one of the constants defined in the Python logging
         module [default: logging.WARNING]
      strict: Set to True to enforce strict compliance to the CRS WKT standard (or as strict as is
         possible given the loose nature of the standard). Set to False to enable non-standard
         features: in the current version this is limited to allowing stand-alone or inline comments
         beginning with the # character [default: True]
      """
      self.debug = kwargs.pop('debug', 0)
      self.strict = kwargs.pop('strict', True)
      self.log_level = kwargs.pop('log_level', DEFAULT_LOG_LEVEL)
      self.coord_sys = None
      self._init_logger()
      if not self.strict : self._enable_lax_mode()

      # Build the lexer and parser
      self.lexer = lex.lex(module=self, debug=self.debug)
      self.parser = yacc.yacc(module=self, debug=self.debug, **kwargs)

   def parse_text(self, wkt) :
      """
      Parse the specified WKT string.
      :param wkt: CRS WKT v1 string.
      :returns: A CrsWktNode object representing the root of the WKT node tree.
      """
      self.coord_sys = self.parser.parse(input=wkt, lexer=self.lexer)
      return self.coord_sys

   def _init_logger(self) :
      """Configure a logger object."""
      console = logging.StreamHandler(stream=sys.stderr)
      console.setLevel(self.log_level)
      fmtr = logging.Formatter(DEFAULT_LOG_FORMAT)
      console.setFormatter(fmtr)
      self.logger = logging.getLogger('crswktparser')
      self.logger.addHandler(console)
      self.logger.setLevel(self.log_level)

   def _enable_lax_mode(self) :
      """
      Add methods to handle extra features supported in lax (i.e. non-strict) parsing mode.
      Note that these methods are added to the current parser instance only, as one would expect.
      """
      from types import MethodType
      # Allow stand-alone and inline comments beginning with the # character
      def t_comment(self, t) :
         r'\#.*'
         pass
      self.t_COMMENT = MethodType(t_comment, self, CrsWkt1Parser)

   def _lexer_test(self, data) :
      """private function for testing the lexer"""
      self.lexer.input(data)
      while 1 :
         t = self.lexer.token()
         if not t : break
         print "%3d: type: %-15s\tvalue: %s" % (t.lexpos, t.type, t.value)

   def _parser_test(self, data) :
      """private function for testing the parser"""
      cs = self.parser.parse(input=data, lexer=self.lexer)
      return cs

   ### TOKEN DEFINITIONS

   def t_AXIS_DIR(self, t) :
      r'NORTH|SOUTH|EAST|WEST|UP|DOWN|OTHER'
      return t

   # keyword
   def t_KEYWORD(self, t) :
      r'[A-Z][A-Z_0-9]*'
      t.type = self.keywords.get(t.value,'KEYWORD')
      return t

   # For now restrict authority codes to a sequence of digits as that seems to be the established
   # usage. The CRS WKT specification does not appear to define the content model for these codes.
   def t_CODE(self, t) :
      r'\"[0-9]+\"'
      t.value = eval(t.value)
      return t

   @TOKEN(textstring)
   def t_NAME(self, t) :
      t.value = eval(t.value)
      return t

   @TOKEN(decimal)
   def t_NUMBER(self, t) :
      return t

   # The CRS WKT specification mandates either [ or ( as opening bracket
   def t_LBRACKET(self, t) :
      r'\[|\('
      return t

   # The CRS WKT specification mandates either ] or ) as closing bracket
   def t_RBRACKET(self, t) :
      r'\]|\)'
      return t

   # newlines
   def t_newline(self, t):
      r'\n+'
      t.lexer.lineno += len(t.value)

   def t_error(self, t):
      msg  = "Illegal character(s) encountered at line number %d, lexical position %d\n" % (t.lineno, t.lexpos)
      msg += "Token value = '%s'" % t.value
      self.logger.warning(msg)
      raise WktSyntaxError(msg)

   ### PARSING RULES

   # this tells the parser which parser rule to kick off with
   start = "coord_sys"

   def p_coord_sys(self, p) :
      """coord_sys : single_cs
                   | compd_cs"""
      self.coord_sys = p[1]
      p[0] = p[1]

   def p_single_cs(self, p) :
      """single_cs : horiz_cs
                   | geocentric_cs
                   | vert_cs
                   | local_cs"""
      p[0] = p[1]

   def p_horiz_cs(self, p) :
      """horiz_cs : geographic_cs
                  | projected_cs"""
      p[0] = p[1]

   def p_compd_cs(self, p) :
      """compd_cs : COMPD_CS LBRACKET NAME ',' single_cs ',' single_cs RBRACKET
                  | COMPD_CS LBRACKET NAME ',' single_cs ',' single_cs ',' authority RBRACKET"""
      self.logger.debug(str(p[1:]))
      compd_cs = CrsWktNode('COMPD_CS', name=p[3], head_cs=p[5], tail_cs=p[7])
      if len(p) > 9 and p[9] is not None : compd_cs.authority = p[9]
      p[0] = compd_cs
      self.logger.info("Read COMPD_CS node '%s'" % compd_cs.name)

   def p_projected_cs(self, p) :
      "projected_cs : PROJ_CS LBRACKET NAME ',' geographic_cs ',' node_list RBRACKET"
      #"projected_cs : PROJ_CS LBRACKET NAME ',' geographic_cs ',' projection ',' param_list ',' linear_unit ',' axis_list ',' authority RBRACKET"
      proj_cs = CrsWktNode('PROJCS', name=p[3], geographic_cs=p[5], param_list=[], axis_list=[])
      if isinstance(p[7], list) :
         for node in p[7] :
            if not node : continue
            if node.node_type == 'PROJECTION' :
               proj_cs.projection = node
            elif node.node_type == 'PARAMETER' :
               proj_cs.param_list.append(node)
            elif node.node_type == 'UNIT' :
               proj_cs.linear_unit = node
            elif node.node_type == 'AXIS' :
               proj_cs.axis_list.append(node)
            elif node.node_type == 'AUTHORITY' :
               proj_cs.authority = node
            else :
               raise WktSyntaxError("%s node is not valid in a PROJCS definition" % node.node_type)
      if len(proj_cs.axis_list) not in (0,2) :
         raise WktSyntaxError("Projected CS accepts 0 or 2 axes, %d defined." % len(proj_cs.axis_list))
      p[0] = proj_cs
      self.logger.info("Read PROJCS node '%s'" % proj_cs.name)

   def p_geographic_cs(self, p) :
      """geographic_cs : GEOG_CS LBRACKET NAME ',' node_list RBRACKET"""
      #"""geographic_cs : GEOG_CS LBRACKET NAME ',' datum ',' primem ',' angular_unit ',' axis_list ',' authority RBRACKET"""
      geog_cs = CrsWktNode('GEOGCS', name=p[3], axis_list=[])
      if isinstance(p[5], list) :
         for node in p[5] :
            if not node : continue
            if node.node_type == 'DATUM' :
               geog_cs.datum = node
            elif node.node_type == 'PRIMEM' :
               geog_cs.prime_meridian = node
            elif node.node_type == 'UNIT' :
               geog_cs.angular_unit = node
            elif node.node_type == 'AXIS' :
               geog_cs.axis_list.append(node)
            elif node.node_type == 'AUTHORITY' :
               geog_cs.authority = node
            else :
               raise WktSyntaxError("%s node is not valid in a GEOGCS definition" % node.node_type)
      if len(geog_cs.axis_list) not in (0,2) :
         raise WktSyntaxError("Geographic CS accepts 0 or 2 axes, %d defined." % len(geog_cs.axis_list))
      p[0] = geog_cs
      self.logger.info("Read GEOGCS node '%s'" % geog_cs.name)

   def p_geocentric_cs(self, p) :
      "geocentric_cs : GEOC_CS LBRACKET NAME ',' node_list RBRACKET"
      #"geocentric_cs : GEOC_CS LBRACKET NAME ',' datum ',' primem ',' linear_unit ',' axis_list ',' authority RBRACKET"
      geoc_cs = CrsWktNode('GEOCCS', name=p[3], axis_list=[])
      if isinstance(p[5], list) :
         for node in p[5] :
            if not node : continue
            if node.node_type == 'DATUM' :
               geoc_cs.datum = node
            elif node.node_type == 'PRIMEM' :
               geoc_cs.prime_meridian = node
            elif node.node_type == 'UNIT' :
               geoc_cs.linear_unit = node
            elif node.node_type == 'AXIS' :
               geoc_cs.axis_list.append(node)
            elif node.node_type == 'AUTHORITY' :
               geoc_cs.authority = node
            else :
               raise WktSyntaxError("%s node is not valid in a GEOGCS definition" % node.node_type)
      if len(geoc_cs.axis_list) not in (0,3) :
         raise WktSyntaxError("Geocentric CS accepts 0 or 3 axes, %d defined." % len(geoc_cs.axis_list))
      p[0] = geoc_cs
      self.logger.info("Read GEOCCS node '%s'" % geoc_cs.name)

   def p_vert_cs(self, p) :
      "vert_cs : VERT_CS LBRACKET NAME ',' node_list RBRACKET"
      #"vert_cs : VERT_CS LBRACKET NAME ',' vert_datum ',' linear_unit ',' axis_list ',' authority RBRACKET"
      vert_cs = CrsWktNode('VERT_CS', name=p[3], axis_list=[])
      if isinstance(p[5], list) :
         for node in p[5] :
            if not node : continue
            if node.node_type == 'VERT_DATUM' :
               vert_cs.vert_datum = node
            elif node.node_type == 'UNIT' :
               vert_cs.linear_unit = node
            elif node.node_type == 'AXIS' :
               vert_cs.axis_list.append(node)
            elif node.node_type == 'AUTHORITY' :
               vert_cs.authority = node
            else :
               raise WktSyntaxError("%s node is not valid in a VERT_CS definition" % node.node_type)
      if len(vert_cs.axis_list) not in (0,1) :
         raise WktSyntaxError("Vertical CS accepts 0 or 1 axes, %d defined." % len(vert_cs.axis_list))
      p[0] = vert_cs
      self.logger.info("Read VERT_CS node '%s'" % vert_cs.name)

   def p_local_cs(self, p) :
      "local_cs : LOCAL_CS LBRACKET NAME ',' node_list RBRACKET"
      #"local_cs : LOCAL_CS LBRACKET NAME ',' local_datum ',' unit ',' axis_list ',' authority RBRACKET"
      local_cs = CrsWktNode('LOCAL_CS', name=p[3], axis_list=[])
      if isinstance(p[5], list) :
         for node in p[5] :
            if not node : continue
            if node.node_type == 'LOCAL_DATUM' :
               local_cs.local_datum = node
            elif node.node_type == 'UNIT' :
               local_cs.unit = node
            elif node.node_type == 'AXIS' :
               local_cs.axis_list.append(node)
            elif node.node_type == 'AUTHORITY' :
               local_cs.authority = node
            else :
               raise WktSyntaxError("%s node is not valid in a VERT_CS definition" % node.node_type)
      if len(local_cs.axis_list) not in (1,2) :
         raise WktSyntaxError("Local CS accepts 1 or 2 axes, %d defined." % len(local_cs.axis_list))
      p[0] = local_cs
      self.logger.info("Read LOCAL_CS node '%s'" % local_cs.name)

   def p_projection(self, p) :
      """projection : PROJECTION LBRACKET NAME RBRACKET
                    | PROJECTION LBRACKET NAME ',' authority RBRACKET"""
      self.logger.debug(str(p[1:]))
      p[0] = CrsWktNode('PROJECTION', name=p[3])
      if len(p) > 5 and p[5] is not None : p[0].authority = p[5]
      self.logger.info("Read PROJECTION node '%s'" % p[3])

   def p_datum(self, p) :
      """datum : DATUM LBRACKET NAME ',' node_list RBRACKET"""
      #"""datum : DATUM LBRACKET NAME ',' spheroid ',' towgs84 ',' authority RBRACKET"""
      self.logger.debug(str(p[1:]))
      datum = CrsWktNode('DATUM', name=p[3])
      if isinstance(p[5], list) :
         for node in p[5] :
            if not node : continue
            if node.node_type == "SPHEROID" :
               datum.spheroid = node
            elif node.node_type == "TOWGS84" :
               datum.towgs84 = node
            elif node.node_type == "AUTHORITY" :
               datum.authority = node
            else :
               raise WktSyntaxError("%s node is not valid in a DATUM definition" % node.node_type)
      p[0] = datum
      self.logger.info("Read DATUM node '%s'" % p[3])

   def p_vert_datum(self, p) :
      """vert_datum : VERT_DATUM LBRACKET NAME ',' datum_type RBRACKET
                    | VERT_DATUM LBRACKET NAME ',' datum_type ',' authority RBRACKET"""
      self.logger.debug(str(p[1:]))
      p[0] = CrsWktNode('VERT_DATUM', name=p[3], datum_type=p[5])
      if len(p) > 7 and p[7] is not None : p[0].authority = p[7]
      self.logger.info("Read VERT_DATUM node '%s'" % p[3])

   def p_local_datum(self, p) :
      """local_datum : LOCAL_DATUM LBRACKET NAME ',' datum_type RBRACKET
                     | LOCAL_DATUM LBRACKET NAME ',' datum_type ',' authority RBRACKET"""
      self.logger.debug(str(p[1:]))
      p[0] = CrsWktNode('LOCAL_DATUM', name=p[3], datum_type=p[5])
      if len(p) > 7 and p[7] is not None : p[0].authority = p[7]
      self.logger.info("Read LOCAL_DATUM node '%s'" % p[3])

   def p_spheroid(self, p) :
      """spheroid : SPHEROID LBRACKET NAME ',' semimajor_axis ',' flattening RBRACKET
                  | SPHEROID LBRACKET NAME ',' semimajor_axis ',' flattening ',' authority RBRACKET"""
      self.logger.debug(str(p[1:]))
      p[0] = CrsWktNode('SPHEROID', name=p[3], semi_major_axis=p[5], inverse_flattening=p[7])
      if len(p) > 9 and p[9] is not None : p[0].authority = p[9]
      self.logger.info("Read SPHEROID node '%s'" % p[3])

   def p_primem(self, p) :
      """primem : PRIMEM LBRACKET NAME ',' longitude RBRACKET
                | PRIMEM LBRACKET NAME ',' longitude ',' authority RBRACKET"""
      self.logger.debug(str(p[1:]))
      p[0] = CrsWktNode('PRIMEM', name=p[3], longitude=p[5])
      if len(p) > 7 and p[7] is not None : p[0].authority = p[7]
      self.logger.info("Read PRIMEM node '%s'" % p[3])

   def p_authority(self, p) :
      """authority : AUTHORITY LBRACKET NAME ',' CODE RBRACKET
                   | empty"""
      self.logger.debug(str(p[1:]))
      if len(p) > 2 :
         p[0] = CrsWktNode('AUTHORITY', name=p[3], code=p[5])
      else :
         p[0] = None
      self.logger.info("Read AUTHORITY node '%s', code '%s'" % (p[3],p[5]))

   def p_node_list(self, p) :
      """node_list : node_list ',' node
                   | node
                   | empty"""
      if len(p) == 2 :
         p[0] = p[1:] if p[1] else list()
      else :
         p[0] = p[1] + p[3:]

   def p_node(self, p) :
      """node : angular_unit
              | authority
              | axis
              | datum
              | linear_unit
              | local_datum
              | param
              | primem
              | projection
              | spheroid
              | towgs84
              | vert_datum"""
      p[0] = p[1]

   def p_axis_list(self, p) :
      """axis_list : axis_list ',' axis
                   | axis
                   | empty"""
      if len(p) == 2 :
         p[0] = p[1:] if p[1] else list()
      else :
         p[0] = p[1] + p[3:]

   def p_axis(self, p) :
      "axis : AXIS LBRACKET NAME ',' AXIS_DIR RBRACKET"
      self.logger.debug(str(p[1:]))
      p[0] = CrsWktNode('AXIS', name=p[3], direction=p[5])
      self.logger.info("Read AXIS node '%s'" % p[3])

   def p_towgs84(self, p) :
      """towgs84 : TOWGS84 LBRACKET seven_params RBRACKET
                 | empty"""
      self.logger.debug(str(p[1:]))
      if len(p) > 2 :
         plist = p[3]
         if isinstance(plist, (list,tuple)) and len(plist) == 7 :
            p[0] = CrsWktNode('TOWGS84', name='unspecified', dx=plist[0], dy=plist[1], dz=plist[2],
                           ex=plist[3], ey=plist[4], ez=plist[5], ppm=plist[6])
         else :
            raise WktContentError("TOWGS84 element incorrectly defined. Expecting list of 7 parameters.")
      self.logger.info("Read TOWGS84 node '%s'" % p[3])

   def p_seven_params(self, p) :
      "seven_params : NUMBER ',' NUMBER ',' NUMBER ',' NUMBER ',' NUMBER ',' NUMBER ',' NUMBER"
      self.logger.debug(str(p[1:]))
      p7 = []
      for i in range(1,15,2) : p7.append(float(p[i]))
      p[0] = p7

   def p_angular_unit(self, p) :
      "angular_unit : unit"
      p[0] = p[1]

   def p_linear_unit(self, p) :
      "linear_unit : unit"
      p[0] = p[1]

   def p_unit(self, p) :
      """unit : UNIT LBRACKET NAME ',' conv_factor RBRACKET
              | UNIT LBRACKET NAME ',' conv_factor ',' authority RBRACKET"""
      self.logger.debug(str(p[1:]))
      p[0] = CrsWktNode('UNIT', name=p[3], conversion_factor=p[5])
      if len(p) > 7 and p[7] is not None : p[0].authority = p[7]
      self.logger.info("Read UNIT node '%s'" % p[3])

   def p_conv_factor(self, p) :
      "conv_factor : NUMBER"
      p[0] = float(p[1])

   def p_semimajor_axis(self, p) :
      "semimajor_axis : NUMBER"
      p[0] = float(p[1])

   def p_flattening(self, p) :
      "flattening : NUMBER"
      p[0] = float(p[1])

   def p_longitude(self, p) :
      "longitude : NUMBER"
      p[0] = float(p[1])

   # Assumes that datum type is an integer. CRS WKT specification is silent in this regard.
   def p_datum_type(self, p) :
      "datum_type : NUMBER"
      p[0] = int(p[1])

   def p_param_list(self, p) :
      """param_list : param_list ',' param
                    | param
                    | empty"""
      if len(p) == 2 :
         p[0] = p[1:] if p[1] else list()
      else :
         p[0] = p[1] + p[3:]

   def p_param(self, p) :
      "param : PARAMETER LBRACKET NAME ',' number RBRACKET"
      self.logger.debug(str(p[1:]))
      p[0] = CrsWktNode('PARAMETER', name=p[3], value=p[5])
      self.logger.info("Read PARAMETER node '%s'" % p[3])

   def p_number(self, p) :
      "number : NUMBER"
      try :
         p[0] = int(p[1])
      except ValueError :
         p[0] = float(p[1])

   def p_empty(self, p) :
      "empty :"
      pass

   def p_error(self, p) :
      """Handles parsing errors."""
      if p :
         errmsg  = "Syntax error at line number %d, lexical position %d\n" % (p.lineno, p.lexpos)
         errmsg += "Token = %s, value = '%s'" % (p.type, p.value)
      else :
         errmsg = "Syntax error: premature end-of-text encountered."
      self.logger.error(errmsg)
      raise WktSyntaxError(errmsg)

#---------------------------------------------------------------------------------------------------
def main() :
#---------------------------------------------------------------------------------------------------
   """Rudimentary main function - primarily for testing and debugging purposes in current form."""
   debug = 0
   if len(sys.argv) < 2 :
      print "usage: python crswktparser.py wktfile [keyword=value, ...]"
      sys.exit(1)
   wktfile = sys.argv[1]
   kwargs = {}
   if len(sys.argv) > 2 :
      keys = [x.split('=')[0] for x in sys.argv[2:]]
      vals = [eval(x.split('=')[1]) for x in sys.argv[2:]]
      kwargs = dict(zip(keys,vals))

   f = open(wktfile)
   wktext = f.read()
   f.close()

   wkt_parser = CrsWkt1Parser(**kwargs)
   coord_sys = wkt_parser.parse_text(wktext)

   print "CS type:", coord_sys.node_type
   print "CS name:", coord_sys.name
   print "CS as str:\n\t", str(coord_sys)
   print "CS as dict:\n\t", coord_sys.as_dict()
   print "CS as json:\n\t", coord_sys.as_json()

#---------------------------------------------------------------------------------------------------
if __name__ == '__main__':
#---------------------------------------------------------------------------------------------------
   main()

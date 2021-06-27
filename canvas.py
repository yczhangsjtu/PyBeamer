import re
import math

# An alternative tool to generate tikz code in builder mode

## Alternative to TikZOptions, not use *args and **kwargs
## because in tikz, options may contain spaces, inconvenient
## to handle in python
class DrawOptions:
  def __init__(self):
    self.switches = set()
    self.properties = dict()

  def isempty(self):
    return len(self.switches) == 0 and len(self.properties) == 0

  def __len__(self):
    return len(self.switches) + len(self.properties)

  def dumps(self):
    items = [item for item in self.switches]
    for key in self.properties:
      value = self.properties[key]
      if not isinstance(value, str):
        value = value.dumps()
      items.append("%s=%s" % (key, value))
    return ",".join(items)

  def set(self, key, value=None):
    if value is None:
      self.switches.add(key)
    else:
      self.properties[key] = value

  def unset(self, key):
    ## Usually, a switch and a key-value property will
    ## never have the same name
    if key in self.switches:
      self.switches.remove(key)
    elif key in self.properties:
      self.properties.remove(key)

  def isset(self, switch):
    return switch in self.switches

  def get(self, key):
    return self.properties.get(key) # Return None when not exist

class HasOptions(object):
  def __init__(self, options=None):
    self.options = options if options is not None else DrawOptions()

  def set(self, key, value=None):
    self.options.set(key, value)
    return self

  def unset(self, key):
    self.options.unset(key)
    return self

  def isset(self, switch):
    return self.options.isset()

  def get(self, key):
    return self.options.get(key)

## Alternative to TikZNode
class Node(HasOptions):
  def __init__(self, canvas, handle):
    super(Node, self).__init__()
    self.text = ""
    self.at = None
    self.canvas = canvas
    self.handle = handle

    self.position_set = None
    self.relative_position = None

  def dumps(self):
    return "\\node%s(%s)%s{%s};" % (
      ("[%s]" % self.options.dumps()) if not self.options.isempty() else "",
      self.handle,
      (("at %s" % self.at) if isinstance(self.at, str) else ("at %s" % self.at.dumps()))
        if self.at is not None else "",
      self.text,
    )

  def set_text(self, text):
    self.text = text
    return self

  def set_pos(self, pos):
    self.at = pos
    return self

  def center(self):
    return NodeAnchor(self, 0, 0)

  def south(self):
    return NodeAnchor(self, -1, 0)

  def north(self):
    return NodeAnchor(self, 1, 0)

  def east(self):
    return NodeAnchor(self, 0, 1)

  def west(self):
    return NodeAnchor(self, 0, -1)

  def southwest(self):
    return NodeAnchor(self, -1, -1)

  def northwest(self):
    return NodeAnchor(self, 1, -1)

  def southeast(self):
    return NodeAnchor(self, -1, 1)

  def northeast(self):
    return NodeAnchor(self, 1, 1)

  def at_positions_short(self, lists):
    self.position_set = PositionSet.from_short_repr(existing=[self], lists=lists)
    return self

  def make_nodes(self):
    ret = self.canvas.make_nodes_with_position_set(self.position_set)
    self.position_set = None
    return self

  def at_relative(self, relative_position):
    if isinstance(relative_position, str):
      relative_position = RelativePosition.from_str(relative_position)
    self.relative_position = relative_position
    return self

  def make_node(self):
    node = self.canvas.make_node()
    if self.relative_position is not None:
      key, value = self.relative_position.get_key_value(self.handle)
      node.set(key, value)
      self.relative_position = None
    return node

class NodeAnchor(object):
  def __init__(self, node, horizontal, vertical):
    self.node = node
    self.horizontal = horizontal
    self.vertical = vertical

  def dumps(self):
    items = []
    if vertical < 0:
      items.append("south")
    elif vertical > 0:
      items.append("north")
    if horizontal < 0:
      items.append("west")
    elif horizontal > 0:
      items.append("east")
    if len(items) == 0:
      return "center"
    if len(items) == 1:
      return items[0]
    return "%s.%s" % (self.node.handle, " ".join(items))

## Fork from PyLaTeX TikZCoordinate
class Coordinate(object):
  """A General Purpose Coordinate Class."""

  _coordinate_str_regex = re.compile(r'(\+\+)?\(\s*(-?[0-9]+(\.[0-9]+)?)\s*'
                                     r',\s*(-?[0-9]+(\.[0-9]+)?)\s*\)')

  def __init__(self, x, y, relative=False):
    """
    Args
    ----
    x: float or int
        X coordinate
    y: float or int
        Y coordinate
    relative: bool
        Coordinate is relative or absolute
    """
    self._x = float(x)
    self._y = float(y)
    self.relative = relative

  def __repr__(self):
    return '%s(%g,%g)' % ('++' if self.relative else '', self._x, self._y)

  def dumps(self):
      """Return representation."""

      return self.__repr__()

  @classmethod
  def from_str(cls, coordinate):
    """Build a TikZCoordinate object from a string."""

    m = cls._coordinate_str_regex.match(coordinate)

    if m is None:
      raise ValueError('invalid coordinate string')

    return Coordinate(
      float(m.group(2)), float(m.group(4)), relative=m.group(1) == '++')

  def __eq__(self, other):
    if isinstance(other, tuple):
      # if comparing to a tuple, assume it to be an absolute coordinate.
      other_relative = False
      other_x = float(other[0])
      other_y = float(other[1])
    elif isinstance(other, Coordinate):
      other_relative = other.relative
      other_x = other._x
      other_y = other._y
    else:
      raise TypeError('can only compare tuple and Coordinate types')

    # prevent comparison between relative and non relative
    # by returning False
    if (other_relative != self.relative):
      return False

    # return comparison result
    return (other_x == self._x and other_y == self._y)

  def _arith_check(self, other):
    if isinstance(other, tuple):
      other_coord = Coordinate(*other)
    elif isinstance(other, Coordinate):
      if other.relative is True or self.relative is True:
        raise ValueError('refusing to add relative coordinates')
      other_coord = other
    else:
      raise TypeError('can only add tuple or Coordinate types')

    return other_coord

  def __add__(self, other):
    other_coord = self._arith_check(other)
    return Coordinate(self._x + other_coord._x,
                      self._y + other_coord._y)

  def __radd__(self, other):
    self.__add__(other)

  def __sub__(self, other):
    other_coord = self._arith_check(other)
    return ZCoordinate(self._x - other_coord._y,
                       self._y - other_coord._y)

  def distance_to(self, other):
    """Euclidean distance between two coordinates."""

    other_coord = self._arith_check(other)
    return math.sqrt(math.pow(self._x - other_coord._x, 2) +
                     math.pow(self._y - other_coord._y, 2))

class Point(HasOptions):
  def __init__(self, data):
    if not isinstance(data, Node) and \
       not isinstance(data, NodeAnchor) and \
       not isinstance(data, Coordinate):
      raise TypeError("point is not one of Node, NodeAnchor, Coordinate")

    self.data = data
    super(Point, self).__init__()

  def dumps(self):
    if isinstance(self.data, Node) or isinstance(self.data, NodeAnchor):
      if self.options.isempty():
        return "(%s)" % self.data.dumps()
      return "([%s]%s)" % (ns, self.options.dumps(), self.data.dumps())

    # Now it is coordinate
    return self.data.dumps()

  @classmethod
  def from_str(cls, s):
    # Currently only coordinate can be parsed from string
    return Point(Coordinate.from_str(s))

  def shiftx(self, distance):
    return self.set("xshift", distance)

  def shifty(self, distance):
    return self.set("yshift", distance)

  def unshift(self):
    return self.unset("xshift").unset("yshift")

class Line(object):
  legal_types = set(['--', '-|', '|-', 'to', 'rectangle', 'circle', 'arc', 'edge'])
  def __init__(self, linetype):
    if not linetype in legal_types:
      raise ValueError("Illegal line type %s" % linetype)
    self.linetype = linetype

    # for example, a node attached to the line
    self.additional = None

  def dumps(self):
    if self.additional is None:
      return self.linetype
    if isinstance(self.additional, Node):
      return "%s node[%s]{%s}" % (
        self.linetype, self.additional.options.dumps(), self.additional.text)
    raise TypeError("Unknown additional information %s" % str(self.additional))

  def set_above_text(self, text):
    self.additional = Node(None, None).set_text(text) \
      .set("midway").set("sloped").set("above").set("anchor", "center")
    return self

class Path(HasOptions):
  def __init__(self, canvas):
    self.items = []
    self.canvas = canvas;
    super(Path, self).__init__()

  def extend(self, item):
    if isinstance(item, Point):
      self.items.append(item)
      return self
    elif isinstance(item, Line):
      if len(self.items) > 0 and isinstance(self.items[-1], Line):
        raise TypeError("Cannot include consecutive lines")
      self.items.append(item)
      return self
    elif isinstance(item, str):
      try:
        coord = Coordinate.from_str(item)
        self.items.append(Point(coord))
        return self
      except:
        pass

      try:
        line = Line(item)
        if len(self.items) > 0 and isinstance(self.items[-1], Line):
          raise TypeError("Cannot include consecutive lines")
        self.items.append(line)
        return
      except:
        pass

      raise ValueError("Invalid path item: %s" % item)
    elif isinstance(item, list):
      for e in item:
        self.extend(e)
      return self

    raise TypeError("Invalid path item type: %s" % str(item))

  def dumps(self):
    if len(self.items) == 0:
      raise ValueError("Empty path")
    if isinstance(self.items[-1], Line):
      raise TypeError("Path cannot end with line")
    pathstr = " ".join([item.dumps() for item in self.items])
    if self.options.isempty():
      return "\\path %s;" % pathstr
    return "\\path[%s] %s;" % (self.options.dumps(), pathstr)

class Onslide(object):
  def __init__(self, start, end=None):
    self.start = start
    self.end = end

  def dumps(self):
    if self.start == self.end:
      return "\\onslide<%d>" % self.start
    if self.end is None:
      return "\\onslide<%d->" % self.start
    return "\\onslide<%d-%d>" % (self.start, self.end)

class Builder(object):
  def __init__(self):
    self.switches = set()
    self.unsets = set()
    self.properties = dict()
    self.to_set_text = None
    self.to_set_pos = None

  def set(self, key, value=None):
    if value is None:
      self.switches.add(key)
    else:
      self.properties[key] = value
    self.unsets.discard(key)

  def unset(self, key):
    ## Usually, a switch and a key-value property will
    ## never have the same name
    if key in self.switches:
      self.switches.remove(key)
    elif key in self.properties:
      self.properties.remove(key)
    self.unsets.add(key)

  def set_text(self, text):
    self.to_set_text = text

  def clear_set_text(self):
    self.to_set_text = None

  def set_pos(self, pos):
    self.to_set_pos = pos

  def clear_set_pos(self):
    self.to_set_pos = None

  def apply(self, item):
    for switch in self.switches:
      item.set(switch)
    for key in self.properties:
      item.set(key, self.properties[key])
    for key in self.unsets:
      item.unset(key)
    if isinstance(item, Node):
      if self.to_set_text is not None:
        item.set_text(self.to_set_text)
      if self.to_set_pos is not None:
        item.set_pos(self.to_set_pos)

class RelativePosition(object):
  def __init__(self, horizontal, vertical):
    """
    horizontal = ("left"/"right", None/"X[cm]")
    vertical = ("above"/"below", None/"X[cm]")
    """
    if horizontal is None and vertical is None:
      raise ValueError("horizontal and vertical should not both be empty")
    self.horizontal = horizontal
    self.vertical = vertical

  def get_key_value(self, target):
    directions, distances = [], []
    if self.vertical is not None:
      direction, distance = self.vertical
      directions.append(direction)
      distances.append(distance)
    if self.horizontal is not None:
      direction, distance = self.horizontal
      directions.append(direction)
      distances.append(distance)

    if len(directions) == 2:
      if distances[0] is None and distances[1] is None:
        return " ".join(directions), "of %s" % target

      if distances[0] is not None and distances[1] is not None:
        return " ".join(directions), "%s of %s" % (" and ".join(distances), target)

      raise ValueError("Cannot leave only one direction to None")

    return directions[0], ("%s of %s" % (distances[0], target)
      if distances[0] is not None else ("of %s" % target))

  @classmethod
  def above(cls, distance=None):
    return RelativePosition(None, ("above", distance))

  @classmethod
  def below(cls, distance=None):
    return RelativePosition(None, ("below", distance))

  @classmethod
  def left(cls, distance=None):
    return RelativePosition(("left", distance), None)

  @classmethod
  def right(cls, distance=None):
    return RelativePosition(("right", distance), None)

  @classmethod
  def above_left(cls, above_dist=None, left_dist=None):
    return RelativePosition(("left", left_dist), ("above", above_dist))

  @classmethod
  def below_left(cls, below_dist=None, left_dist=None):
    return RelativePosition(("left", left_dist), ("below", below_dist))

  @classmethod
  def above_right(cls, above_dist=None, right_dist=None):
    return RelativePosition(("right", right_dist), ("above", above_dist))

  @classmethod
  def below_right(cls, below_dist=None, right_dist=None):
    return RelativePosition(("right", right_dist), ("below", below_dist))

  @classmethod
  def from_str(cls, s):
    if " " in s:
      directions, distances = s.split(" ")
    else:
      directions, distances = s, None

    if "_" in directions:
      directions = directions.split("_")
      if distances is not None:
        distances = distances.split("_")
      else:
        distances = [None, None]
      if not directions[0] in ["above", "below"] or not directions[1] in ["left", "right"]:
        raise ValueError("Invalid relative position %s" % s)
      return RelativePosition((directions[1], distances[1]), (directions[0], distances[0]))
    if directions == "above":
      return RelativePosition.above(distances)
    if directions == "below":
      return RelativePosition.below(distances)
    if directions == "left":
      return RelativePosition.left(distances)
    if directions == "right":
      return RelativePosition.right(distances)
    raise ValueError("Invalid relative position %s" % s)

"""
A position is one of:
- An absolute coordinate
- (RelativePosition, index) # to refer to a node inside this list
- (RelativePosition, Node)
- (RelativePosition, NodeAnchor)
"""
class PositionSet(object):
  def __init__(self):
    self.items = []

  def add(self, item):
    if isinstance(item, list):
      for e in item:
        self.add(e)
    elif isinstance(item, str):
      try:
        coord = Coordinate.from_str(str)
        if coord.relative:
          raise ValueError("Coordinate should not be relative")
        self.items.append(coord)
        return self
      except:
        pass

      raise TypeError("invalid position string %s" % item)
    elif isinstance(item, Coordinate):
      if item.relative:
        raise ValueError("Coordinate should not be relative")
      self.items.append(item)
    elif isinstance(item, tuple):
      relative_position, target = item
      if isinstance(relative_position, str):
        relative_position = RelativePosition.from_str(relative_position)
      self.items.append((relative_position, target))
    return self

  @classmethod
  def from_short_repr(cls, existing=None, coords=None, lists=None):
    """
    Example:
    existing = [NodeA, NodeB.northeast()],
    coords = [(0,1), (1,2), (3,4)]
    lists = [
      ["right", -1, 3, 4],
      ["right", 0, 3, 4],
      ["below", 0, 5, 6],
      ["right", 5, 7, 8],
      ["right", 6, 9, 10, 11],
    ]
    existing nodes are indexed by negative indices, i.e., NodeA -> -2, NodeB -> -1
    The coord nodes are indexed starting from 0, i.e., (3,4) -> 0
    Each list must start from a used index,
    and the rest must be the next unused index
    """
    if existing is None and coords is None:
      raise ValueError("existing and coords cannot both be None")

    position_set = PositionSet()

    if coords is not None:
      for coord in coords:
        x, y = coord
        position_set.add(Coordinate(x, y))

    if lists is not None:
      for lst in lists:
        relative_position = lst[0]
        if isinstance(lst[0], str):
          relative_position = RelativePosition.from_str(lst[0])
        lst = lst[1:]
        if lst[0] >= len(position_set.items):
          raise ValueError("list does not start with used index: %s" % str(lst))
        for i in range(1, len(lst)):
          index = lst[i]
          if index != len(position_set.items):
            raise ValueError("each index should exactly be the next unused index: %d != %d in %s" % (index, len(position_set.items), str(lst)))
          target = lst[i-1]
          if target < 0:
            target = existing[target]
          position_set.add((relative_position, target))

    return position_set

class Canvas(object):
  def __init__(self):
    self.items = []
    self.handle_counter = 0
    self.builder = None
    self.position_set = None

  def next_handle(self):
    ret = "node%d" % self.handle_counter
    self.handle_counter += 1
    return ret

  def onslide(self, start, end=None):
    self.items.append(Onslide(start, end))
    return self

  def make_node(self):
    node = Node(self, self.next_handle())
    if self.builder is not None:
      self.builder.apply(node)
      self.builder = None

    self.items.append(node)
    return node

  def make_path(self):
    path = Path(self)
    if self.builder is not None:
      self.builder.apply(path)
      self.builder = None

    self.items.append(path)
    return path

  def ensure_builder(self):
    if self.builder is None:
      self.builder = Builder()
    return self.builder

  def with_property(self, key, value=None):
    self.ensure_builder().set(key, value)
    return self

  def without_property(self, key):
    self.ensure_builder().unset(key, value)
    return self

  def with_box(self, width, height):
    return self.with_property("minimum width", width).with_property("minimum height", height)

  def with_fill(self, fill):
    return self.with_property("fill", fill)

  def with_text(self, text):
    self.ensure_builder().set_text(text)
    return self

  def at_pos(self, pos):
    self.ensure_builder().set_pos(pos)
    return self

  def at_positions(self, position_set):
    self.position_set = position_set
    return self

  def at_positions_short(self, existing=None, coords=None, lists=None):
    self.position_set = PositionSet.from_short_repr(existing, coords, lists)
    return self

  def make_nodes_with_position_set(self, position_set):
    nodes = []
    for pos in self.position_set.items:
      node = Node(self, self.next_handle())
      if self.builder is not None:
        self.builder.apply(node)
      if isinstance(pos, Coordinate):
        node.set_pos(pos)
      elif isinstance(pos, tuple):
        relative_position, target = pos
        if isinstance(target, int):
          target = nodes[target]
        if isinstance(target, Node):
          key, value = relative_position.get_key_value(target.handle)
        elif isinstance(target, NodeAnchor):
          key, value = relative_position.get_key_value(target.dumps())
        node.set(key, value)
      nodes.append(node)
    return nodes

  def make_nodes(self):
    ret = self.make_nodes_with_position_set(self.position_set)
    self.position_set = None
    return ret

  def dumps(self):
    return "\n".join([item.dumps() for item in self.items])
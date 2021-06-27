from pylatex import *

class TextNode(TikZNode):
  def __init__(self, label, handle="", at=None, **kwargs):
    self.label=label
    self.handle=handle
    super(TextNode, self).__init__(text=label, handle=handle, at=at,
      options=TikZOptions(**kwargs))

class BoxNode(TikZNode):
  def __init__(self, label, handle="", width="2cm", height=None, fill='white', at=None, **kwargs):
    self.label=label
    self.handle=handle
    self.width=width
    if height == None:
      self.height = self.width
    else:
      self.height=height
    self.fill=fill
    super(BoxNode, self).__init__(text=label, handle=handle, at=at,
      options=TikZOptions('draw', fill=fill, align="center", **{"minimum width": self.width, "minimum height": self.height}, **kwargs))

class Arrow(TikZDraw):
  def __init__(self, src, dst, **kwargs):
    self.src=src
    self.dst=dst
    super(Arrow, self).__init__([src, '--', dst], TikZOptions('->', '-stealth', **kwargs))

def path_element_to_str(elem):
  if isinstance(elem, str):
    return str
  elif isinstance(elem, TikZCoordinate):
    return elem.dumps()
  elif isinstance(elem, tuple):
    return TikZCoordinate(*elem).dumps()
  elif isinstance(elem, TikZNode):
    return '({})'.format(elem.handle)
  elif isinstance(elem, TikZNodeAnchor):
    return elem.dumps()
  else:
    raise TypeError('Only str, tuple, TikZCoordinate,'
                    'TikZNode or TikZNodeAnchor types are allowed,'
                    ' got: {}'.format(type(point)))

def draw_arrow_text(pic, src, dst, text, *args, **kwargs):
  src, dst = path_element_to_str(src), path_element_to_str(dst)
  pic.append(NoEscape("%s %s -- %s %s;" % (
    Command("path", options=TikZOptions('->', '-stealth', 'draw', *args, **kwargs)).dumps(),
    src, "node[sloped, anchor=center, midway, above]{%s}" % text, dst
  )))

class Connect(TikZDraw):
  def __init__(self, src, dst):
    self.src=src
    self.dst=dst
    super(Connect, self).__init__([src, '--', dst])

def create_node_row(pic, elems, distance=None, left=None, right=None, above=None, below=None):
    for i in range(len(elems)):
      if elems[i].handle == "":
        elems[i].handle = "%d" % i
    if left is not None:
      elems[-1].options["left"] = left
      for i in range(len(elems)):
        if i < len(elems)-1 and "left" not in elems[i].options._key_value_args:
          s = "of %s" %(elems[i+1].handle)
          if distance is not None:
            s = "%s %s" % (distance, s)
          elems[i].options._key_value_args["left"] = s
    else:
      for i in range(len(elems)):
        if i > 0 and "right" not in elems[i].options._key_value_args:
          s = "of %s" %(elems[i-1].handle)
          if distance is not None:
            s = "%s %s" % (distance, s)
          elems[i].options._key_value_args["right"] = s
      if right is not None:
        elems[0].options._key_value_args["right"] = right
      if above is not None:
        elems[0].options._key_value_args["above"] = above
      if below is not None:
        elems[0].options._key_value_args["below"] = below
    for elem in elems:
      pic.append(elem)
from contextlib import contextmanager
from pylatex import *
from pylatex.utils import *
from pylatex.base_classes import Environment, Arguments, Options
from .canvas import *

@contextmanager
def create_canvas(pic):
  canvas = Canvas()
  yield canvas
  pic.append(NoEscape(canvas.dumps()))

class CommonEnvironmentWithUtility(Environment):
  def vspace(self, height="0.5cm"):
    self.append(Command("vspace", arguments=[height]))

  def hspace(self, width="1cm"):
    self.append(Command("hspace", arguments=[width]))

  def breakline(self):
    self.append(NoEscape("\n"))

  def pause(self):
    self.append(Command("pause"))

  def onslide(self, start, end=None):
    if start == end:
      self.append(Command("onslide<%d>" % start))
    elif end is None:
      self.append(Command("onslide<%d->" % start))
    else:
      self.append(Command("onslide<%d-%d>" % (start, end)))

  def open_onslide(self, start, end=None):
    self.onslide(start, end)
    self.append(NoEscape("{"))

  def close_onslide(self):
    self.append(NoEscape("}"))

  @contextmanager
  def tikz(self, *, node_distance=None):
    options = {}
    if node_distance is not None:
      options["node distance"] = node_distance
    with self.create(TikZ(options=Options(**options))) as tikz:
      yield tikz

  @contextmanager
  def columns(self, widths):
    with self.create(Columns(widths)) as columns:
      yield columns

  def center(self):
    self.append(Command("centering"))

class Frame(CommonEnvironmentWithUtility):
  def __init__(self, *, title=None, options=None, **kwargs):
    super(Frame, self).__init__(**kwargs)
    if title is not None:
      self.append(Command("frametitle", arguments=[title]))

class Column(CommonEnvironmentWithUtility):
  def __init__(self, width, **kwargs):
    self.width=width
    super(Column, self).__init__(arguments=Arguments(NoEscape('%g\\textwidth' % width)), **kwargs)

class Columns(Environment):
  def __init__(self, widths=None, **kwargs):
    self.widths=widths
    super(Columns, self).__init__(**kwargs)
    if widths is None:
      widths = [0.5, 0.5]
    if not isinstance(widths, list):
      print("widths is not list")
      raise
    s = sum(widths)
    if s > 1.1:
      print("columns too wide")
      raise

    self.columns = []
    for w in widths:
      with self.create(Column(w)) as c:
        self.columns.append(c)

class Beamer(object):
  """docstring for Beamer"""
  def __init__(self,
      title,
      author=None,
      date=None,
      outline_each_section=False,
      default_filepath=None,
      theme="default",
      color_theme="orchid",
      inner_theme="rounded",
      disable_pauses=False):

    options = []
    if disable_pauses:
      options.append("handout")
    self.doc = Document(documentclass="beamer", document_options=options, default_filepath=default_filepath)
    self.doc.preamble.append(Command("usetheme", arguments=[theme]))
    if color_theme is not None:
      self.doc.preamble.append(Command("usecolortheme", arguments=[color_theme]))
    if inner_theme is not None:
      self.doc.preamble.append(Command("useinnertheme", arguments=[inner_theme]))
    self.doc.packages.append(Package("tikz"))
    self.doc.preamble.append(Command("usetikzlibrary", arguments=["positioning"]))
    self.doc.preamble.append(Command("usetikzlibrary", arguments=["shapes.geometric"]))
    if outline_each_section:
      self.doc.preamble.append(NoEscape("""
\\AtBeginSection[]
{
    \\begin{frame}
        \\frametitle{Outline}
        \\tableofcontents[currentsection]
    \\end{frame}
}
        """))
    self.doc.preamble.append(Command("title", arguments=[title]))
    if author is not None:
      self.doc.preamble.append(Command("author", arguments=[author]))
    if date is not None:
      self.doc.preamble.append(Command("date", arguments=[date]))

  @contextmanager
  def section(self, title):
    with self.doc.create(Section(title)) as section:
      yield section

  @contextmanager
  def subsection(self, title):
    with self.doc.create(Subsection(title)) as subsection:
      yield subsection

  @contextmanager
  def frame(self, title=None):
    with self.doc.create(Frame(title=title)) as frame:
      yield frame

  def titleframe(self):
    with self.frame() as frame:
      frame.append(Command("maketitle"))

  def outlineframe(self, title="Outline"):
    with self.frame(title) as frame:
      frame.append(Command("tableofcontents"))

  def qaframe(self):
    with self.frame() as frame:
      frame.append(Command("huge"))
      frame.append(Command("center"))
      frame.append("Q&A")

  def generate_tex(self, filepath="default_path"):
    self.doc.generate_tex(filepath)

  def generate_pdf(self, filepath="default_path", compiler=None, clean_tex=True):
    self.doc.generate_pdf(filepath, compiler=compiler, clean_tex=clean_tex)

if __name__ == '__main__':
  beamer = Beamer("Example", author="author", outline_each_section=True)
  beamer.titleframe()
  beamer.outlineframe()
  with beamer.section("First Section"):
    with beamer.frame("First Page") as frame:
      frame.append("Hello")
  beamer.generate_pdf()
  beamer.generate_tex()
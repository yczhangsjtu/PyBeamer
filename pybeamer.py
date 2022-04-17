from contextlib import contextmanager
from pylatex import *
from pylatex.utils import *
from pylatex.base_classes import Environment, Arguments, Options
from pylatex.base_classes.containers import Fragment as _Fragment
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

  def hline(self):
    self.append(NoEscape(
        "\\noindent\\makebox[\\linewidth]{\\rule{\\textwidth}{0.4pt}}"))

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

  def image(self, name):
    fig = Figure()
    fig.add_image(name)
    self.append(fig)

  @contextmanager
  def itemize(self):
    with self.create(Itemize()) as itemize:
      yield itemize

  @contextmanager
  def enum(self):
    with self.create(BeamerEnumerate()) as enum:
      yield enum

  @contextmanager
  def block(self, title):
    with self.create(Block(arguments=[title])) as block:
      yield block

  @contextmanager
  def eqnarray(self, numbering=False):
    with self.create(Eqnarray(numbering)) as array:
      yield array


class BeamerEnumerate(Enumerate, CommonEnvironmentWithUtility):
  _latex_name = "enumerate"
  pass


class Eqnarray(CommonEnvironmentWithUtility):
  def __init__(self, numbering=False, *, options=None, **kwargs):
    super().__init__(options=options, **kwargs)
    self.numbering = numbering
    self.empty = True

  def add_line(self, line):
    if not self.empty:
      self.append(NoEscape("\\\\\n"))
    self.empty = False
    self.append(NoEscape(line))
    if not self.numbering:
      self.append(NoEscape("\\nonumber"))


class Block(CommonEnvironmentWithUtility):
  def __init__(self, *, options=None, **kwargs):
    super(Block, self).__init__(options=options, **kwargs)


class Frame(CommonEnvironmentWithUtility):
  def __init__(self, *, title=None, options=None, **kwargs):
    super(Frame, self).__init__(options=options, **kwargs)
    if title is not None:
      self.append(Command("frametitle", arguments=[title]))


class Column(CommonEnvironmentWithUtility):
  def __init__(self, width, **kwargs):
    self.width = width
    super(Column, self).__init__(arguments=Arguments(
        NoEscape('%g\\textwidth' % width)), **kwargs)


class Columns(Environment):
  def __init__(self, widths=None, **kwargs):
    self.widths = widths
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


class Fragment(_Fragment, CommonEnvironmentWithUtility):
  @contextmanager
  def frame(self, title=None):
    with self.create(Frame(title=title)) as frame:
      yield frame


class CJK(Environment):
  _latex_name = "CJK*"

  def __init__(self, doc, *, options=None, **kwargs):
    super().__init__(arguments=["UTF8", "gbsn"], options=options, **kwargs)
    self.doc = doc

  def __getattr__(self, name):
    return getattr(self.doc, name)


class Beamer(object):
  """docstring for Beamer"""

  def __init__(self,
               title,
               subtitle=None,
               author=None,
               institute=None,
               date=None,
               outline_each_section=False,
               outline_each_subsection=False,
               page_number=True,
               default_filepath=None,
               theme="default",
               color_theme="orchid",
               inner_theme="rounded",
               has_chinese=False,
               font_theme=None,
               main_font=None,
               math_theme=None,
               disable_pauses=False):

    options = []
    if disable_pauses:
      options.append("handout")
    self.doc = Document(documentclass="beamer",
                        document_options=options, default_filepath=default_filepath)
    if page_number:
      self.doc.preamble.append(
          NoEscape(r"\setbeamertemplate{footline}[frame number]"))
    self.doc.preamble.append(Command("usetheme", arguments=[theme]))
    self.doc.packages.append(Package("tikz"))
    self.doc.packages.append(Package("ulem"))
    self.doc.packages.append(Package("bbm"))
    self.doc.packages.append(Package("xcolor"))
    if has_chinese:
      self.doc.preamble.append(Package("CJKutf8"))
    if color_theme is not None:
      self.doc.preamble.append(
          Command("usecolortheme", arguments=[color_theme]))
    if inner_theme is not None:
      self.doc.preamble.append(
          Command("useinnertheme", arguments=[inner_theme]))
    if font_theme is not None:
      self.doc.preamble.append(Command("usefonttheme", arguments=[font_theme]))
    if main_font is not None:
      if main_font in ["bookman", "helvet", "chancery", "charter", "mathptm"]:
        self.doc.packages.append(Package(main_font))
      else:
        self.doc.packages.append(Package("fontspec"))
        self.doc.preamble.append(Command("setmainfont", arguments=[main_font]))
    if math_theme is not None:
      self.doc.preamble.append(Command("usefonttheme", options=[
                               "onlymath"], arguments=[math_theme]))
    self.doc.preamble.append(Command("definecolor", arguments=[
                             "olive", "rgb", "0.3, 0.4, .1"]))
    self.doc.preamble.append(
        Command("definecolor", arguments=["fore", "RGB", "249,242,215"]))
    self.doc.preamble.append(
        Command("definecolor", arguments=["back", "RGB", "51,51,51"]))
    self.doc.preamble.append(
        Command("definecolor", arguments=["title", "RGB", "255,0,90"]))
    self.doc.preamble.append(
        Command("definecolor", arguments=["dgreen", "rgb", "0.,0.6,0."]))
    self.doc.preamble.append(
        Command("definecolor", arguments=["gold", "rgb", "1.,0.84,0."]))
    self.doc.preamble.append(Command("definecolor", arguments=[
                             "JungleGreen", "cmyk", "0.99,0,0.52,0"]))
    self.doc.preamble.append(Command("definecolor", arguments=[
                             "BlueGreen", "cmyk", "0.85,0,0.33,0"]))
    self.doc.preamble.append(Command("definecolor", arguments=[
                             "RawSienna", "cmyk", "0,0.72,1,0.45"]))
    self.doc.preamble.append(
        Command("definecolor", arguments=["Magenta", "cmyk", "0,1,0,0"]))
    self.doc.preamble.append(
        Command("usetikzlibrary", arguments=["positioning"]))
    self.doc.preamble.append(Command("usetikzlibrary", arguments=["shapes"]))
    self.doc.preamble.append(
        Command("usetikzlibrary", arguments=["shapes.geometric"]))
    self.doc.preamble.append(
        Command("usetikzlibrary", arguments=["decorations.pathreplacing"]))
    self.doc.preamble.append(
        Command("usetikzlibrary", arguments=["decorations.text"]))
    self.doc.preamble.append(NoEscape("""
\\newcommand{\\blue}[1]{\\textcolor{blue}{#1}}
\\newcommand{\\green}[1]{\\textcolor{green}{#1}}
\\newcommand{\\dgreen}[1]{\\textcolor{dgreen}{#1}}
\\newcommand{\\orange}[1]{\\textcolor{orange}{#1}}
\\newcommand{\\red}[1]{\\textcolor{red}{#1}}
\\newcommand{\\purple}[1]{\\textcolor{purple}{#1}}
\\newcommand{\\olive}[1]{\\textcolor{olive}{#1}}
        """))
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
    if outline_each_subsection:
      self.doc.preamble.append(NoEscape("""
\\AtBeginSubsection[]
{
    \\begin{frame}
        \\frametitle{Outline}
        \\tableofcontents[currentsection,currentsubsection]
    \\end{frame}
}
        """))
    self.doc.preamble.append(Command("title", arguments=[title]))
    if subtitle is not None:
      self.doc.preamble.append(Command("subtitle", arguments=[subtitle]))
    if author is not None:
      self.doc.preamble.append(Command("author", arguments=[NoEscape(author)]))
    if institute is not None:
      if isinstance(institute, str):
        self.doc.preamble.append(
            Command("institute", arguments=[NoEscape(institute)]))
      elif isinstance(institute, list):
        self.doc.preamble.append(Command("institute", arguments=[
                                 NoEscape(" \\and ".join(institute))]))
    if date is not None:
      self.doc.preamble.append(Command("date", arguments=[date]))
    if has_chinese:
      with self.doc.create(CJK(self.doc)) as cjk:
        self.doc = cjk

  @contextmanager
  def section(self, title, label=True):
    with self.doc.create(Section(title, label=label)) as section:
      yield section

  @contextmanager
  def subsection(self, title, label=True):
    with self.doc.create(Subsection(title, label=label)) as subsection:
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

  def append(self, content):
    self.doc.append(content)


if __name__ == '__main__':
  beamer = Beamer("Example", author="author", outline_each_section=True)
  beamer.titleframe()
  beamer.outlineframe()
  with beamer.section("First Section"):
    with beamer.frame("First Page") as frame:
      frame.append("Hello")
  beamer.generate_pdf()
  beamer.generate_tex()

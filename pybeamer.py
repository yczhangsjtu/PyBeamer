from contextlib import contextmanager
from pylatex import Document, Section, Subsection, Command
from pylatex.base_classes import Environment

class Frame(Environment):
  def __init__(self, *, title=None, options=None, **kwargs):
    super(Frame, self).__init__(**kwargs)
    if title is not None:
      self.append(Command("frametitle", arguments=[title]))

class Beamer(object):
  """docstring for Beamer"""
  def __init__(self,
      title,
      author=None,
      date=None,
      theme="default",
      color_theme="orchid",
      inner_theme="rounded",
      disable_pauses=False):
    options = []
    if disable_pauses:
      options.append("handout")
    self.doc = Document(documentclass="beamer", document_options=options)
    self.doc.preamble.append(Command("usetheme", arguments=[theme]))
    if color_theme is not None:
      self.doc.preamble.append(Command("usecolortheme", arguments=[color_theme]))
    if inner_theme is not None:
      self.doc.preamble.append(Command("useinnertheme", arguments=[inner_theme]))
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

  def generate_tex(self, filepath=None):
    self.doc.generate_tex(filepath)

  def generate_pdf(self, filepath=None, compiler=None):
    self.doc.generate_pdf(filepath, compiler=compiler)

if __name__ == '__main__':
  beamer = Beamer("Example", author="author")
  beamer.titleframe()
  beamer.outlineframe()
  with beamer.section("First Section"):
    with beamer.frame("First Page") as frame:
      frame.append("Hello")
  beamer.generate_pdf()
  beamer.generate_tex()
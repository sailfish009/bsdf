""" Module to generate the website / docs from the markdown in this repo.
"""

import os

import markdown
import pygments
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

# Get root directory of the package
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Page:
    """ Representation of a doc page. It takes in markdown, and can produce
    HTML or RTS (with raw html pieces).
    """
    
    def __init__(self, name, markdown):
        self.name = name
        self.md = markdown
        self.parts = []
        self.headers = []
        self.is_implementation = False
    
    def prepare(self, pages):
        # Convert markdown to HTML
        self.md = self._fix_links(self.md, pages.keys())
        self.md = self._highlight(self.md)
        self._split()  # populates self.parts and self.headers
        
    def _fix_links(self, text, page_names):
        """ Fix the markdown links based on the pages that we know.
        """
        base_url = 'http://gitlab.com/almarklein/bsdf/tree/master/'
        text = text.replace('](bsdf.', '](%s%s/bsdf.' % (base_url, self.name))
        for n in page_names:
            text = text.replace('](%s)' % n, '](%s.html)' % n)
            text = text.replace('](%s.md)' % n.upper(), '](%s.html)' % n)
            text = text.replace('](%s/' % n, '](%s%s/' % (base_url, n))
        return text
    
    def _highlight(self, text):
        """ Apply syntax highlighting.
        """
        lines = []
        code = []
        for i, line in enumerate(text.splitlines()):
            if line.startswith('```'):
                if code:
                    formatter = HtmlFormatter()
                    try:
                        lexer = get_lexer_by_name(code[0])
                    except Exception:
                        lexer = get_lexer_by_name('text')
                    lines.append(pygments.highlight('\n'.join(code[1:]), lexer, formatter))
                    code = []
                else:
                    code.append(line[3:].strip())  # language
            elif code:
                code.append(line)
            else:
                lines.append(line)
        return '\n'.join(lines).strip()
    
    def _split(self):
        """ Split the markdown into parts based on sections.
        Each part is either text or a tuple representing a section.
        """
        text = self.md
        self.parts = parts = []
        self.headers = headers = []
        lines = []
        
        # Split in parts
        for line in text.splitlines():
            if line.startswith(('# ', '## ', '### ', '#### ', '##### ')):
                # Finish pending lines
                parts.append('\n'.join(lines))
                lines = []
                # Process header
                level = len(line.split(' ')[0])
                title = line.split(' ', 1)[1]
                headers.append((level, title))
                parts.append((level, title))
            else:
                lines.append(line)
        parts.append('\n'.join(lines))
        
        # Now convert all text to html
        for i in range(len(parts)):
            if not isinstance(parts[i], tuple):
                parts[i] = markdown.markdown(parts[i], extensions=[]) + '\n\n'
    
    def to_html(self):
        htmlparts = []
        for part in self.parts:
            if isinstance(part, tuple):
                level, header = part
                title = header.split('(')[0].strip().lower()  # short header
                if part[0] == 2 and title:
                    htmlparts.append("<a class='anch' name='{}' href='#{}'>".format(title, title))
                    htmlparts.append('<h%i>%s</h%i>' % (level, header, level))
                    htmlparts.append('</a>')
                else:
                    htmlparts.append('<h%i>%s</h%i>' % (level, header, level))
            else:
                htmlparts.append(part)
        return '\n'.join(htmlparts)

    def to_rst(self):
        rstparts = []
        for part in self.parts:
            if isinstance(part, tuple):
                level, header = part
                char = '==-~"'[level]
                if level == 1:
                    rstparts.append(char * len(header))
                rstparts.append(header)
                rstparts.append(char * len(header))
            elif part.strip():
                rstparts.append('.. raw:: html\n')
                for line in part.splitlines():
                    rstparts.append('    ' + line)
        return '\n'.join(rstparts)


def build(pages=True, rst=False):
    """ Build the pages.
    """
    
    # Create directory if needed
    pages_dir = os.path.join(ROOT_DIR, '_docs', '_pages')
    rst_dir = os.path.join(ROOT_DIR, '_docs')  # or Sphinx wont get it
    if not os.path.isdir(pages_dir):
        os.makedirs(pages_dir)
    
    # Clear
    for fname in os.listdir(pages_dir):
        filename = os.path.join(pages_dir, fname)
        if os.path.isfile(filename):
            os.remove(filename)
    for fname in os.listdir(rst_dir):
        if fname.endswith(('.rst', )):
            filename = os.path.join(pages_dir, fname)
            if os.path.isfile(filename):
                os.remove(filename)

    # Collect markdown pages
    pages = {}
    for fname in os.listdir(ROOT_DIR):
        if fname.endswith('.md'):
            name = fname.split('.')[0].lower()
            filename = os.path.join(ROOT_DIR, fname)
        else:
            name = fname.lower()
            filename = os.path.join(ROOT_DIR, fname, 'README.md')
        if not os.path.isfile(filename) or ' ' in name or name.startswith('_'):
            continue
        name = 'index' if name == 'readme' else name  # Some names need replacing
        pages[name] = Page(name, open(filename, 'rb').read().decode())
        pages[name].is_implementation = '.' not in fname
        del name
        
    
    # Prepare html and generate menu
    menus = {}
    for page in list(pages.values()):
        page.prepare(pages)
        # Build menu
        menu = []
        for is_imp in (False, True):
            menu.append('<hr>' if is_imp else '')
            for pagename in sorted(pages, key=lambda n: (n!='index', n)):
                if is_imp != pages[pagename].is_implementation:
                    continue
                pagenamestr = pagename  #.capitalize() if not is_imp else pagename
                menu.append("<a href='{}.html'>{}</a>".format(pagename, 'BSDF' if pagename == 'index' else pagenamestr))
                if pagename == page.name:
                    menu += ["&nbsp;&nbsp;&nbsp;<a href='#{}'>{}</a>".format(title, title)
                             for level, title in page.headers if level == 2]
            menu.append('')
        menu.append('<hr>')
        menu.append("<a href='http://gitlab.com/almarklein/bsdf'>Source at Gitlab</a>")
        menus[page.name] = '<br />'.join(menu)
    
    # Generate pages
    for page in pages.values():
        
        # HTML
        if pages:
            title = 'BSDF' if page.name == 'index' else 'BSDF - ' + page.name
            css = RESET_CSS + PYGMENTS_CSS + BSDF_CSS
            html = HTML_TEMPLATE.format(title=title, style=css, body=page.to_html(), menu=menus[page.name])
            filename2 = os.path.join(pages_dir, page.name + '.html')
            print('generating', filename2)
            with open(filename2, 'wb') as f:
                f.write(html.encode())
        
        # RST
        if rst:
            toc = ''
            if page.name == 'index':
                toc = 'Contents\n--------\n\n.. toctree::\n    :maxdepth: 1\n\n'
                for p in sorted(pages.values(), key=lambda p: (p.is_implementation, p.name)):
                    if p.name != 'index':
                        toc += '    %s\n' % p.name
            filename3 = os.path.join(rst_dir, page.name + '.rst')
            print('generating', filename3)
            with open(filename3, 'wb') as f:
                f.write('.. autogenerated; no not edit!\n\n'.encode())
                f.write(page.to_rst().encode())
                f.write(('\n\n' + toc + '\n\n').encode())


# The rest are just some strings / templates for the website build task ...

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<title>{title}</title>
<meta charset="utf-8">
<style>
{style}
</style>
</head>
<body>
<div class='menu'>
{menu}
<br /><br />
<a href="https://gitlab.com/almarklein/bsdf/pipelines">
<img alt="pipeline status" src="https://gitlab.com/almarklein/bsdf/badges/master/pipeline.svg" />
</a>
</div>
<div class='content'>
{body}
<hr />
<div class='footer'>© Copyright 2017, Almar Klein -
the text on this page is licensed under <a href='https://creativecommons.org/licenses/by/4.0/'>CC BY 4.0</a>
</div>
</div>
</body>
</html>
"""

BSDF_CSS = """
/* BSDF CSS */
body {
    background: #ace;
}
.content {
    box-sizing: border-box;
    margin: 1em auto;
    padding: 1em 2em;
    width: 100%;
    max-width: 700px;
    background: #fff;
    border-radius: 0.5em;
    box-shadow: 4px 4px 16px rgba(0, 0, 0, 0.5);
}
@media screen and (max-width:  1000px) { /* some browser dont trigger for smaller numbers */
    .content { max-width: 100%; margin:0; }
}
.menu {
    box-sizing: border-box;
    position: fixed;
    top: 1em;
    right: calc(50% + 350px + 10px);
    padding: 0.5em 1em;
    width: 240px;
    max-width: 240px;
    background: #fff;
    border-radius: 0.5em;
    box-shadow: 4px 4px 16px rgba(0, 0, 0, 0.5);
    overflow: hidden;
    white-space: nowrap;
}
@media screen and (max-width: 1200px) {
    .menu { display: none;}
}
a:link, a:visited, a:active {
    color: #48C;
    text-decoration: none;
}
a:hover {
    text-decoration: underline;
}
.menu a {
    color: #246;
}
a.anch:hover {
    text-decoration: none;
}
a.anch:hover h2::after {
    content: " \\00B6";
    color: rgba(0, 0, 0, 0.3);
    font-size: 80%;
}
hr {
    border: 1px solid #ace;
}
.footer {
    color: #777;
    font-size: 90%;
}
code {
    font-family: dejavu sans mono, mono, monospace;
    font-weight: bold;
    font-size: 90%;
    color: #444;
    background: #fff;
    padding-left: 0.2em;
    padding-right: 0.2em;
}
.highlight {  /*pygments */
    font-family: dejavu sans mono, mono, monospace;
    font-size: 12px;
    color: #444;
    background: #ddeeff;
    border: 1px solid #ace;
    padding: 0em 1em;
    border-radius: 0.2em;
 }
h1, h2, h3, h4 {
    color: #246;
}
h2 {
    border-bottom: 1px solid #ace;
}
h3 code, h4 code {
    color: #246;
    padding-left: 0;
}
"""

RESET_CSS = """
/*! normalize.css v3.0.3 | MIT License | github.com/necolas/normalize.css */
html
{font-family:sans-serif;}
body{margin:0}
article,aside,details,figcaption,figure,footer,header,hgroup,main,menu,nav,
section,summary{display:block}
audio,canvas,progress,video{display:inline-block;vertical-align:baseline}
audio:not([controls]){display:none;height:0}
[hidden],template{display:none}
a{background-color:transparent}
a:active,a:hover{outline:0}
abbr[title]{border-bottom:1px dotted}
b,strong{font-weight:bold}
dfn{font-style:italic}
h1{font-size:2em;margin:.67em 0}
mark{background:#ff0;color:#000}
small{font-size:80%}
sub,sup{font-size:75%;line-height:0;position:relative;vertical-align:baseline}
sup{top:-0.5em}
sub{bottom:-0.25em}
img{border:0}
svg:not(:root){overflow:hidden}
figure{margin:1em 40px}
hr{box-sizing:content-box;height:0}
pre{overflow:auto}
code,kbd,pre,samp{font-family:monospace,monospace;font-size:1em}
button,input,optgroup,select,textarea{color:inherit;font:inherit;margin:0}
button{overflow:visible}
button,select{text-transform:none}
button,html input[type="button"],input[type="reset"],input[type="submit"]
{-webkit-appearance:button;cursor:pointer}
button[disabled],html input[disabled]{cursor:default}
button::-moz-focus-inner,input::-moz-focus-inner{border:0;padding:0}
input{line-height:normal}
input[type="checkbox"],input[type="radio"]{box-sizing:border-box;padding:0}
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button{height:auto}
input[type="search"]{-webkit-appearance:textfield;box-sizing:content-box}
input[type="search"]::-webkit-search-cancel-button,
input[type="search"]::-webkit-search-decoration{-webkit-appearance:none}
fieldset{border:1px solid #c0c0c0;margin:0 2px;padding:.35em .625em .75em}
legend{border:0;padding:0}
textarea{overflow:auto}
optgroup{font-weight:bold}
table{border-collapse:collapse;border-spacing:0}
td,th{padding:0}
""".lstrip()

PYGMENTS_CSS = '/* Pygments CSS */\n' + HtmlFormatter(style='vs').get_style_defs('.highlight')

if __name__ == '__main__':
    build()

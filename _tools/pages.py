""" Module to generate the website / docs from the markdown in this repo.
"""

import os

import markdown
import pygments
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

# Get root directory of the package
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build():
    """ Build the pages.
    """
    
    # Create directory if needed
    pages_dir = os.path.join(ROOT_DIR, '_pages')
    if not os.path.isdir(pages_dir):
        os.makedirs(pages_dir)
    
    # Clear it
    for fname in os.listdir(pages_dir):
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
        pages[name] = open(filename, 'rb').read().decode('utf-8')
    
    # Convert to html
    for name, text in list(pages.items()):
        # Insert back button
        if name != 'index':
            text = "<a class='badge' href='index.html'>&lt;&lt;</a>\n\n" + text
        # To markdown
        text = fix_links(text, name, pages.keys())
        text = highlight(text)
        text = add_anchors(text)
        pages[name] = markdown.markdown(text, extensions=[])
    
    # Generate pages
    for name, text in pages.items():
        title = 'BSDF' if name == 'index' else 'BSDF - ' + name
        css = RESET_CSS + PYGMENTS_CSS + BSDF_CSS
        html = HTML_TEMPLATE.format(title=title, style=css, body=text)
        filename2 = os.path.join(pages_dir, name + '.html')
        with open(filename2, 'wb') as f:
            f.write(html.encode('utf-8'))


def fix_links(text, name, page_names):
    """ Fix the markdown links based on the pages that we know.
    """
    base_url = 'http://gitlab.com/almarklein/bsdf/tree/master/'
    text = text.replace('](bsdf.', '](%s%s/bsdf.' % (base_url, name))
    for n in page_names:
        text = text.replace('](%s)' % n, '](%s.html)' % n)
        text = text.replace('](%s.md)' % n.upper(), '](%s.html)' % n)
        text = text.replace('](%s/' % n, '](%s%s/' % (base_url, n))
    return text


def add_anchors(text):
    """ Turn h2 heads into anchors.
    """
    lines = []
    for i, line in enumerate(text.splitlines()):
        if line.startswith('## '):
            title = line[3:].split('(')[0].strip().lower()
            if title:
                lines.append("<a class='anch' name='{}' href='#{}'>".format(title, title))
                lines.append(line)
                lines.append('</a>')
                continue
        lines.append(line)
    return '\n'.join(lines)


def highlight(text):
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

# The rest are just some strings / templates for the website build task ...

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <meta charset="utf-8">
</head>
<body>
<style>
{style}
</style>
{body}
<hr />
<div class='footer'>© Copyright 2017, Almar Klein - BSDF lives on <a href='http://gitlab.com/almarklein/bsdf'>GitLab</a> </div>
</body>
</html>
"""

BSDF_CSS = """
/* BSDF CSS */
html {
    background: #ace;
}
body {
    margin: 1em auto 1em auto;
    padding: 1em 2em 1em 2em;
    max-width: 640px;
    background: #fff;
    border-radius: 0.5em;
    box-shadow: 4px 4px 16px rgba(0, 0, 0, 0.5);
}
a:link, a:visited, a:active {
    color: #48C;
    text-decoration: none;
}
a:hover {
    text-decoration: underline;
}
a.anch:hover {
    text-decoration: none;
}
a.anch:hover h2::after {
    content: " \\00B6";
    color: rgba(0, 0, 0, 0.3);
    font-size: 80%;
}

a.badge {
    margin: 0;
    padding: 0.1em 0.3em 0.1em 0.3em;
    border-radius: 0.2em;
    font-weight: bold;
    color: #246;
    font-size: 90%;
    background: #ace;
}
a.badge:hover {
    text-decoration: none;
    color: #000;
}
span.badge_sep {
    display: none;
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
    background: #def;
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
{font-family:sans-serif;-ms-text-size-adjust:100%;-webkit-text-size-adjust:100%}
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

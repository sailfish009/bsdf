""" Script that defines (and collects from subdirs) tasks for invoke. 
"""

import os
import sys
import subprocess

from invoke import Collection, Task, task


# Get root directory of the package
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Init collection; invoke picks this up as the main "list of tasks"
ns = Collection()

# Collect tasks from sub directories
for dname in os.listdir(ROOT_DIR):
    filename = os.path.join(ROOT_DIR, dname, 'tasks.py')
    if not os.path.isfile(filename):
        continue
    
    # Load the module, simulate importing it
    os.chdir(os.path.join(ROOT_DIR, dname))
    module = {'__file__': filename, '__name__': 'tasks'}
    exec(open(filename, 'rb').read().decode(), module)
    os.chdir(ROOT_DIR)
    
    # Add all tasks from this subdir
    collection = Collection()
    ns.add_collection(collection, dname.replace('_', '-'))
    for ob in module.values():
        if isinstance(ob, Task):
            collection.add_task(ob)
        elif isinstance(ob, Collection):
            ns.add_collection(ob)


# Implement collection default messages, without creating an actual task for it
if len(sys.argv) == 2 and sys.argv[1] in ns.collections.keys():
    lines = subprocess.getoutput(['invoke', '-l']).splitlines()
    lines = [line for line in lines if line.strip().startswith(sys.argv[1] + '.')]
    print('Task {} is a category with available tasks:\n'.format(sys.argv[1]))
    print('\n'.join(lines))
    sys.exit(1)

# Add root tasks ...

@ns.add_task
@task(default=True)
def help(ctx):
    """ Get help on BSDF's development workflow. """
    
    print("""BSDF development workflow
    
    BSDF uses the "invoke" utility to make it easy to invoke tasks such
    as tests. Invoke is a Python utility, so the tasks are defined in
    Python, but most tasks consist of a specific CLI command.
    
    You can cd into each sub directory and use invoke to execute tasks specific
    for that subdir. Use "invoke -l" to get a list of available tasks.
    
    Alternatively, you can use invoke from the root directory in which case
    each task is prefixed with the subdir's name.
    
    Get started by typing "invoke -l".
    """)

@ns.add_task
@task
def build_pages(ctx, show=False):
    """ Build the BSDF website from the markdown files. """
    import markdown
    
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
        # Fix links
        base_url = 'http://gitlab.com/almarklein/bsdf/tree/master/'
        text = text.replace('](bsdf.', '](%s%s/bsdf.' % (base_url, name))
        for n in pages:
            text = text.replace('](%s)' % n, '](%s.html)' % n)
            text = text.replace('](%s.md)' % n.upper(), '](%s.html)' % n)
            text = text.replace('](%s/' % n, '](%s%s/' % (base_url, n))
        # Insert back button
        if name != 'index':
            text = "<a class='badge' href='index.html'>&lt;&lt;</a>\n\n" + text
        # To markdown
        pages[name] = markdown.markdown(text, extensions=[])
    
    # Generate pages
    for name, text in pages.items():
        title = 'BSDF' if name == 'index' else 'BSDF - ' + name
        html = HTML_TEMPLATE.format(title=title, style=RESET + STYLE, body=text)
        filename2 = os.path.join(pages_dir, name + '.html')
        with open(filename2, 'wb') as f:
            f.write(html.encode('utf-8'))
    
    if show:
        import webbrowser
        webbrowser.open(pages_dir + '/index.html')

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

STYLE = """
html {
    background: #ace;
}

body {
    margin: 1em auto 1em auto;
    padding: 1em 2em 1em 2em;
    max-width: 600px;
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

a.badge {
    margin: 0;
    padding: 0.1em 0.3em 0.1em 0.3em;
    border-radius: 0.2em;
    color: #fff;
    font-size: 90%;
    background: #246;
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

RESET = """
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

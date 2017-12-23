# Comparing BSDF with other formats

The question that arises with any new format:
*Why, oh Why? Why yet another format!?*

In short, there was no format that could serialize nd-array data well,
and also work well on the web. The realization that HDF5 is not so great,
a strong need to send scientific data between Python and JavaScript, and
a repeated annoyance with JSON has nudged me to create BSDF.

This page tries to compares BSDF with other formats, and explains
why these formats were in my view insufficient for my needs.


## BSDF vs JSON

Although [JSON](http://www.json.org/) is very widely used, it has several limitations:

* JSON's inability to encode `nan` and `inf` can be painful.
* No support for binary data or nd-arrays (base64 is a compromise worth avoiding).
* It's kind of human readable, but very verbose, and not easy to write
  (e.g. a comma after the last item in a list breaks things).
* Many JSON implementations allow extending the types, but this involves
  an extra function call for each element, which degrades the performance.


## BSDF vs UBJSON et al.

Binary formats commonly used on the web that were considered are
[ubjson](http://ubjson.org/), [msgpack](http://msgpack.org/), [bson](http://bsonspec.org/).
Most are rather web-oriented, or adhere strictly to JSON compatibility (e.g.
no `nan`). Most do not support typed arrays, let alone nd-arrays, and/or
decode such arrays in JavaScript as regular arrays instead of array
buffers. In short; none of these seemed to provide the flexibility that
a scientific data format needs.

BSDF differs from most of them by its flexibility for encoding binary data,
and its simple extension mechanism.

It's worth noting that BSDF does not support typed arrays as one of its base
types, but the extension for typed nd-arrays is a standard extension available
in most implementations.


## BSDF vs HDF5

[HDF5](https://en.wikipedia.org/wiki/Hierarchical_Data_Format) is a popular format for
scientific data, but there are also good reasons to avoid it, as e.g. explained the
[paper on ASDF](http://linkinghub.elsevier.com/retrieve/pii/S2213133715000645)
and this [blog post](http://cyrille.rossant.net/should-you-use-hdf5/).
Summarizing:

* HDF5 is a complex specification and (therefore) there is really just one
  implementation that actually works.
* The implementation sometimes has bugs or performance issue, but there
  are no alternatives.
* Not human readable, and no other tools for inspection except that one
  implementation.
* No proper mappings (dicts) and lists.

HDF5 is certainly more flexible, e.g. with regard to providing lazy
loading parts of compressed data. However, BSDF does support resizing
of binary data, in-place editing, lazy loading, and streamed reading and
writing.


## BSDF vs ASDF

The [ASDF format](http://asdf-standard.readthedocs.io/) has
goals that partly overlap with the purpose of BSDF:

* intrinsic hierarchical structure
* human readable
* based on existing data format (yaml)
* support for references (also to external objects)
* efficient updating
* machine independent, structured data, ndarrays
* support for writing (and reading) streams
* explicit versioning
* explicit extensibility without interference
* support for validation with schemas

ASDF was seriously considered before the development on BSDF started.
The idea of a human readable format is appealing, but ...

* Yaml is a rather ill defined format that is hard to parse, which is
  probably why the parser is so slow.
* Data that consist of many elements (but not so much blobs) will be encoded
  inefficiently.
* Many text editors won't deal well with huge text files.
* If the text is edited, byte alignments are likely to break.
* It makes the format more complex (you basically have two formats).

This is why BSDF drops human readability, gaining a format that
is simple, compact, and fast to parse. This is not to say that
ASDF did it wrong; it is very suited for what it was designed
for. But BSDF is more suited for e.g. inter process communication.


## BSDF vs Arrow

The goals of [Apache Arrow](https://arrow.apache.org/) bear similarities with 
BSDF, with e.g. a clear standard and zero copy reads. However, it's
rather focussed on columnar data (where BSDF supports nd-arrays), and
seems oriented at compiled languages, i.e. less flexible. Although the
specification looks easy to read, the Python implementation is *much*
larger than BSDF's 800 or so lines of code. It's also not pure Python, making
it nontrivial to install on less common Python versions/implementations.


## BSDF vs NPZ

Numpy has a builtin way to encode typed arrays. However, this is limited to
arrays (no meta data), and rather specific to Python.


## BSDF vs SSDF (and BSDF v1)

Around 2011 I developed a human readable [file format called
SSDF](https://bitbucket.org/almarklein/ssdf), suited for storing
hierachical data, similar to JSON, but with support for `nan` and `inf`.
It also supports nd-arrays, via base64 encoding and zlib compression.
I've used this in several (scientific) projects (e.g. it was used in
the [Pyzo IDE](http://github.com/pyzo/pyzo) to store config data).
Although it does serve its purpose, its not terribly good for large
binary datasets. I also kept coming back in need of a format to send
binary data to/from JS, where compression is a problem.

At some point I developed a binary equivalent of SSDF that's fully
compatible, but stored binary data more effectively. The current BSDF
format can be seen as its successor, being both simpler and more
extensible. This is also why BSDF's version number starts at 2.

I am currently of the opinion that a format that is good at binary data
can not also be good at being a human readable (config) format. See e.g.
[toml](https://github.com/toml-lang/toml) for a well-readable format.

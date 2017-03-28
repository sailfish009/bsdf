# Experimentation

This directory contains some of the earlier (experimentary) work. I might
want to use some of it at a later date, so keeping here for reference.
Don't mind the naming; I did not have a name at the time.


Some findings:

* JSON is pretty darn fast, but this is mostly because it's implemented
  in C (since Python 3.x)
* msgpack is >2x faster than JSON, when using the C implementation; the
  py implementation is 5-10x slower.
* Yaml is 100-200x slower than JSON, even with libyaml.
* With this awful Yaml performance, ASDF is out of the question for my usecase.
* zon2 encodes at 1/3d the speed of JSON, is sufficient, I think, also
  because the alg is really simple and thereby easy to port.
* zon2 decodes at about 1/6th the speed if JSON, using mostly regexp.
  This could be better ...
* Zon3 (bsdf precursor) is about 3x slower than JSON in CPython. Same in JS.
  Probably room for optimizations though.

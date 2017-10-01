
addpath('jsonlab');

fname1 = argv(){1};
fname2 = argv(){2};

if strfind(fname1, '.json')  % endsWith not available in Octave
    data = loadjson(fname1, 'SimplifyCell', 0, 'FastArrayParser', 0);
elseif strfind(fname1, '.bsdf')
    data = bsdf(fname1);
else
    error('Expected a json or bsdf file.')
end

'euh wat'
data

if strfind(fname2, '.json')
    savejson('', data, fname2);
elseif strfind(fname2, '.bsdf')
    bsdf(fname2, data);
else
    error('Expected a json or bsdf file.')
end
  
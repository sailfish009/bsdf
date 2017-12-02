function testservice_runner(fname1, fname2)
% This little function gets called in a subprocess by the BSDF test service

addpath('jsonlab');

% Read in
if strfind(fname1, '.json')  % endsWith and contains are not available in Octave
    data = loadjson(fname1, 'SimplifyCell', 0, 'FastArrayParser', 0);
elseif strfind(fname1, '.bsdf')
    % data = bsdf(fname1);
    data = Bsdf().load(fname1);
else
    error('Expected a json or bsdf file.')
end

% Write back
if strfind(fname2, '.json')
    savejson('', data, fname2);
elseif strfind(fname2, '.bsdf')
    % bsdf(fname2, data);
    Bsdf().save(fname2, data);
else
    error('Expected a json or bsdf file.')
end

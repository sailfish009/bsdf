%function test_unit()
% Run unit tests for BSDF.
%
% The tests that use actual filenames are sufficiently covered
% by the testservice.py.
%
% In Matlab functions are not objects, so creating custom converters will
% probably need to be class based or something. We leave that for later.

IS_OCTAVE = (exist ("OCTAVE_VERSION", "builtin") > 0);

% Test that we serialize directly
% (even though bsdf.m will use a tempfile at the moment)
a = {'hello', 3};
b = bsdf(a);
c = bsdf(b);
assert(isequal(a, c));

% Float32 makes smaller files
data = {3, 4, zeros(1000, 0, 'uint8')};    
b1 = bsdf(data, 'float64', 1);
b2 = bsdf(data, 'float64', 0);
b3 = bsdf(data, 'float64', 0, 'compression', 0);  % test options
assert(numel(b1) > numel(b2));
assert(numel(b2) == numel(b3));

if IS_OCTAVE
    % Octave specific tests ...
    
else
    % Matlab specific tests ...
    
    % Compression makes smaller files
    data = {3, 4, zeros(1000, 1, 'uint8')};    
    b1 = bsdf(data, 'compression', 0);
    b2 = bsdf(data, 'compression', 1);    
    assert(numel(b1) > 10 * numel(b2));        
end

disp('All tests succeeded.')
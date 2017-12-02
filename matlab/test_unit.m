%function test_unit()
% Run unit tests for BSDF.
%
% The tests that use actual filenames are sufficiently covered
% by the testservice.py.
%
% In Matlab functions are not objects, so creating custom extensions will
% probably need to be class based or something. We leave that for later.

IS_OCTAVE = (exist ("OCTAVE_VERSION", "builtin") > 0);

bsdf = Bsdf();
assert(isequal(bsdf.compression, false));


% Test that we serialize directly
% (even though bsdf.m will use a tempfile at the moment)
a = {'hello', 3};
b = bsdf.encode(a);
c = bsdf.decode(b);
assert(isequal(a, c));

% Float32 makes smaller files
data = {3, 4, zeros(1000, 0, 'uint8')};
bsdf.float64 = 1;
b1 = bsdf.encode(data);
bsdf.float64 = 0;
b2 = bsdf.encode(data);
assert(numel(b1) > numel(b2));
bsdf.float64 = 1;

if IS_OCTAVE
    % Octave specific tests ...

else
    % Matlab specific tests ...

    % Compression makes smaller files
    data = {3, 4, zeros(1000, 1, 'uint8')};
    bsdf.compression = 0;
    b1 = bsdf.encode(data);
    bsdf.compression = 1;
    b2 = bsdf.encode(data);
    assert(numel(b1) > 10 * numel(b2));
end

disp('All tests succeeded.')

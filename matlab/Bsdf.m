% This file is distributed under the terms of the 2-clause BSD License.
% Copyright (C) 2017 Almar Klein

classdef Bsdf
    % Bsdf class for encoding/decoding data with the BSDF format.
    %   Matlab/Octave implementation of the Binary Structured Data Format (BSDF).
    %   BSDF is a binary format for serializing structured (scientific) data.
    %   See http://bsdf.io for more information.
    %
    %   This is a well tested, but relatively minimal implementation: it does
    %   not (yet) support custom extensions, and (zlib) compression is only
    %   supported in Matlab (not Octave).
    %
    %   Usage:
    %
    %     bsdf = Bsdf()
    %     bsdf.save(filename, data)   % to save data to file
    %     data = bsdf.load(filename)  % to load data from file
    %     blob = bsdf.encode(data)    % to serialize data to bytes (a uint8 array)
    %     data = bsdf.decode(blob)    % to load data from bytes
    %
    %   Options (for writing) are provided as object properties:
    %
    %   - compression: the compression for binary blobs, 0 for raw, 1 for zlib
    %     (not available in Octave).
    %   - float64: whether to export floats as 64 bit (default) or 32 bit.
    %   - use_checksum: whether to write checksums for binary blobs, not yet
    %     implemented.

    properties (SetAccess = private, GetAccess = public)
        VERSION  % The BSDF version of this implementation
    end

    properties (SetAccess = public, GetAccess = public)
        compression  % whether to (ZLIB) compress binary blobs (default false)
        float64  % Whether to encode float values with 64 bits (default true)
        use_checksum  % Whether to write checksums for binary blobs
    end

    % -------------------------------------------------------------------------

    methods (Access = public)

        function serializer = Bsdf()
            VERSION = [2, 2, 0];  % Write such that the BSDF tooling can detect
            serializer.VERSION = VERSION;
            serializer.compression = 0;
            serializer.float64 = true;
            serializer.use_checksum = false;
        end

        function save(serializer, filename, data)
            % Save data to a file

            if ~isa(filename, 'char')
                error([mfilename ': Invalid filename given.']);
            end
            % Write to file
            f = Bsdf.our_fopen(filename, 'w');
            try
                serializer.write_to_file_object(f, data);
                fclose(f);
            catch e
                fclose(f);
                rethrow(e);
            end
        end

        function data = load(serializer, filename)
            % Load data from a file

            % Exists?
            if ~exist(filename, 'file');  error([mfilename ': the specified file does not exist.']);  end
            % Read file
            f = Bsdf.our_fopen(filename, 'r');
            try
                data = serializer.read_from_file_object(f);
                fclose(f);
            catch e
                fclose(f);
                rethrow(e);
            end
        end

        function blob = encode(serializer, data)
            % encode data to bytes (a uint8 array)

            tempfilename = 'bsdf_temp_file.bsdf';
            f = Bsdf.our_fopen(tempfilename, 'w');
            try
                serializer.write_to_file_object(f, data);
                fclose(f);
            catch e
                fclose(f);
                rethrow(e);
            end
            f = Bsdf.our_fopen(tempfilename, 'r');
            blob = fread(f, inf, '*uint8');
            fclose(f);
            delete(tempfilename);
        end

        function data = decode(serializer, blob)
            % decode data from bytes (a uint8 array)

            tempfilename = 'bsdf_temp_file.bsdf';
            f = Bsdf.our_fopen(tempfilename, 'w');
            fwrite(f, blob);
            fclose(f);
            f = Bsdf.our_fopen(tempfilename, 'r');
            try
                data = serializer.read_from_file_object(f);
                fclose(f);
            catch e
                fclose(f);
                rethrow(e);
            end
            delete(tempfilename);
        end

    end % of public methods

    % -------------------------------------------------------------------------

    methods (Access = protected)

        function write_to_file_object(serializer, f, ob)
            % Write header
            fwrite(f, [66; 83; 68; 70]);
            % Write version
            fwrite(f, serializer.VERSION(1));
            fwrite(f, serializer.VERSION(2));
            % Go!
            serializer.bsdf_encode(f, ob);
        end

        function ob = read_from_file_object(serializer, f)
            % Get header
            head = fread(f, 4, '*uint8');
            assert(isequal(head, [66; 83; 68; 70]), 'Not a valid BSDF file');
            % Process version
            major_version = fread(f, 1, '*uint8');
            minor_version = fread(f, 1, '*uint8');
            if major_version ~= serializer.VERSION(1)
                error([mfilename ': file major version does not match implementation version.']);
            elseif minor_version > serializer.VERSION(2)
                warning('BSDF: file minor version is higher than implementation.')
            end
            % Go!
            ob = serializer.bsdf_decode(f);
        end

        function bsdf_encode(serializer, f, value)

            if isa(value, 'struct')
                fwrite(f, 'm');
                keys = fieldnames(value);
                Bsdf.write_length(f, length(keys));
                for i=1:length(keys)
                    key = keys{i};
                    val = value.(key);
                    key_b = Bsdf.string_encode(key);
                    Bsdf.write_length(f, length(key_b));
                    fwrite(f, key_b);
                    serializer.bsdf_encode(f, val);
                end

            elseif isa(value, 'cell')
                fwrite(f, 'l');
                Bsdf.write_length(f, length(value));
                for i=1:length(value)
                    serializer.bsdf_encode(f, value{i});
                end

            elseif isa(value, 'char')
                fwrite(f, 's');
                value_b = Bsdf.string_encode(value);
                Bsdf.write_length(f, length(value_b));
                fwrite(f, value_b);

            elseif isa(value, 'logical')
                if value; fwrite(f, 'y'); else; fwrite(f, 'n'); end

            elseif isa(value, 'uint8') && iscolumn(value)
                % blob (at the top to grab all uint8 instances (also empty and 1-length bytes)
                extra_size = 0;
                compr = serializer.compression;
                if compr == 0  % No compression
                    compressed = value;
                elseif compr == 1
                    % Use java to do zlib compression
                    ff = java.io.ByteArrayOutputStream();
                    g = java.util.zip.DeflaterOutputStream(ff);
                    g.write(value);
                    g.close();
                    % get the result from java
                    compressed = typecast(ff.toByteArray(), 'uint8');
                    ff.close();
                elseif compr == 2
                    error('BSDF: bz2 compression (2) is not yet supported.');
                else
                    error('BSDF: invalid compression');
                end
                data_size = numel(value);
                used_size = numel(compressed);
                allocated_size = used_size + extra_size;
                % Write
                fwrite(f, 'b');
                Bsdf.write_length(f, allocated_size);
                Bsdf.write_length(f, used_size);
                Bsdf.write_length(f, data_size);
                fwrite(f, compr, 'uint8');
                fwrite(f, 0, 'uint8');  % no checksum
                % Byte alignment (only necessary for uncompressed data)
                if compr == 0
                    alignment = 8 - mod(ftell(f) + 1, 8);  % +1 for the byte about to write
                    fwrite(f, alignment, 'uint8');
                    fwrite(f, zeros(alignment, 1), 'uint8');
                else
                    fwrite(f, 0, 'uint8');
                end
                fwrite(f, compressed, 'uint8');
                fwrite(f, zeros(extra_size, 1), 'uint8');

            elseif isa(value, 'numeric')

                if isequal(size(value), [0, 0])  % null - [0, n] would be array
                    fwrite(f, 'v');
                elseif numel(value) == 1  % scalar
                    if ~isreal(value)  % Standard extension: complex
                        fwrite(f, 'L');  % "This is a special list", next is its type
                        extension_id = 'c';
                        Bsdf.write_length(f, length(extension_id));
                        fwrite(f, extension_id);
                        Bsdf.write_length(f, 2);
                        serializer.bsdf_encode(f, double(real(value)));
                        serializer.bsdf_encode(f, double(imag(value)));
                    elseif isa(value, 'float')
                        if serializer.float64
                            fwrite(f, 'd');
                            fwrite(f, value, 'float64');
                        else
                            fwrite(f, 'f');
                            fwrite(f, value, 'float32');
                        end
                    elseif isa(value, 'integer')
                        if value >= -32768 && value <= 32767
                            fwrite(f, 'h');
                            fwrite(f, value, 'int16');
                        else
                            fwrite(f, 'i');
                            fwrite(f, value, 'int64');
                        end
                    else
                        % Fallback, would this ever happen?
                        fwrite(f, 'd');
                        fwrite(f, value, 'float64');
                    end

                else  % ndarray (standard extension)
                    class2dtype = struct('logical','bool', ...
                             'single','float32', 'double','float64', ...
                             'int8','int8', 'int16','int16', 'int32','int32', ...
                              'uint8','uint8', 'uint16','uint16', 'uint32','uint32');
                    % Pack into a dict
                    fwrite(f, 'M');  % "This is a special dict", next is its type
                    extension_id = 'ndarray';
                    Bsdf.write_length(f, length(extension_id));
                    fwrite(f, extension_id);
                    Bsdf.write_length(f, 3);
                    %
                    shape = size(value);
                    key = 'shape'; Bsdf.write_length(f, length(key)); fwrite(f, key);
                    fwrite(f, 'l');
                    Bsdf.write_length(f, length(shape));
                    for i = 1:length(shape); fwrite(f, 'h'); fwrite(f, shape(i), 'int16'); end
                    %
                    key = 'dtype'; Bsdf.write_length(f, length(key)); fwrite(f, key);
                    serializer.bsdf_encode(f, class2dtype.(class(value)));
                    % permuting to make the shape right
                    key = 'data'; Bsdf.write_length(f, length(key)); fwrite(f, key);
                    tmp = length(size(value));
                    value_p = permute(value, linspace(tmp, 1, tmp));
                    data = typecast(value_p(:), 'uint8');
                    serializer.bsdf_encode(f, data);
                end
            else
                error([mfilename ': cannot serialize ' class(value)]);
            end
        end

        % ---------------------------------------------------------------------

        function value = bsdf_decode(serializer, f)
            the_char = fread(f, 1, '*char')';
            c = lower(the_char);

            if numel(the_char) == 0
                error('bsdf:eof', 'end of file');
            elseif ~isequal(c, the_char)
                n = fread(f, 1, 'uint8');
                extension_id = fread(f, n, '*char')';
            else
                extension_id = '';
            end

            if c == 'v'
                value = [];  % null
            elseif c == 'y'
                value = true;
            elseif c == 'n'
                value = false;
            elseif c == 'h'
                value = fread(f, 1, 'int16=>int64');  % int16 -> int64
            elseif c == 'i'
                value = fread(f, 1, '*int64');  % int64 -> int64
            elseif c == 'f'
                value = fread(f, 1, 'float32');  % float32 -> double
            elseif c == 'd'
                value = fread(f, 1, 'float64');  % float64 -> double
            elseif c == 's'
                n = fread(f, 1, '*uint8');
                if n == 253; n = fread(f, 1, 'uint64'); end
                value = Bsdf.string_decode(fread(f, n, '*uint8'));
            elseif c == 'l'
                n = fread(f, 1, '*uint8');
                if n == 255
                    % Unclosed stream. A close stream (254 is threated as normal)
                    n = fread(f, 1, 'uint64');  % unused
                    value = {};
                    count = 0;
                    try
                        while 1
                            value{count+1} = serializer.bsdf_decode(f);
                            count = count + 1;
                        end
                    catch e
                        if ~isequal(e.identifier, 'bsdf:eof')
                            rethrow(e);
                        end
                    end
                else
                    if n == 253 || n == 254; n = fread(f, 1, 'uint64'); end
                    % Populate heterogeneous list
                    value = {};
                    if n > 0; value{n} = 0; end  % pre-alloc
                    for i=1:n
                        value{i} = serializer.bsdf_decode(f);
                    end
                end
            elseif c == 'm'
                n = fread(f, 1, '*uint8');
                if n == 253; n = fread(f, 1, 'uint64'); end
                value = struct();
                for i=1:n
                    n_name = fread(f, 1, '*uint8');
                    if n_name == 253; n_name = fread(f, 1, 'uint64'); end
                    name = Bsdf.string_decode(fread(f, n_name, '*uint8'));
                    value.(name) = serializer.bsdf_decode(f);
                end
            elseif c == 'b'
                % Blob of bytes - header is 5 to 42 bytes
                allocated_size = fread(f, 1, '*uint8');
                if allocated_size == 253; allocated_size = fread(f, 1, 'uint64'); end
                used_size = fread(f, 1, '*uint8');
                if used_size == 253; used_size = fread(f, 1, 'uint64'); end
                data_size = fread(f, 1, '*uint8');
                if data_size == 253; data_size = fread(f, 1, 'uint64'); end
                % Compression and checksum
                compr = fread(f, 1, '*uint8');
                has_checksum = fread(f, 1, '*uint8');
                if has_checksum
                    checksum = fread(f, 16, '*uint8');
                    % todo: validate checksum
                end
                % Skip alignment
                alignment = fread(f, 1, '*uint8');
                fread(f, alignment, '*uint8');
                % Read data
                compressed = fread(f, used_size, '*uint8');
                % Decompress
                if compr == 0
                    value = compressed;
                elseif compr == 1
                    import com.mathworks.mlwidgets.io.InterruptibleStreamCopier
                    a = java.io.ByteArrayInputStream(compressed);
                    b = java.util.zip.InflaterInputStream(a);
                    isc = InterruptibleStreamCopier.getInterruptibleStreamCopier;
                    cc = java.io.ByteArrayOutputStream;
                    isc.copyStream(b, cc);
                    value = typecast(cc.toByteArray, 'uint8')';
                elseif compr == 2
                    error([mfilename ': bz2 compression not supported.']);
                else
                    error([mfilename ': unsupported compression.']);
                end
                % Shape like a byte column-vector
                value = reshape(value, [numel(value), 1]);
                % Skip extra space
                fread(f, allocated_size - used_size, '*uint8');
            else
                error([mfilename ': unknown data type ' c ' ' extension_id]);
            end

            % Convert value if we can
            if extension_id
                if strcmp(extension_id, 'c')
                    value = complex(value{1}, value{2});
                elseif strcmp(extension_id, 'ndarray')
                    dtype2class = struct('bool','logical', ...
                        'float32','single', 'float64','double', ...
                        'int8','int8', 'int16','int16', 'int32','int32', ...
                        'uint8','uint8', 'uint16','uint16', 'uint32','uint32');
                    dtype = value.dtype;
                    shape = cell2mat(value.shape);
                    value = typecast(value.data, dtype2class.(dtype));
                    if prod(shape) ~= numel(value)
                        warning('BSDF: prod(shape) != size');
                    else
                        % in Matlab an array always has two dimensions ...
                        if numel(shape) == 1;  shape = [1 shape];  end
                        % In matlab the indexing occurs (z,y,x), but a(2)
                        % corresponds to a(2,1,1). As our convention says the
                        % x-dimension changes fastest, we need to do some reshaping and
                        % permuting...
                        value = reshape(value, fliplr(shape));
                        tmp = length(shape);
                        value = permute(value, linspace(tmp, 1, tmp));
                        % Note, singleton dimensions may have been dropped
                        % and it seems that we cannot fix that :/
                    end

                else
                    % Ignore, but warn ...
                    warning(['BSDF: no known extension for ' extension_id]);
                end
            end
        end

    end % of protected methods

    % -------------------------------------------------------------------------

    methods (Static, Access = protected)
       % Octave won't allow local functions, so we make them, methods

       function r = isoctave()
            persistent IS_OCTAVE;
            if isempty(IS_OCTAVE)
                IS_OCTAVE = (exist ("OCTAVE_VERSION", "builtin") > 0);
            end
            r = IS_OCTAVE;
       end

       function f = our_fopen(filename, mode)
            % Our version of fopen to open a file in little endian.
            % For the record, this used to open the file in utf-8 encoding using:
            % f = fopen(filename, mode, 'l');  % Octave uses UTF-8 by default
            % f = fopen(filename, mode, 'l', 'utf-8');  % Matlab has extra arg
            % However, it turned out that we needed string_encode and string_decode
            % anyway, because otherwise we could not correctly encode/decode the
            % length of a string. In other words, we now only read/write bytes,
            % so the encoding does not matter.
            f = fopen(filename, mode, 'l');
        end

        function b = string_encode(s)
            % Convert string to utf-8 bytes - even necessary if file is opened with utf8
            if Bsdf.isoctave()
                b = uint8(s);
            else
                b = unicode2native(s, 'utf-8');
            end
        end

        function s = string_decode(b)
            % Convert utf-8 bytes to string
            if Bsdf.isoctave()
                s = char(b');
            else
                s = native2unicode(b', 'utf-8');
            end
        end

        function write_length(f, x)
            % Encode an unsigned integer into a variable sized blob of bytes.
            if x <= 250
                fwrite(f, x, 'uint8');
            else
                fwrite(f, 253, 'uint8');
                fwrite(f, x, 'uint64');
            end
        end

    end % of protected static methods

end % of class

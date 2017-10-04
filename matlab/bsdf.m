function result = bsdf(arg1, arg2)
% BSDF is a binary format for serializing structured (scientific) data.
% This is the Matlab implementation for reading and writing such
% data structures. Read more at https://gitlab.com/almarklein/bsdf
%
% Usage:
%
% data = bsdf(filename) to load data from file
% data = bsdf(bytes) to load data from bytes
% bsdf(filename, data) to save data to file
% bytes = bsdf(data) to serialize data to bytes (a uint8 array)
%
% This file is freely distributed under the terms of the 2-clause BSD License.
% Copyright (C) 2017 Almar Klein
    
    VERSION = [2, 0, 0];
    
    if nargin == 1
        % filename, bytes, or object
        if isa(arg1, 'char') && sum(arg1 == sprintf('\n')) == 0
            % Load from file, exists?
            if ~exist(arg1, 'file');  error([mfilename ': the specified file does not exist.']);  end
            % Read file
            f = our_fopen(arg1, 'r');
            try
                data = load(f, VERSION);
                fclose(f);
            catch e
                fclose(f);
                rethrow(e);
            end
            result = data;
        
        elseif isa(arg1, 'uint8') && isequal(size(arg1), [1, numel(arg1)])
            % Load from bytes
            f = our_fopen(Tempfile, 'w');
            tempfilename = fname(f);
            fwrite(f, arg1);
            fclose(f);
            f = our_fopen(tempfilename, 'r');
            try
                data = load(f, VERSION);
                fclose(f);
            catch e
                fclose(f);
                rethrow(e);
            end
            delete(tempfilename);
            result = data;
        
        else
            % Serialize to bytes
            f = our_fopen(Tempfile, 'w')
            tempfilename = fname(f);
            try
                save(f, arg1, VERSION);
                fclose(f);
            catch e
                fclose(f);
                rethrow(e);
            end
            f = our_fopen(tempfilename, 'r');
            bytes = fread(f, inf);
            fclose(f);
            delete(tempfilename);
            result = bytes;
        end
        
    elseif nargin == 2
        % Write to file, looks like file? Does not have to exist yet, of course
        if ~isa(arg1, 'char')
             error([mfilename ': Invalid filename given.']);
        end
        % Write to file
        f = our_fopen(arg1, 'w');
        try
            save(f, arg2, VERSION);
            fclose(f);
        catch e
            fclose(f);
            rethrow(e);
        end
      
    else
        error([mfilename ': Need one or two input arguments.']);
        
    end

end


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
    if isoctave()
        b = uint8(s);
    else
        b = unicode2native(s, 'utf-8');
    end
end

function s = string_decode(b)
    % Convert utf-8 bytes to string
    if isoctave()
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


function save(f, ob, VERSION)
    % Write header
    fwrite(f, [66; 83; 68; 70]);
    % Write version
    fwrite(f, VERSION(1));
    fwrite(f, VERSION(2));
    % Go!
    bsdf_encode(f, ob);
end


function ob = load(f, VERSION)
    % Get header
    head = fread(f, 4, '*uint8');
    assert(isequal(head, [66; 83; 68; 70]), 'Not a valid BSDF file');    
    % Process version 
    major_version = fread(f, 1, '*uint8');
    minor_version = fread(f, 1, '*uint8');
    if major_version ~= VERSION(1)
        error([mfilename ': file major version does not match implementation version.']);
    elseif minor_version > VERSION(2)
        warning([mfilename ': file minor version is higher than implementation.'])
    end
    % Go!
    ob = bsdf_decode(f);
end


function bsdf_encode(f, value)
  
    % todo: convert ...
    
    switch class(value)
       
        case 'struct'
            fwrite(f, 'm');
            keys = fieldnames(value);
            write_length(f, length(keys));
            for i=1:length(keys)
                key = keys{i};
                val = value.(key);
                write_length(f, length(key));  % assume ASCII key names
                fwrite(f, key);
                bsdf_encode(f, val);
            end
        
        case 'cell'
            fwrite(f, 'l');            
            write_length(f, length(value));
            for i=1:length(value)
                bsdf_encode(f, value{i});
            end
        
        case 'char'
            fwrite(f, 's');
            value_b = string_encode(value);
            write_length(f, length(value_b));
            fwrite(f, value_b);
        
        case {'double', 'single', 'logical', 'uint8','int8','uint16', 'int16', 'uint32', 'int32'}
            sze = size(value);  % Matlab cannot call/index into a termporary array, poor little Matlab :( 
            if isa(value, 'uint8') && ndims(value) == 2 && sze(2) == numel(value)
                % blob (at the top to grab all uint8 instances (also empty and 1-length bytes)
                extra_size = 0;
                compression = 0; 
                compressed = value;
                data_size = numel(value);
                used_size = numel(compressed);
                allocated_size = used_size + extra_size;
                % Write
                fwrite(f, 'b');                
                write_length(f, allocated_size);
                write_length(f, used_size);
                write_length(f, data_size);
                fwrite(f, compression, 'uint8');
                fwrite(f, 0, 'uint8');  % no checksum
                % Byte alignment (only for uncompressed data)
                if compression == 0
                    alignment = mod(ftell(f) + 1, 8);  % +1 for the byte about to write
                    fwrite(f, alignment, 'uint8');
                    fwrite(f, zeros(alignment, 1), 'uint8');
                end
                fwrite(f, value, 'uint8');
                fwrite(f, zeros(extra_size, 1), 'uint8');
            
            elseif numel(value) == 0  % null
                fwrite(f, 'v');
            elseif numel(value) == 1  % scalar
                if ~isreal(value)  % Standard converter: complex
                    fwrite(f, 'L');  % "This is a special list", next is its type
                    converter_id = 'c';
                    write_length(f, length(converter_id));
                    fwrite(f, converter_id);                    
                    write_length(f, 2);
                    bsdf_encode(f, double(real(value)));
                    bsdf_encode(f, double(imag(value)));
                elseif isa(value, 'double')
                    fwrite(f, 'd');
                    fwrite(f, value, 'float64');
                elseif isa(value, 'single')
                    fwrite(f, 'f');
                    fwrite(f, value, 'float32');
                elseif isa(value, 'uint8')
                    fwrite(f, 'u');
                    fwrite(f, value, 'uint8');
                else
                    fwrite(f, 'i');
                    fwrite(f, value, 'int64');
                end
             
            else  % array
                error([mfilename ': arrays are not yet supported (' class(value) ' ' mat2str(size(value)) ')']);
            end
    end      
end


function value = bsdf_decode(f)
    the_char = fread(f, 1, '*char')';
    c = lower(the_char);
    
    if numel(the_char) == 0
        error('bsdf:eof', 'end of file');
    elseif ~isequal(c, the_char)
        n = fread(f, 1, 'uint8');
        converter_id = fread(f, n, '*char')';
    else
        converter_id = '';
    end
    
    if c == 'v'
        value = [];  % null
    elseif c == 'y'
        value = 1;
    elseif c == 'n'
        value = 0;
    elseif c == 'u'
        value = fread(f, 1, 'uint8');  % int as uint8
    elseif c == 'i'
        value = fread(f, 1, 'int64');  % int as int64
    elseif c == 'f'
        value = fread(f, 1, 'float32');  % float32
    elseif c == 'd'
        value = fread(f, 1, 'float64');  % float64
    elseif c == 's'        
        n = fread(f, 1, '*uint8');
        if n == 253; n = fread(f, 1, 'uint64'); end
        value = string_decode(fread(f, n, '*uint8'));
    elseif c == 'l'
        n = fread(f, 1, '*uint8');        
        if n == 255
            % Stream - may be open or closed. If its closed, we use the
            % Given length as a hint, but stay on our guard.
            n = fread(f, 1, 'uint64');  % zero if not closed
            value = {};
            if n > 0; value{n} = 0; end  % pre-alloc
            count = 0;
            try
                while 1
                    value{count+1} = bsdf_decode(f);
                    count = count + 1;
                end
            catch e
                if ~isequal(e.identifier, 'bsdf:eof')
                    rethrow(e);
                end
            end
            if count < n; value = value{1:count}; end  % Truncate
        else
            if n == 253; n = fread(f, 1, 'uint64'); end
            % Populate heterogeneous list
            value = {};
            if n > 0; value{n} = 0; end  % pre-alloc
            for i=1:n
                value{i} = bsdf_decode(f);
            end
        end        
    elseif c == 'm'
        n = fread(f, 1, '*uint8');
        if n == 253; n = fread(f, 1, 'uint64'); end
        value = struct();
        for i=1:n
            n_name = fread(f, 1, '*uint8');
            if n_name == 253; n_name = fread(f, 1, 'uint64'); end
            name = fread(f, n_name, '*char')';
            value.(name) = bsdf_decode(f);
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
        compression = fread(f, 1, '*uint8');
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
        if compression == 0
            value = compressed';
        elseif compression == 1
            import com.mathworks.mlwidgets.io.InterruptibleStreamCopier
            a = java.io.ByteArrayInputStream(compressed);
            b = java.util.zip.InflaterInputStream(a);
            isc = InterruptibleStreamCopier.getInterruptibleStreamCopier;
            cc = java.io.ByteArrayOutputStream;
            isc.copyStream(b, cc);        
            value = typecast(cc.toByteArray, 'uint8')';
        elseif compression == 2
            error([mfilename ': bz2 compression not supported.']);
        else
            error([mfilename ': unsupported compression.']);
        end        
        % Skip extra space
        fread(f, allocated_size - used_size, '*uint8');
    else
        error([mfilename ': unknown data type ' c ' ' converter_id]);
    end
    
    % Convert value if we can
    if converter_id
        if converter_id == 'c'
            value = complex(value{1}, value{2});
        else
            % slicently ignore ...
        end
    end
end

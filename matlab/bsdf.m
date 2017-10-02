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
            if ~exist(arg1, 'file');  error([mfilename ': the specified file does not exist.']);  end;
            % Read file
            f = fopen(arg1, 'r', 'l');%, 'UTF-8');  % read / little endian
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
            f = fopen(Tempfile, 'w', 'l');%, 'UTF-8');  % write / little endian
            tempfilename = fname(f);
            fwrite(f, arg1);
            fclose(f);
            f = fopen(tempfilename, 'r', 'l');%, 'UTF-8');
            try
                data = load(bytes, VERSION);
                fclose(f);
            catch e
                fclose(f);
                rethrow(e);
            end
            delete(tempfilename);
            result = data;
        
        else
            # Serialize to bytes
            f = fopen(Tempfile, 'w', 'l');%, 'UTF-8');  % write / little endian
            tempfilename = fname(f);
            try
                save(f, arg1, VERSION);
                fclose(f);
            catch e
                fclose(f);
                rethrow(e);
            end
            f = fopen(tempfilename, 'r', 'l');%, 'UTF-8');
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
        f = fopen(arg1, 'w', 'l');%, 'UTF-8');  % write / little endian
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


function write_length(f, x)
    % Encode an unsigned integer into a variable sized blob of bytes.
    if x <= 250
        fwrite(f, x, 'uint8');
    # elif x < 65536:
    #     return spack('<BH', 251, x)
    # elif x < 4294967296:
    #     return spack('<BI', 252, x)
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
    if major_version != VERSION(1)
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
            write_length(f, length(value));  % In Octave, this counts #bytes not #chars
            fwrite(f, value);
            %sb = uint8(value);           
            %write_length(f, length(sb));
            %fwrite(f, sb);
                
        case {'double', 'single', 'logical', 'uint8','int8','uint16', 'int16', 'uint32', 'int32'}
          
            if numel(value) == 0  % null
                fwrite(f, 'v');
            elseif numel(value) == 1  % scalar
                if strcmp(class(value), 'double')
                    fwrite(f, 'd');
                    fwrite(f, value, 'float64');
                elseif strcmp(class(value), 'single')
                    fwrite(f, 'f');
                    fwrite(f, value, 'float32');
                elseif strcmp(class(value), 'uint8')
                    fwrite(f, 'u');
                    fwrite(f, value, 'uint8');
                else
                    fwrite(f, 'i');
                    fwrite(f, value, 'int64');
                end
            
            elseif strcmp(class(value), 'uint8') && equals(size(value), [1, numel(value)])
                % blob
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
                # Byte alignment (only for uncompressed data)
                if compression == 0
                    alignment = mod(ftell(f) + 1, 8)  # +1 for the byte about to write
                    fwrite(f, alignment, 'uint8');
                    fwrite(f, zeros(alignment, 0), 'uint8');
                end
                fwrite(f, value, 'uint8');
                fwrite(f, zeros(extra_size, 0), 'uint8');
             
            else  % array
                error([mfilename ': arrays are not yet supported.']);
            end
    end      
end


function value = bsdf_decode(f)
    the_char = fread(f, 1, 'char');
    c = lower(the_char);
    
    if numel(the_char) == 0
        error('bsdf:eof', 'end of file');
    elseif ~isequal(c, the_char)
        error('cannot do custom data yet');
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
        if n == 253; n = fread(f, 1, 'uint64'); end;
        value = char(fread(f, n, 'uint8')');
    elseif c == 'l'
        n = fread(f, 1, '*uint8');        
        stream = 0;        
        if n == 253
            n = fread(f, 1, 'uint64');
        elseif n == 255
             n = fread(f, 1, 'uint64');  % zero if not closed
             stream = 1;
        end
        if stream == 1 && n == 0
            % Unclosed stream, keep reading until fail
            value = {};
            try
                while 1
                    value{end+1} = bsdf_decode(f);
                end
            catch e
                if ~isequal(e.identifier, 'bsdf:eof')
                    rethrow(e);
                end
            end
        else
            % Populate heterogeneous list
            value = {};
            value{n} = 0;
            for i=1:n
                value{i} = bsdf_decode(f);
            end
        end
    elseif c == 'm'
        n = fread(f, 1, '*uint8');
        if n == 253; n = fread(f, 1, 'uint64'); end;
        value = struct();
        for i=1:n
            n_name = fread(f, 1, '*uint8');
            if n_name == 253; n_name = fread(f, 1, 'uint64'); end;
            name = char(fread(f, n_name, 'uint8')');
            value.(name) = bsdf_decode(f);
        end       
    elseif c == 'b'
        % Blob of bytes - header is 5 to 42 bytes
        allocated_size = fread(f, 1, '*uint8');
        if allocated_size == 253; allocated_size = fread(f, 1, 'uint64'); end;
        used_size = fread(f, 1, '*uint8');
        if used_size == 253; used_size = fread(f, 1, 'uint64'); end;
        data_size = fread(f, 1, '*uint8');
        if data_size == 253; data_size = fread(f, 1, 'uint64'); end;
        % Compression and checksum
        compression = fread(f, 1, '*uint8');
        has_checksum = fread(f, 1, '*uint8');
        if has_checksum;
            checksum = fread(f, 16, '*uint8');
        end
        % Skip alignment
        alignment = fread(f, 1, '*uint8');
        fread(f, alignment, '*uint8');
        % Read data
        compressed = fread(f, used_size, '*uint8');
        % Decompress
        if compression == 0
            value = compressed;
        elseif compression == 1
            import com.mathworks.mlwidgets.io.InterruptibleStreamCopier
            a = java.io.ByteArrayInputStream(compressed);
            b = java.util.zip.InflaterInputStream(a);
            isc = InterruptibleStreamCopier.getInterruptibleStreamCopier;
            c = java.io.ByteArrayOutputStream;
            isc.copyStream(b, c);        
            value = typecast(c.toByteArray, 'uint8')';
        elseif compression == 2
            error([mfilename ': bz2 compression not supported.']);
        else
            error([mfilename ': unsupported compression.']);
        end
        % Skip extra space
        fread(f, allocated_size - used_size, '*uint8');
    else
        error([mfilename ': unknown data type ' c]);
    end
    
    % todo: Convert value
end

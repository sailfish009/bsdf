function result = ssdf(arg1, arg2)
% SSDF is a format for storing structured (scientific) data.
%
% The goal of the format is to be easily readable by humans as well 
% as computers. It is aimed for use in interpreted languages like 
% Python or Matlab, but it can be used in any language that supports 
% floats, ints, unicode strings, lists, dictionaries, and 
% multidimensional arrays.
%
% This is the Matlab implementation for reading and writing such 
% data structures. 
% 
% Elements in a data structure can be one of seven different data 
% elements, of which the first two are a container element (which 
% can be nested):
%    * dictionary (struct)
%    * list (cell array)
%    * (Unicode) string
%    * float scalar
%    * integer scalar
%    * array of binary data of various types and of any shape
%    * Null ([])
%
% Usage:
%
% data_structure = ssdf(filename) to load structured data from file
% ssdf(filename, data_structure) to save structured data to file
% text = ssdf(data_structure) to write structured data to text
% data_structure = ssdf(text) to load structured data from text
%
%
% See http://code.google.com/p/ssdf/ for the full specification of the
% standard and for more information.
%
% This file and the SSDF standard are free for all to use (BSD license).
% Copyright (C) 2010 Almar Klein.

% Redistribution and use in source and binary forms, with or without
% modification, are permitted provided that the following conditions are met:
%
%    * Redistributions of source code must retain the above copyright notice, 
%      this list of conditions and the following disclaimer.
%    * Redistributions in binary form must reproduce the above copyright
%      notice, this list of conditions and the following disclaimer in the 
%      documentation and/or other materials provided with the distribution.
%    * Neither the name of the University of Twente nor the names of its 
%      contributors may be used to endorse or promote products derived from
%      this software without specific prior written permission.
%
% THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
% AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
% IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
% ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
% LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
% CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
% SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
% INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
% CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
% ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
% POSSIBILITY OF SUCH DAMAGE.

% for simplicity I included the code for base64 encoding inside this file
% as subfunctions.
% The original code is from Peter J. Acklam and can be found at:
% http://home.online.no/~pjacklam
    

    if nargin==1
        % filename, text, or object
        
        if isa(arg1,'char')
            
            if sum(arg1==sprintf('\n'))
                % multiline text
                result = loads(arg1);
            else
                % file, exists?
                if ~exist(arg1,'file');  error([mfilename ': the specified file does not exist.']);  end;            
                % read file        
                result = load(arg1);
            end
        elseif isa(arg1, 'struct')
            % struct
            result = saves(arg1);
        else
            error([mfilename ': Invalid argument given.']); 
        end
        
    elseif nargin==2
        % Write file
        
        % Test whether char1 can be a filename
        if ~isa(arg1,'char')
             error([mfilename ': Invalid filename given.']); 
        end
        
        if isa(arg2,'char')
            
            % given variablename ok?
            if ~evalin('caller', ['exist(''' arg2 ''',''var'')'])
                error([mfilename ': A variable with that name does not exist.']);
            end
            % get object
            arg2 = evalin('caller',['' arg2 ';']);
        end
        
        % is object a struct?
        if ~isa(arg2,'struct')
           error([mfilename ': The suppplied variable must be a struct.']); 
        end
        
        % parse...        
        save(arg1, arg2);
        
    else
        error([mfilename ': Wont accept more than two input arguments.']);
    end

end


%% STEP 1: file <--> text

function save(filename, ob)
    text = saves(ob);
    text = [sprintf('# This Simple Structured Data Format (SSDF) file was created from Matlab by ssdf.m\n') text];
    
    % make utf8
    bytes = unicode2native(text,'UTF-8');

    % open file
    fid = fopen(filename,'w');
    if fid == -1
        disp(['Cannot open file ''' filename ''' ...']);
        return;
    end
    
    % write
    try
        fwrite(fid,bytes);
        fclose(fid);
    catch
        disp(['Error writing to file ''' filename ''' ...']);
        fclose(fid);
    end
    
end


function ob = load(filename)
    ob = struct();
    
    % open file
    fid = fopen(filename,'r');
    if fid == -1
        disp(['Cannot open file ''' filename ''' ...']);
        return;
    end
    
    % read
    try        
        bytes = fread(fid);
        fclose(fid);
    catch
        disp(['Error writing to file ''' filename ''' ...']);
        fclose(fid);
        return;
    end
    
    % make a string    
    text = native2unicode(bytes,'UTF-8')'; % note the transpose
    
    % load!
    ob = loads(text);

end



%% STEP 2: text <--> (structured) lines

function text = saves(ob)
    % get lines
    base = toString('', ob, -2);
    lines = pack(base);
    
    % build single string
    text = '';
    for i=2:length(lines)
        text = [text lines{i} sprintf('\r\n')];
    end
    
end


function lines = pack(lineObject)
    % This cannot be a part of function saves, as this function
    % is called recursively
    
    % collect lines
    listOfLines = {};
    for i=1:length(lineObject.children)
        child = lineObject.children{i};        
        childLines = pack(child);
        listOfLines{end+1} = childLines;
    end
    
    % make list flat
    lines = {lineObject.line};
    for i=1:length(listOfLines)
        childLines = listOfLines{i};
        lines = {lines{:}, childLines{:} };
    end
    
end


function ob = loads(text)
    
    % pre process text 
    text = strrep(text, sprintf('\t'), '  ');
    text = strrep(text, sprintf('\r\n'), sprintf('\n'));
    text = strrep(text, sprintf('\r'), sprintf('\n'));
    
    % split lines
    lines = regexp(text, sprintf('\n'),'split');
    
    % create structure
    root = LineObject('dict:');
    root.value = 'dict:';
    lineObjects = {root};
    tree = {1};
    
    for linenr=1:length(lines)
       line = lines{linenr};
       line3 = strtrim(line);
       
       % skip comments and empty lines
       if isempty( line3 ) || line3(1)=='#'
           continue;
       end
       
       % find indentation (indent works a bit awkward since lstrip does not exist)      
       new = LineObject(line);
       new.indent = length(deblank(line)) - length(line3);
       
       % set linenr
       new.linenr = linenr;
       
       % split name and value using regexp
       [v1 v2] = regexp(line, '^ *?\w+? *?=');
       if ~isempty(v1)
           new.name = strtrim( line(1:v2-1) );
           new.value = line(v2+1:end);
       else
           new.name = '';
           new.value = line;
       end
       new.value = fliplr(deblank(fliplr( new.value ))); % remove white space in front
       
       % select leaf in tree 
       while new.indent <= lineObjects{tree{end}}.indent
           tree = tree(1:end-1);
       end
       
       % append to leaf       
       lineObjects{end+1} = new;
       id = length(lineObjects);
       lineObjects{tree{end}}.children{end+1} = id;
       tree{end+1} = id;
       
    end
    
    % post process... ARG, stupid value objects
    for i=length(lineObjects):-1:1
        ob = lineObjects{i};
        children = cell(1,length(ob.children));
        for j=1:length(ob.children)
            children{j} = lineObjects{ob.children{j}};
        end
       lineObjects{i}.children = children;
    end
    
    % do the parse pass
    [name, ob] = fromString(lineObjects{1});
    
end

   

%% STEP 3: (structured) lines <--> structured data

function count = countLines(lineObject)
    count = 1; % for this object
    for i = 1:length(lineObject.children)
        count = count + countLines(lineObject.children{i});
    end
end
function sorted = sortChildrenByCountingLines(children)
    counts = zeros(1,length(children));
    for i = 1:length(children)
        counts(i) = countLines( children{i} );
    end
    [counts, I] = sort(counts);
    sorted = children(I);
end

function lineObject = toString(name, value, indent)
   % make a string from the value and indentation
   
   % build indent and name
   line = repmat(' ',1,indent);
   if ~isempty(name)
       line = [line name ' = '];
   end
   
   % list to store children
   children = {};
   
   % do actual value
   
    switch class(value)
       
        case 'struct'
           line = [line 'dict:'];
           keys = fieldnames(value);
           for i=1:length(keys)
               key = keys{i};
               val = value.(key);
               tmp = toString(key, val, indent+2);
               children{end+1} = tmp;
           end
           % Sort children by their amount of lines
           children = sortChildrenByCountingLines(children);
        
        case 'cell'
            % check whether this is a small list
            isSmallList = 1;
            for i=1:length(value)                
                switch class(value{i})
                    case 'char'
                        if ~isempty(strfind(value{i},','))
                            isSmallList = 0;
                        end
                    case {'double', 'single', 'logical', 'uint8','int8','uint16', 'int16', 'uint32', 'int32'}
                        if  numel(value{i})~=1
                            isSmallList = 0;
                        end
                    otherwise                        
                        isSmallList = 0;
                end                
            end
            % Store list
            if isSmallList==1
                line = [line '['];
                sep = '';
                for i=1:length(value)
                    tmp = toString('', value{i}, 0);
                    line = [line sep deblank(tmp.line)];
                    sep = ', ';
                end
                line = [line ']'];
            else
                line = [line 'list:'];
                for i=1:length(value)
                    tmp = toString('', value{i}, indent+2);
                    children{end+1} = tmp;
                end
            end
            
      
        case 'char'
            % make newlines only \n, and escape them
            value = strrep(value,'\','\\');    
            value = strrep(value,sprintf('\r\n'),sprintf('\n'));            
            value = strrep(value,sprintf('\r'),sprintf('\n'));
            value = strrep(value,sprintf('\n'),'\n');
            value = strrep(value,sprintf(''''),'\''');
            line = [line '''' value ''''];
        
        case {'double', 'single', 'logical', 'uint8','int8','uint16', 'int16', 'uint32', 'int32'}
            
            class2dtype = struct('logical','bool', ...
                'single','float32', 'double','float64', ...
                'int8','int8', 'int16','int16', 'int32','int32', ...
                'uint8','uint8', 'uint16','uint16', 'uint32','uint32');
            
            if numel(value)==0
                line = [line 'Null'];
                
            elseif numel(value)==1
                % scalar                
                if strcmp(class(value),'double') || strcmp(class(value),'single')
                    line = [line sprintf('%0.12f', value)];
                else
                    line = [line sprintf('%i', value)];
                end
                
           
            elseif numel(value)<33 
                % short array
                
                % build array preamble
                atts = [shapeString(value) ' ' class2dtype.(class(value)) ' '];
                
                % permuting to make the shape right                
                tmp = length(size(value));
                value = permute( value, linspace(tmp,1,tmp));
                
                % create values
                valstr = '';
                for ii=1:numel(value)
                    valstr = [valstr num2str(value(ii),12) ', '];  
                end
                valstr(end-1:end)=[];
                
                % store
                line = [line 'array ' atts valstr];
                
            else
                % large array, go binary
                atts = [shapeString(value) ' ' class2dtype.(class(value)) ' '];
                % permuting to make the shape right                
                tmp = length(size(value));
                value = permute( value, linspace(tmp,1,tmp));
                % encode and store
                valstr = binencode(value);
                line = [line 'array ' atts valstr];
            end
    end
    
    % make object
    lineObject = LineObject(line);    
    lineObject.children = children;
    
end


function [name, value] = fromString(lineObject)
    
    % init
    name = lineObject.name;
    line = lineObject.value;
    linenr = lineObject.linenr;
    children = lineObject.children;
    
    % the variable line is the part from the '=' (and lstripped)
    % note that there can still be a comment on the line!
    
    % get data
    
    value = []; % there is no Null/None object in matlab!
    [word1, rest] = strtok(line, ' ');
    
    if isempty(line)
        % empty line
        return;
    
    elseif strcmp(word1,'Null')
        return;
    elseif strcmp(word1,'None')
        return;
    
    elseif strcmp(word1,'dict:')
        value = struct();
        for i=1:length(children)
            child = children{i};
            [key, val] = fromString(child);
            if length(key) > 0
                value.(key) = val;
            else
                disp(['Warning: unnamed element in dict on line ' num2str(child.linenr)]);
            end
        end
        
    elseif strcmp(word1,'list:')
        value = {};
        for i=1:length(children)
            child = children{i};
            [key, val] = fromString(child);
            if length(key) > 0
                disp(['Warning: named element in list on line ' num2str(child.linenr)]);
            else
                value{end+1} = val;
            end
        end
    
    elseif line(1)=='['
        % find other end and cut
        rline = fliplr(line);
        i = strfind(rline,']');
        if isempty(i)
            disp(['Warning: list not ended correctly on line ' num2str(linenr)]);
            return
        end
        line = line(2:end-i);        
        % Cut in pieces and process each piece
        pieces = regexp(line, ',', 'split');
        value = {};
        for i=1:length(pieces)
            lo = LineObject('');
            lo.value = strtrim(pieces{i});
            [dummy, value{end+1}] = fromString(lo);
        end
        
    elseif line(1)=='$'
        line = line(2:end);
        if isempty(line); line = ''; end;
        line = strrep(line,'\\',sprintf('\x07'));        
        line = strrep(line,'\n',sprintf('\n'));        
        line = strrep(line,sprintf('\x07'),'\');
        value = line;   
    
    elseif line(1)==''''
        % encode double slasges
        line = strrep(line,'\\',sprintf('\x07'));
        
        % find string using a regular expression
        [v1 v2]= regexp(line, '\''.*?[^\\]\''|''''');
        if isempty(v1)
            disp(['Warning: string not ended correctly on line ' num2str(linenr)]);
            return
        else
            line = line(v1+1:v2-1);
        end
        
        % decode
        line = strrep(line,'\n',sprintf('\n'));
        line = strrep(line,'\''',sprintf(''''));
        line = strrep(line,sprintf('\x07'),'\');
        value = line;
        
    elseif strcmp(word1,'array')
        % get more words
        [word2, rest] = strtok(rest, ' ');
        [word3, word4] = strtok(rest, ' ');
        if isempty(word4)
            disp(['Warning: invalid array definition on line ' num2str(linenr)]);
            return;
        end
        
        % determine shape
        shape = [];
        while ~isempty(word2)
           [i, word2] = strtok(word2, 'x');
           if isempty(i)
               continue;
           end 
           i = str2double(i);           
           if isnan(i)
               disp(['Warning: invalid array shape on line ' num2str(linenr)]);
               return;
           else
               shape(end+1) = i;
           end               
        end
        
        % determine datatype        
        dtype2class = struct('bool','logical', ...
                'float32','single', 'float64','double', ...
                'int8','int8', 'int16','int16', 'int32','int32', ...
                'uint8','uint8', 'uint16','uint16', 'uint32','uint32');   
        dtype = word3;
        if ~isfield(dtype2class, dtype)
            disp(['Warning: invalid array data type on line ' num2str(linenr)]);
            return;
        end
        
        % data itself
        
        if sum(word4==',')
            % as ascii
            
            % preallocate array
            N = sum(word4==',')+1;
            value = zeros(N,1);
            
            % get array
            tmp = regexp(word4, ',', 'split');
            for i=1:length(tmp)
                value(i) = str2double(tmp(i));
            end
            
            % get dtype right
            clss = dtype2class.(dtype);
            value = cast(value,clss);
            
            % get the shape right             
            if prod(shape) == length(value)  
                % in Matlab an array always has two dimensions...
                if numel(shape)==1;  shape = [1 shape];  end; 
                value = reshape(value, fliplr(shape));
                % in Matlab arrays are stored in last dimension first
                tmp = length(shape);
                value = permute( value, linspace(tmp,1,tmp));
            else
                disp(['Warning: prod(shape)!=size on line ' num2str(linenr)]);
            end
            
        else
            % binary
            
            % decode and decompress data
            value = bindecode(word4);
            
            % cast (typecast does not change undelying bytes)
            value = typecast(value, dtype2class.(dtype) );
                        
            % get the shape right
            if prod(shape) == numel(value)  
                % in Matlab an array always has two dimensions...
                if numel(shape)==1;  shape = [1 shape];  end;                 
                % finally.... In matlab the indexing occurs (z,y,x), but a(2)
                % corresponds to a(2,1,1). As our convention says the
                % x-dimension changes fastest, we need to do some reshaping and
                % permuting...
                value = reshape(value, fliplr(shape));
                tmp = length(shape);
                value = permute( value, linspace(tmp,1,tmp));
            else
                disp(['Warning: prod(shape)!=size on line ' num2str(linenr)]);
            end
            
        end
        
    else
        
        % remove comments
        i = strfind(line,'#');
        if ~isempty(i)
            line = line(1:i-1);
        end
        
        % try making int or float
        if strcmp(name,'wrongstring1')
            %keyboard;
        end
        tmp = str2double(line);
        if isnan(tmp)
            disp(['Warning: unknown value on line ' num2str(linenr)]);
            return
        end
        
        % establish whether it was an int
        if sum(line=='.')
            value = tmp;
        else
            value = int32(tmp);
        end
            
    end

end




%% Helper functions


function lineObject = LineObject(line)
    % Factory function that returns a struct
    if nargin==0; line = '';  end;
    lineObject = struct('line',line, 'indent',-2,'linenr',-1, 'name', '', 'value','');
    lineObject.children = {}; % cannot be done in constructor for some reason.
end


function str = shapeString(array)
    s = size(array);
    str = '';
    for i=1:length(s)
        str = [str num2str(s(i)) 'x'];
    end
    str = str(1:end-1);
end


function Z64 = binencode(M)
    % make byte string
    M = typecast(M(:),'uint8');
    
    % in blocks of 1MB, compress and encode
    BS = 1024*1024;
    i = 1;
    texts = {};
    while i <= length(M)
        % get block
        i2 = min(i+BS-1, length(M));
        block = M(i:i2);
        i = i + BS;
        
        % use java to do the deflating
        f = java.io.ByteArrayOutputStream();
        g = java.util.zip.DeflaterOutputStream(f);    
        g.write(block);
        g.close;
        
        % get the result from java
        Z = typecast(f.toByteArray,'uint8');
        f.close;
        
        % encode to base64, remove newlines
        text = base64encode(Z);        
        text(text==sprintf('\n'))=[];
        texts{end+1} = text;
        texts{end+1} = ';'; % separator
    end
    
    % combine blocks
    Z64 = [texts{1:end-1}];
    
end


function M = bindecode(Z64)

    % obtain the blocks
    blocks = regexp(Z64, ';', 'split');
    dataParts = {};
    for i=1:length(blocks)
        block = blocks{i};
        
        % decode base64
        Z = base64decode(block);
        Z = cast(Z,'uint8');
        
        % use java to do the inflating
        import com.mathworks.mlwidgets.io.InterruptibleStreamCopier
        a = java.io.ByteArrayInputStream(Z);
        b = java.util.zip.InflaterInputStream(a);
        isc = InterruptibleStreamCopier.getInterruptibleStreamCopier;
        c = java.io.ByteArrayOutputStream;
        isc.copyStream(b,c);
        
        % make bytes
        dataParts{end+1} = typecast(c.toByteArray,'uint8')';
    end
    
    % combine blocks and return
    M = [dataParts{:}];
    
end

function y = base64decode(x)
    % remove non-base64 chars
    x = x (   ( 'A' <= x & x <= 'Z' ) ...
        | ( 'a' <= x & x <= 'z' ) ...
        | ( '0' <= x & x <= '9' ) ...
        | ( x == '+' ) | ( x == '=' ) | ( x == '/' ) );
    
    % padding
    k = find(x == '=');
    if ~isempty(k)
        x = x(1:k(1)-1);
    end

    % mapping
    y = repmat(uint8(0), size(x));
    i = 'A' <= x & x <= 'Z'; y(i) =    - 'A' + x(i);
    i = 'a' <= x & x <= 'z'; y(i) = 26 - 'a' + x(i);
    i = '0' <= x & x <= '9'; y(i) = 52 - '0' + x(i);
    i =            x == '+'; y(i) = 62 - '+' + x(i);
    i =            x == '/'; y(i) = 63 - '/' + x(i);
    x = y;
    nebytes = length(x);         % number of encoded bytes
    nchunks = ceil(nebytes/4);   % number of chunks/groups

    % add padding if necessary
    if rem(nebytes, 4)
        x(end+1 : 4*nchunks) = 0;
    end
    x = reshape(uint8(x), 4, nchunks);
    y = repmat(uint8(0), 3, nchunks);            % for the decoded data
    
    % Rearrange every 4 bytes into 3 bytes
    y(1,:) = bitshift(x(1,:), 2);                    % 6 highest bits of y(1,:)
    y(1,:) = bitor(y(1,:), bitshift(x(2,:), -4));    % 2 lowest bits of y(1,:)
    y(2,:) = bitshift(x(2,:), 4);                    % 4 highest bits of y(2,:)
    y(2,:) = bitor(y(2,:), bitshift(x(3,:), -2));    % 4 lowest bits of y(2,:)
    y(3,:) = bitshift(x(3,:), 6);                    % 2 highest bits of y(3,:)
    y(3,:) = bitor(y(3,:), x(4,:));                  % 6 lowest bits of y(3,:)

    % remove padding
    switch rem(nebytes, 4)
        case 2
            y = y(1:end-2);
        case 3
            y = y(1:end-1);
    end
    
    % reshape to a row vector and make it a character array
    y = char(reshape(y, 1, numel(y)));
end

function y = base64encode(x, eol)
    % make sure we have the EOL value
    if nargin < 2
        eol = sprintf('\n');
    else
        if sum(size(eol) > 1) > 1
            error('EOL must be a vector.');
        end
        if any(eol(:) > 255)
            error('EOL can not contain values larger than 255.');
        end
    end
    if sum(size(x) > 1) > 1
        error('STR must be a vector.');
    end

    x   = uint8(x);
    eol = uint8(eol);
    ndbytes = length(x);                 % number of decoded bytes
    nchunks = ceil(ndbytes / 3);         % number of chunks/groups
    nebytes = 4 * nchunks;               % number of encoded bytes

    % add padding if necessary, to make the length of x a multiple of 3
    if rem(ndbytes, 3)
        x(end+1 : 3*nchunks) = 0;
    end
    x = reshape(x, [3, nchunks]);        % reshape the data
    y = repmat(uint8(0), 4, nchunks);    % for the encoded data

    % Split up every 3 bytes into 4 pieces
    y(1,:) = bitshift(x(1,:), -2);                  % 6 highest bits of x(1,:)
    y(2,:) = bitshift(bitand(x(1,:), 3), 4);        % 2 lowest bits of x(1,:)
    y(2,:) = bitor(y(2,:), bitshift(x(2,:), -4));   % 4 highest bits of x(2,:)
    y(3,:) = bitshift(bitand(x(2,:), 15), 2);       % 4 lowest bits of x(2,:)
    y(3,:) = bitor(y(3,:), bitshift(x(3,:), -6));   % 2 highest bits of x(3,:)
    y(4,:) = bitand(x(3,:), 63);                    % 6 lowest bits of x(3,:)

    % Now perform the following mapping
    z = repmat(uint8(0), size(y));
    i =           y <= 25;  z(i) = 'A'      + double(y(i));
    i = 26 <= y & y <= 51;  z(i) = 'a' - 26 + double(y(i));
    i = 52 <= y & y <= 61;  z(i) = '0' - 52 + double(y(i));
    i =           y == 62;  z(i) = '+';
    i =           y == 63;  z(i) = '/';
    y = z;

    % Add padding if necessary.
    npbytes = 3 * nchunks - ndbytes;     % number of padding bytes
    if npbytes
        y(end-npbytes+1 : end) = '=';     % '=' is used for padding
    end

    if isempty(eol)
        % reshape to a row vector
        y = reshape(y, [1, nebytes]);
    else
        nlines = ceil(nebytes / 76);      % number of lines
        neolbytes = length(eol);          % number of bytes in eol string
        % pad data so it becomes a multiple of 76 elements
        y(nebytes + 1 : 76 * nlines) = 0;
        y = reshape(y, 76, nlines);
        % insert eol strings
        eol = eol(:);
        y(end + 1 : end + neolbytes, :) = eol(:, ones(1, nlines));
        % remove padding, but keep the last eol string
        m = nebytes + neolbytes * (nlines - 1);
        n = (76+neolbytes)*nlines - neolbytes;
        y(m+1 : n) = '';
        % extract and reshape to row vector
        y = reshape(y, 1, m+neolbytes);
    end

    % output is a character array
    y = char(y);
end

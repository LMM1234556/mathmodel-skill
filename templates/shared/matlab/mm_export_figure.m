function record = mm_export_figure(fig, outputStem, meta, options)
%MM_EXPORT_FIGURE Audit, export, and register one MATLAB evidence figure.

arguments
    fig (1,1) matlab.ui.Figure
    outputStem {mustBeTextScalar}
    meta (1,1) struct
    options.RegistryPath {mustBeTextScalar} = ""
    options.Dpi (1,1) double {mustBeInteger, mustBePositive} = 300
    options.Strict (1,1) logical = true
    options.RequireAxisLabels (1,1) logical = true
end

required = ["figure_id", "claim", "decision", "source_paths", "generator", ...
    "chart_type", "chart_type_rationale", "encoding", "uncertainty", "caption"];
missing = strings(0, 1);
for field = required
    if ~isfield(meta, field) || localEmpty(meta.(field))
        missing(end+1) = field; %#ok<AGROW>
    end
end
if ~isempty(missing)
    error('mathmodel:MissingFigureMetadata', ...
        '缺少图表证据字段: %s', strjoin(missing, ', '));
end

if isfield(meta, 'language')
    mm_style(fig, meta.language);
else
    mm_style(fig, "zh");
end
issues = mm_audit_figure(fig, options.RequireAxisLabels);
if options.Strict && any(strcmp({issues.severity}, 'high'))
    messages = string({issues(strcmp({issues.severity}, 'high')).problem});
    error('mathmodel:FigureAuditFailed', ...
        '图表结构审计未通过: %s', strjoin(messages, '; '));
end

stem = char(outputStem);
[folder, name, ~] = fileparts(stem);
if isempty(folder)
    folder = '.';
end
if ~isfolder(folder)
    mkdir(folder);
end
stem = fullfile(folder, name);
pngPath = [stem '.png'];
pdfPath = [stem '.pdf'];
exportgraphics(fig, pngPath, 'Resolution', options.Dpi, 'BackgroundColor', 'white');
exportgraphics(fig, pdfPath, 'ContentType', 'vector', 'BackgroundColor', 'white');

record = meta;
record.renderer = 'MATLAB';
record.matlab_version = version;
record.outputs = {pngPath, pdfPath};
record.audit_issues = issues;
sidecarPath = [stem '.figure.json'];
record.sidecar = sidecarPath;
localWriteJson(sidecarPath, record);

registryPath = char(options.RegistryPath);
if isempty(registryPath)
    registryPath = fullfile(folder, 'figure_registry.json');
end
existing = {};
if isfile(registryPath)
    data = jsondecode(fileread(registryPath));
    if ~isstruct(data) || ~isfield(data, 'figures')
        error('mathmodel:InvalidFigureRegistry', ...
            '图表 registry 格式错误: %s', registryPath);
    end
    if isstruct(data.figures)
        existing = num2cell(data.figures);
    elseif iscell(data.figures)
        existing = data.figures;
    elseif ~isempty(data.figures)
        error('mathmodel:InvalidFigureRegistry', ...
            '图表 registry figures 必须是对象数组');
    end
end
kept = {};
for k = 1:numel(existing)
    item = existing{k};
    if ~(isstruct(item) && isfield(item, 'figure_id') && ...
            strcmp(string(item.figure_id), string(meta.figure_id)))
        kept{end+1} = item; %#ok<AGROW>
    end
end
data = struct('schema_version', 2, 'figures', { [kept, {record}] });
registryFolder = fileparts(registryPath);
if isempty(registryFolder)
    registryFolder = '.';
end
if ~isfolder(registryFolder)
    mkdir(registryFolder);
end
temporaryPath = [tempname(registryFolder) '.json'];
localWriteJson(temporaryPath, data);
movefile(temporaryPath, registryPath, 'f');
record.registry = registryPath;
end

function yes = localEmpty(value)
if ischar(value) || isstring(value)
    yes = all(strlength(strtrim(string(value))) == 0);
elseif iscell(value)
    yes = isempty(value) || all(strlength(strtrim(string(value))) == 0);
else
    yes = isempty(value);
end
end

function localWriteJson(path, value)
text = jsonencode(value, PrettyPrint=true);
fid = fopen(path, 'w', 'n', 'UTF-8');
if fid < 0
    error('mathmodel:CannotWriteJson', '无法写入 %s', path);
end
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, '%s\n', text);
end

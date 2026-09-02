function theme = mm_style(fig, language)
%MM_STYLE Apply vivid, colorblind-aware defaults for paper figures.

if nargin < 1 || isempty(fig)
    fig = gcf;
end
if nargin < 2 || strlength(string(language)) == 0
    language = "zh";
end

palette = [
      0 114 178
    230 159   0
      0 158 115
    213  94   0
    204 121 167
     86 180 233
    240 228  66
      0   0   0
] / 255;

fontName = localFont(language);
set(groot, ...
    'defaultAxesColorOrder', palette, ...
    'defaultAxesFontName', fontName, ...
    'defaultTextFontName', fontName, ...
    'defaultAxesFontSize', 9, ...
    'defaultTextFontSize', 9, ...
    'defaultLineLineWidth', 1.8, ...
    'defaultLineMarkerSize', 5.5, ...
    'defaultLegendBox', 'off');

set(fig, 'Color', 'white', 'Units', 'inches', ...
    'Position', [1 1 6.4 4.0], 'Renderer', 'painters');
axesList = findall(fig, 'Type', 'axes');
for k = 1:numel(axesList)
    ax = axesList(k);
    set(ax, 'FontName', fontName, 'FontSize', 9, ...
        'LineWidth', 0.8, 'Box', 'off', 'TickDir', 'out', ...
        'ColorOrder', palette, ...
        'LineStyleOrder', {'-o','--s',':^','-.d','-v','-->'});
    grid(ax, 'off');
    ax.XColor = [0.15 0.15 0.15];
    ax.YColor = [0.15 0.15 0.15];
end

theme = struct( ...
    'palette', palette, ...
    'font_name', fontName, ...
    'background', [1 1 1], ...
    'context_gray', [0.60 0.60 0.60]);
end

function name = localFont(language)
available = string(listfonts);
if startsWith(lower(string(language)), "zh")
    candidates = ["Microsoft YaHei", "Noto Sans CJK SC", ...
        "Source Han Sans SC", "SimHei", "Arial Unicode MS"];
else
    candidates = ["Arial", "Liberation Sans", "Helvetica"];
end
name = "Helvetica";
for candidate = candidates
    if any(strcmpi(available, candidate))
        name = candidate;
        return;
    end
end
end

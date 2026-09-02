repoRoot = fileparts(fileparts(fileparts(mfilename('fullpath'))));
helperDir = fullfile(repoRoot, 'templates', 'shared', 'matlab');
addpath(helperDir);

workDir = tempname;
mkdir(workDir);
cleanupDir = onCleanup(@() rmdir(workDir, 's')); %#ok<NASGU>

fig = figure('Visible', 'off');
cleanupFig = onCleanup(@() localCloseFigure(fig)); %#ok<NASGU>
mm_style(fig, 'zh');
x = (1:5)';
y = [2 3 5 8 13]';
plot(x, y, '-o', 'DisplayName', '方案 A');
xlabel('时间（h）');
ylabel('目标值（单位）');
legend('Location', 'best');

recommendation = mm_choose_chart('trend');
assert(strcmp(recommendation.recommended, 'line_with_markers'));

meta = struct( ...
    'figure_id', 'TEST-F01', ...
    'claim', '目标值在测试时段内增加', ...
    'decision', '比较相邻时点的变化', ...
    'source_paths', {{'results/test.csv'}}, ...
    'generator', 'tests/matlab/test_mm_figure_pipeline.m', ...
    'chart_type', recommendation.recommended, ...
    'chart_type_rationale', '时间有序，折线保留真实采样间隔；拒绝柱状图', ...
    'encoding', 'x=时间(h), y=目标值(单位), line=方案A', ...
    'uncertainty', '示例无重复试验，不构造区间', ...
    'caption', '五个时点的示例目标值，折线仅连接有序观测。');

stem = fullfile(workDir, 'figures', 'test_result');
record = mm_export_figure(fig, stem, meta);
assert(strcmp(record.renderer, 'MATLAB'));
assert(isfile([stem '.png']));
assert(isfile([stem '.pdf']));
assert(isfile([stem '.figure.json']));
registry = jsondecode(fileread(fullfile(workDir, 'figures', 'figure_registry.json')));
assert(strcmp(registry.figures(1).figure_id, 'TEST-F01'));

theme = mm_style(fig, 'zh');
assert(size(unique(theme.palette, 'rows'), 1) == 8);
assert(all(theme.palette(:) >= 0 & theme.palette(:) <= 1));

disp('MATLAB_FIGURE_PIPELINE_OK');

function localCloseFigure(fig)
if isgraphics(fig)
    close(fig);
end
end

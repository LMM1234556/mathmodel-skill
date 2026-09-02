function issues = mm_audit_figure(fig, requireAxisLabels)
%MM_AUDIT_FIGURE Return structural issues requiring review.

if nargin < 1 || isempty(fig)
    fig = gcf;
end
if nargin < 2
    requireAxisLabels = true;
end
issues = repmat(struct('severity', '', 'where', '', 'problem', ''), 0, 1);

oldUnits = fig.Units;
cleanup = onCleanup(@() set(fig, 'Units', oldUnits));
fig.Units = 'inches';
pos = fig.Position;
if pos(3) < 3.0 || pos(4) < 2.0
    issues(end+1) = localIssue('high', 'figure', ...
        sprintf('画布过小 (%.1f x %.1f in)，最终排版可能不可读', pos(3), pos(4)));
end

axesList = findall(fig, 'Type', 'axes');
if isempty(axesList)
    issues(end+1) = localIssue('high', 'figure', '图中没有坐标轴');
    return;
end

for k = 1:numel(axesList)
    ax = axesList(k);
    visibleChildren = findall(ax, '-property', 'Visible', 'Visible', 'on');
    visibleChildren(visibleChildren == ax) = [];
    if isempty(visibleChildren)
        issues(end+1) = localIssue('medium', sprintf('axes[%d]', k), ...
            '坐标轴没有可见数据图层'); %#ok<AGROW>
    end
    if requireAxisLabels && ~isempty(visibleChildren)
        if strlength(strtrim(string(ax.XLabel.String))) == 0
            issues(end+1) = localIssue('medium', sprintf('axes[%d].xlabel', k), ...
                '缺少 x 轴名称或单位'); %#ok<AGROW>
        end
        if strlength(strtrim(string(ax.YLabel.String))) == 0
            issues(end+1) = localIssue('medium', sprintf('axes[%d].ylabel', k), ...
                '缺少 y 轴名称或单位'); %#ok<AGROW>
        end
    end
    if numel(ax.YAxis) > 1
        issues(end+1) = localIssue('high', sprintf('axes[%d]', k), ...
            '检测到双 y 轴；除非有明确分析理由，否则改为分面图'); %#ok<AGROW>
    end
    if any(abs(ax.View - [0 90]) > 1e-8)
        issues(end+1) = localIssue('high', sprintf('axes[%d]', k), ...
            '检测到 3-D 视角；需改为可准确比较的二维编码'); %#ok<AGROW>
    end
end
end

function value = localIssue(severity, where, problem)
value = struct('severity', severity, 'where', where, 'problem', problem);
end

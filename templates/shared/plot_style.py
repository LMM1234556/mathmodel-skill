"""Shared, inspectable plotting defaults for modeling-competition figures.

Copy this file into a project utility directory.  It provides consistent
Matplotlib defaults and writes a small evidence sidecar for each exported
figure.  It deliberately does not infer scientific validity from appearance.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Iterable, Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager


COLORBLIND_PALETTE = (
    "#0072B2",  # blue
    "#D55E00",  # vermillion
    "#009E73",  # bluish green
    "#CC79A7",  # reddish purple
    "#E69F00",  # orange
    "#56B4E9",  # sky blue
    "#F0E442",  # yellow
    "#000000",  # black
)


def configure_matplotlib(language: str = "zh") -> str:
    """Apply stable paper defaults and return the selected font family."""

    available = {font.name for font in font_manager.fontManager.ttflist}
    zh_fonts = (
        "Noto Sans CJK SC",
        "Source Han Sans SC",
        "Microsoft YaHei",
        "SimHei",
        "Arial Unicode MS",
        "DejaVu Sans",
    )
    en_fonts = ("Arial", "Liberation Sans", "DejaVu Sans")
    candidates = zh_fonts if language.lower().startswith("zh") else en_fonts
    selected = next((name for name in candidates if name in available), "DejaVu Sans")

    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [selected, "DejaVu Sans"],
            "axes.unicode_minus": False,
            "axes.prop_cycle": mpl.cycler(color=COLORBLIND_PALETTE),
            "figure.figsize": (6.4, 4.0),
            "figure.dpi": 120,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.05,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": False,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "legend.frameon": False,
            "lines.linewidth": 1.6,
            "lines.markersize": 4.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    return selected


def audit_figure(
    fig: mpl.figure.Figure,
    *,
    require_axis_labels: bool = True,
) -> list[dict[str, str]]:
    """Return structural issues that still require human interpretation."""

    issues: list[dict[str, str]] = []
    width, height = fig.get_size_inches()
    if width < 3.0 or height < 2.0:
        issues.append(
            {
                "severity": "high",
                "where": "figure",
                "problem": f"画布过小 ({width:.1f}×{height:.1f} in)，最终排版可能不可读",
            }
        )
    if not fig.axes:
        issues.append(
            {"severity": "high", "where": "figure", "problem": "图中没有坐标轴或可见内容"}
        )
        return issues

    for index, ax in enumerate(fig.axes, start=1):
        visible_artists = [
            artist
            for group in (ax.lines, ax.collections, ax.patches, ax.images)
            for artist in group
            if artist.get_visible()
        ]
        if not visible_artists:
            issues.append(
                {
                    "severity": "medium",
                    "where": f"axes[{index}]",
                    "problem": "坐标轴没有可见数据图层",
                }
            )
        if require_axis_labels and visible_artists:
            if not ax.get_xlabel().strip():
                issues.append(
                    {
                        "severity": "medium",
                        "where": f"axes[{index}].xlabel",
                        "problem": "缺少 x 轴名称或单位",
                    }
                )
            if not ax.get_ylabel().strip():
                issues.append(
                    {
                        "severity": "medium",
                        "where": f"axes[{index}].ylabel",
                        "problem": "缺少 y 轴名称或单位",
                    }
                )

        public_labels = [
            artist.get_label()
            for artist in visible_artists
            if hasattr(artist, "get_label")
            and artist.get_label()
            and not artist.get_label().startswith("_")
        ]
        if len(set(public_labels)) >= 2 and ax.get_legend() is None:
            issues.append(
                {
                    "severity": "medium",
                    "where": f"axes[{index}].legend",
                    "problem": "存在多个已命名数据系列但没有图例",
                }
            )

    return issues


def save_figure(
    fig: mpl.figure.Figure,
    output_stem: str | Path,
    *,
    figure_id: str,
    claim: str,
    caption: str,
    source_paths: Sequence[str | Path],
    generator: str,
    formats: Iterable[str] = ("png", "pdf"),
    dpi: int = 300,
    require_axis_labels: bool = True,
    strict: bool = True,
    registry_path: str | Path | None = None,
) -> dict:
    """Audit, export, and register one evidence-bearing figure."""

    required = {
        "figure_id": figure_id,
        "claim": claim,
        "caption": caption,
        "generator": generator,
    }
    missing = [name for name, value in required.items() if not str(value).strip()]
    sources = [str(Path(path)) for path in source_paths]
    if not sources:
        missing.append("source_paths")
    if missing:
        raise ValueError("缺少图表证据字段: " + ", ".join(missing))

    issues = audit_figure(fig, require_axis_labels=require_axis_labels)
    high = [item for item in issues if item["severity"] == "high"]
    if strict and high:
        raise ValueError("图表结构审计未通过: " + "; ".join(i["problem"] for i in high))

    stem = Path(output_stem)
    if stem.suffix:
        stem = stem.with_suffix("")
    stem.parent.mkdir(parents=True, exist_ok=True)

    outputs: list[str] = []
    for fmt in formats:
        normalized = fmt.lower().lstrip(".")
        if normalized not in {"png", "pdf", "svg"}:
            raise ValueError(f"不支持的图表格式: {fmt}")
        target = stem.with_suffix(f".{normalized}")
        fig.savefig(target, dpi=dpi if normalized == "png" else None)
        outputs.append(str(target))

    record = {
        "figure_id": figure_id,
        "claim": claim,
        "caption": caption,
        "source_paths": sources,
        "generator": generator,
        "outputs": outputs,
        "audit_issues": issues,
    }
    sidecar = stem.with_suffix(".figure.json")
    sidecar.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    record["sidecar"] = str(sidecar)
    registry = Path(registry_path) if registry_path else stem.parent / "figure_registry.json"
    if registry.is_file():
        data = json.loads(registry.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("figures"), list):
            raise ValueError(f"图表 registry 格式错误: {registry}")
    else:
        data = {"schema_version": 1, "figures": []}
    data["figures"] = [
        item for item in data["figures"]
        if isinstance(item, dict) and item.get("figure_id") != figure_id
    ]
    data["figures"].append(record)
    registry.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=registry.parent, delete=False,
        prefix=f".{registry.name}.", suffix=".tmp"
    ) as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, registry)
    record["registry"] = str(registry)
    return record


if __name__ == "__main__":
    configure_matplotlib()
    fig, ax = plt.subplots()
    ax.plot([0, 1, 2], [0, 1, 4], marker="o", label="方案 A")
    ax.set(xlabel="时间（h）", ylabel="目标值（单位）")
    ax.legend()
    save_figure(
        fig,
        Path("figures") / "plot_style_smoke",
        figure_id="DEMO-F01",
        claim="示例目标值随时间增加",
        caption="示例数据，仅用于检查绘图环境。",
        source_paths=["synthetic-demo"],
        generator=__file__,
    )

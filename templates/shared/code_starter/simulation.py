"""
仿真类 code starter — 对应论文 §5.x 仿真 / §6 灵敏度
适用: 蒙特卡罗 / 拉丁超立方采样 (LHS) / 系统动力学 ODE / Agent-based

这是可改写的实现起点，不是竞赛加分配方。只有当参数分布、扰动范围、样本量与当前问题有依据时，才使用相应方法；模型名称应准确描述实际实现。
"""

import numpy as np
import pandas as pd
from scipy.stats import qmc
from scipy.integrate import solve_ivp
from pathlib import Path

np.random.seed(42)
Path("results").mkdir(exist_ok=True)


# ============================================================
# 1. 蒙特卡罗 (Monte Carlo) 基本框架
# ============================================================
def monte_carlo(simulator, n_samples=1000, **distributions):
    """
    Args:
        simulator: 单次仿真函数, 接受关键字参数, 返回标量或 dict
        n_samples: 样本数
        distributions: dict of {param_name: callable returning ndarray of size n}
    Returns:
        list of simulator return values
    """
    samples = {k: dist(n_samples) for k, dist in distributions.items()}
    results = []
    for i in range(n_samples):
        kwargs = {k: samples[k][i] for k in distributions}
        results.append(simulator(**kwargs))
    return results, samples


# ============================================================
# 2. 拉丁超立方采样 LHS（适用于需要覆盖多维参数空间的场景）
# ============================================================
def lhs_sampling(d, n, bounds=None, seed=42):
    """
    Args:
        d: 维度 (扰动参数数量)
        n: 样本数
        bounds: list of (low, high) tuples, 长度 d. 默认 [0, 1]
    Returns:
        ndarray (n, d)
    """
    sampler = qmc.LatinHypercube(d=d, seed=seed)
    unit = sampler.random(n=n)  # ∈ [0, 1]^d
    if bounds is None:
        return unit
    lows = np.array([b[0] for b in bounds])
    highs = np.array([b[1] for b in bounds])
    return lows + unit * (highs - lows)


def joint_sensitivity_lhs(simulator, baseline_params, perturbation_levels=None, n_samples=200):
    """
    对所有 baseline_params 做联合 LHS 扰动 (winning_patterns §7)

    Args:
        simulator: callable(**params) -> scalar
        baseline_params: dict {param: baseline_value}
        perturbation_levels: list of perturbation ratios, e.g., [0.05, 0.10, 0.20]
        n_samples: per level
    Returns:
        dict {level: {"samples": ndarray, "outputs": ndarray, "stats": dict}}
    """
    if perturbation_levels is None:
        # 示例默认值；实际使用时应由历史波动、测量误差或业务边界替换。
        perturbation_levels = [0.05, 0.10, 0.20]

    param_names = list(baseline_params.keys())
    d = len(param_names)
    baseline_values = np.array([baseline_params[k] for k in param_names])

    results = {}
    for level in perturbation_levels:
        bounds = [(v * (1 - level), v * (1 + level)) for v in baseline_values]
        samples = lhs_sampling(d, n_samples, bounds)
        outputs = []
        for i in range(n_samples):
            params = {k: samples[i, j] for j, k in enumerate(param_names)}
            outputs.append(simulator(**params))
        outputs = np.array(outputs)
        stats = {
            "mean": outputs.mean(),
            "std": outputs.std(),
            "p5": np.percentile(outputs, 5),
            "p95": np.percentile(outputs, 95),
            "cv": outputs.std() / abs(outputs.mean() + 1e-12),
        }
        results[level] = {"samples": samples, "outputs": outputs, "stats": stats}
    return results, param_names


# ============================================================
# 3. Sobol 全局灵敏度（存在参数交互且样本预算允许时选用）
# ============================================================
def sobol_indices(simulator, param_names, baseline_params, n_samples=1024):
    """
    需要 SALib 库
    Returns: dict {param: {S1, ST}}
    """
    try:
        from SALib.sample import saltelli
        from SALib.analyze import sobol
    except ImportError:
        print("⚠ SALib 未安装, 跳过 Sobol")
        return None

    bounds = [[v * 0.8, v * 1.2] for v in baseline_params.values()]
    problem = {
        "num_vars": len(param_names),
        "names": param_names,
        "bounds": bounds,
    }
    samples = saltelli.sample(problem, n_samples)
    outputs = np.array([simulator(**dict(zip(param_names, s))) for s in samples])
    Si = sobol.analyze(problem, outputs, print_to_console=False)
    return {param: {"S1": float(Si["S1"][i]), "ST": float(Si["ST"][i])}
            for i, param in enumerate(param_names)}


# ============================================================
# 4. ODE 系统仿真示例（带隔离移除项的 SEIR）
# ============================================================
def seir_with_quarantine(t, y, beta, sigma, gamma, kappa):
    """
    SEIR 示例：感染者以 kappa 速率进入移除状态。

    y = [S, E, I, R]
    """
    S, E, I, R = y
    N = S + E + I + R
    dS = -beta * S * I / N
    dE = beta * S * I / N - sigma * E
    dI = sigma * E - gamma * I - kappa * I  # kappa 是隔离率
    dR = gamma * I + kappa * I
    return [dS, dE, dI, dR]


def simulate_seir(N=10000, I0=10, beta=0.3, sigma=0.2, gamma=0.1, kappa=0.05, T=180):
    y0 = [N - I0, 0, I0, 0]
    sol = solve_ivp(seir_with_quarantine, (0, T), y0,
                     args=(beta, sigma, gamma, kappa), dense_output=True,
                     t_eval=np.arange(0, T + 1))
    return {"t": sol.t, "S": sol.y[0], "E": sol.y[1], "I": sol.y[2], "R": sol.y[3],
            "peak_I": sol.y[2].max(), "peak_t": sol.t[sol.y[2].argmax()]}


# ============================================================
# 5. 导出 MATLAB 绘图数据
# ============================================================
def export_lhs_plot_data(samples, outputs, param_names,
                         path="results/simulation_lhs_plot_data.csv"):
    df = pd.DataFrame(samples, columns=param_names)
    df["output"] = outputs
    df.to_csv(path, index=False)
    return df


def export_sobol_plot_data(sobol_result,
                           path="results/simulation_sobol_plot_data.csv"):
    sorted_items = sorted(sobol_result.items(), key=lambda x: x[1]["S1"])
    data = pd.DataFrame({
        "parameter": [item[0] for item in sorted_items],
        "S1": [item[1]["S1"] for item in sorted_items],
        "ST": [item[1]["ST"] for item in sorted_items],
    })
    data.to_csv(path, index=False)
    return data


# ============================================================
# 主流程示例 (对应论文 §5.x + §6)
# ============================================================
if __name__ == "__main__":
    # SEIR 仿真示例
    result = simulate_seir(N=10000, I0=10, beta=0.3, sigma=0.2, gamma=0.1, kappa=0.05)
    print(f"峰值感染数: {result['peak_I']:.0f}")
    print(f"峰值时间: 第 {result['peak_t']:.1f} 天")

    pd.DataFrame({
        "time_day": result["t"],
        "susceptible": result["S"],
        "exposed": result["E"],
        "infected": result["I"],
        "removed": result["R"],
    }).to_csv("results/simulation_seir_plot_data.csv", index=False)

    # LHS 联合灵敏度
    def simulator(beta, sigma, gamma, kappa):
        r = simulate_seir(beta=beta, sigma=sigma, gamma=gamma, kappa=kappa)
        return r["peak_I"]

    baseline = {"beta": 0.3, "sigma": 0.2, "gamma": 0.1, "kappa": 0.05}
    sens_results, param_names = joint_sensitivity_lhs(
        simulator, baseline, perturbation_levels=[0.05, 0.10, 0.20], n_samples=100
    )
    for level, r in sens_results.items():
        print(f"\n扰动 ±{level*100:.0f}%:")
        print(f"  Peak I 5%-95% 区间: [{r['stats']['p5']:.0f}, {r['stats']['p95']:.0f}]")
        print(f"  CV: {r['stats']['cv']*100:.2f}%")

    export_lhs_plot_data(
        sens_results[0.10]["samples"],
        sens_results[0.10]["outputs"],
        param_names,
    )
    print("\n已保存 MATLAB 绘图数据到 results/")

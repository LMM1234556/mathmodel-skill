"""
分类类 code starter — 对应论文 §5.x 分类/判别
适用: 二分类 / 多分类 / 不平衡数据

国赛常见: Logistic / SVM / 随机森林 / XGBoost
变体名建议: "Stacking 集成分类模型"
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, StackingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
from pathlib import Path

np.random.seed(42)
Path("results").mkdir(exist_ok=True)


# ============================================================
# 1. 单模型评估
# ============================================================
def evaluate_classifier(model, X_train, X_test, y_train, y_test):
    """
    返回完整指标 + 混淆矩阵
    """
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, average='weighted', zero_division=0),
        "recall": recall_score(y_test, y_pred, average='weighted', zero_division=0),
        "f1": f1_score(y_test, y_pred, average='weighted', zero_division=0),
    }

    # AUC (二分类)
    if len(np.unique(y_test)) == 2 and hasattr(model, "predict_proba"):
        y_proba = model.predict_proba(X_test)[:, 1]
        metrics["auc"] = roc_auc_score(y_test, y_proba)

    cm = confusion_matrix(y_test, y_pred)
    return {"model": model, "metrics": metrics, "confusion_matrix": cm,
            "y_pred": y_pred}


# ============================================================
# 2. 多模型对比
# ============================================================
def compare_models(X, y, test_size=0.2):
    """
    跑 5 个模型对比, 报告 5 折交叉验证 + 测试集指标

    标准化放在 Pipeline 内, 确保每个交叉验证折只使用该折的
    训练部分拟合 scaler, 避免折外信息泄漏。
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y)

    models = {
        "Logistic": LogisticRegression(max_iter=1000, random_state=42),
        "SVM-RBF": SVC(kernel='rbf', probability=True, random_state=42),
        "DecisionTree": DecisionTreeClassifier(random_state=42),
        "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42),
        "GBDT": GradientBoostingClassifier(random_state=42),
    }

    results = {}
    for name, model in models.items():
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", model),
        ])
        # 5 折 CV
        cv_scores = cross_val_score(
            pipeline, X_train, y_train, cv=5, scoring='f1_weighted')
        # 测试集
        eval_result = evaluate_classifier(
            pipeline, X_train, X_test, y_train, y_test)
        eval_result["cv_f1_mean"] = cv_scores.mean()
        eval_result["cv_f1_std"] = cv_scores.std()
        results[name] = eval_result

    # 保留旧版 API: 返回一个已在完整训练集上拟合的 scaler。
    scaler = results["Logistic"]["model"].named_steps["scaler"]
    return results, scaler


# ============================================================
# 3. Stacking 集成 (winning_patterns §4 命名变体)
# ============================================================
def stacking_classifier(X_train, X_test, y_train, y_test):
    """
    Stacking: RF + SVM + GBDT → Logistic 元学习器
    """
    base_estimators = [
        ('rf', RandomForestClassifier(n_estimators=100, random_state=42)),
        ('svm', Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', SVC(kernel='rbf', probability=True, random_state=42)),
        ])),
        ('gb', GradientBoostingClassifier(random_state=42)),
    ]
    final_estimator = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', LogisticRegression(random_state=42)),
    ])
    stack = StackingClassifier(
        estimators=base_estimators,
        final_estimator=final_estimator,
        cv=5,
        n_jobs=1,
    )
    return evaluate_classifier(stack, X_train, X_test, y_train, y_test)


# ============================================================
# 4. 不平衡数据处理 (SMOTE)
# ============================================================
def handle_imbalanced(X, y, method="smote"):
    """
    非常用但偶尔需要; 国赛附件数据有时正负样本比例 1:9
    """
    try:
        from imblearn.over_sampling import SMOTE
        from imblearn.under_sampling import RandomUnderSampler
        if method == "smote":
            sampler = SMOTE(random_state=42)
        elif method == "undersample":
            sampler = RandomUnderSampler(random_state=42)
        X_res, y_res = sampler.fit_resample(X, y)
        return X_res, y_res
    except ImportError:
        print("⚠ imblearn 未安装, 直接返回原数据")
        return X, y


# ============================================================
# 5. 导出 MATLAB 绘图数据
# ============================================================
def export_plot_data(results, confusion, class_names=None, output_dir="results"):
    """保存稳定的 CSV，定量图由 MATLAB 读取并生成。"""
    output = Path(output_dir)
    output.mkdir(exist_ok=True)
    comparison = pd.DataFrame([
        {
            "model": name,
            "test_f1": value["metrics"]["f1"],
            "cv_f1_mean": value["cv_f1_mean"],
            "cv_f1_std": value["cv_f1_std"],
        }
        for name, value in results.items()
    ])
    comparison.to_csv(output / "classification_comparison_plot_data.csv", index=False)
    labels = class_names or [f"class_{i}" for i in range(confusion.shape[0])]
    pd.DataFrame(confusion, index=labels, columns=labels).to_csv(
        output / "classification_confusion_matrix_plot_data.csv",
        index_label="actual_class",
    )


# ============================================================
# 主流程示例
# ============================================================
if __name__ == "__main__":
    # 模拟二分类数据 (实际从附件读)
    from sklearn.datasets import make_classification
    X, y = make_classification(n_samples=500, n_features=10, n_informative=5,
                                n_redundant=2, n_classes=2, random_state=42,
                                weights=[0.7, 0.3])  # 不平衡

    # 多模型对比
    results, _ = compare_models(X, y, test_size=0.2)
    print("=== 各模型对比 ===")
    for name, r in results.items():
        print(f"{name}: F1={r['metrics']['f1']:.3f}, CV_F1={r['cv_f1_mean']:.3f}±{r['cv_f1_std']:.3f}")

    # Stacking
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    stack_result = stacking_classifier(X_train, X_test, y_train, y_test)
    print(f"\nStacking 集成: F1={stack_result['metrics']['f1']:.3f}")

    export_plot_data(
        results,
        stack_result["confusion_matrix"],
        class_names=["类 0", "类 1"],
    )
    print("\n已保存 MATLAB 绘图数据到 results/")

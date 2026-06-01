from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# === 1. Путь к results.csv ===
results_path = Path(
    r"D:\Other\university\Works\5th semester\Team Project\segmentation_model_proj\runs\yolo11s_road_damage_768_full_001\results.csv"
)

# === 2. Чтение CSV ===
df = pd.read_csv(results_path)
df.columns = df.columns.str.strip()

# === 3. Папка для сохранения графиков ===
out_dir = results_path.parent
train_plot_path = out_dir / "train_losses.png"
val_plot_path = out_dir / "val_metrics_and_losses.png"
lr_plot_path = out_dir / "learning_rate.png"

# === 4. Поиск лучшей эпохи ===
main_metric = "metrics/mAP50-95(B)"

best_idx = df[main_metric].idxmax()
best_epoch = int(df.loc[best_idx, "epoch"])
best_map5095 = float(df.loc[best_idx, "metrics/mAP50-95(B)"])
best_map50 = float(df.loc[best_idx, "metrics/mAP50(B)"])
best_precision = float(df.loc[best_idx, "metrics/precision(B)"])
best_recall = float(df.loc[best_idx, "metrics/recall(B)"])

print("Best epoch by mAP50-95:")
print(f"epoch      = {best_epoch}")
print(f"precision  = {best_precision:.5f}")
print(f"recall     = {best_recall:.5f}")
print(f"mAP50      = {best_map50:.5f}")
print(f"mAP50-95   = {best_map5095:.5f}")


# === 5. График TRAIN losses ===
plt.figure(figsize=(12, 6))

plt.plot(df["epoch"], df["train/box_loss"], marker="o", label="train/box_loss")
plt.plot(df["epoch"], df["train/cls_loss"], marker="o", label="train/cls_loss")
plt.plot(df["epoch"], df["train/dfl_loss"], marker="o", label="train/dfl_loss")

plt.axvline(best_epoch, linestyle="--", linewidth=1.5,
            label=f"best epoch: {best_epoch}")

plt.title("Training losses")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(train_plot_path, dpi=200)
plt.show()


# === 6. График VALIDATION: метрики + val losses ===
fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

# 6.1 Метрики на валидации
axes[0].plot(df["epoch"], df["metrics/precision(B)"],
             marker="o", label="Precision")
axes[0].plot(df["epoch"], df["metrics/recall(B)"], marker="o", label="Recall")
axes[0].plot(df["epoch"], df["metrics/mAP50(B)"], marker="o", label="mAP50")
axes[0].plot(df["epoch"], df["metrics/mAP50-95(B)"],
             marker="o", label="mAP50-95")

axes[0].axvline(best_epoch, linestyle="--", linewidth=1.5,
                label=f"best epoch: {best_epoch}")
axes[0].scatter(
    [best_epoch],
    [best_map5095],
    s=80,
    zorder=5,
    label=f"best mAP50-95: {best_map5095:.5f}"
)

axes[0].set_title("Validation metrics")
axes[0].set_ylabel("Metric value")
axes[0].grid(True, alpha=0.3)
axes[0].legend()

# 6.2 Losses на валидации
axes[1].plot(df["epoch"], df["val/box_loss"], marker="o", label="val/box_loss")
axes[1].plot(df["epoch"], df["val/cls_loss"], marker="o", label="val/cls_loss")
axes[1].plot(df["epoch"], df["val/dfl_loss"], marker="o", label="val/dfl_loss")

axes[1].axvline(best_epoch, linestyle="--", linewidth=1.5,
                label=f"best epoch: {best_epoch}")

axes[1].set_title("Validation losses")
axes[1].set_xlabel("Epoch")
axes[1].set_ylabel("Loss")
axes[1].grid(True, alpha=0.3)
axes[1].legend()

plt.tight_layout()
plt.savefig(val_plot_path, dpi=200)
plt.show()


# === 7. Отдельный график learning rate, если нужен ===
lr_cols = [col for col in df.columns if col.startswith("lr/")]

plt.figure(figsize=(12, 6))

for col in lr_cols:
    plt.plot(df["epoch"], df[col], label=col)

plt.axvline(best_epoch, linestyle="--", linewidth=1.5,
            label=f"best epoch: {best_epoch}")

plt.title("Learning rate schedule")
plt.xlabel("Epoch")
plt.ylabel("Learning rate")
plt.grid(True, alpha=0.3)
plt.legend(ncol=2)
plt.tight_layout()
plt.savefig(lr_plot_path, dpi=200)
plt.show()


print("\nSaved plots:")
print(train_plot_path)
print(val_plot_path)
print(lr_plot_path)

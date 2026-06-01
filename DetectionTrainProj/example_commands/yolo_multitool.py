import argparse
import subprocess
import sys
from pathlib import Path


# ============================================================
# Paths
# Fill these constants before running the script.
# Leave unused paths empty.
# ============================================================

PYTHON_EXECUTABLE = sys.executable

YOLO_EXECUTABLE = ""
VOC_BUILDER_MODULE = "voc_yolo_builder"

SOURCE_ROOT = ""
OUTPUT_DIR = ""

BEST_MODEL_PATH = ""
PRETRAINED_MODEL_PATH = ""
RESUME_MODEL_PATH = ""

PREDICT_SOURCE = ""
PREDICT_PROJECT_DIR = ""

DATA_YAML_PATH = ""
TRAIN_PROJECT_DIR = ""


# ============================================================
# Dataset build settings
# ============================================================

BUILD_SAMPLE_FRACTION = 1.0
BUILD_MAX_OUTPUT_IMAGES = 40000
BUILD_VALIDATION_RATIO = 0.10
BUILD_TEST_RATIO = 0.10
BUILD_SAMPLING_STRATEGY = "balanced"
BUILD_TARGET_MIN_IMAGES_PER_CLASS = 1200
BUILD_MIN_SOURCE_IMAGES_PER_CLASS = 800
BUILD_RANDOM_SEED = 42
BUILD_USE_HARDLINKS = True


# ============================================================
# Predict settings
# ============================================================

PREDICT_IMAGE_SIZE = 768
PREDICT_CONFIDENCE = 0.22
PREDICT_IOU = 0.7
PREDICT_DEVICE = 0
PREDICT_SAVE = True
PREDICT_SAVE_TXT = True
PREDICT_SAVE_CONF = True
PREDICT_RUN_NAME = "predict_run"


# ============================================================
# Validation settings
# ============================================================

VAL_SPLIT = "test"
VAL_IMAGE_SIZE = 768
VAL_BATCH = 1
VAL_CONFIDENCE = 0.001
VAL_IOU = 0.7
VAL_DEVICE = 0
VAL_PLOTS = True
VAL_SAVE_JSON = True
VAL_SAVE_TXT = True
VAL_SAVE_CONF = True
VAL_RUN_NAME = "validation_run"


# ============================================================
# Training settings
# ============================================================

TRAIN_RUN_NAME = "train_run"
TRAIN_EXIST_OK = False
TRAIN_EPOCHS = 1000
TRAIN_PATIENCE = 100
TRAIN_SAVE = True
TRAIN_SAVE_PERIOD = 1
TRAIN_IMAGE_SIZE = 768
TRAIN_BATCH = -1
TRAIN_DEVICE = 0
TRAIN_AMP = True
TRAIN_CACHE = False
TRAIN_WORKERS = 4
TRAIN_RECT = False

TRAIN_HSV_H = 0.015
TRAIN_HSV_S = 0.45
TRAIN_HSV_V = 0.35
TRAIN_DEGREES = 3
TRAIN_TRANSLATE = 0.08
TRAIN_SCALE = 0.35
TRAIN_SHEAR = 1.0
TRAIN_PERSPECTIVE = 0.0002
TRAIN_FLIPLR = 0.5
TRAIN_FLIPUD = 0.0
TRAIN_MOSAIC = 0.35
TRAIN_CLOSE_MOSAIC = 50
TRAIN_MIXUP = 0.0
TRAIN_CUTMIX = 0.0
TRAIN_COPY_PASTE = 0.0


# ============================================================
# Helpers
# ============================================================

def as_yolo_bool(value: bool) -> str:
    return "True" if value else "False"


def validate_existing_path(name: str, value: str, *, must_be_file: bool = False, must_be_dir: bool = False) -> list[str]:
    errors = []

    if not value:
        errors.append(f"{name} is empty.")
        return errors

    path = Path(value)

    if not path.exists():
        errors.append(f"{name} does not exist: {value}")
        return errors

    if must_be_file and not path.is_file():
        errors.append(f"{name} is not a file: {value}")

    if must_be_dir and not path.is_dir():
        errors.append(f"{name} is not a directory: {value}")

    return errors


def validate_output_path(name: str, value: str) -> list[str]:
    errors = []

    if not value:
        errors.append(f"{name} is empty.")
        return errors

    parent = Path(value).expanduser().resolve().parent

    if not parent.exists():
        errors.append(f"{name} parent directory does not exist: {parent}")

    return errors


def validate_yolo_executable() -> list[str]:
    return validate_existing_path(
        "YOLO_EXECUTABLE",
        YOLO_EXECUTABLE,
        must_be_file=True,
    )


def stop_if_invalid(errors: list[str]) -> None:
    if errors:
        print("Invalid configuration:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)


def run_command(command: list[str]) -> None:
    print("Running command:")
    print(" ".join(f'"{part}"' if " " in str(part)
          else str(part) for part in command))
    print()

    completed_process = subprocess.run(command)

    if completed_process.returncode != 0:
        print(f"Command failed with exit code {completed_process.returncode}.")
        sys.exit(completed_process.returncode)


# ============================================================
# Commands
# ============================================================

def build_dataset() -> None:
    errors = []
    errors += validate_existing_path("SOURCE_ROOT",
                                     SOURCE_ROOT, must_be_dir=True)
    errors += validate_output_path("OUTPUT_DIR", OUTPUT_DIR)
    stop_if_invalid(errors)

    command = [
        PYTHON_EXECUTABLE,
        "-m",
        VOC_BUILDER_MODULE,
        "--source-root",
        SOURCE_ROOT,
        "--output-dir",
        OUTPUT_DIR,
        "--sample-fraction",
        str(BUILD_SAMPLE_FRACTION),
        "--max-output-images",
        str(BUILD_MAX_OUTPUT_IMAGES),
        "--validation-ratio",
        str(BUILD_VALIDATION_RATIO),
        "--test-ratio",
        str(BUILD_TEST_RATIO),
        "--sampling-strategy",
        BUILD_SAMPLING_STRATEGY,
        "--target-min-images-per-class",
        str(BUILD_TARGET_MIN_IMAGES_PER_CLASS),
        "--min-source-images-per-class",
        str(BUILD_MIN_SOURCE_IMAGES_PER_CLASS),
        "--random-seed",
        str(BUILD_RANDOM_SEED),
    ]

    if BUILD_USE_HARDLINKS:
        command.append("--use-hardlinks")

    run_command(command)


def predict() -> None:
    errors = []
    errors += validate_yolo_executable()
    errors += validate_existing_path("BEST_MODEL_PATH",
                                     BEST_MODEL_PATH, must_be_file=True)
    errors += validate_existing_path("PREDICT_SOURCE", PREDICT_SOURCE)
    errors += validate_output_path("PREDICT_PROJECT_DIR", PREDICT_PROJECT_DIR)
    stop_if_invalid(errors)

    command = [
        YOLO_EXECUTABLE,
        "detect",
        "predict",
        f"model={BEST_MODEL_PATH}",
        f"source={PREDICT_SOURCE}",
        f"imgsz={PREDICT_IMAGE_SIZE}",
        f"conf={PREDICT_CONFIDENCE}",
        f"iou={PREDICT_IOU}",
        f"device={PREDICT_DEVICE}",
        f"save={as_yolo_bool(PREDICT_SAVE)}",
        f"save_txt={as_yolo_bool(PREDICT_SAVE_TXT)}",
        f"save_conf={as_yolo_bool(PREDICT_SAVE_CONF)}",
        f"project={PREDICT_PROJECT_DIR}",
        f"name={PREDICT_RUN_NAME}",
    ]

    run_command(command)


def validate_model() -> None:
    errors = []
    errors += validate_yolo_executable()
    errors += validate_existing_path("BEST_MODEL_PATH",
                                     BEST_MODEL_PATH, must_be_file=True)
    errors += validate_existing_path("DATA_YAML_PATH",
                                     DATA_YAML_PATH, must_be_file=True)
    stop_if_invalid(errors)

    command = [
        YOLO_EXECUTABLE,
        "val",
        f"model={BEST_MODEL_PATH}",
        f"data={DATA_YAML_PATH}",
        f"split={VAL_SPLIT}",
        f"imgsz={VAL_IMAGE_SIZE}",
        f"batch={VAL_BATCH}",
        f"conf={VAL_CONFIDENCE}",
        f"iou={VAL_IOU}",
        f"device={VAL_DEVICE}",
        f"plots={as_yolo_bool(VAL_PLOTS)}",
        f"save_json={as_yolo_bool(VAL_SAVE_JSON)}",
        f"save_txt={as_yolo_bool(VAL_SAVE_TXT)}",
        f"save_conf={as_yolo_bool(VAL_SAVE_CONF)}",
        f"name={VAL_RUN_NAME}",
    ]

    run_command(command)


def train() -> None:
    errors = []
    errors += validate_yolo_executable()
    errors += validate_existing_path("PRETRAINED_MODEL_PATH",
                                     PRETRAINED_MODEL_PATH, must_be_file=True)
    errors += validate_existing_path("DATA_YAML_PATH",
                                     DATA_YAML_PATH, must_be_file=True)
    errors += validate_output_path("TRAIN_PROJECT_DIR", TRAIN_PROJECT_DIR)
    stop_if_invalid(errors)

    command = [
        YOLO_EXECUTABLE,
        "detect",
        "train",
        f"model={PRETRAINED_MODEL_PATH}",
        f"data={DATA_YAML_PATH}",
        f"project={TRAIN_PROJECT_DIR}",
        f"name={TRAIN_RUN_NAME}",
        f"exist_ok={as_yolo_bool(TRAIN_EXIST_OK)}",
        f"epochs={TRAIN_EPOCHS}",
        f"patience={TRAIN_PATIENCE}",
        f"save={as_yolo_bool(TRAIN_SAVE)}",
        f"save_period={TRAIN_SAVE_PERIOD}",
        f"imgsz={TRAIN_IMAGE_SIZE}",
        f"batch={TRAIN_BATCH}",
        f"device={TRAIN_DEVICE}",
        f"amp={as_yolo_bool(TRAIN_AMP)}",
        f"cache={as_yolo_bool(TRAIN_CACHE)}",
        f"workers={TRAIN_WORKERS}",
        f"rect={as_yolo_bool(TRAIN_RECT)}",
        f"hsv_h={TRAIN_HSV_H}",
        f"hsv_s={TRAIN_HSV_S}",
        f"hsv_v={TRAIN_HSV_V}",
        f"degrees={TRAIN_DEGREES}",
        f"translate={TRAIN_TRANSLATE}",
        f"scale={TRAIN_SCALE}",
        f"shear={TRAIN_SHEAR}",
        f"perspective={TRAIN_PERSPECTIVE}",
        f"fliplr={TRAIN_FLIPLR}",
        f"flipud={TRAIN_FLIPUD}",
        f"mosaic={TRAIN_MOSAIC}",
        f"close_mosaic={TRAIN_CLOSE_MOSAIC}",
        f"mixup={TRAIN_MIXUP}",
        f"cutmix={TRAIN_CUTMIX}",
        f"copy_paste={TRAIN_COPY_PASTE}",
    ]

    run_command(command)


def resume_training() -> None:
    errors = []
    errors += validate_yolo_executable()
    errors += validate_existing_path("RESUME_MODEL_PATH",
                                     RESUME_MODEL_PATH, must_be_file=True)
    stop_if_invalid(errors)

    command = [
        YOLO_EXECUTABLE,
        "detect",
        "train",
        "resume=True",
        f"model={RESUME_MODEL_PATH}",
    ]

    run_command(command)


# ============================================================
# CLI
# ============================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Project CLI for dataset conversion, YOLO prediction, validation, training, and training resume."
    )

    parser.add_argument(
        "action",
        choices=[
            "build-dataset",
            "predict",
            "validate",
            "train",
            "resume-training",
        ],
        help="Action to execute.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    actions = {
        "build-dataset": build_dataset,
        "predict": predict,
        "validate": validate_model,
        "train": train,
        "resume-training": resume_training,
    }

    actions[args.action]()


if __name__ == "__main__":
    main()

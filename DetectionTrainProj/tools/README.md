# Pascal VOC XML to YOLO Dataset Builder

A small, Windows-friendly Python package that converts Pascal VOC XML annotations into an Ultralytics-compatible YOLO dataset.

## Expected source layout

```text
<root>/
  <region>/
    train/
      images/
        image_001.jpg
      annotations/
        xmls/
          image_001.xml
```

## Run

From the folder that contains `voc_yolo_builder/`:

```bash
python -m voc_yolo_builder --root "D:/datasets/source" --out "D:/datasets/yolo_out"
```

Optional flags:

```bash
python -m voc_yolo_builder \
  --root "D:/datasets/source" \
  --out "D:/datasets/yolo_out" \
  --max-images 20000 \
  --fraction 0.25 \
  --val-ratio 0.10 \
  --sampling balanced \
  --min-images-per-class 1200 \
  --min-global-images-per-class 800 \
  --seed 42 \
  --hardlink
```

## Output layout

```text
<out>/
  data.yaml
  images/
    train/
    val/
  labels/
    train/
    val/
```

Empty `.txt` label files are intentionally written for negative samples.

## Notes

- Pillow is only required when an XML file has missing or invalid `<size>` metadata.
- The internal table printer has no external dependency.
- Existing output files are not deleted automatically. Use a clean output folder for fully reproducible stats.

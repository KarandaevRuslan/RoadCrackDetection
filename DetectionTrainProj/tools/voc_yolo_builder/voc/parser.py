"""Pascal VOC XML parsing and YOLO label conversion."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..system.io_utils import clip, read_image_size_with_pillow, to_float
from ..domain.models import ImageAnnotationPair, VocObject


def parse_voc_xml(
    xml_path: Path,
) -> Tuple[Optional[float], Optional[float], List[VocObject]]:
    """Parse a Pascal VOC XML file and return image size plus object boxes."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    size = root.find("size")
    width = to_float(size.findtext("width") if size is not None else None)
    height = to_float(size.findtext("height") if size is not None else None)

    objects: List[VocObject] = []
    for xml_object in root.findall("object"):
        class_name = (xml_object.findtext("name") or "").strip()
        box = xml_object.find("bndbox")
        if not class_name or box is None:
            continue

        xmin = to_float(box.findtext("xmin"))
        ymin = to_float(box.findtext("ymin"))
        xmax = to_float(box.findtext("xmax"))
        ymax = to_float(box.findtext("ymax"))

        if None in (xmin, ymin, xmax, ymax):
            continue

        if xmax < xmin:  # type: ignore
            xmin, xmax = xmax, xmin
        if ymax < ymin:  # type: ignore
            ymin, ymax = ymax, ymin

        objects.append(
            VocObject(
                class_name,
                xmin,  # type: ignore
                ymin,  # type: ignore
                xmax,  # type: ignore
                ymax))  # type: ignore

    return width, height, objects


def voc_bbox_to_yolo(
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
    image_width: float,
    image_height: float,
) -> Tuple[float, float, float, float]:
    """Convert a VOC bounding box to normalized YOLO format."""
    box_width = max(0.0, (xmax - xmin) / image_width)
    box_height = max(0.0, (ymax - ymin) / image_height)
    x_center = ((xmin + xmax) / 2.0) / image_width
    y_center = ((ymin + ymax) / 2.0) / image_height
    return x_center, y_center, box_width, box_height


def yolo_lines_from_pair(
    pair: ImageAnnotationPair,
    class_to_id: Dict[str, int],
) -> List[str]:
    """Build YOLO label lines for one image/XML pair."""
    width, height, objects = parse_voc_xml(pair.xml_path)

    if not width or not height or width <= 1 or height <= 1:
        image_width, image_height = read_image_size_with_pillow(
            pair.image_path)
        width, height = float(image_width), float(image_height)

    lines: List[str] = []
    for obj in objects:
        class_id = class_to_id.get(obj.class_name)
        if class_id is None:
            continue

        x_center, y_center, box_width, box_height = voc_bbox_to_yolo(
            obj.xmin,
            obj.ymin,
            obj.xmax,
            obj.ymax,
            width,
            height,
        )

        x_center = clip(x_center)
        y_center = clip(y_center)
        box_width = clip(box_width)
        box_height = clip(box_height)

        if box_width <= 0.0 or box_height <= 0.0:
            continue

        lines.append(
            f"{class_id} {x_center:.6f} {y_center:.6f} "
            f"{box_width:.6f} {box_height:.6f}"
        )

    return lines

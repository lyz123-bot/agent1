"""
locator/recognizer/utils.py
──────────────────────────
RF‑DETR 物体检测 —— 单例模型 + 本地权重加载
返回每个检测目标的类别与置信度，以及带框可视化图片 URL
"""

import uuid
import inspect
from pathlib import Path
from typing import Optional, Dict, List

import torch
import argparse
from PIL import Image
from django.conf import settings
import supervision as sv

from rfdetr import RFDETRBase
from rfdetr.util.coco_classes import COCO_CLASSES

# 让 argparse.Namespace 成为安全全局，兼容 PyTorch 2.6+
try:
    torch.serialization.add_safe_globals([argparse.Namespace])
except AttributeError:
    pass

_model: Optional[RFDETRBase] = None
_box_annot = sv.BoxAnnotator()
_label_annot = sv.LabelAnnotator()


def _smart_torch_load(path: Path):
    sig = inspect.signature(torch.load)
    if "weights_only" in sig.parameters:
        return torch.load(path, map_location="cpu", weights_only=False)
    else:
        return torch.load(path, map_location="cpu")


def _get_inner_torch_module(obj):
    if hasattr(obj, "load_state_dict"):
        return obj
    for name in ("model", "net", "module"):
        if hasattr(obj, name):
            found = _get_inner_torch_module(getattr(obj, name))
            if found is not None:
                return found
    return None


def _get_model() -> RFDETRBase:
    global _model
    if _model is not None:
        return _model

    _model = RFDETRBase(pretrained=False)
    weight_path = Path(settings.RFDETR_WEIGHTS_PATH)
    if not weight_path.exists():
        raise FileNotFoundError(f"未找到权重文件: {weight_path}")

    state_dict = _smart_torch_load(weight_path)
    torch_mod = _get_inner_torch_module(_model)
    if torch_mod is None:
        raise RuntimeError("未能找到 nn.Module 实例以加载权重")

    try:
        torch_mod.load_state_dict(state_dict, strict=True)
    except RuntimeError:
        cleaned = {k.replace("module.", ""): v for k, v in state_dict.items()}
        torch_mod.load_state_dict(cleaned, strict=False)
    torch_mod.eval()
    return _model


def recognize_image(image_path: str, threshold: float = 0.5) -> Optional[Dict]:
    """
    返回:
      {
        "image_url": "/media/recognize/xxx.jpg",
        "results": [
          {"type": "person", "confidence": 92.31},
          {"type": "dog",    "confidence": 75.10},
          ...
        ]
      }
    如果 detections 为空，返回 None。
    """
    model = _get_model()
    img = Image.open(image_path).convert("RGB")
    dets = model.predict(img, threshold=threshold)
    if len(dets.confidence) == 0:
        return None

    # 构建多条结果
    results: List[Dict] = []
    for cls_id, score in zip(dets.class_id, dets.confidence):
        label = COCO_CLASSES[int(cls_id)]
        results.append({
            "type": label,
            "confidence": round(float(score) * 100, 2)
        })

    # 可视化
    vis = img.copy()
    vis = _box_annot.annotate(vis, dets)
    vis = _label_annot.annotate(
        vis,
        dets,
        [f"{COCO_CLASSES[int(c)]} {s:.2f}" for c, s in zip(dets.class_id, dets.confidence)]
    )

    # 保存
    save_dir = Path(settings.MEDIA_ROOT) / "recognize"
    save_dir.mkdir(parents=True, exist_ok=True)
    out_name = f"{uuid.uuid4().hex}.jpg"
    out_path = save_dir / out_name
    vis.save(out_path, "JPEG", quality=92)

    return {
        "image_url": f"{settings.MEDIA_URL}recognize/{out_name}",
        "results": results
    }

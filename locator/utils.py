# locator/utils.py

import os
import cv2
import json
from django.conf import settings
from pathlib import Path

from .dataload import DataLoader
from .sift_model import ImageLocalizer

# —— 配置项 ——
DATASET_ROOT = getattr(settings, 'LOCATOR_DATASET_ROOT',
                       os.path.join(settings.BASE_DIR, 'data'))
FEATURES_PATH = getattr(settings, 'LOCATOR_FEATURES_PATH',
                        os.path.join(settings.BASE_DIR, 'val_features.pkl'))
FEATURE_TYPE = getattr(settings, 'LOCATOR_FEATURE_TYPE', 'sift')
# 你的 locations.json 文件路径
LOC_MAP_PATH = getattr(settings, 'LOCATOR_LOCATIONS_MAP',
                       os.path.join(settings.BASE_DIR, 'locations.json'))

# —— 全局初始化 ——
_dataloader = DataLoader(DATASET_ROOT)
_database_features, _database_paths = _dataloader.load_features(FEATURES_PATH)

_localizer = ImageLocalizer(feature_type=FEATURE_TYPE)
_localizer.database_features = _database_features
_localizer.database_paths = _database_paths

# —— 加载地点映射表 ——
_location_map = {}
try:
    if os.path.exists(LOC_MAP_PATH):
        with open(LOC_MAP_PATH, "r", encoding="utf-8") as f:
            _location_map = json.load(f)
except Exception as e:
    print(f"[locator] Failed to load location map: {e}")
    _location_map = {}


def _infer_location(db_name: str) -> str:
    """
    根据文件名获取地点文本，优先查映射表，否则用文件名去掉后缀兜底。
    """
    if db_name in _location_map:
        return _location_map[db_name]  # json 文件中的中文名
    # 兜底：用文件名（去掉后缀）
    return Path(db_name).stem.replace("_", " ").replace("-", " ")


def detect_locations(image_path: str, top_k: int = 1):
    """
    对输入图像做特征匹配，返回 top_k 结果，并附带地点文字。
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"无法读取图像文件：{image_path}")
    h, w = img.shape[:2]

    sims = _localizer.query_image(image_path, top_k=top_k)

    predictions = []
    for db_name, score in sims:
        location_text = _infer_location(db_name)  # ✅ 用映射表取中文名
        predictions.append({
            "label": db_name,
            "location_text": location_text,
            "match_score": score,
            "x": 0,
            "y": 0,
            "width": w,
            "height": h,
        })

    return predictions

# locator/caption/utils.py
"""图像描述：使用 DeepSeek API，不再依赖本地 Qwen VL。"""
from typing import Any, Dict, Optional

from ..deepseek_client import caption_image as _caption_image


def caption_image(
    image_path: str,
    max_new_tokens: int = 180,
    locator_context: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """返回中文描述；出错返回 None。locator_context 为识别/定位结果，写入提示词。"""
    return _caption_image(
        image_path, max_new_tokens=max_new_tokens, locator_context=locator_context
    )


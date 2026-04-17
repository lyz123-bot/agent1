"""
locator/chat/utils.py
─────────────────────
封装两类对话能力，统一走 DeepSeek API（不再依赖本地 Qwen VL）：

1. chat_with_caption          —— 仅用文本 caption 做上下文（纯文字 QA）
2. vqa_chat_with_image        —— 每轮把图片再次送入 API（真正 VQA）
"""

from typing import Any, Dict, List, Optional

from ..deepseek_client import chat_with_caption as _chat_with_caption
from ..deepseek_client import vqa_chat_with_image as _vqa_chat_with_image


def chat_with_caption(
    caption: str,
    history: List[dict],
    question: str,
    max_new_tokens: int = 256,
    locator_context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    caption : 图片描述（assistant 首条）
    history : 之前多轮 [{"role": "...", "content": "..."}]
    question: 当前用户提问
    locator_context: 识别/定位结果，写入提示词
    返回 assistant 回复；出错返回固定字符串。
    """
    return _chat_with_caption(
        caption,
        history,
        question,
        max_new_tokens=max_new_tokens,
        locator_context=locator_context,
    )


def vqa_chat_with_image(
    image_path: str,
    caption: str,
    history: List[dict],
    question: str,
    max_new_tokens: int = 256,
    locator_context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    image_path : 本轮需要再次送入 API 的图片路径
    caption    : 首轮生成的描述
    history    : 之前多轮 [{role, content} ...]
    question   : 当前用户提问
    locator_context: 识别/定位结果，写入提示词
    返回 assistant 回复；出错返回固定字符串。
    """
    return _vqa_chat_with_image(
        image_path,
        caption,
        history,
        question,
        max_new_tokens=max_new_tokens,
        locator_context=locator_context,
    )

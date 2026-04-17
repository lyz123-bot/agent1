"""
locator/deepseek_client.py
──────────────────────────
文本对话走官方 DeepSeek（deepseek-chat）；看图需多模态 OpenAI 兼容接口。

官方 https://api.deepseek.com 的 deepseek-chat 不支持 messages 里的 image_url，
因此未配置 LOCATOR_VISION_MODEL 时：描述由「本地 RF-DETR 标签 + 文本模型扩写」生成；
多轮问答在无视觉模型时回退为仅依据 caption 的文本对话。
"""

import base64
import logging
from typing import Any, Optional, List, Dict, Tuple

from django.conf import settings

from openai import OpenAI

logger = logging.getLogger(__name__)


def _get_client() -> OpenAI:
    api_key = getattr(settings, "DEEPSEEK_API_KEY", None) or ""
    base_url = getattr(settings, "DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    return OpenAI(api_key=api_key.strip(), base_url=base_url.rstrip("/"))


def _vision_configured() -> bool:
    return bool(getattr(settings, "LOCATOR_VISION_MODEL", "").strip())


def _get_vision_client_and_model() -> Tuple[OpenAI, str]:
    api_key = (getattr(settings, "LOCATOR_VISION_API_KEY", None) or "").strip()
    base = (getattr(settings, "LOCATOR_VISION_BASE_URL", None) or "").strip()
    model = getattr(settings, "LOCATOR_VISION_MODEL", "").strip()
    if not model:
        raise RuntimeError("LOCATOR_VISION_MODEL 未配置")
    if not api_key:
        raise RuntimeError("LOCATOR_VISION_API_KEY / DEEPSEEK_API_KEY 未配置")
    if not base:
        base = (getattr(settings, "DEEPSEEK_BASE_URL", "https://api.deepseek.com") or "").strip()
    return OpenAI(api_key=api_key, base_url=base.rstrip("/")), model


def _image_to_data_url(image_path: str, mime: str = "image/jpeg") -> str:
    """将本地图片转为 data URL，供 API 使用。"""
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def _get_model() -> str:
    return getattr(settings, "DEEPSEEK_MODEL", "deepseek-chat")


WHUT_QUALIFIER = "武汉理工大学"


def _whut_value(s: Optional[Any]) -> str:
    """为识别/定位等字段取值加上「武汉理工大学」限定（已带前缀则不再重复）。"""
    text = ("" if s is None else str(s)).strip()
    if not text:
        return ""
    if text.startswith(WHUT_QUALIFIER):
        return text
    return f"{WHUT_QUALIFIER}·{text}"


def format_locator_context_for_prompt(ctx: Optional[Dict]) -> str:
    """
    将前端传来的识别/定位结果格式化为提示词片段。
    各展示字段的取值均冠以限定词「武汉理工大学」。
    """
    if not ctx or not isinstance(ctx, dict):
        return ""
    pred = ctx.get("prediction") if isinstance(ctx.get("prediction"), dict) else None
    label = (ctx.get("label") or (pred or {}).get("label") or "").strip()
    loc = (ctx.get("location_text") or (pred or {}).get("location_text") or "").strip()
    score = ctx.get("match_score")
    if score is None and pred is not None:
        score = pred.get("match_score")
    fn = (ctx.get("filename") or "").strip()

    lines = [
        "【武汉理工大学智能识图·识别/定位结果】",
        "以下各条「取值」均已按要求冠以限定词「武汉理工大学」。"
        "请在后续生成与回答中优先结合这些信息，并可合理关联武汉理工大学校园相关场景（勿编造明显矛盾细节）。",
    ]
    added = False
    if fn:
        lines.append(f"- 上传文件：{_whut_value(fn)}")
        added = True
    if label:
        lines.append(f"- 匹配图像：{_whut_value(label)}")
        added = True
    if loc:
        lines.append(f"- 地点：{_whut_value(loc)}")
        added = True
    if score is not None and str(score).strip() != "":
        lines.append(f"- 匹配分数：{_whut_value(str(score))}")
        added = True
    if not added:
        return ""
    return "\n".join(lines)


def _image_quick_stats(image_path: str) -> str:
    """不依赖 HF：用 PIL 生成简短统计，供无检测标签时的 caption 兜底。"""
    try:
        from PIL import Image

        with Image.open(image_path) as im:
            im = im.convert("RGB")
            w, h = im.size
            tw = max(1, w // 40)
            th = max(1, h // 40)
            thumb = im.resize((tw, th))
            pixels = list(thumb.getdata())
            if not pixels:
                return ""
            n = len(pixels)
            sr = sum(p[0] for p in pixels) / n
            sg = sum(p[1] for p in pixels) / n
            sb = sum(p[2] for p in pixels) / n
            brightness = (sr + sg + sb) / 3
            if brightness < 85:
                lum = "整体偏暗"
            elif brightness > 195:
                lum = "整体偏亮"
            else:
                lum = "亮度适中"
            if h > w * 1.15:
                comp = "纵向构图"
            elif w > h * 1.15:
                comp = "横向构图"
            else:
                comp = "接近正方形构图"
            if sr > sb + 18:
                tone = "色调偏暖"
            elif sb > sr + 18:
                tone = "色调偏冷"
            else:
                tone = "色调相对中性"
            return f"分辨率约 {w}×{h}，{comp}，{lum}，{tone}。"
    except Exception as e:
        logger.debug("image quick stats skipped: %s", e)
        return ""


def _caption_with_vision_llm(
    image_path: str, max_new_tokens: int, locator_context: Optional[Dict] = None
) -> Optional[str]:
    client, model = _get_vision_client_and_model()
    img_url = _image_to_data_url(image_path)
    ctx_block = format_locator_context_for_prompt(locator_context)
    instruct = "请用中文详细描述这张图像。"
    if ctx_block:
        instruct = (
            f"{ctx_block}\n\n"
            "请结合以上识别/定位结果，用中文详细描述这张图像；"
            "在描述中可自然关联武汉理工大学校园语境，但不要生硬堆砌地名。"
        )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": img_url}},
                    {"type": "text", "text": instruct},
                ],
            }
        ],
        max_tokens=max_new_tokens,
    )
    msg = resp.choices[0].message
    if msg and msg.content:
        return msg.content.strip()
    return None


def _caption_from_detector_tags(
    image_path: str, max_new_tokens: int, locator_context: Optional[Dict] = None
) -> Optional[str]:
    """无多模态 API 时：优先 RF-DETR 标签 + 文本扩写；无标签时用图像统计 + 文本生成可用描述。"""
    api_key = (getattr(settings, "DEEPSEEK_API_KEY", None) or "").strip()
    if not api_key:
        return None
    det = None
    try:
        from locator.recognizer.utils import recognize_image

        det = recognize_image(image_path, threshold=0.28)
    except Exception as e:
        logger.warning("caption fallback: recognize_image failed: %s", e)

    stats_line = _image_quick_stats(image_path)
    client = _get_client()

    if det and det.get("results"):
        parts = [
            f"{_whut_value(r['type'])}（置信度约{r['confidence']}%）"
            for r in det["results"][:15]
        ]
        tag_text = "、".join(parts)
        stats_hint = f"\n另有粗略画面统计：{stats_line}" if stats_line else ""
        user_content = (
            "以下是一张照片中「物体检测模型」给出的标签（可能不完整）。你并未直接看到图片。"
            "请根据标签用中文写 2～5 句连贯的场景描述，可合理推测室内外/街景/自然等环境；"
            "不要编造标签里完全没有的物体名称。"
            f"{stats_hint}\n\n检测标签：{tag_text}"
        )
        temperature = 0.55
    else:
        stats_block = stats_line or "（未能读取分辨率与亮度统计。）"
        user_content = (
            "你正在为一张用户照片写「开场白式」的中文场景描述，供后续对话使用；你并未真正看到像素画面。"
            f"\n自动物体检测未返回常见类别标签（风景、建筑、特写、非 COCO 物体时很常见），这不代表照片无效。"
            f"\n以下仅为程序读取的粗略统计（非语义识别）：{stats_block}"
            "\n请仍输出 **一段** 2～4 句自然、连贯的中文：像讲解员一样，可保守推测「可能偏户外/室内/街景氛围之一」，"
            "语气积极中性；不要写「无法推断」「检测失败」「模型未运行」等元说明；不要分条列举原因；"
            "不要断言具体地名或未经验证的物体；直接输出描述正文。"
        )
        temperature = 0.75

    ctx_block = format_locator_context_for_prompt(locator_context)
    if ctx_block:
        user_content = ctx_block + "\n\n---\n\n" + user_content

    resp = client.chat.completions.create(
        model=_get_model(),
        messages=[{"role": "user", "content": user_content}],
        max_tokens=max_new_tokens,
        temperature=temperature,
    )
    msg = resp.choices[0].message
    if msg and msg.content:
        return msg.content.strip()
    return None


def caption_image(
    image_path: str, max_new_tokens: int = 180, locator_context: Optional[Dict] = None
) -> Optional[str]:
    """
    生成中文图像描述。
    若配置了 LOCATOR_VISION_MODEL，则走多模态接口；否则用检测标签 + 文本模型。
    locator_context: 前端识别/定位结果，写入提示词。
    """
    if _vision_configured():
        try:
            out = _caption_with_vision_llm(image_path, max_new_tokens, locator_context)
            if out:
                return out
        except Exception as e:
            logger.warning("caption_image vision LLM failed, fallback to tags: %s", e)
    try:
        return _caption_from_detector_tags(image_path, max_new_tokens, locator_context)
    except Exception as e:
        logger.warning("caption_image fallback failed: %s", e)
        return None


def chat_with_caption(
    caption: str,
    history: List[Dict[str, str]],
    question: str,
    max_new_tokens: int = 256,
    locator_context: Optional[Dict] = None,
) -> str:
    """
    仅用文本 caption 做上下文的纯文字 QA，走 DeepSeek API。
    locator_context: 识别/定位结果文本，写入 system 提示。
    """
    try:
        client = _get_client()
        ctx_block = format_locator_context_for_prompt(locator_context)
        sys_body = (
            "你是图像问答助手。以下「图像描述」来自对图片的自动分析，"
            "请严格依据该描述、识别/定位结果与后续多轮对话作答；不要编造不存在的细节。\n\n"
            f"【图像描述】\n{caption}"
        )
        if ctx_block:
            sys_body = ctx_block + "\n\n" + sys_body
        messages = [
            {
                "role": "system",
                "content": sys_body,
            }
        ]
        messages += [{"role": h["role"], "content": h["content"]} for h in history]
        messages.append({"role": "user", "content": question})

        resp = client.chat.completions.create(
            model=_get_model(),
            messages=messages,
            max_tokens=max_new_tokens,
            temperature=0.7,
            top_p=0.9,
        )
        msg = resp.choices[0].message
        if msg and msg.content:
            return msg.content.strip() or "抱歉，我暂时无法回答。"
        return "抱歉，我暂时无法回答。"
    except Exception as e:
        logger.warning("chat_with_caption error: %s", e)
        return "抱歉，回答失败。"


def vqa_chat_with_image(
    image_path: str,
    caption: str,
    history: List[Dict[str, str]],
    question: str,
    max_new_tokens: int = 256,
    locator_context: Optional[Dict] = None,
) -> str:
    """
    视觉问答：若配置了多模态模型则每轮带图；否则仅依据 caption + 历史文本回答。
    locator_context: 识别/定位结果，写入 system 提示。
    """
    ctx_block = format_locator_context_for_prompt(locator_context)
    if _vision_configured():
        try:
            client, model = _get_vision_client_and_model()
            img_url = _image_to_data_url(image_path)
            sys_intro = (
                "你是视觉问答助手。以下为该图已有的文字摘要，可与当前画面一并参考；"
                "回答须与图像一致，不要编造。"
            )
            if ctx_block:
                sys_intro = ctx_block + "\n\n" + sys_intro
            sys_full = sys_intro + "\n\n【图像描述】\n" + caption
            messages = [
                {
                    "role": "system",
                    "content": sys_full,
                }
            ]
            messages += [{"role": h["role"], "content": h["content"]} for h in history]
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": img_url}},
                        {"type": "text", "text": question},
                    ],
                }
            )
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_new_tokens,
                temperature=0.7,
                top_p=0.9,
            )
            msg = resp.choices[0].message
            if msg and msg.content:
                return msg.content.strip() or "抱歉，我暂时无法回答。"
            return "抱歉，我暂时无法回答。"
        except Exception as e:
            logger.warning("vqa_chat_with_image vision failed, text-only fallback: %s", e)
    return chat_with_caption(
        caption,
        history,
        question,
        max_new_tokens=max_new_tokens,
        locator_context=locator_context,
    )

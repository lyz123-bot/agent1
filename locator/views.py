# locator/views.py
from pathlib import Path
import json, uuid, os
from django.conf import settings
from django.http import Http404, FileResponse
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status, permissions

from .recognizer.utils import recognize_image
from .utils import detect_locations
from .caption.utils import caption_image
from .chat.utils import vqa_chat_with_image
from rest_framework.parsers import JSONParser

class LocatorView(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"detail": "缺少 file 参数"}, status=status.HTTP_400_BAD_REQUEST)

        tmp_dir = Path(settings.MEDIA_ROOT) / 'locator_tmp'
        tmp_dir.mkdir(parents=True, exist_ok=True)
        ext = Path(file_obj.name).suffix or '.jpg'
        tmp_path = tmp_dir / f"{uuid.uuid4().hex}{ext}"
        with open(tmp_path, 'wb') as f:
            for chunk in file_obj.chunks():
                f.write(chunk)
        try:
            preds = detect_locations(str(tmp_path), top_k=1)
            if not preds:
                return Response({"filename": file_obj.name, "best_match": None}, status=status.HTTP_200_OK)
            best = preds[0]
            return Response({
                "filename": file_obj.name,
                "best_match": {
                    "label": best["label"],
                    "x": best["x"], "y": best["y"],
                    "width": best["width"], "height": best["height"],
                    "location_text": best.get("location_text", ""),  # ★ 新增返回
                    "match_score": best.get("match_score", None)     # ★ 可选返回
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"定位失败: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            try: tmp_path.unlink()
            except: pass

class DatabaseImageView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, filename):
        path = Path(settings.LOCATOR_DATASET_ROOT) / 'val' / 'database' / filename
        if not path.exists():
            raise Http404()
        return FileResponse(open(path, 'rb'), content_type='image/jpeg')


class RecognizeView(APIView):
    """
    POST /api/locator/recognize/
    返回:
    {
      "filename": "...",
      "result": {
        "image_url": "...",
        "results": [ {type, confidence}, ... ]
      }
    }
    """
    parser_classes = [MultiPartParser]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"detail": "缺少 file 参数"}, status=status.HTTP_400_BAD_REQUEST)

        tmp_dir = Path(settings.RECOGNIZE_TMP_DIR)
        tmp_dir.mkdir(parents=True, exist_ok=True)
        ext = Path(file_obj.name).suffix or '.jpg'
        tmp_path = tmp_dir / f"{uuid.uuid4().hex}{ext}"
        with open(tmp_path, 'wb') as f:
            for chunk in file_obj.chunks():
                f.write(chunk)
        try:
            res = recognize_image(str(tmp_path))
            if not res:
                res = {"image_url": "", "results": []}
            elif "image_url" in res:
                res["image_url"] = request.build_absolute_uri(res["image_url"])
            return Response({"filename": file_obj.name, "result": res}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"识别失败: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            try: tmp_path.unlink()
            except: pass

class CaptionView(APIView):
    """
    POST /api/locator/caption/
    form-data: file=<image>，可选 locator_context=<json 字符串>（识别/定位结果，写入提示词）
    返回 {"caption": "..."}
    """
    parser_classes = [MultiPartParser]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        f = request.FILES.get("file")
        if not f:
            return Response({"detail": "缺少 file"}, status=400)

        locator_ctx = None
        raw_ctx = request.data.get("locator_context")
        if raw_ctx:
            try:
                locator_ctx = json.loads(raw_ctx) if isinstance(raw_ctx, str) else raw_ctx
            except Exception:
                locator_ctx = None

        tmp_dir = Path(settings.MEDIA_ROOT) / "caption_tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = tmp_dir / f"{uuid.uuid4().hex}.jpg"
        with open(tmp_path, "wb") as w:
            for c in f.chunks(): w.write(c)
        try:
            cap = caption_image(str(tmp_path), locator_context=locator_ctx)
            if not cap:
                return Response(
                    {
                        "detail": "生成失败：请配置 DEEPSEEK_API_KEY；"
                        "若已配置仍失败，请检查 Key 是否有效，或配置 LOCATOR_VISION_MODEL 使用多模态端点。"
                    },
                    status=500,
                )
            return Response({"caption": cap})
        finally:
            try: tmp_path.unlink()
            except: pass


class ChatView(APIView):
    """
    POST /api/locator/chat/

    multipart/form-data:
      file     : <image>
      meta     : json 字符串:
                 { caption, history, question, locator_context? }
                 locator_context 为识别/定位结果，与 caption 一并写入大模型提示词。
    """
    parser_classes    = [MultiPartParser]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        img_file = request.FILES.get("file")
        meta_str = request.data.get("meta", "")
        if not img_file or not meta_str:
            return Response({"detail": "缺少 file 或 meta"}, status=400)

        try:
            meta = json.loads(meta_str)
            caption  = meta["caption"]
            history  = meta.get("history", [])
            question = meta["question"]
            locator_ctx = meta.get("locator_context")
        except Exception:
            return Response({"detail": "meta 解析失败"}, status=400)

        # 保存临时图片
        tmp_dir  = Path(settings.MEDIA_ROOT) / "vqa_tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = tmp_dir / f"{uuid.uuid4().hex}.jpg"
        with open(tmp_path, "wb") as f:
            for c in img_file.chunks(): f.write(c)

        try:
            ans = vqa_chat_with_image(
                str(tmp_path), caption, history, question, locator_context=locator_ctx
            )
            return Response({"answer": ans})
        finally:
            try: tmp_path.unlink()
            except: pass

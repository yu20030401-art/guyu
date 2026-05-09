from __future__ import annotations

import base64
import io
import json
import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from openai import OpenAI
from PIL import Image, ImageStat

load_dotenv()

app = FastAPI(title="Anime Visual Concept Generator")
templates = Jinja2Templates(directory="templates")


def analyze_image_basics(image_bytes: bytes) -> dict[str, Any]:
    """Fallback local image analysis for color and rhythm hints."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    stat = ImageStat.Stat(img)
    mean = stat.mean
    width, height = img.size
    ratio = round(width / height, 3) if height else 1

    return {
        "resolution": f"{width}x{height}",
        "aspect_ratio": ratio,
        "mean_rgb": [round(v, 2) for v in mean],
        "visual_rhythm_hint": (
            "横向延展节奏" if ratio > 1.2 else "纵向聚焦节奏" if ratio < 0.85 else "均衡中心节奏"
        ),
    }


def build_prompt(theme: str, style: str, image_analysis: dict[str, Any] | None) -> str:
    return f"""
你是资深二次元视觉总监。请基于输入生成完整视觉概念方案，输出严格 JSON。

输入:
- 主题: {theme}
- 风格方向: {style}
- 参考图分析: {json.dumps(image_analysis, ensure_ascii=False) if image_analysis else '无'}

请输出 JSON 结构:
{{
  "worldbuilding": "角色世界观概述",
  "visual_elements": ["元素1", "元素2"],
  "layout_plan": "海报版式与视觉节奏说明",
  "detail_optimization": ["细节优化点1", "细节优化点2"],
  "style_keywords": ["关键词1", "关键词2"],
  "prompt_variants": [
    {{"name": "v1", "prompt": "可直接用于文生图的完整prompt"}},
    {{"name": "v2", "prompt": "..."}},
    {{"name": "v3", "prompt": "..."}}
  ],
  "design_directions": ["方向1", "方向2", "方向3"]
}}
""".strip()


def call_llm(prompt: str) -> dict[str, Any]:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    resp = client.responses.create(
        model=model,
        input=prompt,
        temperature=0.8,
        response_format={"type": "json_object"},
    )
    content = resp.output_text
    return json.loads(content)


def to_markdown(theme: str, style: str, result: dict[str, Any]) -> str:
    lines = [
        f"# 视觉概念方案：{theme}",
        "",
        f"- 风格方向：{style}",
        "",
        "## 1) 世界观梳理",
        result.get("worldbuilding", ""),
        "",
        "## 2) 视觉元素组合",
    ]
    for it in result.get("visual_elements", []):
        lines.append(f"- {it}")
    lines += ["", "## 3) 版式生成", result.get("layout_plan", ""), "", "## 4) 细节优化"]
    for it in result.get("detail_optimization", []):
        lines.append(f"- {it}")
    lines += ["", "## 5) 风格关键词"]
    for it in result.get("style_keywords", []):
        lines.append(f"- {it}")
    lines += ["", "## 6) 多版本 Prompt"]
    for p in result.get("prompt_variants", []):
        lines.append(f"### {p.get('name', 'variant')}\n{p.get('prompt', '')}\n")
    lines += ["", "## 7) 设计方向"]
    for d in result.get("design_directions", []):
        lines.append(f"- {d}")
    return "\n".join(lines)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/generate")
async def generate(
    theme: str = Form(...),
    style: str = Form("故障艺术 + 赛博朋克"),
    reference_image: UploadFile | None = File(default=None),
):
    image_analysis = None
    if reference_image:
        raw = await reference_image.read()
        image_analysis = analyze_image_basics(raw)
        image_analysis["file_name"] = reference_image.filename
        image_analysis["preview_base64"] = base64.b64encode(raw).decode("utf-8")[:60]

    prompt = build_prompt(theme=theme, style=style, image_analysis=image_analysis)
    result = call_llm(prompt)
    markdown = to_markdown(theme, style, result)
    return JSONResponse({"json": result, "markdown": markdown, "image_analysis": image_analysis})

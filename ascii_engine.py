"""Offline, Unicode-aware ASCII art rendering with Pillow."""
from __future__ import annotations

import os
import sys
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

STYLES = {"블록": "block", "크게": "large", "윤곽선": "outline", "그림자": "shadow", "3D": "3d", "기울임": "italic"}
FILLS = {"█": "block", "▓": "shade", "#": "#", "*": "*", "@": "@", "·": "."}


def find_font(custom: str | None = None, mono: bool = False) -> str:
    if custom:
        ImageFont.truetype(custom, 24)
        return custom
    windows = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    if mono:
        candidates = [windows / "consola.ttf", "/System/Library/Fonts/Menlo.ttc",
                      "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]
    else:
        candidates = [windows / "malgunbd.ttf", windows / "malgun.ttf",
                      "/System/Library/Fonts/AppleSDGothicNeo.ttc",
                      "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
                      "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                      "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"]
    for path in candidates:
        if Path(path).is_file():
            return str(path)
    # Pillow/fontconfig may resolve a family even when its installation path differs.
    for name in (["DejaVuSansMono.ttf", "LiberationMono-Regular.ttf"] if mono else
                 ["NotoSansCJK-Regular.ttc", "NanumGothic.ttf", "malgun.ttf"]):
        try:
            font = ImageFont.truetype(name, 24)
            return str(font.path)
        except OSError:
            pass
    raise RuntimeError("고정폭 글꼴을 찾을 수 없습니다." if mono else
                       "한글 글꼴을 찾지 못했습니다. ‘글꼴 파일’에서 맑은 고딕 또는 Noto Sans CJK의 TTF/OTF/TTC 파일을 선택하세요.")


def style_mask(source: list[list[float]], style: str) -> list[list[float]]:
    if not source:
        return []
    height, width = len(source), len(source[0])
    if style == "outline":
        def pixel(x, y):
            return source[y][x] if 0 <= x < width and 0 <= y < height else 0
        return [[int(bool(pixel(x, y)) and any(not pixel(x + dx, y + dy)
                 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))))
                 for x in range(width)] for y in range(height)]
    if style not in ("shadow", "3d", "italic"):
        return source
    extra = int(height * .18) + 1 if style == "italic" else 3
    result = [[0.0] * (width + extra) for _ in range(height + (0 if style == "italic" else 3))]
    for y, row in enumerate(source):
        for x, value in enumerate(row):
            if not value:
                continue
            if style == "italic":
                result[y][x + int((height - y - 1) * .18)] = 1
            else:
                for depth in (range(1, 4) if style == "3d" else (3,)):
                    result[y + depth][x + depth] = .5
    if style != "italic":
        for y, row in enumerate(source):
            for x, value in enumerate(row):
                if value:
                    result[y][x] = 1
    return result


def mask_to_text(mask: list[list[float]], fill: str = "block") -> str:
    lines = []
    for y in range(0, len(mask), 2):
        line = []
        for x, top in enumerate(mask[y]):
            bottom = mask[y + 1][x] if y + 1 < len(mask) else 0
            if fill == "block":
                char = "█" if top == bottom == 1 else "▀" if top == 1 else "▄" if bottom == 1 else "░" if top or bottom else " "
            elif fill == "shade":
                char = "▓" if top == 1 or bottom == 1 else "░" if top or bottom else " "
            else:
                char = fill if top or bottom else " "
            line.append(char)
        lines.append("".join(line).rstrip())
    return "\n".join(lines)


def text_to_ascii(text: str, style: str = "block", fill: str = "block", font_path: str | None = None) -> str:
    if not text.strip():
        return ""
    if len(text) > 300:
        raise ValueError("텍스트는 300자까지 입력할 수 있습니다.")
    size = 32 if style == "large" else 24
    font = ImageFont.truetype(find_font(font_path), size)
    lines = []
    for paragraph in unicodedata.normalize("NFC", text).expandtabs(4).split("\n"):
        line = ""
        for char in paragraph:
            if font.getlength(line + char) > 900 and line:
                lines.append(line)
                line = ""
            line += char
        lines.append(line)
    rendered = []
    for line in lines:
        if not line.strip():
            rendered.append("")
            continue
        left, top, right, bottom = font.getbbox(line)
        image = Image.new("L", (max(1, right - min(0, left) + 4), max(1, bottom - top)), 0)
        ImageDraw.Draw(image).text((2 - min(0, left), -top), line, font=font, fill=255)
        pixels = image.load()
        mask = [[int(pixels[x, y] >= 110) for x in range(image.width)] for y in range(image.height)]
        rendered.append(mask_to_text(style_mask(mask, style), fill))
    return "\n\n".join(rendered)


def load_image(path: str | Path) -> Image.Image:
    path = Path(path)
    if path.stat().st_size > 15 * 1024 * 1024:
        raise ValueError("15MB 이하 이미지를 선택하세요.")
    with Image.open(path) as original:
        if original.width * original.height > 40_000_000:
            raise ValueError("4,000만 픽셀 이하 이미지를 선택하세요.")
        original.seek(0)
        return ImageOps.exif_transpose(original).convert("RGBA")


def image_to_ascii(image: Image.Image, width: int = 80, contrast: float = 1.2,
                   invert: bool = False, fill: str = "block") -> str:
    if not 30 <= width <= 180:
        raise ValueError("가로 문자 수는 30~180이어야 합니다.")
    height = max(1, round(width * image.height / image.width * .5))
    if height > 240:
        raise ValueError("너무 세로로 긴 이미지입니다. 가로 문자 수를 줄이거나 이미지를 잘라 주세요.")
    rgba = image.convert("RGBA")
    opaque = Image.new("RGBA", rgba.size, "white")
    opaque.alpha_composite(rgba)
    pixels = opaque.convert("L").resize((width, height), Image.Resampling.LANCZOS).load()
    ramp = " .:-=+*#%@" if fill == "block" else " ░▒▓█" if fill == "shade" else f" .:{fill}{fill}"
    lines = []
    for y in range(height):
        line = []
        for x in range(width):
            darkness = 1 - min(1, max(0, (pixels[x, y] / 255 - .5) * contrast + .5))
            if invert:
                darkness = 1 - darkness
            line.append(ramp[round(darkness * (len(ramp) - 1))])
        lines.append("".join(line).rstrip())
    return "\n".join(lines)


def art_to_image(art: str, dark: bool = False) -> Image.Image:
    font = ImageFont.truetype(find_font(mono=True), 16)
    lines = art.split("\n")
    cell_width, cell_height = font.getlength("M"), 16
    width = round(max(map(len, lines), default=0) * cell_width) + 48
    height = len(lines) * cell_height + 48
    if width * height > 24_000_000 or max(width, height) > 16000:
        raise ValueError("PNG가 너무 큽니다. 텍스트를 줄이거나 TXT로 저장하세요.")
    image = Image.new("RGB", (width, height), "#211e24" if dark else "white")
    draw = ImageDraw.Draw(image)
    color = "#f1eaf0" if dark else "#29242b"
    for y, line in enumerate(lines):
        for x, char in enumerate(line):
            x0, x1, y0 = round(24 + x * cell_width), round(24 + (x + 1) * cell_width), 24 + y * cell_height
            if char in "█▀▄":
                start = 8 if char == "▄" else 0
                end = 8 if char == "▀" else 16
                draw.rectangle((x0, y0 + start, x1 - 1, y0 + end - 1), fill=color)
            elif char != " ":
                draw.text((x0, y0), char, font=font, fill=color, anchor="lt")
    return image


def copy_image_windows(image: Image.Image, window_handle: int = 0) -> None:
    """Transfer a DIB to the Windows clipboard; Windows owns the memory on success."""
    if sys.platform != "win32":
        raise RuntimeError("이미지 복사는 Windows에서 지원합니다. 다른 OS에서는 PNG로 저장하세요.")
    import ctypes
    import io
    from ctypes import wintypes
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, "BMP")
    data = buffer.getvalue()[14:]
    user32, kernel32 = ctypes.WinDLL("user32", use_last_error=True), ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.restype = wintypes.HGLOBAL
    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    handle = kernel32.GlobalAlloc(0x0002, len(data))
    if not handle:
        raise MemoryError("클립보드 메모리 할당 실패")
    try:
        pointer = kernel32.GlobalLock(handle)
        if not pointer:
            raise OSError("클립보드 메모리 접근 실패")
        ctypes.memmove(pointer, data, len(data))
        kernel32.GlobalUnlock(handle)
        if not user32.OpenClipboard(window_handle):
            raise RuntimeError("클립보드가 사용 중입니다. 잠시 후 다시 시도하세요.")
        try:
            if not user32.EmptyClipboard() or not user32.SetClipboardData(8, handle):
                raise OSError("이미지 복사 실패")
            handle = None
        finally:
            user32.CloseClipboard()
    finally:
        if handle:
            kernel32.GlobalFree(handle)

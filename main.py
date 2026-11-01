"""글자공방 — Python/Tkinter desktop ASCII art generator."""
from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import tkinter.font as tkfont

try:
    from PIL import Image, ImageTk
    from ascii_engine import (STYLES, FILLS, text_to_ascii, image_to_ascii, load_image,
                              art_to_image, copy_image_windows, find_font)
except ImportError as exc:
    raise SystemExit("Pillow가 필요합니다. 먼저 python -m pip install -r requirements.txt 를 실행하세요.") from exc


class AsciiStudio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("글자공방 · 한글 ASCII 아트 생성기")
        self.geometry("1120x750")
        self.minsize(920, 620)
        self.option_add("*Font", ("맑은 고딕" if sys.platform == "win32" else "TkDefaultFont", 10))
        self.mode = tk.StringVar(value="텍스트")
        self.art_style = tk.StringVar(value="블록")
        self.fill = tk.StringVar(value="█")
        self.resolution = tk.IntVar(value=80)
        self.contrast = tk.DoubleVar(value=1.2)
        self.invert = tk.BooleanVar(value=False)
        self.zoom = tk.IntVar(value=10)
        self.status = tk.StringVar(value="한글 · 영문 · 숫자 · 기호 · 여러 줄 지원")
        self.dimensions = tk.StringVar()
        self.count = tk.StringVar()
        self.source_image = None
        self.font_path = None
        self.result = ""
        self.dark = False
        self.pending = None
        self.last_error = ""
        self.groups = []
        self.export_buttons = []
        self.palette = {"bg": "#faf9f7", "surface": "#ffffff", "subtle": "#f3f1f4", "fg": "#29242b", "muted": "#817784", "border": "#e2dde3", "accent": "#824363"}
        self.configure(bg=self.palette["bg"])
        self._build()
        self._apply_theme()
        self.render()
        self.protocol("WM_DELETE_WINDOW", self.close)

    def frame(self, parent, tone="surface", **kwargs):
        frame = tk.Frame(parent, bg=self.palette[tone], **kwargs)
        frame._tone = tone
        return frame

    def label(self, parent, text="", muted=False, tone="surface", **kwargs):
        label = tk.Label(parent, text=text, bg=self.palette[tone], fg=self.palette["muted" if muted else "fg"], **kwargs)
        label._tone, label._muted = tone, muted
        return label

    def button(self, parent, text, command, **kwargs):
        return tk.Button(parent, text=text, command=command, bd=0, relief="flat", padx=12, pady=7,
                         cursor="hand2", takefocus=True, **kwargs)

    def segment(self, parent, label, variable, choices, command=None):
        frame = self.frame(parent)
        frame.pack(side="left", padx=(0, 16), pady=4)
        self.label(frame, label, muted=True, font=("맑은 고딕", 9)).pack(side="left", padx=(0, 8))
        buttons = []
        for value in choices:
            def select(v=value):
                variable.set(v)
                self._refresh_segments()
                (command or self.render)()
            btn = self.button(frame, value, select)
            btn.configure(padx=8)
            btn.pack(side="left", padx=1)
            buttons.append((btn, value))
        self.groups.append((variable, buttons))
        return frame

    def _build(self):
        header = self.frame(self)
        header.pack(fill="x")
        self.label(header, "▟  글자공방", font=("맑은 고딕", 17, "bold")).pack(side="left", padx=(28, 10), pady=18)
        self.label(header, "ASCII STUDIO  /  PYTHON", muted=True, font=("Consolas", 9)).pack(side="left")
        self.theme_button = self.button(header, "☾  테마", self.toggle_theme)
        self.theme_button.pack(side="right", padx=26)
        self.label(header, "한글 지원 ●", muted=True).pack(side="right", padx=10)
        body = self.frame(self, "bg")
        body.pack(fill="both", expand=True, padx=28, pady=(20, 12))
        self.label(body, "글자가, 그림이 되는 순간.", tone="bg", font=("맑은 고딕", 22, "bold")).pack(anchor="w")
        self.label(body, "한글도 선명하게. 글자와 사진으로 나만의 ASCII 아트를 만들어 보세요.", tone="bg", muted=True).pack(anchor="w", pady=(6, 18))
        toolbar = self.frame(body, highlightthickness=1)
        toolbar.pack(fill="x")
        top = self.frame(toolbar)
        top.pack(fill="x", padx=12, pady=(9, 0))
        self.segment(top, "모드", self.mode, ("텍스트", "이미지"), self.switch_mode)
        self.style_group = self.segment(top, "글꼴", self.art_style, STYLES)
        self.button(top, "지우기", self.clear).pack(side="right")
        bottom = self.frame(toolbar)
        bottom.pack(fill="x", padx=12, pady=(0, 9))
        self.segment(bottom, "채움", self.fill, FILLS)
        self.font_button = self.button(bottom, "글꼴 파일…", self.choose_font)
        self.font_button.pack(side="right")
        self.font_label = self.label(bottom, "시스템 한글 글꼴", muted=True, font=("맑은 고딕", 9))
        self.font_label.pack(side="right", padx=8)

        self.input_holder = self.frame(body, "bg")
        self.input_holder.pack(fill="x", pady=(16, 12))
        self.text_panel = self.frame(self.input_holder, "bg")
        self.text_panel.pack(fill="x")
        info = self.frame(self.text_panel, "bg")
        info.pack(fill="x", pady=(0, 6))
        self.label(info, "어떤 글자를 그려볼까요?", tone="bg").pack(side="left")
        self.label(info, textvariable=self.count, tone="bg", muted=True).pack(side="right")
        self.text_input = tk.Text(self.text_panel, height=2, font=("맑은 고딕", 13), wrap="word", undo=True,
                                  relief="solid", bd=1, padx=12, pady=10)
        self.text_input.pack(fill="x")
        self.text_input.insert("1.0", "안녕하세요!")
        self.text_input.bind("<<Modified>>", self.on_text_changed)
        self.text_input.edit_modified(False)
        examples = self.frame(self.text_panel, "bg")
        examples.pack(fill="x", pady=(4, 0))
        self.label(examples, "한글 · 영문 · 자모 · 여러 줄 지원", muted=True, tone="bg", font=("맑은 고딕", 9)).pack(side="left")
        for value in ("사랑해 ♥", "HELLO GPT!", "안녕하세요!"):
            self.button(examples, value, lambda v=value: self.set_text(v)).pack(side="right", padx=2)

        self.image_panel = self.frame(self.input_holder, "bg")
        image_top = self.frame(self.image_panel)
        image_top.pack(fill="x", pady=(0, 8))
        self.thumbnail = self.label(image_top, "▧", width=9, font=("맑은 고딕", 20))
        self.thumbnail.pack(side="left", padx=10, pady=10)
        self.image_description = self.label(image_top, "PNG · JPG · WEBP · GIF · BMP\n최대 15MB / 4,000만 픽셀", justify="left", muted=True)
        self.image_description.pack(side="left", padx=10)
        self.button(image_top, "이미지 선택…", self.choose_image).pack(side="right", padx=16)
        controls = self.frame(self.image_panel, "bg")
        controls.pack(fill="x")
        self.label(controls, "가로 문자 수", tone="bg").pack(side="left")
        self.width_scale = tk.Scale(controls, variable=self.resolution, from_=30, to=180, orient="horizontal", length=180, command=self.schedule_render, bd=0, highlightthickness=0)
        self.width_scale.pack(side="left", padx=(6, 18))
        self.label(controls, "대비", tone="bg").pack(side="left")
        self.contrast_scale = tk.Scale(controls, variable=self.contrast, from_=.5, to=2.5, resolution=.1, orient="horizontal", length=180, command=self.schedule_render, bd=0, highlightthickness=0)
        self.contrast_scale.pack(side="left", padx=8)
        self.invert_check = tk.Checkbutton(controls, text="명암 반전", variable=self.invert, command=self.render, bd=0)
        self.invert_check.pack(side="left", padx=16)

        result_frame = self.frame(body, highlightthickness=1)
        result_frame.pack(fill="both", expand=True)
        result_bar = self.frame(result_frame, "subtle")
        result_bar.pack(fill="x")
        self.label(result_bar, "ASCII", tone="subtle", font=("Consolas", 10, "bold")).pack(side="left", padx=(14, 10), pady=11)
        self.label(result_bar, textvariable=self.dimensions, tone="subtle", muted=True, font=("Consolas", 9)).pack(side="left")
        for text, command in (("복사", self.copy_text), ("이미지 복사", self.copy_image), (".png 저장", self.save_png), (".txt 저장", self.save_txt)):
            btn = self.button(result_bar, text, command)
            btn.pack(side="right", padx=3, pady=5)
            self.export_buttons.append(btn)
        output_holder = self.frame(result_frame)
        output_holder.pack(fill="both", expand=True)
        output_holder.rowconfigure(0, weight=1)
        output_holder.columnconfigure(0, weight=1)
        available = tkfont.families(self)
        self.mono_family = next((font for font in ("Consolas", "Cascadia Mono", "Menlo", "DejaVu Sans Mono") if font in available), "Courier")
        self.output = tk.Text(output_holder, height=9, wrap="none", font=(self.mono_family, 10), bd=0,
                              padx=18, pady=18, spacing1=0, spacing2=0, spacing3=0, state="disabled", cursor="xterm")
        vertical = ttk.Scrollbar(output_holder, orient="vertical", command=self.output.yview)
        horizontal = ttk.Scrollbar(output_holder, orient="horizontal", command=self.output.xview)
        self.output.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.output.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        footer = self.frame(result_frame, "subtle")
        footer.pack(fill="x")
        self.label(footer, textvariable=self.status, tone="subtle", muted=True, anchor="w", wraplength=650, font=("맑은 고딕", 9)).pack(side="left", padx=12, pady=8)
        self.zoom_scale = tk.Scale(footer, from_=6, to=18, variable=self.zoom, orient="horizontal", showvalue=True,
                                  command=self.set_zoom, length=110, bd=0, highlightthickness=0)
        self.zoom_scale.pack(side="right", padx=(4, 12))
        self.label(footer, "미리보기", tone="subtle", muted=True, font=("맑은 고딕", 9)).pack(side="right")
        footnote = self.frame(body, "bg")
        footnote.pack(fill="x", pady=(8, 0))
        self.label(footnote, "✦ 모든 변환은 내 컴퓨터에서 처리됩니다. 인터넷 연결이 필요하지 않습니다.", tone="bg", muted=True, font=("맑은 고딕", 9)).pack(side="left")
        self.button(footnote, "설정 초기화 ↺", self.reset).pack(side="right")

    def _refresh_segments(self):
        for variable, buttons in self.groups:
            for button, value in buttons:
                active = variable.get() == value
                button.configure(bg=self.palette["accent"] if active else self.palette["surface"],
                                 fg="white" if active else self.palette["muted"],
                                 activebackground=self.palette["accent"], activeforeground="white")

    def _apply_theme(self):
        p = self.palette
        self.configure(bg=p["bg"])
        def visit(widget):
            for child in widget.winfo_children():
                if isinstance(child, tk.Frame):
                    child.configure(bg=p[getattr(child, "_tone", "surface")], highlightbackground=p["border"])
                elif isinstance(child, tk.Label):
                    child.configure(bg=p[getattr(child, "_tone", "surface")], fg=p["muted" if getattr(child, "_muted", False) else "fg"])
                elif isinstance(child, tk.Button):
                    child.configure(bg=p["surface"], fg=p["fg"], activebackground=p["subtle"], activeforeground=p["fg"])
                elif isinstance(child, tk.Text):
                    child.configure(bg=p["surface"], fg=p["fg"], insertbackground=p["fg"], selectbackground=p["accent"], selectforeground="white")
                elif isinstance(child, (tk.Scale, tk.Checkbutton)):
                    child.configure(bg=p["bg"], fg=p["fg"], activebackground=p["accent"])
                    if isinstance(child, tk.Checkbutton):
                        child.configure(selectcolor=p["surface"])
                visit(child)
        visit(self)
        self._refresh_segments()

    def toggle_theme(self):
        self.dark = not self.dark
        if self.dark:
            self.palette.update(bg="#1c191e", surface="#252127", subtle="#302934", fg="#eee8ed", muted="#b6aaba", border="#443b49")
        else:
            self.palette.update(bg="#faf9f7", surface="#ffffff", subtle="#f3f1f4", fg="#29242b", muted="#817784", border="#e2dde3")
        self.theme_button.configure(text="☀  테마" if self.dark else "☾  테마")
        self._apply_theme()

    def on_text_changed(self, _event=None):
        if not self.text_input.edit_modified():
            return
        self.text_input.edit_modified(False)
        self.schedule_render()

    def schedule_render(self, *_):
        if self.pending:
            self.after_cancel(self.pending)
        self.pending = self.after(130, self.render)

    def render(self):
        if self.pending:
            self.after_cancel(self.pending)
            self.pending = None
        text = self.text_input.get("1.0", "end-1c")
        self.count.set(f"{len(text)} / 300")
        self.last_error = ""
        try:
            if self.mode.get() == "텍스트":
                self.result = text_to_ascii(text, STYLES[self.art_style.get()], FILLS[self.fill.get()], self.font_path)
            elif self.source_image is not None:
                self.result = image_to_ascii(self.source_image, self.resolution.get(), self.contrast.get(), self.invert.get(), FILLS[self.fill.get()])
            else:
                self.result = ""
            self.status.set("고정폭 글꼴로 붙여넣으면 모양이 유지됩니다." if self.result else "글자나 이미지를 넣으면 이곳에 작품이 나타납니다.")
        except (OSError, ValueError, RuntimeError) as error:
            self.result = ""
            self.last_error = str(error)
            self.status.set(str(error))
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", self.result)
        self.output.configure(state="disabled")
        lines = self.result.split("\n")
        self.dimensions.set(f"{max(map(len, lines))} × {len(lines)}" if self.result else "")
        for button in self.export_buttons:
            button.configure(state="normal" if self.result else "disabled")

    def switch_mode(self):
        self.text_panel.pack_forget()
        self.image_panel.pack_forget()
        (self.text_panel if self.mode.get() == "텍스트" else self.image_panel).pack(fill="x")
        for button, _ in self.groups[1][1]:
            button.configure(state="normal" if self.mode.get() == "텍스트" else "disabled")
        self.render()

    def set_text(self, value):
        self.text_input.delete("1.0", "end")
        self.text_input.insert("1.0", value)
        self.text_input.edit_modified(False)
        self.render()

    def choose_font(self):
        path = filedialog.askopenfilename(parent=self, title="한글을 지원하는 글꼴 선택", filetypes=[("글꼴", "*.ttf *.otf *.ttc"), ("모든 파일", "*")])
        if not path:
            return
        try:
            find_font(path)
            self.font_path = path
            self.font_label.configure(text=Path(path).name)
            self.render()
        except (OSError, ValueError) as error:
            messagebox.showerror("글꼴 오류", str(error), parent=self)

    def choose_image(self):
        path = filedialog.askopenfilename(parent=self, title="이미지 선택", filetypes=[("이미지", "*.png *.jpg *.jpeg *.webp *.gif *.bmp"), ("모든 파일", "*")])
        if not path:
            return
        try:
            image = load_image(path)
            preview = image.copy()
            preview.thumbnail((80, 65))
            self.thumbnail_image = ImageTk.PhotoImage(preview)
            self.thumbnail.configure(image=self.thumbnail_image, text="", width=80)
            self.source_image = image
            self.image_description.configure(text=f"{Path(path).name[:65]}\n{image.width} × {image.height} · GIF는 첫 프레임 사용")
            self.render()
        except (OSError, ValueError, Image.DecompressionBombError) as error:
            messagebox.showerror("이미지 오류", str(error), parent=self)

    def clear(self):
        if self.mode.get() == "텍스트":
            self.set_text("")
        else:
            self.source_image = None
            self.thumbnail.configure(image="", text="▧", width=9)
            self.image_description.configure(text="PNG · JPG · WEBP · GIF · BMP\n최대 15MB / 4,000만 픽셀")
            self.render()

    def set_zoom(self, *_):
        self.output.configure(font=(self.mono_family, self.zoom.get()))

    def reset(self):
        self.art_style.set("블록")
        self.fill.set("█")
        self.resolution.set(80)
        self.contrast.set(1.2)
        self.invert.set(False)
        self.zoom.set(10)
        self.font_path = None
        self.font_label.configure(text="시스템 한글 글꼴")
        self._refresh_segments()
        self.set_zoom()
        self.render()

    def copy_text(self):
        if not self.result:
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(self.result)
            self.update_idletasks()
            self.status.set("ASCII 아트를 복사했습니다.")
        except tk.TclError as error:
            messagebox.showerror("복사 오류", str(error), parent=self)

    def copy_image(self):
        if not self.result:
            return
        try:
            copy_image_windows(art_to_image(self.result, self.dark), self.winfo_id())
            self.status.set("이미지를 복사했습니다. 그림판이나 메신저에 붙여넣으세요.")
        except (OSError, RuntimeError, ValueError, MemoryError) as error:
            messagebox.showerror("이미지 복사", str(error), parent=self)

    def save_txt(self):
        self.save("txt")

    def save_png(self):
        self.save("png")

    def save(self, extension):
        if not self.result:
            return
        path = filedialog.asksaveasfilename(parent=self, title=f"{extension.upper()} 저장", initialfile=f"ASCII-art.{extension}", defaultextension=f".{extension}", filetypes=[(extension.upper(), f"*.{extension}")])
        if not path:
            return
        try:
            if extension == "txt":
                Path(path).write_text(self.result, encoding="utf-8-sig")
            else:
                art_to_image(self.result, self.dark).save(path, "PNG")
            self.status.set(f"저장 완료: {Path(path).name}")
        except (OSError, ValueError, RuntimeError) as error:
            messagebox.showerror("저장 오류", str(error), parent=self)

    def close(self):
        if self.pending:
            self.after_cancel(self.pending)
        self.destroy()


if __name__ == "__main__":
    AsciiStudio().mainloop()

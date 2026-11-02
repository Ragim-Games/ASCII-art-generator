# ASCII Studio

A **Python command-line ASCII art generator** for Windows CMD, PowerShell, and other terminals. It runs entirely in the terminal and never opens a GUI, browser, or file dialog. All commands, prompts, errors, and documentation are in English. Korean text rendering is still supported.

## Installation

Requires Python 3.10 or later and Pillow. Tkinter is not required.

```cmd
python -m pip install -r requirements.txt
```

## Quick start (Windows CMD)

Run without arguments to enter one line of text at the terminal prompt:

```cmd
python main.py
```

Or pass text directly:

```cmd
python main.py --text "HELLO GPT!"
python main.py --text "ASCII STUDIO" --style outline --fill "#"
run.bat --text "Hello" --style 3d
```

You can enter Korean text in exactly the same way. Use a font containing the required Korean characters. No network connection or API key is needed after installation.

## Input and output

```cmd
python main.py --text-file message.txt
type message.txt | python main.py
python main.py --text "Hello" --output result.txt
python main.py --text "Hello" --png result.png --dark
python main.py --text "Hello" --output result.txt --png result.png --quiet
python main.py --text "Hello" > result.txt
python main.py --image photo.jpg --width 80 --contrast 1.5
python main.py --image photo.png --invert --fill shade --output photo-art.txt
python main.py --text "Hello" --copy
python main.py --text "Hello" --copy-image
python main.py --help
```

Text files and redirected output use UTF-8. A UTF-8 BOM is accepted in input files. For multiple lines, use `--text-file` or stdin. A literal `\n` in CMD arguments is not converted to a line break. Standard output contains only the art; prompts, save confirmations, and errors go to standard error. `--quiet` suppresses the art when saving or copying. Existing output files are replaced; input image, text, and font files are protected from being used as output paths. Parent output directories must already exist.

`run.bat` forwards arguments and exit codes without changing the current directory, so relative file paths are resolved from the directory where you run the command. It does not pause or open another window.

## Options

| Option | Description |
| --- | --- |
| `--text`, `-t` | Text to render, up to 300 characters |
| `--text-file` | UTF-8 text file, including multiline text |
| `--image`, `-i` | Local image input; mutually exclusive with text inputs |
| `--style` | `block`, `large`, `outline`, `shadow`, `3d`, or `italic` (text only) |
| `--fill` | `block`, `shade`, `#`, `*`, `@`, or `.` |
| `--font` | Custom TTF, OTF, or TTC font for text rendering |
| `--columns` | Text wrapping width, 40-900 columns; defaults to terminal width |
| `--width` | Image output width, 30-180 columns; default 80 |
| `--contrast` | Image contrast, 0.5-2.5; default 1.2 |
| `--invert` | Invert image brightness |
| `--output`, `-o` | Save a UTF-8 text file |
| `--png` | Save a PNG image |
| `--dark` | Dark background for PNG exports and image copies |
| `--copy` | Copy art as text to the Windows clipboard |
| `--copy-image` | Copy a rendered image to the Windows clipboard |
| `--quiet`, `-q` | Suppress stdout when saving or copying |

## Korean text and terminal display

Pillow renders actual font glyphs before converting pixels into characters. The program automatically searches for Malgun Gothic on Windows, Apple SD Gothic Neo on macOS, and Noto Sans CJK or Nanum Gothic on Linux. If detection fails, specify a font:

```cmd
python main.py --text-file message.txt --font "C:\Windows\Fonts\malgunbd.ttf"
```

The default `block` fill uses Unicode block characters to preserve fine strokes. Choose `--fill "#"`, `"*"`, `"@"`, or `"."` for strict ASCII output. Use a monospace terminal font such as Consolas. If an older CMD configuration displays incorrect characters, run `chcp 65001` before starting the program. Narrow consoles wrap long art; use `--columns 80` for text or `--width 60` for images, or export a file.

PNG export uses a system monospace font. Missing glyphs depend on the selected font. Clipboard options are Windows-only and operate without Tkinter or dialogs; if the clipboard is unavailable, use `--output` or `--png`.

## Limits

- Text: 300 Unicode characters; longer input returns an English error.
- Images: at most 15 MB and 40 million pixels; PNG, JPG, WEBP, GIF, and BMP supported.
- Animated GIF: first frame only; EXIF orientation is applied.
- Image art: at most 180 columns and 240 rows. Very tall images require cropping or a smaller `--width`.
- PNG: at most 24 million pixels and 16,000 pixels per dimension.
- Exit codes: `0` success, `1` processing error, `2` invalid arguments, `130` cancelled input.

## Tests

```cmd
python -m unittest discover -s tests -v
```

Tests cover Korean rendering, all styles, transparency, PNG generation, terminal input, English diagnostics, UTF-8 pipes, file exports, and CMD argument forwarding. They do not open windows or require a desktop session. Tested on Windows with Python 3.15 and Pillow 13.

## Files

| File | Purpose |
| --- | --- |
| `main.py` | Argument parsing, terminal input/output, export commands |
| `ascii_engine.py` | Text and image rendering, PNG export, native clipboard support |
| `requirements.txt` | Pillow dependency |
| `run.bat` | Windows CMD launcher |
| `tests/` | Headless rendering and CLI regression tests |

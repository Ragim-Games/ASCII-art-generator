"""ASCII Studio: a terminal-only text and image ASCII art generator."""
from __future__ import annotations

import argparse
import math
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create ASCII art in your terminal. Korean text is supported. No GUI is opened.",
        epilog='Example: python main.py --text "HELLO" --style outline',
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--text", "-t", help="Text to render (up to 300 characters).")
    source.add_argument("--text-file", type=Path, help="Read multiline text from a UTF-8 file.")
    source.add_argument("--image", "-i", type=Path, help="Convert a local PNG, JPG, WEBP, GIF, or BMP image.")
    parser.add_argument("--style", choices=("block", "large", "outline", "shadow", "3d", "italic"), default="block", help="Text style (default: block).")
    parser.add_argument("--fill", choices=("block", "shade", "#", "*", "@", "."), default="block", help="Fill characters (default: block). Use # for strict ASCII.")
    parser.add_argument("--font", type=Path, help="Path to a TTF, OTF, or TTC font with the required glyphs.")
    parser.add_argument("--columns", type=int, default=max(40, min(900, shutil.get_terminal_size((120, 24)).columns - 1)), help="Maximum text-art columns, 40-900 (default: terminal width).")
    parser.add_argument("--width", type=int, default=80, help="Image-art width, 30-180 characters (default: 80).")
    parser.add_argument("--contrast", type=float, default=1.2, help="Image contrast, 0.5-2.5 (default: 1.2).")
    parser.add_argument("--invert", action="store_true", help="Invert image brightness.")
    parser.add_argument("--output", "-o", type=Path, help="Save art to a UTF-8 text file.")
    parser.add_argument("--png", type=Path, help="Save art as a PNG image.")
    parser.add_argument("--dark", action="store_true", help="Use a dark background in PNG exports and image copies.")
    parser.add_argument("--copy", action="store_true", help="Copy text to the Windows clipboard.")
    parser.add_argument("--copy-image", action="store_true", help="Copy a rendered image to the Windows clipboard.")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress art on stdout; use with a save or copy option.")
    return parser


def configure_streams() -> None:
    # Windows console handles support Unicode; redirected streams need UTF-8 too.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def copy_text(text: str) -> None:
    if sys.platform != "win32":
        raise ValueError("Clipboard copying is supported on Windows only. Use --output instead.")
    subprocess.run(["clip.exe"], input=text.encode("utf-16"), check=True)


def save_text(art: str, name: str | None = None) -> Path:
    """Save art as UTF-8 text; without a name, use a timestamped file in the current directory."""
    path = Path(name) if name else Path(f"ascii_art_{datetime.now():%Y%m%d_%H%M%S}.txt")
    path.write_text(art + "\n", encoding="utf-8")
    return path


def interactive_session(args: argparse.Namespace, convert) -> int:
    """Keep results visible and accept more text until the user explicitly exits."""
    print("ASCII Studio - terminal mode\nEnter text and press Enter to generate art.\n"
          "Commands: copy = copy the latest art to the clipboard, txt [file] = save the latest art as .txt, :q = quit.\n"
          "Press Enter on an empty line to continue.\n", file=sys.stderr, flush=True)
    session: dict[str, str] = {}  # session["last_art"] holds the most recently generated art
    while True:
        try:
            print("Enter text (up to 300 characters, copy, txt, :q to quit): ", end="", file=sys.stderr, flush=True)
            text = input()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye.", file=sys.stderr)
            return 0
        command, _, argument = text.strip().partition(" ")
        command = command.lower().lstrip(":")
        if text.strip().lower() == ":q":
            print("Goodbye.", file=sys.stderr)
            return 0
        if not text.strip():
            continue
        if command in ("copy", "txt") and (command == "txt" or not argument):
            if "last_art" not in session:
                print("Error: No art has been generated yet. Enter some text first.", file=sys.stderr)
                continue
            try:
                if command == "copy":
                    copy_text(session["last_art"])
                    print("Copied the latest art to the clipboard.", file=sys.stderr)
                else:
                    print(f"Saved TXT: {save_text(session['last_art'], argument.strip() or None)}", file=sys.stderr)
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                print(f"Error: Could not {command} the latest art ({error}).", file=sys.stderr)
            continue
        args.text = text
        # Processing errors are reported by convert; the prompt stays available.
        if convert(args, session) == 130:
            print("Goodbye.", file=sys.stderr)
            return 0


def main(argv: list[str] | None = None) -> int:
    configure_streams()
    parser = build_parser()
    args = parser.parse_args(argv)
    if not 40 <= args.columns <= 900:
        parser.error("--columns must be between 40 and 900.")
    if not 30 <= args.width <= 180:
        parser.error("--width must be between 30 and 180.")
    if not math.isfinite(args.contrast) or not .5 <= args.contrast <= 2.5:
        parser.error("--contrast must be between 0.5 and 2.5.")
    if args.quiet and not any((args.output, args.png, args.copy, args.copy_image)):
        parser.error("--quiet requires --output, --png, --copy, or --copy-image.")
    if args.output and args.png and args.output.resolve() == args.png.resolve():
        parser.error("--output and --png must use different paths.")
    inputs = [path.resolve() for path in (args.image, args.text_file, args.font) if path]
    if any(path.resolve() in inputs for path in (args.output, args.png) if path):
        parser.error("An output path must not overwrite an input image, text file, or font.")
    try:
        import ascii_engine  # Check dependencies before starting an interactive session.
    except ImportError:
        print("Error: Pillow is required. Run: python -m pip install -r requirements.txt", file=sys.stderr)
        return 1
    if args.text is None and args.text_file is None and args.image is None and sys.stdin.isatty():
        return interactive_session(args, convert)
    return convert(args)


def convert(args: argparse.Namespace, session: dict[str, str] | None = None) -> int:
    from PIL import Image
    from ascii_engine import text_to_ascii, image_to_ascii, load_image, art_to_image, copy_image_windows

    try:
        if args.image:
            art = image_to_ascii(load_image(args.image), args.width, args.contrast, args.invert, args.fill)
        else:
            if args.text is not None:
                text = args.text
            elif args.text_file:
                with args.text_file.open(encoding="utf-8-sig") as source:
                    text = source.read(301)
            else:
                text = sys.stdin.read(302).removeprefix("\ufeff")
            if not text.strip():
                raise ValueError("No text provided. Use --text, --text-file, or pipe text into stdin.")
            art = text_to_ascii(text, args.style, args.fill, str(args.font) if args.font else None, args.columns)
        if session is not None:
            session["last_art"] = art
        png = art_to_image(art, args.dark) if args.png or args.copy_image else None
        if args.output:
            args.output.write_text(art + "\n", encoding="utf-8")
            print(f"Saved TXT: {args.output}", file=sys.stderr)
        if args.png:
            png.save(args.png, "PNG")
            print(f"Saved PNG: {args.png}", file=sys.stderr)
        if args.copy:
            copy_text(art)
            print("Copied text to the clipboard.", file=sys.stderr)
        if args.copy_image:
            copy_image_windows(png)
            print("Copied image to the clipboard.", file=sys.stderr)
        if not args.quiet:
            print(art, flush=True)
        return 0
    except (OSError, ValueError, RuntimeError, MemoryError, UnicodeError, Image.DecompressionBombError, subprocess.SubprocessError) as error:
        # OS error strings can follow the system locale; keep diagnostics in English.
        if isinstance(error, OSError):
            message = f"Could not read or write the requested file or resource (error code: {error.errno}). Check paths, permissions, fonts, and file formats."
        elif isinstance(error, UnicodeError):
            message = "Could not decode text. Use UTF-8 for input files and redirected input."
        else:
            message = str(error)
        print(f"Error: {message}", file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

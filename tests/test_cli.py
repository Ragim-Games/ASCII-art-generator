"""Headless command-line integration tests; no GUI or clipboard is opened."""
import builtins
import contextlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
import main
from ascii_engine import text_to_ascii

ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def run_cli(self, *args, input="", cwd=ROOT):
        return subprocess.run([sys.executable, str(ROOT / "main.py"), *map(str, args)],
                              input=input, capture_output=True, encoding="utf-8", cwd=cwd, timeout=15)

    def test_help_is_english_and_import_never_loads_tkinter(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("No GUI is opened", result.stdout)
        self.assertNotRegex(result.stdout, "[\uac00-\ud7a3]")
        code = "import main,sys; assert 'tkinter' not in sys.modules; main.main(['--text','Hello','--fill','#'])"
        result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0)

    def test_korean_stdin_and_argument_match(self):
        korean = "\ud55c\uae00 ABC\n\u3131\u3134\u3137 123"
        by_arg = self.run_cli("--text", korean, "--columns", "90")
        by_pipe = self.run_cli("--columns", "90", input=korean)
        self.assertEqual(by_arg.returncode, 0)
        self.assertEqual(by_arg.stdout, by_pipe.stdout)
        self.assertIn("█", by_arg.stdout)
        self.assertEqual(by_arg.stderr, "")
        self.assertLessEqual(max(map(len, by_arg.stdout.splitlines())), 90)

    def test_interactive_prompt(self):
        terminal = io.StringIO()
        terminal.isatty = lambda: True
        out, err = io.StringIO(), io.StringIO()
        with patch.object(sys, "stdin", terminal), patch.object(builtins, "input", return_value="Hello"), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main.main(["--fill", "#"])
        self.assertEqual(code, 0)
        self.assertIn("Enter text", err.getvalue())
        self.assertLessEqual(set(out.getvalue()), {"#", " ", "\n"})

    def test_styles_and_fills_fit_terminal(self):
        for style in ("block", "large", "outline", "shadow", "3d", "italic"):
            art = text_to_ascii("\ud55c\uae00 Hello WORLD", style=style, columns=40)
            self.assertLessEqual(max(map(len, art.splitlines())), 40)
        result = self.run_cli("--text", "Hello", "--fill", "#")
        self.assertEqual(result.returncode, 0)
        self.assertLessEqual(set(result.stdout), {"#", " ", "\n"})

    def test_files_and_image_mode(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            source, txt, png = folder / "input text.txt", folder / "result.txt", folder / "result.png"
            source.write_text("\ud55c\uae00\nHello", encoding="utf-8-sig")
            result = self.run_cli("--text-file", source, "--output", txt, "--png", png, "--quiet", "--dark")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertIn("Saved TXT:", result.stderr)
            self.assertIn("█", txt.read_text(encoding="utf-8"))
            with Image.open(png) as image:
                self.assertEqual(image.format, "PNG")
                self.assertEqual(image.getpixel((0, 0)), (33, 30, 36))
            converted = self.run_cli("--image", png, "--width", "40", "--invert")
            self.assertEqual(converted.returncode, 0, converted.stderr)
            self.assertTrue(converted.stdout.strip())
            self.assertLessEqual(max(map(len, converted.stdout.splitlines())), 40)

    def test_errors_are_english_without_tracebacks(self):
        for args, code in ((["--width", "1"], 2), (["--contrast", "nan"], 2), (["--quiet"], 2),
                           (["--text", "A", "--image", "image.png"], 2), (["--text", "A" * 301], 1),
                           (["--text-file", "missing-file.txt"], 1), (["--text", ""], 1)):
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, code)
                self.assertIn("error", result.stderr.lower())
                self.assertNotIn("Traceback", result.stderr)
                self.assertNotRegex(result.stderr, "[\uac00-\ud7a3]")

    def test_input_files_are_protected(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "input.txt"
            source.write_text("Hello", encoding="utf-8")
            result = self.run_cli("--text-file", source, "--output", source)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(source.read_text(encoding="utf-8"), "Hello")

    @unittest.skipUnless(sys.platform == "win32", "Windows CMD launcher test")
    def test_cmd_launcher_forwards_arguments_paths_and_exit_codes(self):
        with tempfile.TemporaryDirectory() as folder:
            # Run from outside the repository to verify caller-relative output paths.
            command = f'""{ROOT / "run.bat"}" --text "HELLO CMD" --fill "#" --output "result with spaces.txt" --quiet"'
            cmd_exe = os.environ.get("COMSPEC", "cmd.exe")
            result = subprocess.run(f'"{cmd_exe}" /d /s /c {command}', cwd=folder, capture_output=True, encoding="utf-8", timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((Path(folder) / "result with spaces.txt").is_file())
            command = f'""{ROOT / "run.bat"}" --width 1"'
            result = subprocess.run(f'"{cmd_exe}" /d /s /c {command}', cwd=folder, capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()

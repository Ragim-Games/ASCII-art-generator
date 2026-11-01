"""Native widget integration tests. Run explicitly with a desktop session."""
import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile

from PIL import Image
from main import AsciiStudio


class GuiTests(unittest.TestCase):
    def setUp(self):
        self.app = AsciiStudio()
        self.app.withdraw()
        self.app.update_idletasks()

    def tearDown(self):
        self.app.close()

    def test_modes_styles_zoom_and_clear(self):
        app = self.app
        self.assertTrue(app.result)
        app.set_text("한글 ABC\n테스트 123")
        self.assertIn("\n\n", app.result)
        for style in ("윤곽선", "그림자", "3D", "기울임", "크게"):
            app.art_style.set(style)
            app.render()
            self.assertFalse(app.last_error)
        app.zoom.set(14)
        app.set_zoom()
        app.toggle_theme()
        app.mode.set("이미지")
        app.switch_mode()
        self.assertFalse(app.result)
        app.source_image = Image.new("RGB", (200, 100), "black")
        app.render()
        self.assertTrue(app.result)
        app.clear()
        self.assertFalse(app.result)
        app.mode.set("텍스트")
        app.switch_mode()
        self.assertTrue(app.result)
        app.reset()
        app.clear()
        self.assertFalse(app.result)
        self.assertTrue(all(str(b.cget("state")) == "disabled" for b in app.export_buttons))

    def test_exports_and_image_selection(self):
        app = self.app
        with tempfile.TemporaryDirectory() as folder:
            txt, png = Path(folder) / "한글.txt", Path(folder) / "한글.png"
            with patch("main.filedialog.asksaveasfilename", return_value=str(txt)):
                app.save_txt()
            self.assertEqual(txt.read_text(encoding="utf-8-sig"), app.result)
            with patch("main.filedialog.asksaveasfilename", return_value=str(png)):
                app.save_png()
            with Image.open(png) as image:
                self.assertEqual(image.format, "PNG")
            app.mode.set("이미지")
            app.switch_mode()
            with patch("main.filedialog.askopenfilename", return_value=str(png)):
                app.choose_image()
            self.assertIsNotNone(app.source_image)
            self.assertTrue(app.result)


if __name__ == "__main__":
    unittest.main()

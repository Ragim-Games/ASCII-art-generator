import tempfile
import unittest
from pathlib import Path

from PIL import Image
from ascii_engine import (text_to_ascii, mask_to_text, style_mask, image_to_ascii,
                          load_image, art_to_image, STYLES)


class EngineTests(unittest.TestCase):
    def test_hangul_syllables_render_distinctly(self):
        values = [text_to_ascii(char) for char in "가나다힣"]
        self.assertEqual(len(set(values)), 4)
        self.assertTrue(all("█" in value for value in values))

    def test_decomposed_hangul_is_normalized(self):
        self.assertEqual(text_to_ascii("한"), text_to_ascii("한"))

    def test_multiline_and_ascii_fill(self):
        text = text_to_ascii("한글 ABC\nㄱㄴㄷ 123", fill="#")
        self.assertIn("\n\n", text)
        self.assertLessEqual(set(text), {"#", " ", "\n"})

    def test_all_styles_are_distinct(self):
        values = [text_to_ascii("한글", style=style) for style in STYLES.values()]
        self.assertEqual(len(set(values)), 6)

    def test_empty_and_input_limit(self):
        self.assertEqual(text_to_ascii(" \n"), "")
        with self.assertRaises(ValueError):
            text_to_ascii("가" * 301)

    def test_half_blocks(self):
        self.assertEqual(mask_to_text([[1, 1, 0], [1, 0, 1], [0, 1, 0]]), "█▀▄\n ▀")

    def test_outline_and_shadow(self):
        self.assertEqual(style_mask([[1]*3 for _ in range(3)], "outline")[1][1], 0)
        result = style_mask([[1, 0], [0, 1]], "3d")
        self.assertEqual(result[1][1], 1)
        self.assertEqual(result[4][4], .5)

    def test_transparency_and_inversion(self):
        transparent = Image.new("RGBA", (30, 30), (0, 0, 0, 0))
        self.assertFalse(image_to_ascii(transparent, width=30).strip())
        self.assertEqual(set(image_to_ascii(transparent, width=30, invert=True)), {"@", "\n"})

    def test_image_geometry_and_tall_image(self):
        art = image_to_ascii(Image.new("RGB", (160, 80), "black"), width=80)
        self.assertEqual(len(art.splitlines()), 20)
        self.assertEqual(len(art.splitlines()[0]), 80)
        with self.assertRaises(ValueError):
            image_to_ascii(Image.new("RGB", (1, 1000)), width=80)

    def test_png_and_unicode_path_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "한글 결과.png"
            art_to_image(text_to_ascii("한글")).save(path)
            image = load_image(path)
            self.assertEqual(image.mode, "RGBA")
            self.assertGreater(image.width, 48)
            self.assertGreater(image.height, 48)


if __name__ == "__main__":
    unittest.main()

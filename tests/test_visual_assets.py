import json
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path):
    with (ROOT / relative_path).open(encoding="utf-8") as handle:
        return json.load(handle)


def png_dimensions(path):
    with path.open("rb") as handle:
        header = handle.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"{path} is not a PNG image")
    return struct.unpack(">II", header[16:24])


class VisualAssetContractTests(unittest.TestCase):
    def test_hero_uses_a_local_high_resolution_portrait(self):
        hero = load_json("data/hero.json")
        relative_path = hero.get("avatarUrl")

        self.assertTrue(relative_path, "Hero portrait path is empty")
        portrait = ROOT / relative_path
        self.assertTrue(portrait.is_file(), f"Missing portrait: {relative_path}")
        width, height = png_dimensions(portrait)
        self.assertGreaterEqual(width, 1000)
        self.assertGreaterEqual(height, 1200)
        self.assertGreater(height, width)

    def test_every_employer_and_school_resolves_to_a_local_logo(self):
        experience = load_json("data/experience.json")["experiences"]
        education = load_json("data/education.json")["education"]
        entries = [
            (item["company"], item.get("logo")) for item in experience
        ] + [
            (item.get("institution") or item["school"], item.get("logo"))
            for item in education
        ]

        for name, relative_path in entries:
            with self.subTest(organization=name):
                self.assertTrue(relative_path, f"{name} is missing a logo path")
                logo_path = ROOT / relative_path
                self.assertTrue(logo_path.is_file(), f"Missing logo asset: {relative_path}")
                self.assertIn(logo_path.suffix.lower(), {".svg", ".png", ".webp"})

    def test_every_project_has_unique_large_card_artwork(self):
        projects = load_json("data/projects.json")["projects"]
        image_paths = [project.get("image") for project in projects]

        self.assertNotIn(None, image_paths)
        self.assertNotIn("", image_paths)
        self.assertEqual(len(image_paths), len(set(image_paths)), "Project art must be unique")

        for project, relative_path in zip(projects, image_paths):
            with self.subTest(project=project["title"]):
                artwork = ROOT / relative_path
                self.assertTrue(artwork.is_file(), f"Missing artwork: {relative_path}")
                width, height = png_dimensions(artwork)
                self.assertGreaterEqual(width, 1200)
                self.assertGreaterEqual(height, 700)


if __name__ == "__main__":
    unittest.main()

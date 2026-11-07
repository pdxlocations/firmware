import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("meshoregon_package", Path(__file__).with_name("package.py"))
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.build = self.root / "build"
        self.build.mkdir()
        (self.build / "firmware-test.factory.bin").write_bytes(b"factory")
        (self.build / "littlefs-test.bin").write_bytes(b"filesystem")
        (self.build / "firmware-test.mt.json").write_text(json.dumps({"part": [{"name": "spiffs", "offset": "0x300000", "size": "0x100000"}]}))
        self.artifacts = self.root / "artifacts"
        self.output = self.artifacts / "meshoregon-test"
        self.expected = self.root / "targets.json"
        self.expected.write_text('[{"board":"test"}]')

    def board(self):
        return package.package_board(self.build, self.output, "test", "esp32", "test-sha")

    def test_catalog_keeps_the_filesystem_partition_and_source_commit(self):
        record = self.board()
        self.assertEqual(record["flash"], [{"name": "firmware-test.factory.bin", "address": 0}, {"name": "littlefs-test.bin", "address": 0x300000}])
        package.catalog(self.artifacts, self.root / "release", self.expected, "test-sha", "test-version")
        catalog = json.loads((self.root / "release/meshoregon.json").read_text())
        self.assertEqual(catalog["targets"][0]["commit"], "test-sha")
        self.assertTrue((self.root / "release/meshoregon-test.zip").exists())

    def test_missing_board_blocks_publication(self):
        self.board()
        self.expected.write_text('[{"board":"test"},{"board":"missing"}]')
        with self.assertRaisesRegex(ValueError, "coverage mismatch"):
            package.catalog(self.artifacts, self.root / "release", self.expected, "test-sha", "version")

    def test_modified_archive_blocks_publication(self):
        self.board()
        (self.output / "meshoregon-test.zip").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            package.catalog(self.artifacts, self.root / "release", self.expected, "test-sha", "version")

    def test_overlapping_partitions_block_packaging(self):
        (self.build / "firmware-test.mt.json").write_text(json.dumps({"part": [{"name": "spiffs", "offset": "0x0", "size": "0x100000"}]}))
        with self.assertRaisesRegex(ValueError, "Overlapping"):
            self.board()

    def test_companion_ota_is_included_only_when_the_board_partition_fits(self):
        companion = self.build / "mt-esp32-ota.bin"
        companion.write_bytes(b"ota")
        for size in (None, "0x2", "0x100000"):
            with self.subTest(size=size):
                parts = [{"name": "spiffs", "offset": "0x300000", "size": "0x100000"}]
                if size:
                    parts.append({"name": "app1", "offset": "0x200000", "size": size})
                (self.build / "firmware-test.mt.json").write_text(json.dumps({"part": parts}))
                record = self.board()
                self.assertEqual(companion.name in [p["name"] for p in record["files"]], size == "0x100000")
                self.assertEqual(companion.name in [p["name"] for p in record["flash"]], size == "0x100000")

    def test_mui_companion_uses_the_flashapp_partition(self):
        (self.build / "mt-esp32s3-ota.bin").write_bytes(b"ota")
        (self.build / "firmware-test.mt.json").write_text(json.dumps({"part": [
            {"name": "flashApp", "subtype": "ota_1", "offset": "0x5D0000", "size": "0x0A0000"},
            {"name": "spiffs", "offset": "0x670000", "size": "0x180000"},
        ]}))
        self.assertIn({"name": "mt-esp32s3-ota.bin", "address": 0x5D0000}, self.board()["flash"])


if __name__ == "__main__":
    unittest.main()

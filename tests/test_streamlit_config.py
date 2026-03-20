import os
import tempfile
import unittest
from pathlib import Path

from modules.streamlit_ui.views import _config as streamlit_config


class TestStreamlitConfig(unittest.TestCase):
    def setUp(self):
        self.keys = ["API_BASE_URL", "STORAGE_PATH", "PIPELINE_SUMMARY_PATH"]
        self.saved_env = {key: os.environ.get(key) for key in self.keys}

    def tearDown(self):
        for key, value in self.saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_explicit_environment_values_win(self):
        os.environ["API_BASE_URL"] = "https://example.test/api"
        os.environ["STORAGE_PATH"] = "custom/records.json"
        os.environ["PIPELINE_SUMMARY_PATH"] = "custom/summary.json"

        self.assertEqual(
            streamlit_config.get_config_value("API_BASE_URL", default="http://127.0.0.1:8000"),
            "https://example.test/api",
        )
        self.assertEqual(
            streamlit_config.get_config_value("STORAGE_PATH", default="data/records.json"),
            "custom/records.json",
        )
        self.assertEqual(
            streamlit_config.get_config_value("PIPELINE_SUMMARY_PATH", default="reports/pipeline_run_summary.json"),
            "custom/summary.json",
        )

    def test_local_defaults_apply_when_env_missing(self):
        for key in self.keys:
            os.environ.pop(key, None)

        self.assertEqual(
            streamlit_config.get_config_value("API_BASE_URL", default="http://127.0.0.1:8000"),
            "http://127.0.0.1:8000",
        )
        self.assertTrue(
            streamlit_config.get_config_value(
                "STORAGE_PATH",
                default=str(streamlit_config.PROJECT_ROOT / "data" / "records.json"),
            ).replace("\\", "/").endswith("data/records.json")
        )
        self.assertTrue(
            streamlit_config.get_config_value(
                "PIPELINE_SUMMARY_PATH",
                default=str(streamlit_config.PROJECT_ROOT / "reports" / "pipeline_run_summary.json"),
            ).replace("\\", "/").endswith("reports/pipeline_run_summary.json")
        )

    def test_local_env_file_sets_missing_values_only(self):
        os.environ.pop("API_BASE_URL", None)
        os.environ.pop("PIPELINE_SUMMARY_PATH", None)
        os.environ["STORAGE_PATH"] = "env-wins.json"

        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            env_path.write_text(
                "API_BASE_URL=http://localhost:9000\n"
                "STORAGE_PATH=file-from-dotenv.json\n"
                "PIPELINE_SUMMARY_PATH=reports/from-dotenv.json\n",
                encoding="utf-8",
            )

            streamlit_config.load_local_env_file(env_path)

        self.assertEqual(os.environ["API_BASE_URL"], "http://localhost:9000")
        self.assertEqual(os.environ["STORAGE_PATH"], "env-wins.json")
        self.assertEqual(os.environ["PIPELINE_SUMMARY_PATH"], "reports/from-dotenv.json")

    def test_missing_required_value_error_is_clear(self):
        os.environ.pop("API_BASE_URL", None)

        with self.assertRaises(RuntimeError) as context:
            streamlit_config.get_config_value("API_BASE_URL")

        self.assertIn("Missing required Streamlit config: API_BASE_URL", str(context.exception))
        self.assertIn(".env", str(context.exception))


if __name__ == "__main__":
    unittest.main()
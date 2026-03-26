import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import modules.config.runtime_config as runtime_config_module
from modules.config.runtime_config import load_runtime_config


class TestRuntimeConfigModes(unittest.TestCase):
    def setUp(self):
        self.required_env_keys = [
            "APP_ENV",
            "APP_VERSION",
            "PORT",
            "UPLOAD_ACCESS_CODE",
            "PERSISTENCE_MODE",
            "STORAGE_PATH",
            "LOG_LEVEL",
            "ALLOW_LOCAL_FALLBACK",
            "BLOB_ACCOUNT",
            "BLOB_CONTAINER",
            "BLOB_PATH",
            "API_BASE_URL",
            "ENABLE_PIPELINE",
            "INPUT_SOURCE_PATH",
            "PIPELINE_SUMMARY_PATH",
        ]
        self._saved_env = {key: os.environ.get(key) for key in self.required_env_keys}

    def tearDown(self):
        for key, value in self._saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def _set_base_env(self):
        os.environ["APP_VERSION"] = "1.0.0"
        os.environ["PORT"] = "8000"
        os.environ["UPLOAD_ACCESS_CODE"] = "test-access-code"
        os.environ["PERSISTENCE_MODE"] = "json"
        os.environ["STORAGE_PATH"] = "data/test-records.json"
        os.environ["LOG_LEVEL"] = "INFO"
        os.environ["API_BASE_URL"] = "http://localhost:8000"
        os.environ["ENABLE_PIPELINE"] = "true"
        os.environ["INPUT_SOURCE_PATH"] = "data/opsight_sample_sales.csv"
        os.environ["PIPELINE_SUMMARY_PATH"] = "reports/pipeline_run_summary.json"
        os.environ.pop("BLOB_ACCOUNT", None)
        os.environ.pop("BLOB_CONTAINER", None)
        os.environ.pop("BLOB_PATH", None)

    def test_dev_mode_allows_local_fallback(self):
        self._set_base_env()
        os.environ["APP_ENV"] = "dev"
        os.environ["ALLOW_LOCAL_FALLBACK"] = "true"

        config = load_runtime_config()

        self.assertEqual(config.app_env, "dev")
        self.assertTrue(config.allow_local_fallback)

    def test_prod_mode_fails_when_local_fallback_enabled(self):
        self._set_base_env()
        os.environ["APP_ENV"] = "prod"
        os.environ["ALLOW_LOCAL_FALLBACK"] = "true"
        os.environ["BLOB_ACCOUNT"] = "acc"
        os.environ["BLOB_CONTAINER"] = "container"

        with self.assertRaises(RuntimeError) as context:
            load_runtime_config()

        self.assertIn("Local fallback is not allowed in production", str(context.exception))

    def test_prod_mode_fails_when_blob_config_missing(self):
        self._set_base_env()
        os.environ["APP_ENV"] = "prod"
        os.environ["ALLOW_LOCAL_FALLBACK"] = "false"

        with tempfile.TemporaryDirectory() as tmp_dir:
            missing_env_path = Path(tmp_dir) / ".env"
            with patch.object(runtime_config_module, "LOCAL_ENV_PATH", missing_env_path):
                with self.assertRaises(RuntimeError) as context:
                    load_runtime_config()

        message = str(context.exception)
        self.assertTrue(
            "Production mode requires BLOB_ACCOUNT to be set" in message
            or "Production mode requires BLOB_CONTAINER to be set" in message
            or "Production mode requires BLOB_PATH to be set" in message
        )

    def test_prod_mode_passes_with_blob_config_present(self):
        self._set_base_env()
        os.environ["APP_ENV"] = "prod"
        os.environ["ALLOW_LOCAL_FALLBACK"] = "false"
        os.environ["BLOB_ACCOUNT"] = "acc"
        os.environ["BLOB_CONTAINER"] = "container"
        os.environ["BLOB_PATH"] = "incoming/data.csv"

        config = load_runtime_config()

        self.assertEqual(config.app_env, "prod")
        self.assertFalse(config.allow_local_fallback)
        self.assertEqual(config.blob_account, "acc")
        self.assertEqual(config.blob_container, "container")
        self.assertEqual(config.blob_path, "incoming/data.csv")

    def test_local_env_file_sets_missing_values_only(self):
        for key in self.required_env_keys:
            os.environ.pop(key, None)
        os.environ["APP_VERSION"] = "2.0.0"

        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            env_path.write_text(
                "APP_ENV=dev\n"
                "APP_VERSION=1.0.0\n"
                "PORT=8000\n"
                "UPLOAD_ACCESS_CODE=local-dev-access-code\n"
                "PERSISTENCE_MODE=json\n"
                "STORAGE_PATH=data/from-dotenv.json\n"
                "LOG_LEVEL=INFO\n"
                "ALLOW_LOCAL_FALLBACK=true\n"
                "API_BASE_URL=http://127.0.0.1:8000\n"
                "ENABLE_PIPELINE=true\n"
                "INPUT_SOURCE_PATH=data/opsight_sample_sales.csv\n"
                "PIPELINE_SUMMARY_PATH=reports/from-dotenv.json\n",
                encoding="utf-8",
            )

            with patch.object(runtime_config_module, "LOCAL_ENV_PATH", env_path):
                config = load_runtime_config()

        self.assertEqual(config.app_env, "dev")
        self.assertEqual(config.app_version, "2.0.0")
        self.assertEqual(config.storage_path, "data/from-dotenv.json")
        self.assertEqual(config.pipeline_summary_path, "reports/from-dotenv.json")

    def test_missing_required_value_mentions_local_env_file(self):
        for key in self.required_env_keys:
            os.environ.pop(key, None)

        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"

            with patch.object(runtime_config_module, "LOCAL_ENV_PATH", env_path):
                with self.assertRaises(RuntimeError) as context:
                    load_runtime_config()

        self.assertIn("Missing required environment variable: APP_ENV", str(context.exception))
        self.assertIn(".env", str(context.exception))


if __name__ == "__main__":
    unittest.main()

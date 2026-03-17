import os
import unittest

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


if __name__ == "__main__":
    unittest.main()

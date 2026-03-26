import os
import tempfile
import unittest
from pathlib import Path

from scripts.validate_azure_container_app_runtime import validate_runtime_contract


class TestValidateAzureContainerAppRuntime(unittest.TestCase):
    def setUp(self):
        self.env_keys = [
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
            "CORS_ALLOWED_ORIGINS",
            "AZURE_STORAGE_CONNECTION_STRING",
        ]
        self.saved_env = {key: os.environ.get(key) for key in self.env_keys}

    def tearDown(self):
        for key, value in self.saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def _write_valid_env_file(self, env_file: Path) -> None:
        env_file.write_text(
            "APP_ENV=prod\n"
            "APP_VERSION=1.0.0\n"
            "PORT=8000\n"
            "UPLOAD_ACCESS_CODE=super-secret-code\n"
            "PERSISTENCE_MODE=json\n"
            "STORAGE_PATH=data/records.json\n"
            "LOG_LEVEL=INFO\n"
            "ALLOW_LOCAL_FALLBACK=false\n"
            "BLOB_ACCOUNT=stopsightdev\n"
            "BLOB_CONTAINER=opsight-raw\n"
            "BLOB_PATH=csv/Sample - Superstore.csv\n"
            "API_BASE_URL=https://opsight-api.calmstone-581ea79a.eastus.azurecontainerapps.io\n"
            "ENABLE_PIPELINE=true\n"
            "INPUT_SOURCE_PATH=data/opsight_sample_sales.csv\n"
            "PIPELINE_SUMMARY_PATH=reports/pipeline_run_summary.json\n"
            "AZURE_STORAGE_CONNECTION_STRING=secret-connection-string\n",
            encoding="utf-8",
        )

    def test_validation_passes_with_complete_runtime_contract(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_file = Path(tmp_dir) / "production.env"
            self._write_valid_env_file(env_file)

            is_valid, failures, summary = validate_runtime_contract(env_file)

        self.assertTrue(is_valid)
        self.assertEqual(failures, [])
        self.assertIn("APP_ENV=prod", summary)
        self.assertIn("Required secrets present", summary)

    def test_validation_fails_for_placeholder_secret_values(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_file = Path(tmp_dir) / "production.env"
            self._write_valid_env_file(env_file)
            env_file.write_text(
                env_file.read_text(encoding="utf-8").replace(
                    "UPLOAD_ACCESS_CODE=super-secret-code",
                    "UPLOAD_ACCESS_CODE=replace-me",
                ),
                encoding="utf-8",
            )

            is_valid, failures, _ = validate_runtime_contract(env_file)

        self.assertFalse(is_valid)
        self.assertTrue(any("UPLOAD_ACCESS_CODE" in failure for failure in failures))

    def test_validation_fails_when_connection_string_missing(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_file = Path(tmp_dir) / "production.env"
            self._write_valid_env_file(env_file)
            env_file.write_text(
                env_file.read_text(encoding="utf-8").replace(
                    "AZURE_STORAGE_CONNECTION_STRING=secret-connection-string\n",
                    "",
                ),
                encoding="utf-8",
            )

            is_valid, failures, _ = validate_runtime_contract(env_file)

        self.assertFalse(is_valid)
        self.assertTrue(any("AZURE_STORAGE_CONNECTION_STRING" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
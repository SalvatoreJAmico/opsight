import unittest

from modules.api.session_state import (
    get_session_state,
    reset_session_state,
    set_active_dataset,
    set_anomaly_status,
    set_dataset_source_metadata,
    set_pipeline_status,
    set_prediction_status,
)


class TestSessionState(unittest.TestCase):
    def setUp(self):
        reset_session_state()

    def test_default_session_state(self):
        self.assertEqual(
            get_session_state(),
            {
                "active_dataset": None,
                "dataset_source_metadata": None,
                "pipeline_status": "not_run",
                "anomaly_status": "idle",
                "prediction_status": "idle",
            },
        )

    def test_dataset_change_resets_processing_state(self):
        set_active_dataset("sales_csv")
        set_pipeline_status("completed")
        set_anomaly_status("completed")
        set_prediction_status("completed")

        set_active_dataset("transactions_json")

        self.assertEqual(
            get_session_state(),
            {
                "active_dataset": "transactions_json",
                "dataset_source_metadata": None,
                "pipeline_status": "not_run",
                "anomaly_status": "idle",
                "prediction_status": "idle",
            },
        )

    def test_dataset_source_metadata_can_be_set_and_is_cleared_on_dataset_change(self):
        set_active_dataset("sales_csv")
        set_dataset_source_metadata(
            {
                "dataset_id": "sales_csv",
                "source_name": "Superstore Sales Dataset",
                "source_url": "https://www.kaggle.com/datasets/vivek468/superstore-dataset-final",
                "source_location": "opsight-raw/csv/Sample - Superstore.csv",
                "source_type": "blob",
            }
        )

        state_with_metadata = get_session_state()
        self.assertIsNotNone(state_with_metadata["dataset_source_metadata"])
        self.assertEqual(
            state_with_metadata["dataset_source_metadata"]["source_name"],
            "Superstore Sales Dataset",
        )

        set_active_dataset("transactions_json")
        self.assertIsNone(get_session_state()["dataset_source_metadata"])


if __name__ == "__main__":
    unittest.main()

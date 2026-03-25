import unittest

from modules.api.session_state import (
    get_session_state,
    reset_session_state,
    set_active_dataset,
    set_anomaly_status,
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
                "pipeline_status": "not_run",
                "anomaly_status": "idle",
                "prediction_status": "idle",
            },
        )


if __name__ == "__main__":
    unittest.main()

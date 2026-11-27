import unittest
from src.audit_dataset import audit
class AuditedDatasetTest(unittest.TestCase):
    def test_release(self):
        result=audit()
        self.assertEqual(result["rows"],119)
        self.assertEqual(result["missing_cells"],74)
        self.assertEqual(result["duplicate_months"],0)

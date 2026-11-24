import io
import unittest
from unittest.mock import patch
from app import app, normalize_postcode


class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def upload(self, csv, approved=True):
        data = {'file': (io.BytesIO(csv.encode()), 'synthetic.csv'), 'destinations': 'gri'}
        if approved:
            data.update({field: 'yes' for field in ('secure_environment', 'permission', 'external_transfer')})
        return self.client.post('/api/process', data=data, headers={'X-API-Key': 'synthetic-test-key'})

    def test_postcode_format(self):
        self.assertEqual(normalize_postcode('g1 1aa'), 'G1 1AA')
        self.assertIsNone(normalize_postcode('not a postcode'))

    @patch('app.calculate_distances')
    def test_approval_required(self, calculate):
        self.assertEqual(self.upload('postcode\nG1 1AA\n', False).status_code, 400)
        calculate.assert_not_called()

    @patch('app.calculate_distances')
    def test_invalid_input_not_transmitted(self, calculate):
        self.assertEqual(self.upload('postcode\nnot a postcode\n').status_code, 400)
        calculate.assert_not_called()

    @patch('app.calculate_distances', return_value=([1.2], [5], [None]))
    def test_synthetic_success(self, calculate):
        response = self.upload('id,postcode\n001,G1 1AA\n')
        self.assertEqual(response.status_code, 200)
        self.assertIn('001,G1 1AA,1.2,5,5', response.json['csv'])
        self.assertEqual(calculate.call_count, 2)

    def test_cross_origin_rejected(self):
        response = self.client.post('/api/process', headers={'Origin': 'https://example.invalid'})
        self.assertEqual(response.status_code, 403)

    def test_no_store(self):
        self.assertEqual(self.client.get('/').headers['Cache-Control'], 'no-store')


if __name__ == '__main__':
    unittest.main()

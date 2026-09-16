import unittest
from unittest.mock import Mock
from gateway_retry import create_with_retry

class Failure(Exception):
    def __init__(self, status, delay=120):
        self.status_code = status
        self.body = {'retry_after': delay}

class GatewayRetryTests(unittest.TestCase):
    def test_504_preserves_request_and_honors_delay(self):
        response = Mock()
        response.model_dump.return_value = {'choices': []}
        fn = Mock(side_effect=[Failure(504, 150), response])
        sleep = Mock()
        result, attempts = create_with_retry(fn, {'max_tokens':8192}, sleep=sleep)
        self.assertEqual(fn.call_args_list[0], fn.call_args_list[1])
        sleep.assert_called_once_with(150)
        self.assertEqual(len(attempts), 2)
        self.assertTrue(attempts[0]['usage_unknown'])

    def test_exhaustion_stops_after_three_and_records_unknown_usage(self):
        fn = Mock(side_effect=Failure(504))
        sleep = Mock()
        with self.assertRaises(Failure) as caught:
            create_with_retry(fn, {}, sleep=sleep)
        self.assertEqual(fn.call_count,3)
        self.assertEqual(sleep.call_count,2)
        self.assertEqual(len(caught.exception.gateway_attempts),3)

    def test_auth_failure_is_not_retried(self):
        fn=Mock(side_effect=Failure(401)); sleep=Mock()
        with self.assertRaises(Failure):
            create_with_retry(fn, {}, sleep=sleep)
        sleep.assert_not_called()
        self.assertEqual(fn.call_count,1)

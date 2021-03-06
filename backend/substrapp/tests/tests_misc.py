from django.test import TestCase

from mock import patch

from substrapp.utils import raise_if_path_traversal, uncompress_path

from substrapp.ledger.exceptions import LedgerAssetNotFound, LedgerInvalidResponse

from substrapp.ledger.api import get_object_from_ledger, log_fail_tuple, log_start_tuple, \
    log_success_tuple, query_tuples, call_ledger

from .assets import traintuple

import os


DIRECTORY = '/tmp/testmisc/'
CHANNEL = 'mychannel'


class MockDevice():
    """A mock device to temporarily suppress output to stdout
    Similar to UNIX /dev/null.
    """

    def write(self, s):
        pass


class MockArchive:
    def __init__(self, traversal=True):
        if traversal:
            self.files = ['../../foo.csv', '../bar.csv']
        else:
            self.files = ['foo.csv', 'bar.csv']

    def __iter__(self):
        return iter(self.files)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return True

    def namelist(self):
        return self.files

    def getnames(self):
        return self.files


class MiscTests(TestCase):
    """Misc tests"""

    def test_get_object_from_ledger(self):
        with patch('substrapp.ledger.api.query_ledger') as mquery_ledger:
            mquery_ledger.side_effect = LedgerAssetNotFound('Not Found')
            self.assertRaises(LedgerAssetNotFound, get_object_from_ledger, CHANNEL, 'key', 'fake_query')

        with patch('substrapp.ledger.api.query_ledger') as mquery_ledger:
            mquery_ledger.side_effect = LedgerInvalidResponse('Bad Response')
            self.assertRaises(LedgerInvalidResponse, get_object_from_ledger, CHANNEL, 'key', 'fake_query')

        with patch('substrapp.ledger.api.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = {'key': 'key'}
            data = get_object_from_ledger(CHANNEL, 'key', 'good_query')
            self.assertEqual(data['key'], 'key')

    def test_log_fail_tuple(self):
        with patch('substrapp.ledger.api.update_ledger') as mupdate_ledger:
            mupdate_ledger.return_value = None
            log_fail_tuple(CHANNEL, 'traintuple', 'key', 'error_msg')

        with patch('substrapp.ledger.api.update_ledger') as mupdate_ledger:
            mupdate_ledger.return_value = None
            log_fail_tuple(CHANNEL, 'testtuple', 'key', 'error_msg')

    def test_log_start_tuple(self):
        with patch('substrapp.ledger.api.update_ledger') as mupdate_ledger:
            mupdate_ledger.return_value = None
            log_start_tuple(CHANNEL, 'traintuple', 'key')

        with patch('substrapp.ledger.api.update_ledger') as mupdate_ledger:
            mupdate_ledger.return_value = None
            log_start_tuple(CHANNEL, 'testtuple', 'key')

    def test_log_success_tuple(self):
        with patch('substrapp.ledger.api.update_ledger') as mupdate_ledger:
            mupdate_ledger.return_value = None
            res = {
                'end_model_key': '<some_key>',
                'end_model_checksum': 'hash',
                'end_model_storage_address': 'storage_address',
                'job_task_log': 'log',
            }
            log_success_tuple(CHANNEL, 'traintuple', 'key', res)

        with patch('substrapp.ledger.api.update_ledger') as mupdate_ledger:
            mupdate_ledger.return_value = None
            res = {
                'global_perf': '0.99',
                'job_task_log': 'log',
            }
            log_success_tuple(CHANNEL, 'testtuple', 'key', res)

    def test_query_tuples(self):
        with patch('substrapp.ledger.api.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = None
            query_tuples(CHANNEL, 'traintuple', 'data_owner')

        with patch('substrapp.ledger.api.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = None
            query_tuples(CHANNEL, 'testtuple', 'data_owner')

    def test_path_traversal(self):
        # Zip
        with patch('substrapp.utils.zipfile.is_zipfile') as mock_is_zipfile, \
                patch('substrapp.utils.ZipFile') as mock_zipfile:
            mock_is_zipfile.return_value = True
            mock_zipfile.return_value = MockArchive()

            self.assertRaises(Exception,
                              uncompress_path('', DIRECTORY))

        # Tar
        with patch('substrapp.utils.zipfile.is_zipfile') as mock_is_zipfile, \
                patch('substrapp.utils.tarfile.is_tarfile') as mock_is_tarfile, \
                patch('substrapp.utils.tarfile.open') as mock_tarfile:
            mock_is_zipfile.return_value = False
            mock_is_tarfile.return_value = True
            mock_tarfile.return_value = MockArchive()

            self.assertRaises(Exception,
                              uncompress_path('', DIRECTORY))

        # Models
        with self.assertRaises(Exception):
            model_dst_path = os.path.join(DIRECTORY, 'model/../../hackermodel')
            raise_if_path_traversal([model_dst_path], os.path.join(DIRECTORY, 'model/'))

    def test_call_ledger_with_bookmark(self):

        with patch('substrapp.ledger.api._call_ledger') as m_call_ledger:
            m_call_ledger.side_effect = [
                {'results': traintuple[i:i + 2], 'bookmark': f'bookmark_{i}'}
                for i in range(0, len(traintuple), 2)
            ] + [{'results': "", 'bookmark': 'bookmark_end'}]
            response = call_ledger(CHANNEL, 'query', 'queryTraintuples')
            self.assertEqual(response, traintuple)

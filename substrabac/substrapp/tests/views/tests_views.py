import mock


from rest_framework.test import APITestCase

from substrapp.views.utils import ComputeHashMixin
from substrapp.views.datasample import path_leaf
from substrapp.utils import compute_hash
from substrapp.ledger_utils import get_object_from_ledger

from ..assets import objective

MEDIA_ROOT = "/tmp/unittests_views/"


# APITestCase
class ViewTests(APITestCase):
    def test_data_sample_path_view(self):
        self.assertEqual('tutu', path_leaf('/toto/tata/tutu'))
        self.assertEqual('toto', path_leaf('/toto/'))

    def test_utils_ComputeHashMixin(self):

        compute = ComputeHashMixin()
        myfile = 'toto'
        key = 'tata'

        myfilehash = compute_hash(myfile)
        myfilehashwithkey = compute_hash(myfile, key)

        self.assertEqual(myfilehash, compute.compute_hash(myfile))
        self.assertEqual(myfilehashwithkey, compute.compute_hash(myfile, key))

    def test_utils_get_object_from_ledger(self):

        with mock.patch('substrapp.ledger_utils.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = objective
            data = get_object_from_ledger('', 'queryObjective')

            self.assertEqual(data, objective)
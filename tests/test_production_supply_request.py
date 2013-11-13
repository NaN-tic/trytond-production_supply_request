#!/usr/bin/env python
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.

import sys
import os
DIR = os.path.abspath(os.path.normpath(os.path.join(__file__,
    '..', '..', '..', '..', '..', 'trytond')))
if os.path.isdir(DIR):
    sys.path.insert(0, os.path.dirname(DIR))

import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import test_depends
from trytond.backend.sqlite.database import Database as SQLiteDatabase


class TestCase(unittest.TestCase):
    '''
    Test module.
    '''

    def setUp(self):
        trytond.tests.test_tryton.install_module('production_supply_request')

    def test0006depends(self):
        '''
        Test depends.
        '''
        test_depends()


def doctest_dropdb(test):
    database = SQLiteDatabase().connect()
    cursor = database.cursor(autocommit=True)
    try:
        database.drop(cursor, ':memory:')
        cursor.commit()
    finally:
        cursor.close()


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCase))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

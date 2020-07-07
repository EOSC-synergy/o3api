# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019 Karlsruhe Institute of Technology - Steinbuch Centre for Computing
# This code is distributed under the MIT License
# Please, see the LICENSE file
#
"""
Created on Sat June 30 23:47:51 2020
@author: vykozlov
"""

import pkg_resources
import unittest

class TestModelMethods(unittest.TestCase):

    def setUp(self):
        module = __name__.split('.', 1)
        pkg = pkg_resources.get_distribution(module[0])
        self.meta = {
            'name' : None,
            'version' : None,
            'summary' : None,
            'home-page' : None,
            'author' : None,
            'author-email' : None,
            'license' : None
        }
        for line in pkg.get_metadata_lines("PKG-INFO"):
            line_low = line.lower() # to avoid inconsistency due to letter cases
            for par in self.meta:
                if line_low.startswith(par.lower() + ":"):
                    _, value = line.split(": ", 1)
                    self.meta[par] = value


    def test_metadata_type(self):
        """
        Test that self.meta is dict
        """
        self.assertTrue(type(self.meta) is dict)


    def test_metadata_values(self):
        """
        Test that metadata contains right values (subset)
        """
        self.assertEqual(self.meta['name'].replace('-','_'),
                        'o3as'.replace('-','_'))
        self.assertEqual(self.meta['author'], 'KIT-IMK')
        self.assertEqual(self.meta['author-email'].lower(), 'tobias.kerzenmacher@kit.edu'.lower())
        self.assertEqual(self.meta['license'], 'GNU LGPLv3')


if __name__ == '__main__':
    unittest.main()

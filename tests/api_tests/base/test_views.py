# -*- coding: utf-8 -*-
from nose.tools import *  # flake8: noqa

from tests.base import ApiTestCase
from api.base.settings.defaults import API_PREFIX

class TestApiBaseViews(ApiTestCase):

    def test_root_returns_200(self):
        res = self.app.get('/{}'.format(API_PREFIX))  # TODO this is '...//v2/' but should be '.../v2/' - but passes
        assert_equal(res.status_code, 200)

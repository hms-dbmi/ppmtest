import unittest
import yaml
import time
import os

import roles_hypatio as roles
from browser import Browser

import logging
from selenium.webdriver.remote.remote_connection import LOGGER as SeleniumLogger
SeleniumLogger.setLevel(logging.WARNING)

logger = logging.getLogger('hypatio-test-suite')


class HypatioTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # Set the environment
        cls.environment = os.environ.get('HYPATIO_TEST_ENVIRONMENT', 'local')
        cls.test_integrations = os.environ.get('HYPATIO_TEST_INTEGRATIONS', False)

        # Get the path
        path = os.path.dirname(__file__)

        # Determine places
        with open(os.path.join(path, 'urls.yml'), 'r') as stream:
            try:
                cls.urls = yaml.load(stream)['urls'][cls.environment]
            except Exception as e:
                logger.exception(e)
                quit()

        # Load accounts
        with open(os.path.join(path, 'accounts.yml'), 'r') as stream:
            try:
                cls.accounts = yaml.load(stream)['accounts'][cls.environment]
            except Exception as e:
                logger.exception(e)
                quit()

        logger.debug('Starting tests...')

        super(HypatioTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):

        logger.debug('Cleaning up tests...')

        super(HypatioTestCase, cls).tearDownClass()

    @staticmethod
    def cleanupBrowsers(browsers):

        # Release browsers
        for browser in browsers:

            # Close all tabs
            browser.close_tabs()
            browser.quit()
            del browser

    def _test_public(self, independent=False, browser_name='firefox'):

        # Create the browser
        browser = Browser(browser_name, url=self.urls['selenium'])

        # Make sure browsers are released
        self.addCleanup(self.cleanupBrowsers, [browser])

    def test_hypatio_chrome(self):
        self._test_public(False, 'remote_chrome')

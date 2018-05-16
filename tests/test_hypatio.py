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

WAIT_TIME = 10


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

    def _test_n2c2_t1(self, independent=False, browser_name='firefox'):

        # Create the browser
        browser = Browser(browser_name, url=self.urls['selenium'])

        # Make sure browsers are released
        self.addCleanup(self.cleanupBrowsers, [browser])

        browser.go_to_tab('hypatio')

        browser.visit("http://hypatio.local.test.com/projects/list_data_challenges/")
        browser.is_element_present_by_partial_text('National NLP Clinical Challenges (n2c2)', 5)

        browser.click_link_by_partial_text('2018 Track 1')

        assert (browser.is_element_visible_by_partial_text('Click here for more details', 5))

        browser.click_link_by_text('Click here for more details')

        browser.click_link_by_partial_text('Register / Sign In')

        assert (browser.is_element_visible_by_name('email', 5))

        browser.fill('email', "test@test.com")
        browser.fill('password', "test1234!!")

        browser.find_by_css('.auth0-lock-submit').first.click()

        if browser.is_element_visible_by_name('first_name', 5):
            browser.fill('first_name', "test_first")
            browser.fill('last_name', "test_last")
            browser.fill('professional_title', "test_title")
            browser.select("country", "US")

            browser.find_by_text("Update").click()

        if browser.is_element_visible_by_id('person-name', 5):
            browser.find_by_id("person-name").fill("test_name")
            browser.find_by_id("email").fill("test_email")
            browser.find_by_id("organization").fill("test_organization")
            browser.find_by_id("e-signature").fill("test_signature")
            browser.find_by_id("professional-title").fill("test_title")
            browser.find_by_id("i-agree").check()

            browser.find_by_name("submit_form").first.click()

        if browser.is_element_visible_by_id('registrant-is', 5):
            browser.find_by_id("registrant-is").click()
            browser.find_by_id("person-name").fill("test_name")
            browser.find_by_id('professional-title').first.fill("test_title")
            browser.find_by_id("institution").fill("test_institution")
            browser.find_by_id("address").fill("test_address")
            browser.find_by_id("city").fill("test_city")
            browser.find_by_id("state").fill("test_state")
            browser.find_by_id("zip").fill("test_zip")
            browser.find_by_id("country").fill("test_country")
            browser.find_by_id("person-phone").fill("test_phone")
            browser.find_by_id("person-email").fill("test_email")
            browser.find_by_id("electronic-signature").fill("test_signature")
            browser.find_by_xpath("//input[@id='professional-title']")[1].fill("test_title")
            browser.find_by_id("i-agree").check()
            browser.find_by_name("submit_form").first.click()

        if browser.is_element_visible_by_text('Create Team', 5):
            browser.find_by_text('Create Team').click()
            if browser.is_element_visible_by_text('Sign me up!', 5):
                browser.find_by_text('Sign me up!').click()

        if browser.is_element_visible_by_css('.btn.btn-danger.finalize-team', 5):
            browser.find_by_css('.btn.btn-danger.finalize-team').click()

    def test_hypatio_chrome(self):
        self._test_n2c2_t1(False, 'remote_chrome')

import unittest
import yaml
import time
import os

import roles
from browser import Browser
from ppm_fhir.fhir_services import FHIRServices

import logging
from selenium.webdriver.remote.remote_connection import LOGGER as SeleniumLogger
SeleniumLogger.setLevel(logging.WARNING)

logger = logging.getLogger('ppm-test-suite')


class PPMTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # Set the environment
        cls.environment = os.environ.get('PPM_TEST_ENVIRONMENT', 'local')
        cls.test_integrations = os.environ.get('PPM_TEST_INTEGRATIONS', False)

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

        # Connect to FHIR.
        cls.fhir = FHIRServices(cls.urls['fhir'])

        logger.debug('Starting tests...')

        super(PPMTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):

        logger.debug('Cleaning up tests...')

        super(PPMTestCase, cls).tearDownClass()

    @staticmethod
    def cleanupBrowsers(browsers):

        # Release browsers
        for browser in browsers:

            # Close all tabs
            browser.close_tabs()
            browser.quit()
            del browser

    @staticmethod
    def cleanupUser(browser, admin, fhir_id):

        # Have the admin delete the user
        admin.delete_user(browser, fhir_id)

    def _test_autism(self, independent=False, browser_name='firefox'):

        # Create the browser
        browser = Browser(browser_name, url=self.urls['selenium'])

        # Make sure browsers are released
        self.addCleanup(self.cleanupBrowsers, [browser])

        # Create an email inbox.
        email = roles.Email(url=self.urls['inbox'])

        # Create the entities.
        user_key = 'asd-independent' if independent else 'asd-dependent'
        user = roles.AutismUser(self.urls,
                                email_address=self.accounts[user_key]['email'],
                                password=self.accounts[user_key]['password'],
                                independent=independent)

        # Sign up.
        signed_up = user.log_in_to_p2m2(browser)
        self.assertTrue(signed_up, msg='Patient could not log in')

        # Verify email.
        user.verify_email(browser, email)

        # Make sure emails get cleared
        self.addCleanup(email.clear, browser)

        # Register.
        user.register(browser)

        # Check for the user in the DB.
        record = user.data.get_patient_record()
        self.assertIsNotNone(record,
                             msg='Patient record does not exist in the FHIR database')

        # Get their ID
        fhir_id = record['fhir_id']

        # Ensure the user gets cleaned up
        self.addCleanup(admin.delete_user, admin_browser, fhir_id)

        # Check enrollment status.
        status = user.data.get_enrollment_status()
        self.assertEqual('registered', status,
                         msg='Patient enrollment status is \'{}\', (should be \'registered\') '
                             'following registration submission'.format(status))

        # Fill out consent.
        user.consent(browser)

        # Check enrollment status.
        status = user.data.get_enrollment_status()
        self.assertEqual('consented', status,
                         msg='Patient enrollment status is not \'consented\' following consent submission')

        # Fill in points of care.
        user.points_of_care(browser,
                            ['Massachusetts General Hospital',
                             'Beth Isreal Deaconess Medical Center',
                             'Brigham and Women\'s Hospital'])

        # Ensure the admin received an email with the approval link.
        admin_link = admin.get_signup_notification_link(browser, email)
        self.assertIn('participants/{}'.format(fhir_id), admin_link,
                      msg='Link in admin notification email is not correct: {}'.format(admin_link))

        # Create the admin browser
        admin_browser = Browser(browser_name, url=self.urls['selenium'])

        # Make sure browsers are released
        self.addCleanup(self.cleanupBrowsers, [admin_browser])

        # Create an admin user.
        admin = roles.Administrator(self.urls,
                                    email_address=self.accounts['admin']['email'],
                                    password=self.accounts['admin']['password'])

        # Login in
        admin.log_in_to_p2m2_admin(admin_browser)

        # Approve them.
        admin.approve_user(admin_browser, fhir_id)

        # Pause
        time.sleep(3)

        # Reload.
        user.go_to_dashboard(browser)
        browser.reload()

        # Ensure the admin received an email with the approval link.
        user_link = user.get_approval_link(browser, email)
        self.assertIn('dashboard/dashboard', user_link,
                      msg='Link in user approval notification email is not correct: {}'.format(user_link))

        # Do the questionnaire.
        user.questionnaire(browser)

        # Do Twitter.
        user.twitter_handle(browser)

        # Check for integration testing
        if self.test_integrations:

            # TODO: Implement FitBit integration

            # Log into Facebook
            user.facebook(browser, email_address=self.accounts['facebook']['email'],
                          password=self.accounts['facebook']['password'])

        # View the profile.
        user.go_to_profile(browser)

    def _test_neer(self, browser_name='firefox'):

        # Create the browser
        browser = Browser(browser_name, url=self.urls['selenium'])

        # Make sure browsers are released
        self.addCleanup(self.cleanupBrowsers, [browser])

        # Create an email inbox.
        email = roles.Email(url=self.urls['inbox'])

        # Create the entities.
        user = roles.NEERUser(self.urls,
                              email_address=self.accounts['neer']['email'],
                              password=self.accounts['neer']['password'])

        # Sign up.
        signed_up = user.log_in_to_p2m2(browser)
        self.assertTrue(signed_up, msg='Patient could not log in')

        # Verify email.
        user.verify_email(browser, email)

        # Make sure emails get cleared
        self.addCleanup(email.clear, browser)

        # Register.
        user.register(browser)

        # Check for the user in the DB.
        record = user.data.get_patient_record()
        self.assertIsNotNone(record,
                             msg='Patient record does not exist in the FHIR database')

        # Get their ID
        fhir_id = record['fhir_id']

        # Ensure the user gets cleaned up
        self.addCleanup(admin.delete_user, admin_browser, fhir_id)

        # Check enrollment status.
        status = user.data.get_enrollment_status()
        self.assertEqual('registered', status,
                         msg='Patient enrollment status is \'{}\', (should be \'registered\') '
                             'following registration submission'.format(status))

        # Fill out consent.
        user.consent(browser)

        # Check enrollment status.
        status = user.data.get_enrollment_status()
        self.assertEqual('consented', status,
                         msg='Patient enrollment status is not \'consented\' following consent submission')

        # Do the questionnaire.
        user.questionnaire(browser)

        # Ensure the admin received an email with the approval link.
        admin_link = admin.get_signup_notification_link(browser, email)
        self.assertIn('participants/{}'.format(fhir_id), admin_link,
                      msg='Link in admin notification email is not correct: {}'.format(admin_link))

        # Create the admin browser
        admin_browser = Browser(browser_name, url=self.urls['selenium'])

        # Make sure browsers are released
        self.addCleanup(self.cleanupBrowsers, [admin_browser])

        # Create an admin user.
        admin = roles.Administrator(self.urls,
                                    email_address=self.accounts['admin']['email'],
                                    password=self.accounts['admin']['password'])

        # Login in
        admin.log_in_to_p2m2_admin(admin_browser)

        # Approve them.
        admin.approve_user(admin_browser, fhir_id)

        # Pause
        time.sleep(3)

        # Reload.
        user.go_to_dashboard(browser)
        browser.reload()

        # Ensure the admin received an email with the approval link.
        user_link = user.get_approval_link(browser, email)
        self.assertIn('dashboard/dashboard', user_link,
                      msg='Link in user approval notification email is not correct: {}'.format(user_link))

        # Fill in points of care.
        user.points_of_care(browser,
                            ['Massachusetts General Hospital',
                             'Beth Isreal Deaconess Medical Center',
                             'Brigham and Women\'s Hospital'])

        # Do Twitter.
        user.twitter_handle(browser)

        # Check for integration testing
        if self.test_integrations:

            # TODO: Implement FitBit integration

            # Log into Facebook
            user.facebook(browser, email_address=self.accounts['facebook']['email'],
                          password=self.accounts['facebook']['password'])

        # View the profile.
        user.go_to_profile(browser)

    # Do the tests here.
    def test_autism_independent_firefox(self):
        self._test_autism(True, 'remote_firefox')

    def test_autism_independent_chrome(self):
        self._test_autism(True, 'remote_chrome')

    def test_autism_dependent_firefox(self):
        self._test_autism(False, 'remote_firefox')

    def test_autism_dependent_chrome(self):
        self._test_autism(False, 'remote_chrome')

    def test_neer_firefox(self):
        self._test_neer('remote_firefox')

    def test_neer_chrome(self):
        self._test_neer('remote_chrome')


import time
import random
import string
import re
import yaml
import furl
from datetime import datetime


from browser import Browser

import logging
logger = logging.getLogger('ppm-test-suite')

# Set a default wait time in seconds
WAIT_TIME = 10


class _User:
    """
    This class provides convenience methods for performing various tasks as a user in PPM
    """

    def __init__(self, urls, email_address=None, password='PPMIsGreat!', project='none', independent=True,
                 first_name='John', last_name='Smith', address='10 Main St.', address_cont='#199',
                 city='Boston', state='MA', zip='02445', phone='(555) 555-5555',
                 twitter='jsmith', date_of_birth='01/01/1980'):

        # Save the parameters.
        if email_address is None:
            self.email_address = self.get_random_email(project)
        else:
            self.email_address = email_address

        # Retain passed parameters.
        self.password = password
        self.independent = independent
        self.project = project
        self.first_name = first_name
        self.last_name = last_name
        self.address = address
        self.address_cont = address_cont
        self.city = city
        self.state = state
        self.zip = zip
        self.phone = phone
        self.twitter = twitter
        self.date_of_birth = date_of_birth

        # Save URLs
        self.urls = urls

        # Get a data connection.
        self.data = Data(self.urls['fhir'], self.email_address, self.project)

    def clear(self):

        # Delete everything from FHIR.
        self.data.delete_all()

    @staticmethod
    def get_random_email(project):

        # Generate one.
        random_id = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
        email = 'ppmtest-{}-{}@ppm.com'.format(project, random_id).lower()

        return email

    def sign_up_to_p2m2(self, browser, wait_time=WAIT_TIME):

        # Go to the correct tab.
        browser.go_to_tab('p2m2')

        # Check the URL.
        if browser.url != '{}{}'.format(self.urls['p2m2'], self.project):
            browser.visit('{}{}'.format(self.urls['p2m2'], self.project))
            logger.debug('Going to the dashboard...')

        if not browser.is_element_visible_by_partial_text('Start the registration process', wait_time):
            logger.error('Link to sign up was not found')
            return False

        browser.find_by_text('Start the registration process').first.click()
        logger.debug('Starting registration...')

        if not browser.is_element_visible_by_partial_text('Click here to proceed', wait_time):
            logger.error('Link to proceed to registration was not found')
            return False

        time.sleep(2)
        browser.find_by_text('Click here to proceed').first.click()
        logger.debug('Proceeding to registration...')

        # Sign into Auth0
        time.sleep(5)
        if not browser.is_element_visible_by_partial_text('Sign Up', wait_time):
            logger.error('"Sign Up" button was not found')
            return False

        browser.click_link_by_text('Sign Up')
        logger.debug('Opting to sign up...')

        time.sleep(2)

        if not browser.is_element_visible_by_name('email', wait_time):
            logger.error('E-Mail input field was not found')
            return False

        browser.fill('email', self.email_address)
        browser.fill('password', self.password)

        time.sleep(2)

        browser.find_by_css('.auth0-lock-submit').first.click()
        logger.debug('Submitting credentials...')

        time.sleep(2)

        # Wait for the reload.
        if not browser.is_element_present_by_partial_text('Dashboard', wait_time):
            logger.error('Dashboard was not reached')
            return False

        return True


class AutismUser(_User):

    def __init__(self, urls, email_address=None, password='PPMIsGreat!', independent=True,
                 first_name='John', last_name='Smith', address='10 Main St.', address_cont='#199',
                 city='Boston', state='MA', zip='02445', phone='(555) 555-5555',
                 twitter='jsmith', date_of_birth='01/01/1980'):

        # Call super with 'autism' as the project.
        _User.__init__(self, urls, email_address, password, 'autism', independent, first_name,
                       last_name, address, address_cont, city, state, zip, phone, twitter,
                       date_of_birth)

class Email:
    """
    This class provides convenience methods for actions surrounding email
    """

    def __init__(self, url):

        # Save the URL
        self.url = url

    def clear(self, browser, wait_time=WAIT_TIME):

        # Go to the correct tab.
        browser.go_to_tab('inbox')

        # Ensure we're at the inbox.
        browser.visit(self.url)

        # Refresh.
        self.refresh(browser, wait_time)

        # Check for the button.
        if not browser.is_element_present_by_partial_text('Delete all messages', wait_time):
            logger.error('"Delete all messages" link could not be found')
            return False

        # Click it.
        browser.click_link_by_partial_text('Delete all messages')

        # Check for the confirmation alert.
        if not browser.is_element_visible_by_css('.btn.btn-danger', wait_time):
            logger.error('Delete confirmation alert could not be found')
            return False

        # Confirm.
        browser.find_by_css('.btn.btn-danger').first.click()

        return True

    def refresh(self, browser, wait_time=WAIT_TIME):

        # Go to the correct tab.
        browser.go_to_tab('inbox')

        # Check for the refresh button.
        if not browser.is_element_visible_by_xpath('//button[@title="Refresh"]', wait_time):
            logger.error('Refresh button could not be found ')
            return False

        # Click it.
        browser.find_by_xpath('//button[@title="Refresh"]', wait_time).first.click()

        return True

    def get_email_at_index(self, browser, index=0, html=False, wait_time=WAIT_TIME):

        # Go to the correct tab.
        browser.go_to_tab('inbox')

        # Ensure we're at the inbox.
        browser.visit(self.url)

        # Refresh.
        self.refresh(browser, wait_time)

        # Get the mail list.
        if not browser.is_element_visible_by_css('.messages.container-fluid.ng-scope', wait_time):
            logger.error('Message list is not visible')
            print('Message list is not visible')
            return None

        # Check for messages.
        if not browser.is_element_visible_by_css('.msglist-message.row.ng-scope', wait_time):
            logger.error('No messages in the list')
            print('No messages in the list')
            return None

        # Get the message divs.
        messages = browser.find_by_css('.msglist-message.row.ng-scope')

        # Ensure one for the index exists.
        if index > len(messages):
            logger.error('The passed index is greater than the number of messages')
            print('The passed index is greater than the number of messages')
            return None

        # Get the first row.
        messages[index].click()

        # Return it.
        return self._get_html_content(browser) if html else self._get_plain_content(browser)

    def get_email_with_subject(self, browser, subject, html=False, wait_time=WAIT_TIME):

        # Go to the correct tab.
        browser.go_to_tab('inbox')

        # Ensure we're at the inbox.
        browser.visit(self.url)

        # Refresh.
        self.refresh(browser, wait_time)

        # Get the mail list.
        if not browser.is_element_visible_by_css('.messages.container-fluid.ng-scope', wait_time):
            logger.error('Message list is not visible')
            return None

        # Check for messages.
        if not browser.is_element_visible_by_css('.msglist-message.row.ng-scope', wait_time):
            logger.error('No messages in the list')
            return None

        # Get the message divs.
        messages = browser.find_by_css('.msglist-message.row.ng-scope')

        # Search each one.
        for message in messages:

            # Check its subject.
            if message.find_by_xpath('//span[contains(text(),"{}")]'.format(subject)):
                message.click()

                # Return it.
                return self._get_html_content(browser) if html else self._get_plain_content(browser)

        return None

    def _get_html_content(self, browser, wait_time=WAIT_TIME):

        # Go to the correct tab.
        browser.go_to_tab('inbox')

        # Check for the message content.
        if not browser.is_element_visible_by_text('Source', wait_time):
            logger.error('Message did not load content')
            return None

        # Click the plain text tab.
        browser.click_link_by_text('Source')

        # Get the div.
        if not browser.is_element_visible_by_id('preview-source', wait_time):
            logger.error('Message did not load content its source content')
            return None

        # Return it.
        return browser.find_by_id('preview-source').first.text

    def _get_plain_content(self, browser, wait_time=WAIT_TIME):

        # Go to the correct tab.
        browser.go_to_tab('inbox')

        # Check for the message content.
        if not browser.is_element_visible_by_text('Plain text', wait_time):
            logger.error('Message did not load content')
            return None

        # Click the plain text tab.
        browser.click_link_by_text('Plain text')

        # Get the div.
        if not browser.is_element_visible_by_id('preview-plain', wait_time):
            logger.error('Message did not load content its plain text content')
            return None

        # Return it.
        return browser.find_by_id('preview-plain').first.text


class Data:
    """
    This class contains convenience methods for interrogating the state of the data
    in the application at any point during testing.
    """

    def __init__(self, url, email_address, project):

        # Keep the email.
        self.email_address = email_address
        self.project = project
        self.url = url

        # Get an instance of the FHIR client.
        self.fhir = FHIRServices(url)

    def get_patient_record(self):

        # Sleep
        time.sleep(3)

        return self.fhir.query_patient_record(self.email_address, flatten_return=True)

    def get_enrollment_status(self):

        # Sleep
        time.sleep(3)

        return self.fhir.query_enrollment_status(self.email_address)

    def delete_all(self):

        # Remove consents.
        try:
            self.fhir.remove_questionnaire(self.email_address, self.project)
        except Exception as e:
            logger.exception('[roles.Data.delete_all] Exception: {}'.format(e))

        try:
            self.fhir.remove_point_of_care_list(self.email_address)
        except Exception as e:
            logger.exception('[roles.Data.delete_all] Exception: {}'.format(e))

        try:
            self.fhir.remove_consent_response(self.email_address, 'quiz')
        except Exception as e:
            logger.exception('[roles.Data.delete_all] Exception: {}'.format(e))

        try:
            self.fhir.remove_consent_response(self.email_address, 'guardian-quiz')
        except Exception as e:
            logger.exception('[roles.Data.delete_all] Exception: {}'.format(e))

        try:
            self.fhir.remove_consent(self.email_address)
        except Exception as e:
            logger.exception('[roles.Data.delete_all] Exception: {}'.format(e))

        try:
            self.fhir.remove_enrollment_flag(self.email_address)
        except Exception as e:
            logger.exception('[roles.Data.delete_all] Exception: {}'.format(e))

        try:
            self.fhir.remove_patient(self.email_address)
        except Exception as e:
            logger.exception('[roles.Data.delete_all] Exception: {}'.format(e))


class URLs:

    @staticmethod
    def load(path, environment):

        # Load them
        with open(path, 'r') as stream:
            try:
                urls = yaml.load(stream)['urls']

                # Get the ones for the passed environment
                environment_urls = urls[environment]
                return environment_urls

            except Exception as e:
                logger.exception(e)
                return  None


class Accounts:

    @staticmethod
    def load(path):

        # Load them
        with open(path, 'r') as stream:
            try:
                accounts = yaml.load(stream)['accounts']

                return accounts

            except Exception as e:
                logger.exception(e)
                return  None


def go_to_registration(user, email):

    # Sign up.
    user.sign_up_to_p2m2()

    # Verify email.
    user.verify_email(email)


def go_to_consent(user, email):

    # Sign up.
    user.sign_up_to_p2m2()

    # Verify email.
    user.verify_email(email)

    # Register.
    user.register()


def go_to_twitter(user, email, admin):

    # Sign up.
    user.sign_up_to_p2m2()

    # Verify email.
    user.verify_email(email)

    # Register.
    user.register()

    # Fill out consent.
    user.consent()

    # Fill in points of care.
    user.points_of_care(['Massachusetts General Hospital',
                         'Beth Isreal Deaconess Medical Center',
                         'Brigham and Women\'s Hospital'])

    # Approve them.
    admin.approve_user(user.email_address, user.project)

    # Reload.
    user.browser.reload()

    # Do the questionnaire.
    user.questionnaire()

    # Do Twitter.
    user.twitter_handle()


def go_to_admin(environment):

    # Get the URLs
    urls = URLs.load('../urls.yml', environment)
    accounts = Accounts.load('../accounts.yml')

    # Create the admin
    admin = Administrator(urls, email_address=accounts['admin']['email'], password=accounts['admin']['password'])

    # Create the browser.
    browser = Browser('remote_chrome')

    # Log in
    admin.log_in_to_p2m2_admin(browser)

    return browser, admin

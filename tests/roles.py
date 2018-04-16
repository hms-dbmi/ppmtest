import time
import random
import string
import re
import yaml
import furl
from datetime import datetime


from browser import Browser
from ppm_fhir.fhir_services import FHIRServices

import logging
logger = logging.getLogger('ppm-test-suite')

# Set a default wait time in seconds
WAIT_TIME = 3


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

    def log_in_to_p2m2(self, browser, wait_time=WAIT_TIME):

        # Go to the correct tab.
        browser.go_to_tab('p2m2')

        # Check the URL.
        if browser.url != '{}{}'.format(self.urls['p2m2'], self.project):
            browser.visit('{}{}'.format(self.urls['p2m2'], self.project))

        if not browser.is_element_visible_by_partial_text('Sign in', wait_time):
            logger.error('"Sign in" button was not found')
            return False

        browser.find_by_text('Sign in').first.click()

        # Sign into Auth0
        time.sleep(2)
        if not browser.is_element_visible_by_name('email', wait_time):
            logger.error('E-Mail input field was not found')
            return False

        browser.fill('email', self.email_address)
        browser.fill('password', self.password)
        browser.find_by_css('.auth0-lock-submit').first.click()

        # Wait for the reload.
        if not browser.is_element_present_by_partial_text('Dashboard', wait_time):
            logger.error('Dashboard was not reached')
            return False

        return True

    def verify_email(self, browser, email, wait_time=WAIT_TIME):

        # Go to dashboard.
        self.go_to_dashboard(browser)

        # Check if already verified.
        if browser.is_element_present_by_partial_text('Your e-mail has been confirmed.', wait_time):
            logger.debug('This user has already verified their email')
            return True

        # Send the verification email.
        if not browser.make_element_visible_by_id('submit_verification_email', wait_time):
            logger.error('E-Mail confirmation button could not be found')
            return False

        browser.click_link_by_id('submit_verification_email')

        # Get the last email.
        message = email.get_email_with_subject(browser, 'People-Powered Medicine - E-Mail Verification')
        if not message:
            logger.error('No email was found, halting...')
            return False
        else:
            logger.debug('Found email:\n\n{}'.format(message))

        # Get the link.
        matches = re.search(r'(.*email_confirm_value.*)', message)
        if matches is not None:

            link = matches.group(1)

            # Go back to the dashboard.
            self.go_to_dashboard(browser, reload=True)

            # Wait for the reload.
            if not browser.is_element_present_by_partial_text('Dashboard', wait_time):
                logger.error('Dashboard was not reached')
                return False

            # Go there.
            browser.visit(link)

            # Wait for the reload.
            if not browser.is_element_present_by_partial_text('Your e-mail has been confirmed.', wait_time=5):
                logger.error('Dashboard does not show e-mail as having been confirmed')
                return False

        else:
            logger.error('The email confirmation link was not found in the email:\n\n{}'.format(email))
            return False

        return True

    def register(self, browser, wait_time=WAIT_TIME):

        # Go to the dashboard.
        self.go_to_dashboard(browser)

        # Check if already registered.
        if browser.is_element_present_by_partial_text('Your registration was filled out.'):
            logger.debug('This user has already registered')
            return True

        # Check for the form.
        if not browser.make_element_visible_by_id('panel-register', wait_time):
            logger.error('Registration form could not be found')
            return False

        # Fill out the fields.
        browser.fill_form({
            'firstname': self.first_name,
            'lastname': self.last_name,
            'street_address1': self.address,
            'street_address2': self.address_cont,
            'city': self.city,
            'state': self.state,
            'zip': self.zip,
            'phone': self.phone,
        })

        # Submit.
        if not browser.make_element_visible_by_partial_classname('btn btn-primary', wait_time):
            logger.error('Registration form submit button could not be found')
            return False

        # Continue.
        browser.find_by_css('.btn.btn-primary').first.click()

        # Check the results.
        if not browser.is_element_present_by_partial_text('Your registration was filled out.', wait_time):
            logger.error('Dashboard does not show registration as being filled out')
            return False

        return True

    def points_of_care(self, browser, points_of_care=[], wait_time=WAIT_TIME):

        # Go to the dashboard.
        self.go_to_dashboard(browser)

        if browser.is_element_present_by_partial_text('You have entered your points of care.', wait_time):
            logger.debug('This user has already entered their points of care')
            return True

        # Check for the points of care form.
        # TODO: Use a more specific selector for the POC form
        if not browser.make_element_visible_by_tag('form', wait_time):
            logger.error('Could not find the point of care form')
            return False

        # Get the form.
        form = browser.find_by_tag('form').first

        # Iterate through the passed points of care.
        for index, point_of_care in enumerate(points_of_care):

            # Get the first input field.
            div = form.find_by_id('sortable-form').last

            # Set the name of the input.
            point_of_care_input = 'form-{}-location'.format(index)

            # Check for the point of care input.
            if not browser.is_element_visible_by_name(point_of_care_input, wait_time):
                logger.error('Point of care input "{}" could not be found'.format(index))
                return False

            # Add a point of care.
            browser.fill(point_of_care_input, point_of_care)

            # Add another point of care form field if more points of care need entered.
            if index < len(points_of_care) - 1:
                div.find_by_tag('button')[1].click()

        # Check for the submit button.
        if not browser.make_element_visible_by_partial_classname('btn btn-primary', wait_time):
            logger.error('The Point of Care "Submit" button could not be found')
            return False

        # Continue.
        browser.find_by_css('.btn.btn-primary').first.click()

        # Check the results.
        if not browser.is_element_present_by_partial_text('You have entered your points of care.', wait_time):
            logger.error('Dashboard does not show that points of care have been submitted')
            return False

        return True

    def twitter_handle(self, browser, wait_time=WAIT_TIME):

        # Go to the dashboard.
        self.go_to_dashboard(browser)

        # Check if already surveyed.
        if browser.is_element_present_by_partial_text('Your Twitter handle has been', wait_time):
            logger.debug('This user has already entered their Twitter handle')
            return True

        # Check for the twitter handle input.
        if not browser.make_element_visible_by_name('twitter_handle', wait_time):
            logger.error('The Twitter handle input could not be found')
            return False

        # Use the email address, sans domain.
        browser.fill('twitter_handle', self.email_address.split('-')[2][:8])

        # Check for the submit button.
        if not browser.make_element_visible_by_partial_classname('btn btn-primary', wait_time):
            logger.error('The Twitter handle "Submit" button could not be found')
            return False

        # Continue.
        browser.find_by_css('.btn.btn-primary').first.click()

        # Check the results.
        if not browser.is_element_present_by_partial_text('Your Twitter handle has been', wait_time):
            logger.error('Dashboard does not show as Twitter handle as having been submitted')
            return False

        return True

    def facebook(self, browser, email_address, password, wait_time=WAIT_TIME):

        # Go to the dashboard.
        self.go_to_dashboard(browser)

        # Check if already connected.
        if browser.is_element_present_by_partial_text('Your Facebook has been', wait_time):
            logger.debug('This user has already connected their Facebook')
            return True

        # Check for the Facebook link.
        if not browser.make_element_visible_by_text('Click here to link your public Facebook data.', wait_time):
            logger.error('The Facebook link could not be found')
            return False

        # Follow the link
        browser.click_link_by_text('Click here to link your public Facebook data.')

        # Wait for the page to load
        if not browser.make_element_visible_by_text('Log into Facebook', wait_time):
            logger.error('The Facebook sign-in page could not load')
            return False

        # Continue.
        browser.fill_form({
            'email': email_address,
            'pass': password,
        })

        browser.find_by_id('loginbutton').first.click()

        # Wait for the permissions page to load
        # TODO: Implement this if using a fresh Facebook account, otherwise assume permissions already granted

        # Check the results.
        if not browser.is_element_present_by_partial_text('Your public Facebook data has been linked', wait_time):
            logger.error('Dashboard does not show as Facebook as having been connected')
            return False

        return True

    def get_confirmation_link(self, browser, email, wait_time=WAIT_TIME):

        # Check for an email for a user pending approval.
        message = email.get_email_with_subject(browser, 'People-Powered Medicine - E-Mail Verification', wait_time)

        # Get the link.
        matches = re.search(r'(.*email_confirm_value.*)', message)
        if matches:

            return matches.group(1)

        return None

    def get_approval_link(self, browser, email, wait_time=WAIT_TIME):

        # Check for an email for a user pending approval.
        message = email.get_email_with_subject(browser, 'People-Powered Medicine - Approved!', wait_time)

        # Get the link.
        matches = re.search(r'(.*dashboard/dashboard.*)', message)
        if matches:

            return matches.group(1)

        return None

    def is_pending_approval(self, browser, wait_time=WAIT_TIME):

        # Go to the dashboard.
        self.go_to_dashboard(browser)

        # Check the results.
        if not browser.is_element_present_by_partial_text('Your consent is currently pending.', wait_time):
            logger.debug('Dashboard does not show the current user is pending approval')
            return False

        return True

    def is_email_confirmed(self, browser, wait_time=WAIT_TIME):

        # Go to the dashboard.
        self.go_to_dashboard(browser)

        # Check if already verified.
        if not browser.is_element_present_by_partial_text('Your e-mail has been confirmed.', wait_time):
            logger.debug('Dashboard does not show the current user as having confirmed their email')
            return False

        return True

    def is_registered(self, browser, wait_time=WAIT_TIME):

        # Go to the dashboard.
        self.go_to_dashboard(browser)

        # Check if already verified.
        if not browser.is_element_present_by_partial_text('Your registration was filled out.', wait_time):
            logger.debug('Dashboard does not show the current user as having registered')
            return False

        return True

    def is_consented(self, browser, wait_time=WAIT_TIME):

        # Go to the dashboard.
        self.go_to_dashboard(browser)

        # Check if already verified.
        if not browser.is_element_present_by_partial_text('Click here to download your signed consent form', wait_time):
            logger.debug('Dashboard does not show the current user as having consented')
            return False

        return True

    def has_entered_points_of_care(self, browser, wait_time=WAIT_TIME):

        # Go to the dashboard.
        self.go_to_dashboard(browser)

        # Check if already verified.
        if not browser.is_element_present_by_partial_text('You have entered your points of care.', wait_time):
            logger.debug('Dashboard does not show the current user as having entered their points of care')
            return False

        return True

    def has_surveyed(self, browser, wait_time=WAIT_TIME):

        # Go to the dashboard.
        self.go_to_dashboard(browser)

        # Check if already verified.
        if not browser.is_element_present_by_partial_text('You have filled out this survey.', wait_time):
            logger.debug('Dashboard does not show the current user as having filled out the survey')
            return False

        return True

    def has_entered_twitter_handle(self, browser, wait_time=WAIT_TIME):

        # Go to the dashboard.
        self.go_to_dashboard(browser)

        # Check if already verified.
        if not browser.is_element_present_by_partial_text('Your Twitter handle has been', wait_time):
            logger.debug('Dashboard does not show the current user as having submitted their Twitter handle')
            return False

        return True

    def has_completed(self, browser, task, completion_text, wait_time=WAIT_TIME):

        # Go to the dashboard.
        self.go_to_dashboard(browser)

        # Check if already verified.
        if not browser.is_element_present_by_partial_text(completion_text, wait_time):
            logger.debug('Task {} has not been completed'.format(task))
            return False

        return True

    def go_to_dashboard(self, browser, reload=False):

        # Go to the correct tab.
        browser.go_to_tab('p2m2')

        # Check if already there.
        if not 'dashboard/dashboard' in browser.url:
            browser.visit(self.urls['dashboard'])

        elif reload:
            browser.reload()

    def go_to_profile(self, browser):

        # Go to the correct tab.
        browser.go_to_tab('p2m2')

        # Check if already there.
        if not 'dashboard/profile' in browser.url:
            browser.visit(self.urls['profile'])


class Administrator(_User):
    """
    This class provides convenience methods for administrator actions
    """

    def __init__(self, urls, email_address, password='PPMIsGreat!', project='autism', independent=True,
                 first_name='John', last_name='Smith', address='10 Main St.', address_cont='#199',
                 city='Boston', state='MA', zip='02445', phone='(555) 555-5555',
                 twitter='jsmith', date_of_birth='01/01/1980'):

        # Call super with 'autism' as the project.
        _User.__init__(self, urls, email_address, password, project, independent, first_name,
                       last_name, address, address_cont, city, state, zip, phone, twitter,
                       date_of_birth)

    def log_in_to_p2m2_admin(self, browser, wait_time=WAIT_TIME):

        # Go to the correct tab.
        browser.go_to_tab('admin')

        # Check the URL.
        browser.visit('{}'.format(self.urls['p2m2-admin']))

        # Sign into Auth0
        time.sleep(2)
        if not browser.is_element_visible_by_name('email', wait_time):
            logger.error('E-Mail input field was not found')
            return False

        browser.fill('email', self.email_address)
        browser.fill('password', self.password)
        browser.find_by_css('.auth0-lock-submit').first.click()

        # Wait for the reload.
        if not browser.is_element_present_by_partial_text('Participants', wait_time=20):
            logger.error('Participants view was not reached')
            return False

        return True

    def approve_user(self, browser, fhir_id, wait_time=WAIT_TIME):

        # Go to their detail view
        self.go_to_pending_participants(browser, fhir_id)

        # Check for the approve button
        if not browser.is_element_present_by_id('enrollment-label', wait_time=WAIT_TIME):
            logger.error('Participant view was not reached')
            return False

        # Ensure the status is 'Proposed'
        if browser.find_by_id('enrollment-label').first.text != 'Proposed':
            logger.error('Participant\'s status is not "proposed": {}'.format(
                browser.find_by_id('enrollment-label').first.text))
            return False

        # Check for the approve button
        if not browser.is_element_present_by_partial_text('Accept Participant', wait_time=WAIT_TIME):
            logger.error('Participant acceptance button was not present')
            return False

        # Click it.
        browser.find_by_partial_text('Accept Participant').first.click()

        # Let it refresh
        time.sleep(2)

        # Ensure their status is 'Accepted'
        if browser.find_by_id('enrollment-label').first.text != 'Accepted':
            logger.error('Participant\'s status is not "accepted": {}'.format(
                browser.find_by_id('enrollment-label').first.text))
            return False

        return True

    def delete_user(self, browser, fhir_id, wait_time=WAIT_TIME):

        # Go to their detail view
        self.go_to_pending_participants(browser, fhir_id)

        # Check for the approve button
        if not browser.is_element_present_by_id('enrollment-label', wait_time=WAIT_TIME):
            logger.error('Participant view was not reached')
            return False

        # Check for the delete button
        if not browser.make_element_visible_by_id('participant-delete-button', wait_time=WAIT_TIME):
            logger.error('Participant delete button was not present')
            return False

        # Click it.
        browser.find_by_id('participant-delete-button').first.click()

        # Confirm
        if not browser.is_element_visible_by_css('.bootstrap-dialog-footer', wait_time=WAIT_TIME):
            logger.error('Participant delete confirmation button was not present')
            return False

        # Click it.
        browser.find_by_css('.bootstrap-dialog-footer').first.find_by_css('.btn.btn-danger').first.click()

        # Wait for the redirect
        time.sleep(3)

        return True

    def reload_participants(self, browser):

        # Go to the pending participants dashboard.
        self.go_to_pending_participants(browser)

        if not browser.is_element_present_by_id('participants-table', WAIT_TIME):
            logger.error('Participants view was not reached')
            return False

        # Click the reload button
        browser.click_link_by_id('participants-reload')

        # Give some time to reload
        time.sleep(2)

    def check_participant(self, browser, fhir_id, email_address, project, status, wait_time=WAIT_TIME):

        # Go to the pending participants dashboard.
        self.go_to_pending_participants(browser)

        # Reload.
        browser.reload()

        if not browser.is_element_present_by_id('participants-table', WAIT_TIME):
            logger.error('Participants view was not reached')
            return False

        # Let the table load
        time.sleep(WAIT_TIME)

        # Select the project panel.
        participants_table = browser.find_by_id('participants-table').first

        # Count the number of users.
        participants = participants_table.find_by_tag('tr')[1:]

        # Find each user.
        for index, row in enumerate(participants):

            # Check the email address.
            if email_address in row.find_by_tag('td')[2].text:

                # Expand the panel.
                row.find_by_tag('button').first.click()

                # Get the acceptance button and click it.
                row.find_by_text('Approve for Participation').first.click()

                return True

        logger.error('User with email "{}" could not be found'.format(email_address))
        return False

    def get_signup_notification_link(self, browser, email, wait_time=WAIT_TIME):

        # Check for an email for a user pending approval.
        message = email.get_email_with_subject(browser, 'People Powered Medicine - New User Signup', wait_time)

        # Get the link.
        matches = re.search(r'(.*/participants/.*)', message)
        if matches:

            return matches.group(1)

        return None

    def go_to_pending_participants(self, browser, participant=None):

        # Go to the correct tab.
        browser.go_to_tab('admin')

        # Check for a participant
        if participant:
            participant_url = furl.furl(self.urls['p2m2-admin'])
            participant_url.path.add(participant)

            browser.visit(participant_url.url)
        else:
            browser.visit(self.urls['p2m2-admin'])


class AutismUser(_User):

    def __init__(self, urls, email_address=None, password='PPMIsGreat!', independent=True,
                 first_name='John', last_name='Smith', address='10 Main St.', address_cont='#199',
                 city='Boston', state='MA', zip='02445', phone='(555) 555-5555',
                 twitter='jsmith', date_of_birth='01/01/1980'):

        # Call super with 'autism' as the project.
        _User.__init__(self, urls, email_address, password, 'autism', independent, first_name,
                       last_name, address, address_cont, city, state, zip, phone, twitter,
                       date_of_birth)

    def consent(self, browser, wait_time=WAIT_TIME):

        # Go to the dashboard.
        self.go_to_dashboard(browser)

        # Check if already consented.
        if browser.is_element_present_by_partial_text('Click here to download your signed consent form', wait_time):
            logger.debug('This user has already consented')
            return True

        # Go to the consent.
        if not browser.make_element_visible_by_partial_text('Click here to read and enter your consent.', wait_time):
            logger.error('Link to fill out consent could not be found')
            return False

        browser.click_link_by_text('Click here to read and enter your consent.')

        # Select the consent type and continue.
        if not browser.make_element_visible_by_name('consent-type', wait_time):
            logger.error('Consent type form could not be found')
            return False

        browser.choose('consent-type', 'individual' if self.independent else 'guardian')

        # Select the consent type and continue.
        if not browser.make_element_visible_by_text('Continue', wait_time):
            logger.error('Consent "Continue" button could not be found')
            return False

        browser.find_by_text('Continue').first.click()

        # Find the quiz.
        if not browser.make_element_visible_by_tag('form', wait_time):
            logger.error('Consent quiz form could not be found')
            return False

        # Different responses for consent type.
        if self.independent:
            browser.choose('question-1',
                                     'You agreed that you could be contacted in the future.')
            browser.choose('question-2',
                                     'This study will post your electronic health data on Twitter.')
            browser.choose('question-3',
                                     'You will get a copy of all your genetic data obtained from sequencing your DNA.')
            browser.choose('question-4',
                                     'Data from this study will go into your medical record.')
        else:
            browser.choose('question-1',
                                     'You agreed that you could be contacted in the future.')
            browser.choose('question-2',
                                     "This study will store your child's social web data (e.g., Facebook, Twitter) "
                                     "with your permission, along with your child's health record data.")
            browser.choose('question-3',
                                     "You will get a copy of all your child's genetic data obtained from sequencing "
                                     "your child's DNA.")
            browser.choose('question-4',
                                     'You and your child can withdraw from the study whenever you wish.')

        # Check for the submit button.
        if not browser.make_element_visible_by_text('Submit', wait_time):
            logger.error('The "Submit" button could not be found')
            return False

        # Move along.
        browser.find_by_text('Submit').first.click()

        # Check for the right context.
        if not browser.is_element_visible_by_partial_text('Signature', wait_time):
            logger.error('Signature form header could not be found')
            return False

        # Fill out the signature.
        if not browser.make_element_visible_by_tag('form', wait_time):
            logger.error('Signature form could not be found')
            return False

        # Get the form.
        form = browser.find_by_tag('form').first

        # Get the checkboxes and opt out of everything.
        checkboxes = form.find_by_xpath('//../input[@type="checkbox"]')
        for checkbox in checkboxes[-1:]:
            checkbox.click()

        # Ensure the field has loaded.
        if not browser.make_element_visible_by_name('name-of-participant', wait_time):
            logger.error('Consent signature form could not be found')
            return False

        if self.independent:

            # Fill out the signature.
            browser.fill_form({
                'name-of-participant': '{} {}'.format(self.first_name, self.last_name),
                'signature-of-participant': '{} {}'.format(self.first_name, self.last_name),
            })

        else:
            # Fill out additional fields on guardian consent.
            browser.fill_form({
                'name-of-participant': '{} {}'.format(self.first_name, self.last_name),
                'name-of-guardian': '{} {} Sr.'.format(self.first_name, self.last_name),
                'signature-of-guardian': '{} {} Sr.'.format(self.first_name, self.last_name),
            })

            # Make the guardian selection.
            browser.choose('explained', 'no')

            # Fill out the sub form.
            browser.fill_form({
                'explained-reason': 'Participant is too young to understand',
                'explained-signature': '{} {}'.format(self.first_name, self.last_name),
            })

            # Continue to the assent.
            if not browser.make_element_visible_by_text('Continue', wait_time):
                logger.error('Consent "Continue" button could not be found')
                return False

            # Continue.
            form.find_by_text('Continue').first.click()

            time.sleep(2)

            # Ensure the field has loaded.
            if not browser.make_element_visible_by_tag('form', wait_time):
                logger.error('Consent signature form could not be found')
                return False

            # Get the form.
            form = browser.find_by_tag('form').first

            # Get the checkboxes and opt out of everything.
            checkboxes = form.find_by_xpath('//../input[@type="checkbox"]')
            for checkbox in checkboxes:
                checkbox.click()

            # Fill out fields on assent form.
            browser.fill_form({
                'signature-of-participant': '{} {}'.format(self.first_name, self.last_name),
            })

        # Check for the submit button.
        if not browser.make_element_visible_by_text('Continue', wait_time):
            logger.error('The "Continue" button could not be found')
            return False

        # Continue.
        form.find_by_text('Continue').first.click()

        # Check the results.
        if not browser.is_element_present_by_partial_text('Click here to download your signed consent form', wait_time):
            logger.error('Dashboard does not show as consent having been submitted')
            return False

        return True

    def questionnaire(self, browser, wait_time=WAIT_TIME):

        # Go to the dashboard.
        self.go_to_dashboard(browser)

        # Check if already surveyed.
        if browser.is_element_present_by_partial_text('You have filled out this survey.', wait_time):
            logger.debug('This user has already filled out the survey')
            return True

        # Go to the consent.
        if not browser.make_element_visible_by_partial_text('Click here to fill out the survey.', wait_time):
            logger.error('The link to fill out the survey could not be found')
            return False

        browser.click_link_by_text('Click here to fill out the survey.')

        # Make selections.
        if not browser.is_element_visible_by_name('question-1', wait_time):
            logger.error('Survey form could not be found')
            return False

        browser.choose('question-1', 'I have autism')

        # Get the form.
        form = browser.find_by_tag('form').first

        # Get the checkboxes and select some people
        q2_checkboxes = form.find_by_xpath('//../input[@type="checkbox" and @name="question-2"]')
        for checkbox in q2_checkboxes:
            checkbox.click()

        # Select some disorders.
        q3_checkboxes = form.find_by_xpath('//../input[@type="checkbox" and @name="question-3"]')
        for index, checkbox in enumerate(q3_checkboxes):
            checkbox.click()

            # Get the text input.
            if browser.is_element_visible_by_xpath(
                    '//../input[@type="text" and @name="question-3-{}"]'.format(index + 1), wait_time):
                form.find_by_xpath('//../input[@name="question-3-{}"]'.format(index + 1)).first.fill('Family Member')

        # Select some medications.
        q3_checkboxes = form.find_by_xpath('//../input[@type="checkbox" and @name="question-4"]')
        for index, checkbox in enumerate(q3_checkboxes):
            checkbox.click()

            # Get the text input.
            if browser.is_element_visible_by_xpath(
                    '//../input[@type="text" and @name="question-4-{}"]'.format(index + 1),
                    wait_time):
                form.find_by_xpath('//../input[@name="question-4-{}"]'.format(index + 1)).first.fill(
                    'Medication'.format(index))

        # Check for the submit button.
        if not browser.make_element_visible_by_text('Submit', wait_time):
            logger.error('The "Submit" button could not be found')
            return False

        # Submit the questionnaire.
        browser.find_by_text('Submit').first.click()

        # Check the results.
        if not browser.is_element_present_by_partial_text('You have filled out this survey.', wait_time):
            logger.error('Dashboard does not show as survey having been submitted')
            return False

        return True


class NEERUser(_User):

    def __init__(self, urls, email_address=None, password='PPMIsGreat!', independent=True,
                 first_name='John', last_name='Smith', address='10 Main St.', address_cont='#199',
                 city='Boston', state='MA', zip='02445', phone='(555) 555-5555',
                 twitter='jsmith', date_of_birth='01/01/1980'):

        # Call super with 'neer' as the project.
        _User.__init__(self, urls, email_address, password, 'neer', independent, first_name,
                       last_name, address, address_cont, city, state, zip, phone, twitter,
                       date_of_birth)

    def consent(self, browser, wait_time=WAIT_TIME):

        # Go to the dashboard.
        self.go_to_dashboard(browser)

        # Check if already consented.
        if browser.is_element_present_by_partial_text('Click here to download your signed consent form', wait_time):
            logger.debug('This user has already consented')
            return True

        # Go to the consent.
        if not browser.make_element_visible_by_partial_text('Click here to read and enter your consent.', wait_time):
            logger.error('Link to fill out consent could not be found')
            return False

        browser.click_link_by_text('Click here to read and enter your consent.')

        # Continue.
        if not browser.make_element_visible_by_partial_text('Continue', wait_time):
            logger.error('Continue button after first consent page could not be found')
            return False

        browser.find_by_text('Continue').first.click()

        # Fill out the signature.
        if not browser.is_element_visible_by_partial_text('Signature', wait_time):
            logger.error('Signature form header could not be found')
            return False

        if not browser.make_element_visible_by_tag('form', wait_time):
            logger.error('Signature form could not be found')
            return False

        # Get the form.
        form = browser.find_by_tag('form').first

        # Get the checkboxes and opt out of everything.
        checkboxes = form.find_by_xpath('//../input[@type="checkbox"]')
        for checkbox in checkboxes:
            checkbox.click()

        # Fill out the signature.
        browser.fill_form({
            'name-of-participant': '{} {}'.format(self.first_name, self.last_name),
            'signature-of-participant': '{} {}'.format(self.first_name, self.last_name)
        })

        # Check for the continue button.
        if not browser.make_element_visible_by_text('Continue', wait_time):
            logger.error('The "Continue" button could not be found')
            return False

        # Continue.
        form.find_by_text('Continue').first.click()

        # Check the results.
        if not browser.is_element_present_by_partial_text('Click here to download your signed consent form', wait_time):
            logger.error('Dashboard does not show as consent having been submitted')
            return False

        return True

    def questionnaire(self, browser, wait_time=WAIT_TIME):

        # Go to the dashboard.
        self.go_to_dashboard(browser)

        # Check if already surveyed.
        if browser.is_element_present_by_partial_text('You have filled out this survey.', wait_time):
            logger.debug('This user has already filled out the survey')
            return True

        # Go to the consent.
        if not browser.make_element_visible_by_partial_text('Click here to fill out the survey.', wait_time):
            logger.error('The link to fill out the survey could not be found')
            return False

        browser.click_link_by_text('Click here to fill out the survey.')

        # Make selections.
        if not browser.is_element_visible_by_name('question-5', wait_time):
            logger.error('Survey form could not be found')
            return False

        # Fill out name
        browser.fill_form({
            'question-5': self.date_of_birth,
        })

        # Make some selections.
        browser.choose('question-6', '0')
        browser.choose('question-7', '0')
        browser.choose('question-8', 'Male')
        browser.choose('question-9', '1')

        # Fill in the fields.
        browser.fill_form({
            'question-10': 'Father, Grandmother, Great Aunt',
            'question-11': 'Breast Cancer, Lymphoma',
            'question-12': 'Lymphoma',
            'question-13': 'Massachusetts General Hospital',
            'question-14': '01/01/2017',
            'question-15': 'Massachusetts General Hospital',
            'question-16': 'N/A',
            'question-17': 'N/A',
            'question-18': 'Agent #1',
            'question-19': '06/01/2017',
        })

        # Set as still in treatment.
        browser.choose('question-20', '1')

        # Fill out more forms.
        browser.fill_form({
            'question-21': 'N/A',
            'question-22': 'For some reasons...',
        })

        # Select genome analysis
        browser.choose('question-23', '1')

        # Fill out the form.
        browser.fill_form({
            'question-24': 'Dr. Susan Smith',
            'question-25': 'Dr. Gregory Smith',
        })

        # Check for the submit button.
        if not browser.make_element_visible_by_text('Submit', wait_time):
            logger.error('The form "Submit" button could not be found')
            return False

        # Submit the questionnaire.
        browser.find_by_text('Submit').first.click()

        # Check the results.
        if not browser.is_element_present_by_partial_text('You have filled out this survey.', wait_time):
            logger.error('Dashboard does not show as survey having been submitted')
            return False

        return True


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

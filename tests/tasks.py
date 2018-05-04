import os

from browser import Browser
from roles import *


def admin(environment='docker'):

    # Create browsers.
    admin_browser = Browser('firefox')

    # Get the path
    path = os.path.dirname(__file__)

    # Get the URLs
    urls = URLs.load(os.path.join(path, 'urls.yml'), environment)
    accounts = Accounts.load(os.path.join(path, 'accounts.yml'))[environment]

    # Get an admin
    admin = Administrator(urls, email_address='bryan_larson@hms.harvard.edu', password='ppmisgreat')
    admin.log_in_to_p2m2_admin(admin_browser)

    return admin_browser, admin


def user(environment='docker'):

    # Create browsers.
    user_browser = Browser('chrome')

    # Get the path
    path = os.path.dirname(__file__)

    # Get the URLs
    urls = URLs.load(os.path.join(path, 'urls.yml'), environment)
    accounts = Accounts.load(os.path.join(path, 'accounts.yml'))[environment]

    # Get a user
    user = AutismUser(urls, email_address='usersaw@ppm.com', password='ppmisgreat', independent=False)
    user.sign_up_to_p2m2(user_browser)

    email = Email(urls['inbox'])
    user.verify_email(user_browser, email)

    user.register(user_browser)

    user.consent(user_browser)

    return user_browser, user, email


def all(environment='docker'):
    # Create browsers.
    user_browser = Browser('chrome')
    admin_browser = Browser('firefox')

    # Get the path
    path = os.path.dirname(__file__)

    # Get the URLs
    urls = URLs.load(os.path.join(path, 'urls.yml'), environment)
    accounts = Accounts.load(os.path.join(path, 'accounts.yml'))[environment]

    # Get a user
    user = NEERUser(urls, email_address='user@ppm.com', password='ppmisgreat')
    user.log_in_to_p2m2(user_browser)

    # Get an admin
    admin = Administrator(urls, email_address='bryan_larson@hms.harvard.edu', password='ppmisgreat')
    admin.log_in_to_p2m2_admin(admin_browser)

    email = Email(urls['inbox'])
    user.verify_email(user_browser, email)

    return user_browser, user, admin_browser, admin, email


def poc(environment='docker'):

    # Get the path
    path = os.path.dirname(__file__)

    # Get the URLs
    urls = URLs.load(os.path.join(path, 'urls.yml'), environment)
    accounts = Accounts.load(os.path.join(path, 'accounts.yml'))[environment]
    user_account = accounts['neer']
    admin_account = accounts['admin']

    # Create browsers.
    user_browser = Browser('remote_chrome', url=urls['selenium'])

    # Create an email inbox.
    email = Email(url=urls['inbox'])

    # Get a user
    user = NEERUser(urls, user_account['email'], user_account['password'])
    user.log_in_to_p2m2(user_browser)

    # Verify email
    user.verify_email(user_browser, email)

    # Register
    user.register(user_browser)

    # Fill out consent.
    user.consent(user_browser)

    # Do the questionnaire.
    user.questionnaire(user_browser)

    # Check for the user in the DB.
    record = user.data.get_patient_record()

    # Get their ID
    fhir_id = record['fhir_id']

    # Get an admin
    admin_browser = Browser('remote_firefox', url=urls['selenium'])
    admin = Administrator(urls, admin_account['email'], admin_account['password'])
    admin.log_in_to_p2m2_admin(admin_browser)

    # Approve them.
    admin.approve_user(admin_browser, fhir_id)

    # Pause
    time.sleep(3)

    # Close all tabs
    admin_browser.close_tabs()
    admin_browser.quit()
    del admin_browser

    # Reload.
    user.go_to_dashboard(user_browser)
    user_browser.reload()

    time.sleep(3)

    # Do the questionnaire.
    user.points_of_care(user_browser, ['one', 'two', 'three'])

    return user_browser, user
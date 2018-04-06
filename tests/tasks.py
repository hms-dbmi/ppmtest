import os

from browser import Browser
from roles import *


def admin(environment='ppm'):

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


def user(environment='ppm'):

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


def all(environment='ppm'):
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
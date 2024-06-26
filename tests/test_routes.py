"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app
from service import talisman

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"

HTTPS_ENVIRON = {'wsgi.url_scheme': 'https'}


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)
        talisman.force_https = False

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...

    def test_read_an_account(self):
        """It should Read an Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_account = response.get_json()

        response = self.client.get(BASE_URL + "/" + str(new_account["id"]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_account_not_found(self):
        """It should not Read an Account"""
        response = self.client.get(BASE_URL + "/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_an_account(self):
        """It should Update an Account"""
        accounts = self._create_accounts(1)
        account = accounts[0]
        account.address = "New address boulevard, 666"
        response = self.client.put(BASE_URL + "/" + str(account.id), json=account.serialize())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        retrieved_account = response.get_json()
        self.assertEqual(retrieved_account["address"], account.address)

    def test_account_not_found_on_update(self):
        """It should not Update an Account"""
        accounts = self._create_accounts(1)
        account = accounts[0]
        account.address = "New address boulevard, 666"
        response = self.client.put(BASE_URL + "/0", json=account.serialize())
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_an_account(self):
        """It should Delete an Account"""
        accounts = self._create_accounts(2)
        account_to_delete = accounts[0]
        account_to_preserve = accounts[1]
        response = self.client.delete(BASE_URL + "/" + str(account_to_delete.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(BASE_URL + "/" + str(account_to_delete.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.get(BASE_URL + "/" + str(account_to_preserve.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_accounts(self):
        """It should List all the Accounts"""
        num_of_accounts = 3
        accounts = self._create_accounts(num_of_accounts)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(accounts), num_of_accounts)

    def test_method_not_supported(self):
        """It should return HTTP_405"""
        response = self.client.post(BASE_URL + "/0")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_security_headers(self):
        """It should respond with security headers"""
        response = self.client.get("/", None, environ_overrides=HTTPS_ENVIRON)
        x_frame_options = response.headers.get("X-Frame-Options", None)
        self.assertEqual(x_frame_options, "SAMEORIGIN")
        x_content_type_options = response.headers.get("X-Content-Type-Options", None)
        self.assertEqual(x_content_type_options, "nosniff")
        content_security_policy = response.headers.get("Content-Security-Policy", None)
        self.assertEqual(content_security_policy, "default-src 'self'; object-src 'none'")
        referrer_policy = response.headers.get("Referrer-Policy", None)
        self.assertEqual(referrer_policy, "strict-origin-when-cross-origin")

    def test_cors_headers(self):
        """It should respond with CORS headers"""
        response = self.client.get("/", None, environ_overrides=HTTPS_ENVIRON)
        access_control_allow_origin = response.headers.get("Access-Control-Allow-Origin", None)
        self.assertEquals(access_control_allow_origin, "*")

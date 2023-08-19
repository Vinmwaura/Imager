import os
import re
import time

import unittest

from bcrypt import gensalt, hashpw

from apps import create_app, db

import apps.auth as auth
import apps.api as api


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.app = create_app("config.TestingConfig")
        self.appctx = self.app.app_context()
        self.appctx.push()

        self.client = self.app.test_client()

        # Hack to remove any tables if any are present in Test Database.
        db.drop_all()

        # Creates a temporary test database.
        db.create_all()

        # Test User account configurations.
        self.created_user_username = "john_doe"
        self.created_user_firstname = "John"
        self.created_user_lastname = "Doe"
        self.created_user_email = "jdoe@email.com"
        self.created_user_pwd = "M'dNzF9[$PjS>}a*"

        # Explicitly create an activated account.
        with self.app.app_context():
            # Role Model.
            user_role = auth.models.Role(name="GENERAL")
            db.session.add(user_role)
            db.session.commit()

            # Permission Model.
            for permission in auth.auth.GENERAL_USER_PERMISSIONS:
                role_permission = auth.models.Permissions(
                    role_id=user_role.id,
                    permission=permission.value)

                db.session.add(role_permission)
            db.session.commit()

            # User Model.
            self.salt = gensalt(16)
            hashed_pwd = hashpw(
                self.created_user_pwd.encode("utf-8"),
                self.salt)
            user_account = auth.models.User(
                username=self.created_user_username,
                first_name=self.created_user_firstname,
                last_name=self.created_user_lastname,
                email=self.created_user_email,
                password_hash=hashed_pwd.decode("utf-8"),
                email_confirmed=True,
                user_role=user_role.id)
            db.session.add(user_account)
            db.session.commit()

    def tearDown(self):
        db.drop_all()

        self.appctx.pop()
        self.app = None
        self.appctx = None

    def test_load_api_documentation_page(self):
        response = self.client.get("/api/v1/")
        self.assertEqual(response.status_code, 200)
    
    def test_load_create_client_page(self):
        with self.app.app_context():
            self.client.post(
                "/auth/login",
                data={
                    "username_email": self.created_user_username,
                    "password": self.created_user_pwd,
                    "next": ""},
                follow_redirects=True)

            response = self.client.get(
                "/api/v1/create_client",
                follow_redirects=True)
            self.assertEqual(response.status_code, 200)

    def test_create_client(self):
        with self.app.app_context():
            self.client.post(
                "/auth/login",
                data={
                    "username_email": self.created_user_username,
                    "password": self.created_user_pwd,
                    "next": ""},
                follow_redirects=True)

            response = self.client.post(
                "/api/v1/create_client",
                data={
                    "client_name": "Test Client",
                    "redirect_uris": "",
                    "token_endpoint_auth_method": "client_secret_basic"
                }, follow_redirects=True)

            self.assertEqual(response.status_code, 200)
            self.assertTrue(re.search("Client Info", response.get_data(as_text=True)))

if __name__ == "__main__":
    unittest.main()

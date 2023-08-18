import os
import unittest

import re
from bcrypt import gensalt, hashpw, checkpw
from itsdangerous.url_safe import URLSafeTimedSerializer

import apps.api as api
import apps.auth as auth

from apps import create_app, db


class TestAuth(unittest.TestCase):
    def setUp(self):
        self.app = create_app("config.TestingConfig")
        self.appctx = self.app.app_context()
        self.appctx.push()

        self.client = self.app.test_client()
        
        # Valid User configurations for testing.
        self.valid_test_username = "testuser"
        self.valid_test_firstname = "test"
        self.valid_test_lastname = "user"
        self.valid_test_email = "test@testemail.com"
        self.valid_test_pwd = "*('y3nW;"

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
        self.created_user_role = 1

        # Explicitly create an activated account for testing.
        with self.app.app_context():
            user_role = auth.models.Role(name="GENERAL")
            db.session.add(user_role)
            db.session.commit()
            for permission in auth.auth.GENERAL_USER_PERMISSIONS:
                role_permission = auth.models.Permissions(
                    role_id=user_role.id,
                    permission=permission.value)

                db.session.add(role_permission)
            db.session.commit()

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

    def test_token_generation(self):
        email_activation_token = auth.controllers.generate_token(
            self.created_user_email,
            self.salt)

        self.assertIsNotNone(email_activation_token)
        self.assertRegex(
            email_activation_token,
            r"\w+.\w.\w",
            msg=None)
    
    def test_validate_token(self):
        with self.app.app_context():
            # Generates token.
            secret_key = os.environ.get("SECRET_KEY")
            timed_serializer = URLSafeTimedSerializer(secret_key)
            email_activation_token = timed_serializer.dumps(
                self.created_user_email,
                salt=self.salt)

            # Validates Token.
            user, error_status = auth.controllers.validate_token(
                email_activation_token,
                self.salt,
                auth.utils.REGISTRATION_TOKEN_MAX_AGE)
        self.assertIsNotNone(user)
        self.assertIsNone(error_status)
    
    def test_confirm_email(self):
        # Manually create deactivated user account.
        with self.app.app_context():
            role = auth.models.Role().query.filter_by(
                name="GENERAL").one_or_none()

            hashed_pwd = hashpw(
                self.valid_test_pwd.encode("utf-8"),
                self.salt)
            user_account = auth.models.User(
                username=self.valid_test_username,
                first_name=self.valid_test_firstname,
                last_name=self.valid_test_lastname,
                email=self.valid_test_email,
                password_hash=hashed_pwd.decode("utf-8"),
                user_role=role.id)

            status, error = auth.controllers.confirm_email(user_account)

            self.assertTrue(status)
            self.assertIsNone(error)
            self.assertTrue(user_account.email_confirmed)

    def test_change_username(self):
        # Manually create deactivated user account.
        with self.app.app_context():
            role = auth.models.Role().query.filter_by(
                name="GENERAL").one_or_none()

            hashed_pwd = hashpw(
                self.valid_test_pwd.encode("utf-8"),
                self.salt)
            user_account = auth.models.User(
                username=self.valid_test_username,
                first_name=self.valid_test_firstname,
                last_name=self.valid_test_lastname,
                email=self.valid_test_email,
                password_hash=hashed_pwd.decode("utf-8"),
                email_confirmed=True,
                active=True,
                user_role=role.id)

            new_username = "new_user_name"
            status = auth.controllers.change_username(
                user_account,
                new_username)
            self.assertTrue(status)
            self.assertEqual(user_account.username, new_username)
    
    def test_change_firstname(self):
        # Manually create deactivated user account.
        with self.app.app_context():
            role = auth.models.Role().query.filter_by(
                name="GENERAL").one_or_none()

            hashed_pwd = hashpw(
                self.valid_test_pwd.encode("utf-8"),
                self.salt)
            user_account = auth.models.User(
                username=self.valid_test_username,
                first_name=self.valid_test_firstname,
                last_name=self.valid_test_lastname,
                email=self.valid_test_email,
                password_hash=hashed_pwd.decode("utf-8"),
                email_confirmed=True,
                active=True,
                user_role=role.id)

            new_firstname = "new_first_name"
            status = auth.controllers.change_firstname(
                user_account,
                new_firstname)
            self.assertTrue(status)
            self.assertEqual(user_account.first_name, new_firstname)

    def test_change_lasttname(self):
        # Manually create deactivated user account.
        with self.app.app_context():
            role = auth.models.Role().query.filter_by(
                name="GENERAL").one_or_none()

            hashed_pwd = hashpw(
                self.valid_test_pwd.encode("utf-8"),
                self.salt)
            user_account = auth.models.User(
                username=self.valid_test_username,
                first_name=self.valid_test_firstname,
                last_name=self.valid_test_lastname,
                email=self.valid_test_email,
                password_hash=hashed_pwd.decode("utf-8"),
                email_confirmed=True,
                active=True,
                user_role=role.id)

            new_lastname = "new_last_name"
            status = auth.controllers.change_lastname(
                user_account,
                new_lastname)
            self.assertTrue(status)
            self.assertEqual(user_account.last_name, new_lastname)
    
    def test_change_user_password(self):
        # Manually create deactivated user account.
        with self.app.app_context():
            role = auth.models.Role().query.filter_by(
                name="GENERAL").one_or_none()

            hashed_pwd = hashpw(
                self.valid_test_pwd.encode("utf-8"),
                self.salt)
            user_account = auth.models.User(
                username=self.valid_test_username,
                first_name=self.valid_test_firstname,
                last_name=self.valid_test_lastname,
                email=self.valid_test_email,
                password_hash=hashed_pwd.decode("utf-8"),
                email_confirmed=True,
                active=True,
                user_role=role.id)

            new_password = "hSC5e3c#r{u{'3qd"
            status = auth.controllers.change_user_password(
                user_account,
                new_password)
            
            encoded_pw = new_password.encode("utf-8")
            stored_pw = user_account.password_hash.encode("utf-8")

            self.assertTrue(status)
            self.assertTrue(checkpw(encoded_pw, stored_pw))
      
    def test_check_username_exists(self):
        with self.app.app_context():
            exists_status = auth.controllers.check_username_exists(
                self.created_user_username)
            self.assertTrue(exists_status)
    
    def test_check_email_exists(self):
        with self.app.app_context():
            exists_status = auth.controllers.check_email_exists(
                self.created_user_email)
            self.assertTrue(exists_status)
    
    def test_get_user_role(self):
        with self.app.app_context():
            user_role = auth.controllers.get_Role(
                role_name="GENERAL")
            self.assertIsNotNone(user_role)
    
    def test_get_user_permission(self):
        with self.app.app_context():
            role = auth.models.Role().query.filter_by(
                name="GENERAL").one_or_none()
            user_permissions = auth.controllers.get_Permission(role=role)

            self.assertIsNotNone(user_permissions)
            self.assertGreater(len(user_permissions), 0)
    
    def test_add_role(self):
        test_role = auth.controllers.add_Role(role_name="TestRole")
        self.assertIsNotNone(test_role)

    def test_add_permission(self):
        with self.app.app_context():
            role = auth.models.Role().query.filter_by(
                name="GENERAL").one_or_none()
            
        permission_val = auth.auth.GENERAL_USER_PERMISSIONS[0]
        test_permission = auth.controllers.add_Permission(
            role_id=role.id,
            permission_index=permission_val)
        
        self.assertIsNotNone(test_permission)
    
    def test_add_user(self):
        with self.app.app_context():
            role = auth.models.Role().query.filter_by(
                name="GENERAL").one_or_none()

        user_dict = {
            "username": self.valid_test_username,
            "first_name": self.valid_test_firstname,
            "last_name": self.valid_test_lastname,
            "email": self.valid_test_email,
            "user_role": role.id,
            "password": self.valid_test_pwd
        }

        created_user = auth.controllers.add_User(user_details=user_dict)
        self.assertTrue(created_user)

    def test_search_by_username(self):
        with self.app.app_context():
            user_searched = auth.controllers.search_by_username(
                self.created_user_username)
            self.assertGreater(len(user_searched), 0)
    
    def test_account_creation(self):
        with self.app.app_context():
            role = auth.models.Role().query.filter_by(
                name="GENERAL").one_or_none()

        user_dict = {
            "username": self.valid_test_username,
            "first_name": self.valid_test_firstname,
            "last_name": self.valid_test_lastname,
            "email": self.valid_test_email,
            "user_role": role.id,
            "password": self.valid_test_pwd
        }
        role_name = "GENERAL"
        permissions = auth.auth.GENERAL_USER_PERMISSIONS

        user_created = auth.controllers.account_creation(
            user_details=user_dict,
            role_name=role_name,
            permissions=permissions)
        self.assertTrue(user_created)
    
    def test_authenticate_user_with_username(self):
        with self.app.app_context():
            user = auth.controllers.authenticate_user(
                self.created_user_username,
                self.created_user_pwd)

            self.assertIsNotNone(user)
            self.assertEqual(user.username, self.created_user_username)
    
    def test_authenticate_user_with_email(self):
        with self.app.app_context():
            user = auth.controllers.authenticate_user(
                self.created_user_email,
                self.created_user_pwd)

            self.assertIsNotNone(user)
            self.assertEqual(user.email, self.created_user_email)

    def test_load_login_page(self):
        response = self.client.get('/auth/login')
        self.assertEqual(response.status_code, 200)
    
    def test_load_registration_page(self):
        response = self.client.get('/auth/registration')
        self.assertEqual(response.status_code, 200)

    def test_load_forgot_password_page(self):
        response = self.client.get('/auth/forgot_password')
        self.assertEqual(response.status_code, 200)

    def test_load_reset_password_page(self):
        response = self.client.get('/auth/reset_password')
        self.assertEqual(response.status_code, 302)
        # self.assertEqual(response.request.path, '/')
    
    def test_user_registration(self):
        with self.app.app_context():
            response = self.client.post('/auth/registration', data={
                'username': self.valid_test_username,
                'first_name': self.valid_test_firstname,
                'last_name': self.valid_test_lastname,
                "email": self.valid_test_email,
                'password': self.valid_test_pwd,
                "password_confirmation": self.valid_test_pwd
            }, follow_redirects=True)
            
            self.assertEqual(response.status_code, 200)
            
            user_created = auth.models.User.query.filter_by(
                username=self.valid_test_username).one_or_none()
            self.assertIsNotNone(user_created)
            self.assertEqual(user_created.username, self.valid_test_username)
            self.assertEqual(user_created.first_name, self.valid_test_firstname)
            self.assertEqual(user_created.last_name, self.valid_test_lastname)
            self.assertEqual(user_created.email, self.valid_test_email)
            self.assertFalse(user_created.email_confirmed)
            self.assertTrue(user_created.active)
    
    def test_user_login(self):
        with self.app.app_context():
            response = self.client.post(
                "/auth/login",
                data={
                    "username_email": self.created_user_username,
                    "password": self.created_user_pwd,
                    "next": ""
                }, follow_redirects=True)
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.request.path, '/')

    def test_logout_functionality(self):
        with self.app.app_context():
            _ = self.client.post(
                "/auth/login",
                data={
                    "username_email": self.created_user_username,
                    "password": self.created_user_pwd,
                    "next": ""},
                follow_redirects=True)
            response = self.client.get('/auth/logout', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.request.path, '/')

    def test_forgot_password(self):
        with self.app.app_context():
            reset_token = auth.utils.RESET_PASSWORD_TOKEN
            response = self.client.post("/auth/forgot_password",
                data={
                    "email": self.created_user_email,
                    "reset_token": reset_token
                },
                follow_redirects=True)
            
            self.assertEqual(response.status_code, 200)
            self.assertTrue(
                re.search(
                    auth.utils.RESET_LINK_SENT_NO_EMAIL,
                    response.get_data(as_text=True)))

    def test_reset_password_form(self):
        with self.app.app_context():
            # Generates token.
            secret_key = os.environ.get("SECRET_KEY")
            timed_serializer = URLSafeTimedSerializer(secret_key)
            password_reset_token = timed_serializer.dumps(
                self.created_user_email,
                salt=auth.utils.RESET_PASSWORD_TOKEN)

            response = self.client.post(f"/auth/reset_password", data={
                "password": "qK>bmb(+DUE-73*&",
                "password_confirmation": "qK>bmb(+DUE-73*&",
                "reset_token": password_reset_token
            }, follow_redirects=True)

            self.assertEqual(response.status_code, 200)
            self.assertTrue(re.search(auth.utils.SUCCESS_PWD_CHANGE, response.get_data(as_text=True)))

if __name__ == "__main__":
    unittest.main()

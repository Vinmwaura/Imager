import unittest

import re

from apps import create_app, db

from bcrypt import gensalt, hashpw

import apps.auth as auth
import apps.admin_panel as admin_panel

from .config import *


class TestAdminPanel(unittest.TestCase):
    def setUp(self):
        self.app = create_app(test_config)
        self.appctx = self.app.app_context()
        self.appctx.push()

        self.client = self.app.test_client()

        # Hack to remove any tables if any are present in Test Database.
        db.drop_all()

        # Creates a temporary test database.
        db.create_all()

        # Test Admin account configurations.
        self.created_admin_username = "captain_jack"
        self.created_admin_firstname = "Jack"
        self.created_admin_lastname = "Sparrow"
        self.created_admin_email = "jspa@email.com"
        self.created_admin_pwd = "M'dNzF9[$PjS>}a*"

        # Test User account configurations.
        self.created_user_username = "john_doe"
        self.created_user_firstname = "John"
        self.created_user_lastname = "Doe"
        self.created_user_email = "jdoe@email.com"
        self.created_user_pwd = "M'dNzF9[$PjS>}a*"

        # Manually create an admin account.
        with self.app.app_context():
            # Role Model for test Admin and General User.
            admin_role = auth.models.Role(name=auth.auth.DEFAULT_ADMIN_ROLE)
            user_role = auth.models.Role(name=auth.auth.DEFAULT_GENERAL_USER_ROLE)

            db.session.add(admin_role)
            db.session.add(user_role)

            db.session.commit()

            # Admin Permissions.
            for permission in auth.auth.ADMIN_PERMISSION_LIST:
                admin_role_permission = auth.models.Permissions(
                    role_id=admin_role.id,
                    permission=permission.value)

                db.session.add(admin_role_permission)
            db.session.commit()

            # General User Permission Model.
            for permission in auth.auth.GENERAL_USER_PERMISSIONS:
                user_role_permission = auth.models.Permissions(
                    role_id=user_role.id,
                    permission=permission.value)

                db.session.add(user_role_permission)
            db.session.commit()

            # Admin User Model.
            self.admin_salt = gensalt(16)
            hashed_pwd = hashpw(
                self.created_admin_pwd.encode("utf-8"),
                self.admin_salt)
            admin_account = auth.models.User(
                username=self.created_admin_username,
                first_name=self.created_admin_firstname,
                last_name=self.created_admin_lastname,
                email=self.created_admin_email,
                password_hash=hashed_pwd.decode("utf-8"),
                email_confirmed=True,
                user_role=admin_role.id)
            db.session.add(admin_account)
            db.session.commit()

            # General User Model.
            self.general_salt = gensalt(16)
            hashed_pwd = hashpw(
                self.created_user_pwd.encode("utf-8"),
                self.general_salt)
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

    def test_anon_admin_panel_redirect(self):
        response = self.client.get("/admin", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request.path, "/auth/login")
    
    def test_general_user_admin_panel_redirect(self):
        with self.app.app_context():
            response = self.client.post(
                    "/auth/login",
                    data={
                        "username_email": self.created_user_username,
                        "password": self.created_user_pwd,
                        "next": "/admin"},
                    follow_redirects=True)

            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.text, admin_panel.utils.ACCESS_DENIED)

    def test_load_logged_in_user_admin_panel_page(self):
        with self.app.app_context():
            response = self.client.post(
                "/auth/login",
                data={
                    "username_email": self.created_admin_username,
                    "password": self.created_admin_pwd,
                    "next": "/admin"},
                follow_redirects=True)
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.request.path, "/admin/")

    def test_load_view_users_page(self):
        with self.app.app_context():
            response = self.client.post(
                "/auth/login",
                data={
                    "username_email": self.created_admin_username,
                    "password": self.created_admin_pwd,
                    "next": "/admin/view/users"},
                follow_redirects=True)
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.request.path, "/admin/view/users")

    def test_load_edit_user_role_page(self):
        with self.app.app_context():
            user = auth.models.User.query.filter_by(
                username=self.created_user_username).first()
            
            response = self.client.post(
                "/auth/login",
                data={
                    "username_email": self.created_admin_username,
                    "password": self.created_admin_pwd,
                    "next": f"/admin/edit/user/role/{user.id}"},
                follow_redirects=True)
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.request.path, f"/admin/edit/user/role/{user.id}")
    
    def test_load_edit_user_status_page(self):
        with self.app.app_context():
            user = auth.models.User.query.filter_by(
                username=self.created_user_username).first()
            
            response = self.client.post(
                "/auth/login",
                data={
                    "username_email": self.created_admin_username,
                    "password": self.created_admin_pwd,
                    "next": f"/admin/edit/user/status/{user.id}"},
                follow_redirects=True)
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.request.path, f"/admin/edit/user/status/{user.id}")
    
    def test_load_view_roles_page(self):
        with self.app.app_context():
            response = self.client.post(
                "/auth/login",
                data={
                    "username_email": self.created_admin_username,
                    "password": self.created_admin_pwd,
                    "next": "/admin/view/roles"},
                follow_redirects=True)
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.request.path, "/admin/view/roles")
    
    def test_load_add_role_page(self):
        with self.app.app_context():
            response = self.client.post(
                "/auth/login",
                data={
                    "username_email": self.created_admin_username,
                    "password": self.created_admin_pwd,
                    "next": "/admin/add/role"},
                follow_redirects=True)
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.request.path, "/admin/add/role")
    
    def test_load_edit_role_page(self):
        with self.app.app_context():
            role = auth.models.Role.query.filter_by(
                name=auth.auth.DEFAULT_GENERAL_USER_ROLE).first()
            
            response = self.client.post(
                "/auth/login",
                data={
                    "username_email": self.created_admin_username,
                    "password": self.created_admin_pwd,
                    "next": f"/admin/edit/role/{role.id}"},
                follow_redirects=True)
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.request.path, f"/admin/edit/role/{role.id}")

    def test_load_delete_role_page(self):
        with self.app.app_context():
            role = auth.models.Role.query.filter_by(
                name=auth.auth.DEFAULT_GENERAL_USER_ROLE).first()
            
            response = self.client.post(
                "/auth/login",
                data={
                    "username_email": self.created_admin_username,
                    "password": self.created_admin_pwd,
                    "next": f"/admin/delete/role/{role.id}"},
                follow_redirects=True)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.request.path, f"/admin/delete/role/{role.id}")

    def test_edit_user_role(self):
        with self.app.app_context():
            user = auth.models.User.query.filter_by(
                username=self.created_user_username).first()
            admin_role = auth.models.Role.query.filter_by(
                name=auth.auth.DEFAULT_ADMIN_ROLE).first()
            # Log In Admin.
            self.client.post(
                "/auth/login",
                data={
                    "username_email": self.created_admin_username,
                    "password": self.created_admin_pwd,
                    "next": ""},
                follow_redirects=True)
            
            response = self.client.post(
                f"/admin/edit/user/role/{user.id}",
                data={
                    "role": admin_role.id
                },
                follow_redirects=True)
            
            #user = auth.models.User.query.filter_by(
            #    username=self.created_user_username).first()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(user.role.name, auth.auth.DEFAULT_ADMIN_ROLE)
    
    def test_edit_user_status_deactivate(self):
        with self.app.app_context():
            user = auth.models.User.query.filter_by(
                username=self.created_user_username).first()

            # Log In Admin.
            self.client.post(
                "/auth/login",
                data={
                    "username_email": self.created_admin_username,
                    "password": self.created_admin_pwd,
                    "next": ""},
                follow_redirects=True)
            
            response = self.client.post(
                f"/admin/edit/user/status/{user.id}",
                follow_redirects=True)
            
            self.assertEqual(response.status_code, 200)
            self.assertFalse(user.active)
    
    def test_edit_user_status_activate(self):
        with self.app.app_context():
            user = auth.models.User.query.filter_by(
                username=self.created_user_username).first()
            user.active = False
            db.session.commit()

            # Log In Admin.
            self.client.post(
                "/auth/login",
                data={
                    "username_email": self.created_admin_username,
                    "password": self.created_admin_pwd,
                    "next": ""},
                follow_redirects=True)
            
            response = self.client.post(
                f"/admin/edit/user/status/{user.id}",
                follow_redirects=True)
            
            self.assertEqual(response.status_code, 200)
            self.assertTrue(user.active)
    
    def test_edit_role(self):
        with self.app.app_context():
            general_role = auth.models.Role.query.filter_by(
                name=auth.auth.DEFAULT_GENERAL_USER_ROLE).first()

            # Log In Admin.
            self.client.post(
                "/auth/login",
                data={
                    "username_email": self.created_admin_username,
                    "password": self.created_admin_pwd,
                    "next": ""},
                follow_redirects=True)
            
            response = self.client.post(
                f"/admin/edit/role/{general_role.id}",
                data={"role_name": "GENERAL_123"},
                follow_redirects=True)
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.request.path, "/admin/view/roles")

if __name__ == "__main__":
    unittest.main()

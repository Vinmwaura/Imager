import io
import os
import re
import uuid
import shutil

from bcrypt import (
    gensalt,
    hashpw)

import unittest
from unittest import mock

import werkzeug
from werkzeug.datastructures import FileStorage

import apps.api as api
import apps.auth as auth
import apps.imager as imager
from apps import create_app, db


class TestImager(unittest.TestCase):
    def setUp(self):
        self.app = create_app("config.TestingConfig")
        self.appctx = self.app.app_context()
        self.appctx.push()

        self.client = self.app.test_client()

        current_dir = os.path.dirname(
            os.path.abspath(__file__))
        self.img_path = os.path.join(
            current_dir,
            "assets/test_image_512.jpg")
        self.thumbnail_path = os.path.join(
            current_dir,
            "assets/test_image_64.jpg")
        
        self.upload_path = os.path.join(
            current_dir,
            "test_user_uploads")
        self.app.config["UPLOAD_PATH"] = os.path.join(
            current_dir,
            "test_user_uploads")
        self.app.config["UPLOAD_EXTENSIONS"] = [".jpg", ".png", ".jpeg"]

        # Hack to remove any tables if any are present in Test Database.
        db.drop_all()

        # Creates a temporary test database.
        db.create_all()

        # UserContent configurations.
        # Generates a random unique id for user's directory.
        self.directory_name = uuid.uuid4().hex

        # User upload directory
        self.user_upload_directory = os.path.join(
            self.upload_path,
            str(self.directory_name))

        # Directory for storing each user's image thumbnails.
        thumbnail_directory = os.path.join(
            self.user_upload_directory,
            "thumbnails")

        # ImageContent configurations.
        self.img_title = "Test Image."
        self.img_description = "Test Description..."
        self.file_name = "%s" % os.urandom(8).hex()

        # Test User account configurations.
        self.created_user_username = "john_doe"
        self.created_user_firstname = "John"
        self.created_user_lastname = "Doe"
        self.created_user_email = "jdoe@email.com"
        self.created_user_pwd = "M'dNzF9[$PjS>}a*"
        self.created_user_role = 1

        # Tags.
        self.tag_name = "Test Tags"

        # Explicitly create an activated account.
        with self.app.app_context():
            # Role Model.
            user_role = auth.models.Role(
                name=auth.auth.DEFAULT_GENERAL_USER_ROLE)
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
            
            # User Content Model.
            user_content = imager.models.UserContent(
                user_id=user_account.id,
                content_location=self.directory_name,
                user=user_account
            )
            db.session.add(user_account)
            db.session.commit()

            # Image Content Model.
            image_content = imager.models.ImageContent(
                user_content_id=user_content.id,
                file_id=self.file_name,
                title=self.img_title,
                description=self.img_description,
            )
            db.session.add(image_content)
            db.session.commit()

            os.makedirs(
                thumbnail_directory,
                exist_ok=True)
            # Moves test image for testing.
            shutil.copy(
                self.img_path,
                os.path.join(
                    self.user_upload_directory,
                    self.file_name + ".jpg"))
            # Moves test image for testing as thumbnail.
            shutil.copy(
                self.thumbnail_path,
                os.path.join(
                    thumbnail_directory,
                    self.file_name + ".jpg"))

            # Tags Model.
            tag = imager.models.Tags(tag_name=self.tag_name)
            db.session.add(tag)
            db.session.commit()

            # Image Tags Model.
            img_tags = imager.models.ImageTags(
                tag_id=tag.id,
                image_content_id=image_content.id)
            db.session.add(img_tags)
            db.session.commit()

            # Client Model.
            self.client_id = "flrY8gMmp6ThpGAVIx5PFXRe"
            self.client_secret = "4aEhxXePQQahDO8HK3qoE1nYri2h9lAvxzZlOUCAccHSUhz7"
            auth_client = api.models.OAuth2Client(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_id=user_account.id,)
            db.session.add(auth_client)
            db.session.commit()

            # Token Model.
            self.access_token = "K8vq5c4tzrVSkfMsxzGCZCkVKAVvnqEaIjxgzS1G53"
            self.refresh_token = "yadCnq3usjl4jPeGwuvI3LaGrdFYxpn9MJjp9cS0s6FUkNGP"

            auth_token = api.models.OAuth2Token(
                token_type="Bearer",
                access_token=self.access_token,
                refresh_token=self.refresh_token,
                revoked=False,
                client_id=auth_client.id,
                user_id=user_account.id,)
            db.session.add(auth_token)
            db.session.commit()

    def tearDown(self):
        db.drop_all()

        # Removes directory created for testing uploading and uploaded image functionalities.
        shutil.rmtree(
            self.upload_path,
            ignore_errors=True,
            onerror=None)

        self.appctx.pop()
        self.app = None
        self.appctx = None

    @mock.patch('flask_login.utils._get_user')
    def test_get_image_details(self, current_user):
        with self.app.app_context():
            user = auth.models.User().query.filter_by(
                username=self.created_user_username
            ).one_or_none()

            user = mock.MagicMock() 
            user.__repr__ = lambda self: user.username
            current_user.return_value = user

            image_content = imager.models.ImageContent.query.order_by(
                imager.models.ImageContent.upload_time.asc())

            image_pagination = image_content.paginate(
                page=1,
                per_page=1,
                error_out=False,
                max_per_page=2).items

            data_dict = imager.controllers.get_image_details(
                user,
                image_pagination)
            self.assertIsInstance(data_dict, list)
            self.assertGreater(len(data_dict), 0)
    
    def test_update_gallery(self):
        with self.app.app_context():
            image_content = imager.models.ImageContent.query.order_by(
                imager.models.ImageContent.upload_time.asc()).one_or_none()
            status = imager.controllers.update_gallery(
                image_content,
                {"title": "New Title"}
            )
            self.assertTrue(status)

            status = imager.controllers.update_gallery(
                image_content,
                {"description": "New Description"}
            )
            self.assertTrue(status)

            status = imager.controllers.update_gallery(
                image_content,
                {"should_fail": "Some Test"}
            )
            self.assertFalse(status)

    def test_get_user_content(self):
        with self.app.app_context():
            user = auth.models.User().query.filter_by(
                username=self.created_user_username
            ).first()
            user_content = imager.controllers.get_user_content(user)
            self.assertIsNotNone(user_content)
    
    def test_get_image_contents_by_time(self):
        with self.app.app_context():
            image_content_asc = imager.controllers.get_image_contents_by_time(
                sort_order="asc")
            self.assertIsNotNone(image_content_asc)
            
            image_content_desc = imager.controllers.get_image_contents_by_time(
                sort_order="desc")
            self.assertIsNotNone(image_content_desc)
            
            image_content_invalid = imager.controllers.get_image_contents_by_time(
                sort_order="not_a_valid_input")
            self.assertIsNone(image_content_invalid)
    
    def test_get_image_contents_by_score(self):
        with self.app.app_context():
            image_content_asc = imager.controllers.get_image_contents_by_score(
                sort_order="asc")
            self.assertIsNotNone(image_content_asc)
            
            image_content_desc = imager.controllers.get_image_contents_by_score(
                sort_order="desc")
            self.assertIsNotNone(image_content_desc)
            
            image_content_invalid = imager.controllers.get_image_contents_by_score(
                sort_order="not_a_valid_input")
            self.assertIsNone(image_content_invalid)

    def test_get_image_by_user(self):
        with self.app.app_context():
            user = auth.models.User().query.filter_by(
                username=self.created_user_username
            ).first()
            image_content = imager.controllers.get_image_by_user(
                user, self.file_name)
            self.assertIsNotNone(image_content)

            not_user = None
            none_image_content = imager.controllers.get_image_by_user(
                not_user, self.file_name)
            self.assertIsNone(none_image_content)

            not_image_id = None
            none_image_content = imager.controllers.get_image_by_user(
                user, not_image_id)
            self.assertIsNone(none_image_content)

            none_image_content = imager.controllers.get_image_by_user(
                not_user, not_image_id)
            self.assertIsNone(none_image_content)
    
    def test_get_image_contents_by_user(self):
        with self.app.app_context():
            valid_categories = ["upload_time", "score"]
            valid_categories_filters = ["asc", "desc"]
            
            # Valid Everything.
            for valid_category in valid_categories:
                for valid_category_filter in valid_categories_filters:
                    user, image_content = imager.controllers.get_image_contents_by_user(
                        username=self.created_user_username,
                        category=valid_category,
                        category_filter=valid_category_filter)
                    self.assertIsNotNone(user)
                    self.assertIsNotNone(image_content)
            
            # Invalid Category Filter Only.
            invalid_filter = "invalid_filter"
            for valid_category in valid_categories:
                user, image_content = imager.controllers.get_image_contents_by_user(
                    username=self.created_user_username,
                    category=valid_category,
                    category_filter=invalid_filter)
                self.assertIsNotNone(user)
                self.assertIsNone(image_content)

            # Invalid Catgory Only.
            invalid_categories = "invalid_category"
            for valid_category_filter in valid_categories_filters:
                user, image_content = imager.controllers.get_image_contents_by_user(
                    username=self.created_user_username,
                    category=invalid_categories,
                    category_filter=valid_category_filter)
                self.assertIsNotNone(user)
                self.assertIsNone(image_content)
            
            # Invalid Category and Category Filter.
            user, image_content = imager.controllers.get_image_contents_by_user(
                username=self.created_user_username,
                category="not_a_category",
                category_filter="not_a_filter")
            self.assertIsNotNone(user)
            self.assertIsNone(image_content)

            # Invalid User only.
            user, image_content = imager.controllers.get_image_contents_by_user(
                username=None,
                category="upload_time",
                category_filter="asc")
            self.assertIsNone(user)
            self.assertIsNone(image_content)
    
    def test_get_image_by_tags(self):
        with self.app.app_context():
            image_content = imager.controllers.get_images_by_tags(self.tag_name)
            self.assertIsNotNone(image_content)

            invalid_tag_name = "not_a_tag"
            image_content = imager.controllers.get_images_by_tags(invalid_tag_name)
            self.assertIsNone(image_content)
    
    def test_get_image_content_by_id(self):
        with self.app.app_context():
            image_content = imager.controllers.get_image_content_by_id(self.file_name)
            self.assertIsNotNone(image_content)

            invalid_image_id = "not_image_id"
            image_content = imager.controllers.get_image_content_by_id(invalid_image_id)
            self.assertIsNone(image_content)
    
    def test_get_imagecontent_neighbours(self):
        with self.app.app_context():
            image_content_1 = imager.models.ImageContent.query.one_or_none()
            user_content = imager.models.UserContent.query.one_or_none()

            # Add two more image_content for testing.
            image_content_2 = imager.models.ImageContent(
                user_content_id=user_content.id,
                file_id="123",
                title="img_2",
                description="")
            db.session.add(image_content_2)

            image_content_3 = imager.models.ImageContent(
                user_content_id=user_content.id,
                file_id="456",
                title="img_3",
                description="")
            db.session.add(image_content_3)
            db.session.commit()

            all_image_contents = imager.models.ImageContent.query.all()

            neighbours_img_1 = imager.controllers.get_imagecontent_neighbours(
                image_content_1,
                all_image_contents)
            self.assertIsNone(neighbours_img_1["prev"])
            self.assertEqual(neighbours_img_1["next"].title, "img_2")
            
            neighbours_img_2 = imager.controllers.get_imagecontent_neighbours(
                image_content_2,
                all_image_contents)
            self.assertEqual(neighbours_img_2["prev"].title, self.img_title)
            self.assertEqual(neighbours_img_2["next"].title, "img_3")

            neighbours_img_3 = imager.controllers.get_imagecontent_neighbours(
                image_content_3,
                all_image_contents)
            self.assertEqual(neighbours_img_3["prev"].title, "img_2")
            self.assertIsNone(neighbours_img_3["next"])
    
    def test_load_user_images(self):
        with self.app.app_context():
            user = auth.models.User().query.filter_by(
                username=self.created_user_username
            ).first()
            image_content = imager.controllers.load_user_images(user.id, self.file_name)
            self.assertIsInstance(image_content, list)
            self.assertGreater(len(image_content), 0)

            # No Image Content for User.
            image_content = imager.controllers.load_user_images(69, self.file_name)
            self.assertIsInstance(image_content, list)
            self.assertEqual(len(image_content), 0)
    
    def test_search_by_title(self):
        with self.app.app_context():
            title_list = imager.controllers.search_by_title(
                self.img_title[:2],
                get_list=True)
            self.assertIsInstance(title_list, list)
            self.assertGreater(len(title_list), 0)

            title_obj = imager.controllers.search_by_title(
                self.img_title[:2],
                get_list=False)
            self.assertNotIsInstance(title_obj, list)
            
            no_title_list = imager.controllers.search_by_title(
                "not_a_title",
                get_list=True)
            self.assertIsInstance(no_title_list, list)
            self.assertEqual(len(no_title_list), 0)

            no_title_obj = imager.controllers.search_by_title(
                "not_a_title",
                get_list=False)
            self.assertNotIsInstance(no_title_obj, list)

    def test_search_by_tags(self):
        with self.app.app_context():
            tag = imager.controllers.search_by_tags(self.tag_name[:2])
            self.assertIsInstance(tag, list)
            self.assertGreater(len(tag), 0)

            invalid_tag = "not_a_tag"
            no_tag = imager.controllers.search_by_tags(invalid_tag)
            self.assertIsInstance(no_tag, list)
            self.assertEqual(len(no_tag), 0)
    
    def test_create_user_content(self):
        with self.app.app_context():
            user = auth.models.User().query.filter_by(
                username=self.created_user_username
            ).first()
            test_directory_name = "Test123"
            status = imager.controllers.create_user_content(user, test_directory_name)
            self.assertTrue(status)

            user_content = imager.models.UserContent.query.filter_by(
                content_location=test_directory_name).one_or_none()
            self.assertIsNotNone(user_content)

    def test_create_or_get_user_content(self):
        with self.app.app_context():
            user = auth.models.User().query.filter_by(
                username=self.created_user_username
            ).first()
            user_content = imager.controllers.create_or_get_user_content(user)
            self.assertIsNotNone(user_content)
    
    def test_save_user_image(self):
        image_details = {
            "title": "Second Test Title",
            "description": "Some Description."
        }

        with open(self.img_path, "rb") as f:
            stream = io.BytesIO(f.read())

        uploaded_file = FileStorage(
            stream=stream,
            filename="test_image_512.jpg",
            name='file',
            content_type='image/jpg')
        with self.app.app_context():
            user = auth.models.User().query.filter_by(
                username=self.created_user_username
            ).first()

            status = imager.controllers.save_user_image(
                user,
                uploaded_file,
                image_details)

            image_content = imager.models.ImageContent.query.filter_by(
                title=image_details["title"]).one_or_none()
            
            self.assertTrue(status)
            self.assertIsNotNone(image_content)
            
            image_path = os.path.join(
                self.upload_path,
                image_content.user_content.content_location,
                image_content.file_id + ".jpg")

            thumbnail_path = os.path.join(
                self.upload_path,
                image_content.user_content.content_location,
                'thumbnails',
                image_content.file_id + ".jpg")
            self.assertTrue(os.path.exists(image_path))
            self.assertTrue(os.path.exists(thumbnail_path))

    def test_image_content_pagination(self):
        with self.app.app_context():
            image_contents = imager.models.ImageContent.query
            image_content_pagination = imager.controllers.image_content_pagination(
                image_contents,
                page=1)
            self.assertIsNotNone(image_content_pagination)

            with self.assertRaises(werkzeug.exceptions.NotFound):
                image_content_pagination = imager.controllers.image_content_pagination(
                    image_contents,
                    page=10)
    
    def test_upvote(self):
        with self.app.app_context():
            user = auth.models.User().query.filter_by(
                username=self.created_user_username
            ).first()
            status = imager.controllers.upvote(user, self.file_name)
            self.assertTrue(status)

            upvote_obj = imager.models.VoteCounter().query.filter_by(
                user_id=user.id,
                image_file_id=self.file_name).one_or_none()
            self.assertIsNotNone(upvote_obj)
            self.assertEqual(upvote_obj.vote, imager.models.VoteEnum.UPVOTE.value)

    def test_downvote(self):
        with self.app.app_context():
            user = auth.models.User().query.filter_by(
                username=self.created_user_username
            ).first()
            status = imager.controllers.downvote(user, self.file_name)
            self.assertTrue(status)

            downvote_obj = imager.models.VoteCounter().query.filter_by(
                user_id=user.id,
                image_file_id=self.file_name).one_or_none()
            self.assertIsNotNone(downvote_obj)
            self.assertEqual(downvote_obj.vote, imager.models.VoteEnum.DOWNVOTE.value)
    
    def test_image_metric(self):
        with self.app.app_context():
            metric_data = imager.controllers.image_metric(self.file_name)
            self.assertIsNotNone(metric_data)
            self.assertIsInstance(metric_data, dict)
    
    def test_delete_user_content(self):
        with self.app.app_context():
            user_role = auth.models.Role.query.filter_by(
                name=auth.auth.DEFAULT_GENERAL_USER_ROLE
            ).one_or_none()
            # User Model.
            salt = gensalt(16)
            hashed_pwd = hashpw(
                "G3q_gf>^$9F}-Y=Sbt8A".encode("utf-8"),
                salt)
            user_account = auth.models.User(
                username="new_username",
                first_name="New",
                last_name="User",
                email="newuser@email.com",
                password_hash=hashed_pwd.decode("utf-8"),
                email_confirmed=True,
                user_role=user_role.id)
            db.session.add(user_account)
            db.session.commit()
            
            # User Content Model.
            user_content = imager.models.UserContent(
                user_id=user_account.id,
                content_location=self.directory_name,
                user=user_account
            )
            db.session.add(user_account)
            db.session.commit()

            # Image Content Model.
            file_name = "%s" % os.urandom(8).hex()
            image_content = imager.models.ImageContent(
                user_content_id=user_content.id,
                file_id=file_name,
                title="New Title",
                description="New Description",
            )
            db.session.add(image_content)
            db.session.commit()

            status, image_name, user_directory = imager.controllers.delete_user_content(
                user_account,
                file_name)
            self.assertTrue(status)
            self.assertEqual(image_name, "New Title")
            self.assertEqual(user_directory, self.directory_name)
            
            # No User Content to delete Test.
            status, image_name, user_directory = imager.controllers.delete_user_content(
                user_account,
                file_name)
            self.assertFalse(status)
            self.assertIsNone(image_name)
            self.assertIsNone(user_directory)

    def test_load_home_page(self):
        with self.app.app_context():
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)
    
    def test_load_about_page(self):
        with self.app.app_context():
            response = self.client.get('/about')
            self.assertEqual(response.status_code, 200)
    
    def test_anon_user_settings_redirect(self):
        with self.app.app_context():
            response = self.client.get('/settings', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.request.path, '/auth/login')
        
    def test_anon_user_settings_delete_redirect(self):
        with self.app.app_context():
            response = self.client.get('/settings/delete/1', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.request.path, '/auth/login')
        
    def test_anon_user_settings_revoke_redirect(self):
        with self.app.app_context():
            response = self.client.get('/settings/revoke/1', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.request.path, '/auth/login')
    
    def test_logged_in_user_load_settings_page(self):
        with self.app.app_context():
            response = self.client.post(
                "/auth/login",
                data={
                    "username_email": self.created_user_username,
                    "password": self.created_user_pwd,
                    "next": "/settings"},
                follow_redirects=True)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.request.path, "/settings")

    def test_logged_in_user_load_delete_client_settings(self):
        with self.app.app_context():
            response = self.client.post(
                "/auth/login",
                data={
                    "username_email": self.created_user_username,
                    "password": self.created_user_pwd,
                    "next": f"/settings/delete/{self.client_id}"},
                follow_redirects=True)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.request.path, "/settings")
            self.assertTrue(re.search(f"Successfully deleted client: {self.client_id}", response.get_data(as_text=True)))
    
    def test_logged_in_user_revoke_token_settings(self):
        with self.app.app_context():
            user = auth.models.User().query.filter_by(
                username=self.created_user_username
            ).first()

            token = api.models.OAuth2Token.query.filter_by(
                user_id=user.id).one_or_none()
            
            response = self.client.post(
                "/auth/login",
                data={
                    "username_email": self.created_user_username,
                    "password": self.created_user_pwd,
                    "next": f"/settings/revoke/{token.id}"},
                follow_redirects=True)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.request.path, "/settings")
            self.assertTrue(re.search("Successfully revoked token", response.get_data(as_text=True)))
    
    def test_anon_user_upload_image_redirect(self):
        with self.app.app_context():
            response = self.client.get("/upload", follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.request.path, '/auth/login')

    def test_logged_in_user_load_upload_image(self):
        with self.app.app_context():
            response = self.client.post(
                '/auth/login',
                data={
                    "username_email": self.created_user_username,
                    "password": self.created_user_pwd,
                    "next": "/upload"},
                follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.request.path, '/upload')
    
    def test_logged_in_user_upload_image(self):
        with self.app.app_context():
            self.client.post(
                '/auth/login',
                data={
                    "username_email": self.created_user_username,
                    "password": self.created_user_pwd,
                    "next": "/upload"},
                follow_redirects=True)

            with open(self.img_path, "rb") as f:
                stream = io.BytesIO(f.read())
            
            response = self.client.post(
                "/upload", 
                data={
                    "title": "Third Test Title",
                    "description": "Another Description...",
                    "file": (stream, "test_image_512.jpg")
                },
                follow_redirects=True,
                content_type="multipart/form-data"
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.request.path, "/")
            self.assertTrue(re.search("Image Successfully added.", response.get_data(as_text=True)))

            uploaded_image_content = imager.models.ImageContent.query.filter_by(
                title="Third Test Title").one_or_none()
            self.assertIsNotNone(uploaded_image_content)

            image_path = os.path.join(
                self.upload_path,
                uploaded_image_content.user_content.content_location,
                uploaded_image_content.file_id + ".jpg")

            thumbnail_path = os.path.join(
                self.upload_path,
                uploaded_image_content.user_content.content_location,
                'thumbnails',
                uploaded_image_content.file_id + ".jpg")
            self.assertTrue(os.path.exists(image_path))
            self.assertTrue(os.path.exists(thumbnail_path))
    
    def test_load_image_by_id_invalid_page(self):
        with self.app.app_context():
            response = self.client.get('/upload/image/-69420')
            self.assertEqual(response.status_code, 404)

    def test_load_image_by_id_valid_page(self):
        with self.app.app_context():
            image_content = imager.models.ImageContent.query.filter_by(
                file_id=self.file_name).one_or_none()    
            response = self.client.get(f"/upload/image/{image_content.file_id}")
            self.assertEqual(response.status_code, 200)
            response.close()  # Stops ResourceWarning.

    def test_load_thumbnail_by_id_valid_page(self):
        with self.app.app_context():
            image_content = imager.models.ImageContent.query.filter_by(
                file_id=self.file_name).one_or_none()    
            response = self.client.get(f"/upload/thumbnail/{image_content.file_id}")
            self.assertEqual(response.status_code, 200)
            response.close()  # Stops ResourceWarning.

    def test_load_thumbnail_by_id_invalid_page(self):
        with self.app.app_context():
            response = self.client.get('/upload/thumbnail/-69420')
            self.assertEqual(response.status_code, 404)

    def test_load_gallery_page_invalid(self):
        with self.app.app_context():
            response_invalid_img_id = self.client.get('/gallery/-69420')
            self.assertEqual(response_invalid_img_id.status_code, 404)
            
            response_invalid_cat = self.client.get('/gallery/69/potato')
            self.assertEqual(response_invalid_cat.status_code, 404)
            
            response_invalid_filter = self.client.get('/gallery/69/upload_time/mango')
            self.assertEqual(response_invalid_filter.status_code, 404)

    def test_load_gallery_page_valid(self):
        with self.app.app_context():
            self.client.post(
                '/auth/login',
                data={
                    "username_email": self.created_user_username,
                    "password": self.created_user_pwd,
                    "next": ""},
                follow_redirects=True)
            
            image_content = imager.models.ImageContent.query.filter_by(
                file_id=self.file_name).one_or_none()

            response = self.client.get(f"/gallery/{image_content.file_id}")
            self.assertEqual(response.status_code, 200)

    def test_load_gallery_search(self):
        with self.app.app_context():
            self.client.post(
                '/auth/login',
                data={
                    "username_email": self.created_user_username,
                    "password": self.created_user_pwd,
                    "next": ""},
                follow_redirects=True)

            response = self.client.get(f"/gallery/search?q={self.img_title}&page=1")
            self.assertEqual(response.status_code, 200)

    def test_anon_user_edit_gallery_redirect(self):
        with self.app.app_context():
            response = self.client.get('/edit/gallery/-69420', follow_redirects=True)
            self.assertEqual(response.request.path, '/auth/login')

    def test_load_logged_in_user_edit_gallery_page(self):
        with self.app.app_context():
            response = self.client.post(
                '/auth/login',
                data={
                    "username_email": self.created_user_username,
                    "password": self.created_user_pwd,
                    "next": f"/edit/gallery/{self.file_name}"},
                follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.request.path, f"/edit/gallery/{self.file_name}")

    def test_load_image_by_username_invalid_options(self):
        with self.app.app_context():
            response_invalid_username = self.client.get('/gallery/user/-69')
            self.assertEqual(response_invalid_username.status_code, 404)
    
    def test_load_image_by_username_valid_options_page(self):
        with self.app.app_context():
            user = auth.models.User().query.filter_by(
                username=self.created_user_username
            ).first()

            response_valid_username = self.client.get(f"/gallery/user/{user.username}")
            self.assertEqual(response_valid_username.status_code, 200)
    
    def test_anon_user_user_profile_redirect(self):
        response = self.client.get('/edit/user/profile', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request.path, '/auth/login')

    def test_load_logged_in_user_user_profile_page(self):
        with self.app.app_context():
            response = self.client.post(
                '/auth/login',
                data={
                    "username_email": self.created_user_username,
                    "password": self.created_user_pwd,
                    "next": f"/user/profile"},
                follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.request.path, f"/user/profile")

    def test_load_edit_user_profile_page(self):
        with self.app.app_context():
            self.client.post(
                "/auth/login",
                data={
                    "username_email": self.created_user_username,
                    "password": self.created_user_pwd,
                    "next": ""},
                follow_redirects=True)

            response = self.client.get("/edit/user/profile")
            self.assertEqual(response.status_code, 200)
    
    def test_edit_user_profile(self):
        with self.app.app_context():
            self.client.post(
                "/auth/login",
                data={
                    "username_email": self.created_user_username,
                    "password": self.created_user_pwd,
                    "next": ""},
                follow_redirects=True)

            response = self.client.post(
                "/edit/user/profile",
                data={
                    "username": "new_username",
                    "first_name": "new",
                    "last_name": "username",
                    "email": "new@gmail.com"
                },
                follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            new_user = auth.models.User().query.filter_by(
                username="new_username"
            ).one_or_none()

            self.assertIsNotNone(new_user)
            self.assertEqual(new_user.username, "new_username")
            self.assertEqual(new_user.first_name, "new")
            self.assertEqual(new_user.last_name, "username")
            self.assertEqual(new_user.email, "new@gmail.com")

    def test_load_images_by_tag_valid(self):
        # Feature disabled for now.
        pass

    def test_load_images_by_tag_invalid(self):
        # Feature disabled for now.
        pass

    def test_anon_user_upvote_counter_valid(self):
        with self.app.app_context():
            response = self.client.post(
                "/upvote",
                data={
                    "image_id": self.file_name
                })
            self.assertEqual(response.status_code, 302)

    def test_logged_in_user_upvote_counter_valid(self):
        with self.app.app_context():
            _ = self.client.post(
                "/auth/login",
                data={
                    "username_email": self.created_user_username,
                    "password": self.created_user_pwd,
                    "next": ""},
                follow_redirects=True)

            response = self.client.post(
                "/upvote",
                data={
                    "image_id": self.file_name
                })
            
            upvote_model = imager.models.VoteCounter.query.filter_by(
                image_file_id=self.file_name).one_or_none()
            self.assertIsNotNone(upvote_model)
            self.assertEqual(upvote_model.vote, 1)
            self.assertEqual(response.status_code, 200)
            self.assertIsInstance(response.json, dict)

    def test_logged_in_user_upvote_counter_invalid(self):
        with self.app.app_context():
            _ = self.client.post(
                "/auth/login",
                data={
                    "username_email": self.created_user_username,
                    "password": self.created_user_pwd,
                    "next": ""},
                follow_redirects=True)

            response = self.client.post(
                "/upvote",
                data={
                    "image_id": "invalid_file_id"
                })
            
            self.assertEqual(response.status_code, 400)
    
    def test_anon_user_downvote_counter_valid(self):
        with self.app.app_context():
            response = self.client.post(
                "/downvote",
                data={
                    "image_id": self.file_name
                })
            self.assertEqual(response.status_code, 302)

    def test_logged_in_user_downvote_counter_valid(self):
        with self.app.app_context():
            _ = self.client.post(
                "/auth/login",
                data={
                    "username_email": self.created_user_username,
                    "password": self.created_user_pwd,
                    "next": ""},
                follow_redirects=True)

            response = self.client.post(
                "/downvote",
                data={
                    "image_id": self.file_name
                }
            )
            downvote_model = imager.models.VoteCounter.query.filter_by(
                image_file_id=self.file_name).one_or_none()
            self.assertIsNotNone(downvote_model)
            self.assertEqual(downvote_model.vote, -1)
            self.assertEqual(response.status_code, 200)
            self.assertIsInstance(response.json, dict)

    def test_logged_in_user_downvote_counter_invalid(self):
        with self.app.app_context():
            _ = self.client.post(
                "/auth/login",
                data={
                    "username_email": self.created_user_username,
                    "password": self.created_user_pwd,
                    "next": ""},
                follow_redirects=True)

            response = self.client.post(
                "/downvote",
                data={
                    "image_id": "invalid_image_id"
                }
            )
            self.assertEqual(response.status_code, 400)

    def test_vote_metric_valid(self):
        with self.app.app_context():
            response = self.client.get(f"/metric/{self.file_name}")
            self.assertEqual(response.status_code, 200)
            self.assertIsInstance(response.json, dict)

    def test_vote_metric_invalid(self):
        with self.app.app_context():
            response = self.client.get(f"/metric/does_not_exist")
            self.assertEqual(response.status_code, 400)

if __name__ == "__main__":
    unittest.main()

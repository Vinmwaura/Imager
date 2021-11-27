from .. import db
from sqlalchemy.sql import func


class UserContent(db.Model):
    __tablename__ = "user_content"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False)
    content_location = db.Column(
        db.String(100),
        nullable=False)
    profile_pic = db.relationship(
        "ProfileImages",
        back_populates="user_content",
        uselist=False)  # One-to-one relationship

    def __repr__(self):
        return "<UserContent %s>" % self.id


class ImageContent(db.Model):
    __tablename__ = "image_content"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_content_id = db.Column(
        db.Integer,
        db.ForeignKey('user_content.id'))
    file_location = db.Column(
        db.String(100),
        nullable=False)
    image_name = db.Column(db.String(20), nullable=False)
    image_desc = db.Column(db.String(100))
    upload_time = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now())
    tags = db.relationship(
        "ImageTags",
        back_populates="image_content",
        uselist=False)  # One-to-one relationship

    def __repr__(self):
        return "<ImageContent %s>" % self.id


class ImageTags(db.Model):
    __tablename__ = "image_tags"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    image_id = db.Column(db.Integer, db.ForeignKey("image_content.id"))
    tag_1 = db.Column(db.String(20), nullable=True)
    tag_2 = db.Column(db.String(20), nullable=True)
    tag_3 = db.Column(db.String(20), nullable=True)
    tag_4 = db.Column(db.String(20), nullable=True)
    tag_5 = db.Column(db.String(20), nullable=True)
    tag_6 = db.Column(db.String(20), nullable=True)
    tag_7 = db.Column(db.String(20), nullable=True)
    tag_8 = db.Column(db.String(20), nullable=True)


class ProfileImages(db.Model):
    __tablename__ = "profile_images"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_content_id = db.Column(
        db.Integer,
        db.ForeignKey('user_content.id'))
    file_location = db.Column(
        db.String(100),
        nullable=False)

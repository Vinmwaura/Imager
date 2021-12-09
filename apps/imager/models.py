from .. import db
from sqlalchemy.sql import func

from enum import Enum


class VoteEnum(Enum):
    DOWNVOTE = -1
    UPVOTE = 1


class VoteCounter(db.Model):
    __tablename__ = "vote_counter"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False)
    image_file_id = db.Column(
        db.String(50),
        db.ForeignKey('image_content.file_id'))
    vote = db.Column(
        db.Integer,
        nullable=False)

    def get_image_vote(self, file_id):
        vote_counter = self.query.filter_by(
            image_file_id=file_id).first() or None
        if vote_counter:
            return vote_counter.vote
        else:
            return None

    def __repr__(self):
        return "<VoteCounter %s>" % self.id


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
        backref="user_content",
        uselist=False)  # One-to-one relationship

    user = db.relationship(
        "User",
        backref="user_content",
        uselist=False)

    def __repr__(self):
        return "<UserContent %s>" % self.id


class ImageContent(db.Model):
    __tablename__ = "image_content"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_content_id = db.Column(
        db.Integer,
        db.ForeignKey('user_content.id'))
    file_id = db.Column(
        db.String(50),
        unique=True,
        nullable=False)
    file_location = db.Column(
        db.String(100))
    title = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    upload_time = db.Column(
        db.DateTime(timezone=True),
        server_default=func.utcnow())

    tags = db.relationship(
        "ImageTags",
        backref="image_content")

    user_content = db.relationship(
        "UserContent",
        backref="image_content")

    def __repr__(self):
        return "<ImageContent %s>" % self.id


class Tags(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tag_name = db.Column(
        db.String(20),
        unique=True,
        nullable=False)

    def __repr__(self):
        return "<ImageTags %s>" % self.tag_name


class ImageTags(db.Model):
    __tablename__ = "image_tags"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tag_id = db.Column(
        db.Integer,
        db.ForeignKey('tags.id'))
    image_content_id = db.Column(
        db.Integer,
        db.ForeignKey('image_content.id'))

    def __repr__(self):
        return "<ImageTags %s>" % self.id


class ProfileImages(db.Model):
    __tablename__ = "profile_images"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_content_id = db.Column(
        db.Integer,
        db.ForeignKey('user_content.id'))
    file_id = db.Column(
        db.String(100),
        nullable=False)

    def __repr__(self):
        return "<ProfileImages %s>" % self.id

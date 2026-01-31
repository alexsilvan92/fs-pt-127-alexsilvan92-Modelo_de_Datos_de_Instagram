from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime, String, Boolean, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

db = SQLAlchemy()


class MediaType(enum.Enum):
    photo = "photo"
    video = "video"
    gif = "gif"


class User(db.Model):
    __tablename__ = "user"

    # Identificador único del usuario
    id: Mapped[int] = mapped_column(primary_key=True)

    # Datos básicos
    username: Mapped[str] = mapped_column(
        String(120), unique=True, nullable=False)
    
    email: Mapped[str] = mapped_column(
        String(120), unique=True, nullable=False)
    
    firstname: Mapped[str] = mapped_column(String(120), nullable=False)

    lastname: Mapped[str] = mapped_column(String(120), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    # Un usuario puede tener muchos posts
    posts: Mapped[list["Post"]] = relationship(
        "Post",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # Un usuario puede escribir muchos comentarios
    comments: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="author",
        cascade="all, delete-orphan"
    )

    # Usuarios a los que este usuario sigue
    following: Mapped[list["Follower"]] = relationship(
        "Follower",
        foreign_keys="Follower.user_from_id",    # obligatorio cuando hay 2 FK a la misma tabla
        back_populates="user_from",
        cascade="all, delete-orphan"
    )

    # Usuarios que siguen a este usuario
    followers: Mapped[list["Follower"]] = relationship(
        "Follower",
        foreign_keys="Follower.user_to_id",    # obligatorio cuando hay 2 FK a la misma tabla
        back_populates="user_to",
        cascade="all, delete-orphan"
    )

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def serialize_with_counts(self):
        data = self.serialize()
        data["posts_count"] = len(self.posts)
        data["followers_count"] = len(self.followers)
        data["following_count"] = len(self.following)
        return data


class Follower(db.Model):
    __tablename__ = "follower"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Usuario_Id que sigue
    user_from_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"), nullable=False)
    
    # Usuario_Id seguido
    user_to_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"), nullable=False)

    # Usuario que sigue
    user_from: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_from_id],    # obligatorio cuando hay 2 FK a la misma tabla
        back_populates="following"
    )

    # Usuario seguido
    user_to: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_to_id],    # obligatorio cuando hay 2 FK a la misma tabla
        back_populates="followers"
    )

    def serialize(self):
        return {
            "id": self.id,
            "user_from_id": self.user_from_id,
            "user_to_id": self.user_to_id
        }


class Post(db.Model):
    __tablename__ = "post"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_to_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"), nullable=False)

    # Usuario propietario del post
    user: Mapped["User"] = relationship(
        "User",
        back_populates="posts"
    )

    # Un post puede tener muchos medias
    media: Mapped[list["Media"]] = relationship(
        "Media",
        back_populates="post",
        cascade="all, delete-orphan"
    )

    # Un post puede tener muchos comentarios
    comments: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="post",
        cascade="all, delete-orphan"
    )

    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_to_id
        }

    def serialize_full(self):
        data = self.serialize()
        data["media"] = [media.serialize() for media in self.media]
        data["comments_count"] = len(self.comments)
        data["comments"] = [comment.serialize() for comment in self.comments]
        return data


class Media(db.Model):
    __tablename__ = "media"

    id: Mapped[int] = mapped_column(primary_key=True)

    type: Mapped[MediaType] = mapped_column(
        Enum(
            MediaType,
            name="media_type_enum",
            create_type=False
        ),
        nullable=False
    )

    url: Mapped[str] = mapped_column(String(255), nullable=False)

    post_id: Mapped[int] = mapped_column(ForeignKey("post.id"), nullable=False)

    # La media pertenece a un único post
    post: Mapped["Post"] = relationship(
        "Post",
        back_populates="media"
    )

    def serialize(self):
        return {
            "id": self.id,
            "type": self.type.value,  # Enum → string
            "url": self.url,
            "post_id": self.post_id
        }


class Comment(db.Model):
    __tablename__ = "comment"

    id: Mapped[int] = mapped_column(primary_key=True)

    comment_text: Mapped[str] = mapped_column(String(999), nullable=False)

    author_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"), nullable=False)
    
    post_id: Mapped[int] = mapped_column(ForeignKey("post.id"), nullable=False)

    # Usuario que escribe el comentario
    author: Mapped["User"] = relationship(
        "User",
        back_populates="comments"
    )

    # Post comentado
    post: Mapped["Post"] = relationship(
        "Post",
        back_populates="comments"
    )

    def serialize(self):
        return {
            "id": self.id,
            "comment_text": self.comment_text,
            "author_id": self.author_id,
            "post_id": self.post_id
        }

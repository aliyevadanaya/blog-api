from django.db.models import (
    CASCADE,
    SET_NULL,
    CharField,
    DateTimeField,
    ForeignKey,
    ManyToManyField,
    Model,
    SlugField,
    TextChoices,
    TextField,
)

from apps.auths.models import CustomUser


class Category(Model):
    """Categories database table"""
    
    NAME_MAX_LEN = 100
    
    name = CharField(
        max_length=NAME_MAX_LEN,
    )
    slug = SlugField(
        unique=True
    )
    

class Tag(Model):
    """Tags database table"""
    
    NAME_MAX_LEN = 100
    
    name = CharField(
        max_length=NAME_MAX_LEN,
    )
    slug = SlugField(
        unique=True,
    )
    
    
class Post(Model):
    """Posts database table"""
    
    TITLE_MAX_LEN = 200
    
    author = ForeignKey(
        to=CustomUser,
        on_delete=CASCADE,
    )
    title = CharField(
        max_length=200,
    )
    slug = SlugField(
        unique=True,
    )
    body = TextField()
    category = ForeignKey(
        to=Category,
        on_delete=SET_NULL,
        null=True,
    )
    tags = ManyToManyField(
        to=Tag,
        blank=True,
    )
    
    class Status(TextChoices):
        """Text choices for status field"""
        
        DRAFT = 'draft'
        PUBLISHED = 'published'
        
    status = CharField(
        choices=Status.choices,
    )
    created_at = DateTimeField(
        auto_created=True,
    )
    updated_at = DateTimeField(
        auto_now=True
    )
    
    
class Comment(Model):
    """Comments database table"""
    
    post = ForeignKey(
        to=Post,
        on_delete=CASCADE,
    )
    author = ForeignKey(
        to=CustomUser,
        on_delete=CASCADE,
    )
    body = TextField()
    created_at = DateTimeField(
        auto_created=True
    )
    
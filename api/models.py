from datetime import date

from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from rest_framework.exceptions import ValidationError


class User(AbstractUser):
    class RoleChoices(models.TextChoices):
        USER = "user", "user"
        MODERATOR = "moderator", "moderator"
        ADMIN = "admin", "admin"

    is_active = models.BooleanField(default=False)
    email = models.EmailField(max_length=60, unique=True)
    bio = models.CharField(max_length=200, blank=True)
    role = models.CharField(
        max_length=30, choices=RoleChoices.choices, default=RoleChoices.USER
    )

    def save(self, *args, **kwargs):
        self.is_active = True
        if self.role == "moderator":
            self.is_staff = True
        if self.role == "admin":
            self.is_superuser = True
        super(User, self).save(*args, **kwargs)


def validate_date(value):
    current_year = int(date.today().year)
    if value > current_year or value <= 0:
        raise ValidationError('Wrong date!')


class Category(models.Model):
    name = models.TextField('название', blank=False, max_length=150)
    slug = models.SlugField('slug', blank=False, unique=True, db_index=True)

    def __str__(self):
        return self.name[0:10]


class Genre(models.Model):
    name = models.TextField('название', blank=False, max_length=150)
    slug = models.SlugField('slug', blank=False, unique=True, db_index=True)

    def __str__(self):
        return self.name[0:10]


class Title(models.Model):
    name = models.TextField(
        'название',
        blank=False,
        max_length=200,
        db_index=True
    )
    year = models.IntegerField('год', blank=True, validators=[validate_date])
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='titles',
        verbose_name='категория'
    )
    genre = models.ManyToManyField(
        Genre,
        blank=True,
        db_index=True,
        related_name='titles',
        verbose_name='жанр'
    )
    description = models.CharField(
        'описание',
        max_length=200,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name[0:10]


class Review(models.Model):
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    text = models.TextField()
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    pub_date = models.DateTimeField(
        'date published', auto_now_add=True, blank=True
    )

    class Meta:
        ordering = ('-pub_date',)


class Comment(models.Model):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField()
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    pub_date = models.DateTimeField(
        'date published', auto_now_add=True, blank=True
    )

    class Meta:
        ordering = ('-pub_date',)

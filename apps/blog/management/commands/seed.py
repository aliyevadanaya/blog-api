import random
import time
from typing import Any

from faker import Faker

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils.text import slugify

from apps.auths.models import CustomUser
from apps.blog.models import Category, Comment, Post, Tag

DEFAULT_USERS = 20
DEFAULT_POSTS = 100
DEFAULT_COMMENTS = 500
TITLE_WORDS = 6
BODY_PARAGRAPHS = 3
MIN_POST_TAGS = 0
MAX_POST_TAGS = 5
MIN_COMMENT_SENTENCES = 1
MAX_COMMENT_SENTENCES = 3
FIRST_UNIQUE_SUFFIX = 2

SEED_PASSWORD = "qwerty1234!"

INACTIVE_USER_RATE = 0.1
STAFF_USER_RATE = 0.05
PUBLISHED_POST_RATE = 0.7
NO_CATEGORY_RATE = 0.1

CATEGORIES = [
    "Python",
    "Django",
    "DevOps",
    "Java",
    "Spring",
    "PhP",
    "Angular",
    "React",
]

TAGS = [
    "API",
    "Docker",
    "PostgreSQL",
    "MySQL",
    "Git",
    "Backend",
    "Frontend",
    "Testing",
    "Deployment",
    "HTML",
    "CSS",
    "JavaScript",
    "Linux",
    "Microservices",
    "AI / Machine Learning",
    "Redis",
    "Go",
    "Fullstack",
    "MongoDB",
    "Security",
]


class Command(BaseCommand):
    help = "Fill the database with fake data."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--users",
            type=int,
            default=DEFAULT_USERS,
            help="Number of users to create",
        )
        parser.add_argument(
            "--posts",
            type=int,
            default=DEFAULT_POSTS,
            help="Number of posts to create",
        )
        parser.add_argument(
            "--comments",
            type=int,
            default=DEFAULT_COMMENTS,
            help="Number of comments to create",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing data before seeding",
        )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        started_at = time.perf_counter()

        users_count = options["users"]
        posts_count = options["posts"]
        comments_count = options["comments"]
        clear = options["clear"]

        if users_count < 0 or posts_count < 0 or comments_count < 0:
            raise CommandError("Number can't be negative.")

        if (posts_count > 0 or comments_count > 0) and users_count == 0:
            existing_users = CustomUser.objects.exists()
            if not existing_users:
                raise CommandError("Can't create posts or comments without users.")

        if clear:
            Comment.objects.all().delete()
            Post.objects.all().delete()
            Tag.objects.all().delete()
            Category.objects.all().delete()
            CustomUser.objects.filter(is_superuser=False).delete()

        fake = Faker()

        categories_created = 0
        categories = []

        for name in CATEGORIES:
            category, created = Category.objects.get_or_create(
                slug=slugify(name),
                defaults={"name": name},
            )
            categories.append(category)

            if created:
                categories_created += 1

        tags_created = 0
        tags = []

        for name in TAGS:
            tag, created = Tag.objects.get_or_create(
                slug=slugify(name),
                defaults={"name": name},
            )
            tags.append(tag)

            if created:
                tags_created += 1

        existing_emails = set(CustomUser.objects.values_list("email", flat=True))

        new_users = []
        hashed_password = make_password(SEED_PASSWORD)

        for _ in range(users_count):
            first_name = fake.first_name()
            last_name = fake.last_name()

            email_base = f"{slugify(first_name)}.{slugify(last_name)}"

            email = f"{email_base}@example.com"
            suffix = FIRST_UNIQUE_SUFFIX

            while email in existing_emails:
                email = f"{email_base}{suffix}@example.com"
                suffix += 1

            existing_emails.add(email)

            new_users.append(
                CustomUser(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=hashed_password,
                    is_active=random.random() >= INACTIVE_USER_RATE,
                    is_staff=random.random() < STAFF_USER_RATE,
                )
            )

        if new_users:
            CustomUser.objects.bulk_create(new_users)

        users = list(CustomUser.objects.all())

        if (posts_count > 0 or comments_count > 0) and not users:
            raise CommandError("Can't create posts or comments without users.")

        used_slugs = set(Post.objects.values_list("slug", flat=True))
        slug_max_length = Post._meta.get_field("slug").max_length

        new_posts = []

        for _ in range(posts_count):
            title = fake.sentence(nb_words=TITLE_WORDS).rstrip(".")
            base_slug = slugify(title)[:slug_max_length].rstrip("-")

            if not base_slug:
                base_slug = "post"

            slug = base_slug
            suffix = FIRST_UNIQUE_SUFFIX

            while slug in used_slugs:
                ending = f"-{suffix}"
                slug = f"{base_slug[: slug_max_length - len(ending)]}{ending}"
                suffix += 1

            used_slugs.add(slug)

            category = (
                None
                if random.random() < NO_CATEGORY_RATE
                else random.choice(categories)
            )

            status = (
                Post.Status.PUBLISHED
                if random.random() < PUBLISHED_POST_RATE
                else Post.Status.DRAFT
            )

            new_posts.append(
                Post(
                    author=random.choice(users),
                    title=title,
                    slug=slug,
                    body="\n\n".join(fake.paragraphs(nb=BODY_PARAGRAPHS)),
                    category=category,
                    status=status,
                )
            )

        if new_posts:
            Post.objects.bulk_create(new_posts)

        created_posts = list(
            Post.objects.filter(slug__in=[post.slug for post in new_posts])
        )

        for post in created_posts:
            selected_tags = random.sample(
                tags,
                k=random.randint(MIN_POST_TAGS, min(MAX_POST_TAGS, len(tags))),
            )
            post.tags.set(selected_tags)

        published_posts = list(Post.objects.filter(status=Post.Status.PUBLISHED))

        if comments_count > 0 and not published_posts:
            raise CommandError("Can't create comments: there are no published posts.")

        new_comments = []

        for _ in range(comments_count):
            sentences = fake.sentences(
                nb=random.randint(MIN_COMMENT_SENTENCES, MAX_COMMENT_SENTENCES)
            )

            new_comments.append(
                Comment(
                    post=random.choice(published_posts),
                    author=random.choice(users),
                    body=" ".join(sentences),
                )
            )

        if new_comments:
            Comment.objects.bulk_create(new_comments)

        elapsed_time = time.perf_counter() - started_at

        self.stdout.write(
            self.style.SUCCESS(
                f"Users: {len(new_users)} created\n"
                f"Categories: {categories_created} created\n"
                f"Tags: {tags_created} created\n"
                f"Posts: {len(new_posts)} created\n"
                f"Comments: {len(new_comments)} created\n"
                f"Shared test password: {SEED_PASSWORD}\n"
                f"Done in: {elapsed_time:.2f} seconds"
            )
        )

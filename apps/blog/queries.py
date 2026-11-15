from datetime import date, timedelta
from typing import Any

from apps.blog.models import Category, Comment, Post, Tag
from django.contrib.auth import get_user_model
from django.db.models import (
    Avg,
    Case,
    CharField,
    Count,
    Exists,
    F,
    Max,
    Min,
    OuterRef,
    Prefetch,
    Q,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Coalesce, Concat, TruncMonth
from django.db.models.query import QuerySet
from django.utils import timezone
from django.utils.text import slugify

NEWEST_POSTS_LIMIT = 5
PAGE_SIZE = 10
HOUR_LIMIT = 1
UNCATEGORIZED_NAME = "Uncategorized"
POPULARITY_HOT_LIMIT = 10
POPULARITY_NORMAL_LIMIT = 3
PUBLISHED_FEED_LIMIT = 50
NEWEST_TAGGED_POSTS_LIMIT = 20

User = get_user_model()

def categories_by_name() -> QuerySet[Category]:
    """Return all categories sorted by name."""
    return Category.objects.order_by("name")

def published_posts() -> QuerySet[Post]:
    """Return published posts, newest first."""
    return Post.objects.filter(
        status=Post.Status.PUBLISHED
    ).order_by("-created_at")
    
def newest_published_posts() -> QuerySet[Post]:
    """Return the five newest published posts."""
    return published_posts()[:NEWEST_POSTS_LIMIT]

def post_by_slug(slug: str) -> Post | None:
    """Return a post by slug or None if it doesn't exist."""
    return Post.objects.filter(slug=slug).first()
    
def active_users_count() -> int:
    """Count active users who are not staff."""
    return User.objects.filter(is_active=True, is_staff=False).count()

def has_drafts() -> bool:
    """Check at least one draft exists."""
    return Post.objects.filter(status=Post.Status.DRAFT).exists()

def published_posts_page(page: int) -> QuerySet[Post]:
    """Return one page of published posts, newest first."""
    start = (page - 1) * PAGE_SIZE
    return published_posts()[start:start + PAGE_SIZE]

def posts_with_word_in_title(word: str) -> QuerySet[Post]:
    """Find posts whose title contain the given word."""
    return Post.objects.filter(title__icontains=word)

def users_with_email_domain(domain: str) -> QuerySet:
    """Find users whose email ends with the given domain."""
    return User.objects.filter(email__iendswith=f"@{domain}")

def posts_without_category() -> QuerySet[Post]:
    """Return posts that don't have a category."""
    return Post.objects.filter(category__isnull=True)

def categories_by_slugs(slugs: list[str]) -> QuerySet[Category]:
    """Return categories whose slugs are in the given list."""
    return Category.objects.filter(slug__in=slugs)
    
def posts_in_month(year: int, month: int) -> QuerySet[Post]:
    """Return posts created during specified month and year."""
    return Post.objects.filter(created_at__year=year, created_at__month=month)

def posts_last_days(days: int) -> QuerySet[Post]:
    """Return posts created during the last given number of days."""
    cutoff = timezone.now() - timedelta(days=days)
    return Post.objects.filter(created_at__gte=cutoff)  

def posts_between(start: date, end: date) -> QuerySet[Post]:
    """Returns posts created between two dates, including both days."""
    return Post.objects.filter(
        created_at__date__gte=start,
        created_at__date__lte=end,
    )
    
def author_published_posts(email: str) -> QuerySet[Post]:
    """Return published posts writteen by the specified author."""
    return Post.objects.filter(
        author__email__iexact=email,
        status=Post.Status.PUBLISHED,
    )
    
def posts_with_tag(tag_slug: str) -> QuerySet[Post]:
    """Return posts that have a tag with the specified slug."""
    return Post.objects.filter(tags__slug=tag_slug).distinct()

def comments_in_category(category_slug: str) -> QuerySet[Comment]:
    """Return comments on posts belonging to the specified category."""
    return Comment.objects.filter(post__category__slug=category_slug)

def users_with_published_posts() -> QuerySet:
    """Return users who has at least one published posts."""
    published_posts_subquery = Post.objects.filter(
        author=OuterRef("pk"),
        status=Post.Status.PUBLISHED,
    )
    return User.objects.filter(Exists(published_posts_subquery))

def posts_without_tags() -> QuerySet[Post]:
    """Return posts that don't have any tags"""
    return Post.objects.filter(tags__isnull=True)

def users_without_comments() -> QuerySet:
    """Return users who have never written a comment."""
    user_comments = Comment.objects.filter(author=OuterRef("pk"))
    return User.objects.filter(~Exists(user_comments))

def posts_with_both_tags(first_slug: str, second_slug: str) -> QuerySet[Post]:
    """Return posts that have both specified tags."""
    return Post.objects.filter(tags__slug=first_slug).filter(tags__slug=second_slug).distinct()

def search_posts(text: str) -> QuerySet[Post]:
    """Find posts containing text in their title or body."""
    return Post.objects.filter(
        Q(title__icontains=text) | Q(body__icontains=text)
    )
    
def published_posts_missing_info() -> QuerySet[Post]:
    """Return published posts that don't have any tags or a category."""
    return Post.objects.filter(
        Q(category__isnull=True) | Q(tags__isnull=True),
        status=Post.Status.PUBLISHED,
    ).distinct()
    
def edited_posts() -> QuerySet[Post]:
    """Return posts edited more than one hour after creation."""
    return Post.objects.filter(
        updated_at__gt=F("created_at") + timedelta(hours=HOUR_LIMIT)
    )
    
def comments_by_post_author() -> QuerySet[Comment]:
    """Return comments written by the author of the commented post."""
    return Comment.objects.filter(author_id=F("post__author_id"))

def comments_before_post() -> QuerySet[Comment]:
    """Return comments created before their post was created."""
    return Comment.objects.filter(created_at__lt=F("post__created_at"))

def published_authors_emails() -> list[str]:
    """Return unique emails of published post authors, sorted A to Z."""
    return list(
        User.objects.filter(post__status=Post.Status.PUBLISHED)
        .values_list("email", flat=True)
        .distinct()
        .order_by("email")
    )
    
def published_posts_overview() -> list[dict[str, Any]]:
    """Return a compact overview of published posts."""
    return list(
        Post.objects.filter(status=Post.Status.PUBLISHED)
        .annotate(
            author_email=F("author__email"),
            category_name=Coalesce(
                "category__name",
                Value(UNCATEGORIZED_NAME),
                output_field=CharField(),
            ),
        )
        .values("title", "author_email", "category_name")
    )
    
def posts_stats() -> dict[str, Any]:
    """Return total, published, draft, first and last post statistics."""
    return Post.objects.aggregate(
        total=Count("id"),
        published=Count("id", filter=Q(status=Post.Status.PUBLISHED)),
        drafts=Count("id", filter=Q(status=Post.Status.DRAFT)),
        first_post_at=Min("created_at"),
        last_post_at=Max("created_at"),
    )
    
def average_comments_per_post() -> float:
    """Return the average comment count per published post."""
    result = (
        Post.objects.filter(status=Post.Status.PUBLISHED)
        .annotate(comment_count=Count("comment"))
        .aggregate(average=Avg("comment_count"))
    )
    return float(round(result["average"] or 0, 2))

def categories_with_post_count() -> QuerySet[Category]:
    """Return categories annotated with their total post count."""
    return Category.objects.annotate(
        post_count=Count("post", distinct=True)
    ).order_by("-post_count", "name")
    
def categories_with_published_count() -> QuerySet[Category]:
    """Return all categories with their published post count."""
    return Category.objects.annotate(
        published_count=Count(
            "post",
            filter=Q(post__status=Post.Status.PUBLISHED),
            distinct=True,
        )
    ).order_by("-published_count", "name")
    
def top_authors() -> QuerySet:
    """Return the five users with the most published posts."""
    return User.objects.annotate(
        published_count=Count(
            "post",
            filter=Q(post__status=Post.Status.PUBLISHED),
            distinct=True,
        )
    ).order_by("-published_count", "email")[:NEWEST_POSTS_LIMIT]
    
def popular_tags(min_posts: int) -> QuerySet[Tag]:
    """Return tags used in at least the specified number of posts."""
    return Tag.objects.annotate(
        post_count=Count("post", distinct=True)
    ).filter(post_count__gte=min_posts).order_by("-post_count", "name")
    
def posts_per_status() -> list[dict[str, Any]]:
    """Return the number of posts grouped by status."""
    return list(
        Post.objects.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )
    
def users_activity() -> QuerySet:
    """Return users annotated with their post and comment counts."""
    return User.objects.annotate(
        post_count=Count("post", distinct=True),
        comment_count=Count("comment", distinct=True),
    ).order_by("email")
    
def search_users_by_full_name(text: str) -> QuerySet:
    """Find users by their full name and annotate full name."""
    return User.objects.annotate(
        full_name=Concat(
            "first_name",
            Value(" "),
            "last_name",
            output_field=CharField(),
        )
    ).filter(full_name__icontains=text)
    
def published_posts_per_month() -> list[dict[str, Any]]:
    """Return the number of published posts grouped by month."""
    return list(
        Post.objects.filter(status=Post.Status.PUBLISHED)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )
    
def posts_with_popularity() -> QuerySet[Post]:
    """Return posts with comment counts and popularity labels."""
    return Post.objects.annotate(
        comment_count=Count("comment", distinct=True)
    ).annotate(
        popularity=Case(
            When(comment_count__gte=POPULARITY_HOT_LIMIT, then=Value("hot")),
            When(comment_count__gte=POPULARITY_NORMAL_LIMIT, then=Value("normal")),
            default=Value("quiet"),
            output_field=CharField(),
        )
    )

def get_or_create_tag(name: str) -> tuple[Tag, bool]:
    """Return an existing tag or create it using a slug from its name."""
    return Tag.objects.get_or_create(
        slug=slugify(name),
        defaults={"name": name},
    )
    
def publish_old_drafts(days: int) -> int:
    """Publish drafts older than the specified number of days."""
    now = timezone.now()
    cutoff = now - timedelta(days=days)
    return Post.objects.filter(
        status=Post.Status.DRAFT,
        created_at__lt=cutoff,
    ).update(status=Post.Status.PUBLISHED, updated_at=now)
    
def tag_category_posts(category_slug: str, tag_slug: str) -> int:
    """Add the specified tag to every post in a category."""
    posts = list(Post.objects.filter(category__slug=category_slug))
    tag = Tag.objects.get(slug=tag_slug)
    if posts:
        tag.post_set.add(*posts)
    return len(posts)

def merge_categories(source_slug: str, target_slug: str) -> int:
    """Move posts from one category to another and delete the source."""
    source = Category.objects.get(slug=source_slug)
    target = Category.objects.get(slug=target_slug)
    
    if source.pk == target.pk:
        return 0
    
    moved_count = Post.objects.filter(category=source).update(category=target)
    source.delete()
    return moved_count

def delete_inactive_users_comments() -> int:
    """Delete comments written by inactive users."""
    deleted_count, _ = Comment.objects.filter(author__is_active=False).delete()
    return deleted_count

def published_feed() -> list[str]:
    """Return the 50 newest published posts as formatted text lines."""
    posts = (
        Post.objects.filter(status=Post.Status.PUBLISHED)
        .select_related("author", "category")
        .order_by("-created_at")[:PUBLISHED_FEED_LIMIT]
    )
    return [
        (
            f"{post.title} | {post.author.email} | "
            f"{post.category.name if post.category else UNCATEGORIZED_NAME}"
        )
        for post in posts
    ]
    
def newest_posts_with_tags() -> list[str]:
    """Return the 20 newest posts with their tag names."""
    posts = (
        Post.objects.order_by("-created_at")
        .prefetch_related(
            Prefetch("tags", queryset=Tag.objects.order_by("name"))
        )[:NEWEST_TAGGED_POSTS_LIMIT]
    )
    return [
        f"{post.title}: {', '.join(tag.name for tag in post.tags.all())}"
        for post in posts
    ]
    
def categories_with_published_posts() -> dict[str, list[str]]:
    """Return each category with titles of its published posts."""
    categories = Category.objects.prefetch_related(
        Prefetch(
            "post_set",
            queryset=Post.objects.filter(
                status=Post.Status.PUBLISHED
            ).order_by("-created_at"),
            to_attr="published_posts",
        )
    )
    return {
        category.name: [post.title for post in category.published_posts]
        for category in categories
    }
    
def posts_with_last_comment() -> QuerySet[Post]:
    """Return published posts annotated with their newest comment body."""
    latest_comment = Comment.objects.filter(
        post=OuterRef("pk")
    ).order_by("-created_at")
    return Post.objects.filter(
        status=Post.Status.PUBLISHED
    ).annotate(
        last_comment=Subquery(latest_comment.values("body")[:1])
    )
    
def posts_with_staff_comments() -> QuerySet[Post]:
    """Return posts that  have at least one comment from a staff user."""
    staff_comments = Comment.objects.filter(
        post=OuterRef("pk"),
        author__is_staff=True,
    )
    return Post.objects.filter(Exists(staff_comments))

def users_with_draft_as_latest_post() -> QuerySet:
    """Returns users whose newest post is a draft."""
    latest_post = Post.objects.filter(
        author=OuterRef("pk")
    ).order_by("-created_at")
    return User.objects.annotate(
        latest_post_status=Subquery(latest_post.values("status")[:1])
    ).filter(latest_post_status=Post.Status.DRAFT)
    

QUERIES = {
    1: categories_by_name,
    2: published_posts,
    3: newest_published_posts,
    4: post_by_slug,
    5: active_users_count,
    6: has_drafts,
    7: published_posts_page,
    8: posts_with_word_in_title,
    9: users_with_email_domain,
    10: posts_without_category,
    11: categories_by_slugs,
    12: posts_in_month,
    13: posts_last_days,
    14: posts_between,
    15: author_published_posts,
    16: posts_with_tag,
    17: comments_in_category,
    18: users_with_published_posts,
    19: posts_without_tags,
    20: users_without_comments,
    21: posts_with_both_tags,
    22: search_posts,
    23: published_posts_missing_info,
    24: edited_posts,
    25: comments_by_post_author,
    26: comments_before_post,
    27: published_authors_emails,
    28: published_posts_overview,
    29: posts_stats,
    30: average_comments_per_post,
    31: categories_with_post_count,
    32: categories_with_published_count,
    33: top_authors,
    34: popular_tags,
    35: posts_per_status,
    36: users_activity,
    37: search_users_by_full_name,
    38: published_posts_per_month,
    39: posts_with_popularity,
    40: get_or_create_tag,
    41: publish_old_drafts,
    42: tag_category_posts,
    43: merge_categories,
    44: delete_inactive_users_comments,
    45: published_feed,
    46: newest_posts_with_tags,
    47: categories_with_published_posts,
    48: posts_with_last_comment,
    49: posts_with_staff_comments,
    50: users_with_draft_as_latest_post,
}

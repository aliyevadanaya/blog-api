import json
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.aggregates import Count
from django.http import HttpRequest
from django.urls import reverse_lazy

from apps.blog.models import Category, Comment, Post

User = get_user_model()
TOP_AUTHORS_LIMIT = 5
PERCENTAGE_TOTAL = 100


def dashboard_callback(request: HttpRequest, context: dict[str, Any]) -> dict[str, Any]:
    users_count = User.objects.count()

    published_count = Post.objects.filter(status=Post.Status.PUBLISHED).count()

    drafts_count = Post.objects.filter(status=Post.Status.DRAFT).count()

    comments_count = Comment.objects.count()

    total_posts = published_count + drafts_count

    categories = Category.objects.annotate(
        posts_count=Count("post", distinct=True)
    ).order_by("-posts_count")

    category_labels = [category.name for category in categories]

    category_data = [category.posts_count for category in categories]

    chart_data = {
        "labels": category_labels,
        "datasets": [
            {
                "label": "Posts",
                "data": category_data,
            }
        ],
    }

    top_authors = (
        User.objects.annotate(posts_count=Count("post", distinct=True))
        .filter(posts_count__gt=0)
        .order_by("-posts_count")[:TOP_AUTHORS_LIMIT]
    )

    published_percentage = (
        round(published_count / total_posts * PERCENTAGE_TOTAL)
        if total_posts > 0
        else 0
    )

    drafts_percentage = (
        round(drafts_count / total_posts * PERCENTAGE_TOTAL) if total_posts > 0 else 0
    )

    context.update(
        {
            "users_count": users_count,
            "published_count": published_count,
            "drafts_count": drafts_count,
            "comments_count": comments_count,
            "chart_data": json.dumps(chart_data),
            "top_authors": top_authors,
            "published_percentage": published_percentage,
            "drafts_percentage": drafts_percentage,
        }
    )

    return context


def environment_callback(request: HttpRequest) -> tuple[str, str]:
    if settings.ENV_ID == "local":
        return "Local", "warning"
    return "Production", "danger"


def drafts_badge(request: HttpRequest) -> str:
    return str(Post.objects.filter(status=Post.Status.DRAFT).count())


def sidebar_navigation(request: HttpRequest) -> list[dict[str, Any]]:
    navigation = [
        {
            "title": "Overview",
            "items": [
                {
                    "title": "Dashboard",
                    "icon": "dashboard",
                    "link": reverse_lazy("admin:index"),
                }
            ],
        },
        {
            "title": "Content",
            "items": [
                {
                    "title": "Posts",
                    "icon": "article",
                    "link": reverse_lazy("admin:blog_post_changelist"),
                    "badge": "apps.blog.callbacks.drafts_badge",
                },
                {
                    "title": "Comments",
                    "icon": "comment",
                    "link": reverse_lazy("admin:blog_comment_changelist"),
                },
                {
                    "title": "Categories",
                    "icon": "category",
                    "link": reverse_lazy("admin:blog_category_changelist"),
                },
                {
                    "title": "Tags",
                    "icon": "label",
                    "link": reverse_lazy("admin:blog_tag_changelist"),
                },
            ],
        },
    ]
    if request.user.is_superuser:
        navigation.append(
            {
                "title": "Users & Access",
                "items": [
                    {
                        "title": "Users",
                        "icon": "group",
                        "link": reverse_lazy("admin:auths_customuser_changelist"),
                    },
                    {
                        "title": "Groups",
                        "icon": "admin_panel_settings",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            }
        )
    return navigation

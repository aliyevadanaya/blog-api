from typing import Any

from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    AutocompleteSelectFilter,
    ChoicesDropdownFilter,
    MultipleRelatedDropdownFilter,
    RangeDateTimeFilter,
    RelatedDropdownFilter,
)
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.decorators import action, display
from unfold.sections import TableSection

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Prefetch, QuerySet, TextField
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse

from .models import Category, Comment, Post, Tag

COMMENT_PREVIEW_LENGTH = 60
COMMENTS_PER_PAGE = 10


class CategoryPostsSection(TableSection):
    verbose_name = "Posts"
    related_name = "post_set"
    fields = ("title", "author", "status", "created_at")


class PostCommentsSection(TableSection):
    verbose_name = "Comments"
    related_name = "comment_set"
    fields = ("author", "body", "created_at")


class CommentInline(TabularInline):
    model = Comment
    extra = 0
    fields = ("author", "body", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("author",)
    show_change_link = True
    per_page = COMMENTS_PER_PAGE
    tab = True
    ordering = ("created_at", "pk")


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    """Category model admin configuration class"""

    list_display = ("name", "slug", "posts_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    list_sections = (CategoryPostsSection,)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Category]:
        queryset = super().get_queryset(request)
        return queryset.annotate(
            posts_count=Count("post", distinct=True)
        ).prefetch_related(
            Prefetch("post_set", queryset=Post.objects.select_related("author"))
        )

    @display(description="Posts", ordering="posts_count")
    def posts_count(self, obj: Category) -> int:
        return obj.posts_count


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    """Tag model admin configuration class"""

    list_display = ("name", "slug", "posts_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request: HttpRequest) -> QuerySet[Tag]:
        queryset = super().get_queryset(request)
        return queryset.annotate(posts_count=Count("post", distinct=True))

    @display(description="Posts", ordering="posts_count")
    def posts_count(self, obj: Tag) -> int:
        return obj.posts_count


@admin.register(Post)
class PostAdmin(ModelAdmin):
    """Post model admin configuration class"""

    list_display = (
        "post_header",
        "colored_status",
        "category",
        "tags_display",
        "comments_count",
        "created_at",
    )
    list_filter = (
        ("status", ChoicesDropdownFilter),
        ("category", RelatedDropdownFilter),
        ("tags", MultipleRelatedDropdownFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    )
    list_filter_submit = True
    search_fields = ("title", "body", "author__email")
    autocomplete_fields = ("author", "category", "tags")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("author", "category")
    list_sections = (PostCommentsSection,)
    inlines = [CommentInline]
    actions = ("publish_posts", "move_to_drafts")
    actions_row = ("toggle_publication",)
    actions_list = ("publish_all_drafts",)
    actions_detail = ("open_comments",)
    actions_submit_line = ("save_and_publish",)
    warn_unsaved_form = True
    formfield_overrides = {TextField: {"widget": WysiwygWidget}}
    fieldsets = (
        (
            "Content",
            {
                "classes": ("tab",),
                "fields": ("title", "slug", "body"),
            },
        ),
        (
            "Classification",
            {
                "classes": ("tab",),
                "fields": ("category", "tags", "status"),
            },
        ),
        (
            "Meta",
            {
                "classes": ("tab",),
                "fields": ("author", "created_at", "updated_at"),
            },
        ),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Post]:
        queryset = super().get_queryset(request)
        return (
            queryset.annotate(comments_count=Count("comment", distinct=True))
            .select_related("author", "category")
            .prefetch_related(
                "tags",
                Prefetch(
                    "comment_set",
                    queryset=Comment.objects.select_related("author").order_by(
                        "created_at", "pk"
                    ),
                ),
            )
        )

    @display(description="Post", header=True, ordering="title")
    def post_header(self, obj: Post) -> tuple[str, str]:
        return obj.title, obj.author.email

    @display(
        description="Status",
        label={
            Post.Status.PUBLISHED: "success",
            Post.Status.DRAFT: "warning",
        },
    )
    def colored_status(self, obj: Post) -> tuple[str, str]:
        return obj.status, obj.get_status_display()

    @display(description="Tags", dropdown=True)
    def tags_display(self, obj: Post) -> dict[str, Any]:
        tags = obj.tags.all()
        return {
            "title": f"{len(tags)} tags",
            "items": [{"title": tag.name} for tag in tags],
        }

    @display(description="Comments", ordering="comments_count")
    def comments_count(self, obj: Post) -> int:
        return obj.comments_count

    @admin.action(description="Publish selected posts")
    def publish_posts(self, request: HttpRequest, queryset: QuerySet[Post]) -> None:
        queryset.update(status=Post.Status.PUBLISHED)

    @admin.action(description="Move selected posts to drafts")
    def move_to_drafts(self, request: HttpRequest, queryset: QuerySet[Post]) -> None:
        queryset.update(status=Post.Status.DRAFT)

    @action(description="Publish / unpublish", icon="publish", permissions=["change"])
    def toggle_publication(self, request: HttpRequest, object_id: str) -> HttpResponse:
        post = get_object_or_404(self.get_queryset(request), pk=object_id)
        if not self.has_change_permission(request, post):
            raise PermissionDenied
        status = (
            Post.Status.DRAFT
            if post.status == Post.Status.PUBLISHED
            else Post.Status.PUBLISHED
        )
        if request.method == "POST":
            post.status = status
            post.save(update_fields=["status", "updated_at"])
            return redirect("admin:blog_post_changelist")
        return TemplateResponse(
            request,
            "admin/blog/post/confirm_status.html",
            {
                **self.admin_site.each_context(request),
                "title": f"Move to {status}: {post.title}",
                "opts": self.model._meta,
            },
        )

    @action(description="Publish all drafts", icon="publish", permissions=["change"])
    def publish_all_drafts(self, request: HttpRequest) -> HttpResponse:
        if request.method == "POST":
            Post.objects.filter(status=Post.Status.DRAFT).update(
                status=Post.Status.PUBLISHED
            )
            return redirect("admin:blog_post_changelist")
        return TemplateResponse(
            request,
            "admin/blog/post/confirm_status.html",
            {
                **self.admin_site.each_context(request),
                "title": "Publish all drafts",
                "opts": self.model._meta,
            },
        )

    @action(description="Open comments", icon="comment", permissions=["view"])
    def open_comments(self, request: HttpRequest, object_id: str) -> HttpResponse:
        post = get_object_or_404(self.get_queryset(request), pk=object_id)
        return redirect(
            f"{reverse('admin:blog_comment_changelist')}?post__id__exact={post.pk}"
        )

    @action(description="Save & publish", icon="publish", permissions=["change"])
    def save_and_publish(self, request: HttpRequest, obj: Post) -> None:
        obj.status = Post.Status.PUBLISHED
        obj.save(update_fields=["status"])


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    """Comment model admin configuration class"""

    list_display = ("post", "author", "short_body", "created_at")
    list_filter = (
        ("post", AutocompleteSelectFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    )
    list_filter_submit = True
    search_fields = ("body", "author__email", "post__title")
    autocomplete_fields = ("post", "author")
    readonly_fields = ("created_at",)
    list_select_related = ("post", "author")

    @display(description="Comment")
    def short_body(self, obj: Comment) -> str:
        if len(obj.body) > COMMENT_PREVIEW_LENGTH:
            return f"{obj.body[:COMMENT_PREVIEW_LENGTH]}..."
        return obj.body

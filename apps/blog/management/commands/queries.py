from datetime import date, timedelta

from apps.blog import queries as query_functions
from apps.blog.models import Category, Comment, Post, Tag
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import connection, models
from django.db.models.query import QuerySet
from django.test.utils import CaptureQueriesContext


QUERIES = {
    1: "categories_by_name",
    2: "published_posts",
    3: "newest_published_posts",
    4: "post_by_slug",
    5: "active_users_count",
    6: "has_drafts",
    7: "published_posts_page",
    8: "posts_with_word_in_title",
    9: "users_with_email_domain",
    10: "posts_without_category",
    11: "categories_by_slugs",
    12: "posts_in_month",
    13: "posts_last_days",
    14: "posts_between",
    15: "author_published_posts",
    16: "posts_with_tag",
    17: "comments_in_category",
    18: "users_with_published_posts",
    19: "posts_without_tags",
    20: "users_without_comments",
    21: "posts_with_both_tags",
    22: "search_posts",
    23: "published_posts_missing_info",
    24: "edited_posts",
    25: "comments_by_post_author",
    26: "comments_before_post",
    27: "published_authors_emails",
    28: "published_posts_overview",
    29: "posts_stats",
    30: "average_comments_per_post",
    31: "categories_with_post_count",
    32: "categories_with_published_count",
    33: "top_authors",
    34: "popular_tags",
    35: "posts_per_status",
    36: "users_activity",
    37: "search_users_by_full_name",
    38: "published_posts_per_month",
    39: "posts_with_popularity",
    40: "get_or_create_tag",
    41: "publish_old_drafts",
    42: "tag_category_posts",
    43: "merge_categories",
    44: "delete_inactive_users_comments",
    45: "published_feed",
    46: "newest_posts_with_tags",
    47: "categories_with_published_posts",
    48: "posts_with_last_comment",
    49: "posts_with_staff_comments",
    50: "users_with_draft_as_latest_post",
}

MODIFYING_QUERIES = {40, 41, 42, 43, 44}

def get_sample_arguments() -> dict[int, dict]:
    """Prepare sample arguments for queries that require parameters."""
    
    User = get_user_model()
    
    post = Post.objects.first()
    published_posts = Post.objects.filter(status=Post.Status.PUBLISHED).first()
    
    user = User.objects.exclude(email="").first()
    
    categories = list(Category.objects.all())[:2]
    tags = list(Tag.objects.all())[:2]
    
    post_with_tag = (
        Post.objects.filter(tags__isnull=False).distinct().first()
    )
    
    category_with_comments = (
        Comment.objects.filter(post__category__isnull=False).values_list("post__category__slug", flat=True).first()
    )
    
    post_with_two_tags = (
        Post.objects.annotate(
            tag_count=models.Count("tags", distinct=True)
        ).filter(tag_count__gte=2).first()
    )
    
    if post_with_two_tags:
        two_tag_slugs = list(post_with_two_tags.tags.values_list("slug", flat=True)[:2])
    else:
        two_tag_slugs = [tag.slug for tag in tags]
        
    today = date.today()
    
    arguments = {
        4: {
            "slug": post.slug if post else "",
        },
        7: {
            "page": 1,
        },
        8: {
            "word": "Django",
        },
        9: {
            "domain": user.email.split("@")[-1] if user else "example.com",
        },
        11: {
            "slugs": [category.slug for category in categories],
        },
        12: {
            "year": today.year,
            "month": today.month,
        },
        13: {
            "days": 30,
        },
        14: {
            "start": today - timedelta(days=365),
            "end": today,
        },
        15: {
            "email": published_posts.author.email if published_posts else "",
        },
        16: {
            "tag_slug": (
                post_with_tag.tags.first().slug
                if post_with_tag and post_with_tag.tags.exists()
                else tags[0].slug if tags else ""
            ),
        },
        17: {
            "category_slug": category_with_comments or (categories[0].slug if categories else ""),
        },
        21: {
            "first_slug": two_tag_slugs[0] if len(two_tag_slugs) > 0 else "",
            "second_slug": two_tag_slugs[1] if len(two_tag_slugs) > 1 else "",
        },
        22: {
            "text": "Django",
        },
        34: {
            "min_posts": 1,
        },
        37: {
            "text": user.first_name if user else "",
        },
        40: {
            "name": "Test Tag",
        },
        41: {
            "days": 30,
        },
        42: {
            "category_slug": categories[0].slug if categories else "",
            "tag_slug": tags[0].slug if tags else "",
        },
        43: {
            "source_slug": categories[0].slug if len(categories) > 0 else "",
            "target_slug": categories[1].slug if len(categories) > 1 else "",
        },
    }
    
    return arguments

def print_result(result, output, limit: int = 5) -> None:
    """Print query results and total number of returned rows."""
    
    if isinstance(result, QuerySet):
        result = list(result)
        
    if isinstance(result, (list, tuple)):
        output.write(f"Total rows: {len(result)}")
        
        for index, item in enumerate(result[:limit], start=1):
            output.write(f"{index}. {item}")
            
        if len(result) > limit:
            output.write(f"... and {len(result) - limit} more rows")
            
    else:
        output.write(f"Result: {result}")
        
        
class Command(BaseCommand):
    """Run blog ORM queries and display their results."""
    
    help = "Run blog queries and count SQL database operations."
    
    def add_arguments(self, parser: CommandParser) -> None:
        """Define optional command-line arguments"""
        
        parser.add_argument(
            "--number",
            type=int,
            help="Run only the query with this number",
        )
        
        parser.add_argument(
            "--sql",
            action="store_true",
            help="Display the SQL statements.",
        )
        
    def handle(self, *args, **options) -> None:
        """Execute selected queries and display their results."""
        
        number = options["number"]
        show_sql = options["sql"]
        
        if number is not None and number not in QUERIES:
            raise CommandError(
                f"Query number {number} doesn't exist."
            )
            
        if number is None:
            selected_numbers = [
                query_number 
                for query_number in QUERIES
                if query_number not in MODIFYING_QUERIES
            ]
        
        else: 
            selected_numbers = [number]
            
        sample_arguments = get_sample_arguments()
        
        for query_number in selected_numbers:
            function_name = QUERIES[query_number]
            
            function = getattr(query_functions, function_name)
            
            function_arguments = sample_arguments.get(
                query_number, {}
            )
            
            self.stdout.write("")
            self.stdout.write(
                self.style.MIGRATE_HEADING(
                    f"Query #{query_number}: {function_name}"
                )
            )
            
            try:
                with CaptureQueriesContext(connection) as queries:
                    result = function(**function_arguments)
                    if isinstance(result, QuerySet):
                        result = list(result)
                        
                self.stdout.write(
                    f"SQL queries: {len(queries)}"
                )
                self.stdout.write("Results:")
                print_result(result, self.stdout)
                
                if show_sql:
                    self.stdout.write("SQL statements:")
                    
                    for sql_number, query in enumerate(
                        queries, start=1
                    ):
                        self.stdout.write(
                            f"{sql_number}. {query['sql']}"
                        )
            except Exception as error:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error in query #{query_number}: {error}"
                    )
                )
    
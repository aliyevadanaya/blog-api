from django.contrib import admin

from .models import Category, Comment, Post, Tag


class CategoryAdmin(admin.ModelAdmin):
    """Category model admin configuration class"""
    list_display = ('name',)
    

class TagAdmin(admin.ModelAdmin):
    """Tag model admin configuration class"""
    list_display = ('name',)
    

class PostAdmin(admin.ModelAdmin):
    """Post model admin configuration class"""
    
    list_display = ('author', 'title')
    
    
class CommentAdmin(admin.ModelAdmin):
    """Comment model admin configuration class"""
    list_display = ('post', 'author')
    
    
admin.site.register(Category, CategoryAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)

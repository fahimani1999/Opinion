from django.contrib import admin
from .models import (
    BlogPost,
    Comment,
    PostLike,
    CommentLike,
    PostRating,
)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'author',
        'created_at',
        'comment_count',
        'like_count',
        'average_rating',
    )

    search_fields = (
        'title',
        'content',
        'author__username',
    )

    list_filter = (
        'created_at',
        'author',
    )

    def comment_count(self, obj):
        return obj.comments.count()

    comment_count.short_description = 'Comments'

    def like_count(self, obj):
        return obj.post_likes.count()

    like_count.short_description = 'Likes'

    def average_rating(self, obj):

        ratings = obj.ratings.all()

        if not ratings:
            return 0

        total = sum(
            rating.rating
            for rating in ratings
        )

        return round(
            total / len(ratings),
            2
        )

    average_rating.short_description = 'Rating'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'post',
        'author',
        'parent',
        'created_at',
    )

    search_fields = (
        'content',
        'author__username',
        'post__title',
    )

    list_filter = (
        'created_at',
    )


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):

    list_display = (
        'post',
        'user',
        'created_at',
    )

    search_fields = (
        'post__title',
        'user__username',
    )


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):

    list_display = (
        'comment',
        'user',
        'created_at',
    )

    search_fields = (
        'comment__content',
        'user__username',
    )


@admin.register(PostRating)
class PostRatingAdmin(admin.ModelAdmin):

    list_display = (
        'post',
        'user',
        'rating',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'post__title',
        'user__username',
    )

    list_filter = (
        'rating',
    )
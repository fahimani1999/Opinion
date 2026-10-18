from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import (
    Avg,
    Count,
    Sum,
    Min,
    Max,
    Q,
)
from django.http import Http404
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from .forms import BlogPostForm, CommentForm, RatingForm
from .models import (
    BlogPost,
    Comment,
    PostLike,
    CommentLike,
    PostRating,
)


# ==========================================================
# HOME
# ==========================================================

def home(request):
    posts = (
        BlogPost.objects
        .select_related('author')
        .annotate(
            total_likes=Count('post_likes', distinct=True),
            total_comments=Count('comments', distinct=True),
            total_ratings=Count('ratings', distinct=True),
            average_rating=Avg('ratings__rating'),
        )
        .prefetch_related(
            'post_likes',
            'ratings',
            'comments'
        )
    )

    search = request.GET.get('q', '').strip()

    if search:
        posts = posts.filter(
            Q(title__icontains=search) |
            Q(content__icontains=search) |
            Q(author__username__icontains=search)
        )

    # Popular posts using Annotation + Ordering
    popular_posts = posts.order_by(
        '-total_likes',
        '-total_comments',
        '-average_rating',
        '-created_at'
    )[:5]

    # Aggregation example
    statistics = BlogPost.objects.aggregate(
        total_posts=Count('id'),
        total_likes=Count('post_likes', distinct=True),
        total_comments=Count('comments', distinct=True),
        total_ratings=Count('ratings', distinct=True),
        average_rating=Avg('ratings__rating'),
        rating_sum=Sum('ratings__rating'),
        minimum_rating=Min('ratings__rating'),
        maximum_rating=Max('ratings__rating'),
    )

    return render(
        request,
        'home.html',
        {
            'posts': posts,
            'popular_posts': popular_posts,
            'statistics': statistics,
            'search': search,
        }
    )


# ==========================================================
# POST DETAIL
# ==========================================================

def post_detail(request, pk):
    post = get_object_or_404(
        BlogPost.objects
        .select_related('author')
        .prefetch_related(
            'post_likes',
            'ratings',
            'comments__author',
            'comments__comment_likes'
        ),
        pk=pk
    )

    comments = post.comments.all()

    # Build nested comment tree
    comment_map = {}

    for comment in comments:
        comment_map[comment.id] = {
            'comment': comment,
            'replies': []
        }

    root_comments = []

    for comment in comments:
        node = comment_map[comment.id]

        if comment.parent_id:
            parent = comment_map.get(comment.parent_id)

            if parent:
                parent['replies'].append(node)
        else:
            root_comments.append(node)

    user_rating = None

    if request.user.is_authenticated:
        user_rating = PostRating.objects.filter(
            post=post,
            user=request.user
        ).first()

    context = {
        'post': post,
        'comments': comments,
        'comment_tree': root_comments,
        'comment_form': CommentForm(),
        'rating_form': RatingForm(
            instance=user_rating
        ),
        'user_rating': user_rating,
    }

    return render(
        request,
        'post_details.html',
        context
    )


# ==========================================================
# CREATE POST
# ==========================================================

@login_required
def create_post(request):

    if request.method == 'POST':
        form = BlogPostForm(request.POST)

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()

            messages.success(
                request,
                'Post created successfully.'
            )

            return redirect('post_detail', pk=post.pk)

    else:
        form = BlogPostForm()

    return render(
        request,
        'post_form.html',
        {
            'form': form,
            'title': 'Create Post',
        }
    )


# ==========================================================
# EDIT POST
# ==========================================================

@login_required
def edit_post(request, pk):

    post = get_object_or_404(
        BlogPost,
        pk=pk
    )

    if post.author != request.user:
        messages.error(
            request,
            'You can only edit your own posts.'
        )
        return redirect('post_detail', pk=post.pk)

    if request.method == 'POST':
        form = BlogPostForm(
            request.POST,
            instance=post
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Post updated successfully.'
            )

            return redirect(
                'post_detail',
                pk=post.pk
            )

    else:
        form = BlogPostForm(
            instance=post
        )

    return render(
        request,
        'post_form.html',
        {
            'form': form,
            'title': 'Edit Post',
        }
    )


# ==========================================================
# DELETE POST
# ==========================================================

@login_required
def delete_post(request, pk):

    post = get_object_or_404(
        BlogPost,
        pk=pk
    )

    if post.author != request.user:
        messages.error(
            request,
            'You can only delete your own posts.'
        )

        return redirect(
            'post_detail',
            pk=post.pk
        )

    if request.method == 'POST':
        post.delete()

        messages.success(
            request,
            'Post deleted successfully.'
        )

        return redirect('home')

    return render(
        request,
        'post_confirm_delete.html',
        {
            'post': post
        }
    )


# ==========================================================
# MY POSTS
# ==========================================================

@login_required
def my_posts(request):

    posts = (
        BlogPost.objects
        .filter(author=request.user)
        .select_related('author')
        .annotate(
            total_likes=Count(
                'post_likes',
                distinct=True
            ),
            total_comments=Count(
                'comments',
                distinct=True
            ),
            average_rating=Avg(
                'ratings__rating'
            )
        )
    )

    return render(
        request,
        'my_posts.html',
        {
            'posts': posts
        }
    )


# ==========================================================
# ADD COMMENT
# ==========================================================

@login_required
def add_comment(request, pk):

    post = get_object_or_404(
        BlogPost,
        pk=pk
    )

    if request.method != 'POST':
        return redirect(
            'post_detail',
            pk=post.pk
        )

    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user

        parent_id = request.POST.get('parent_id')

        if parent_id:
            parent = get_object_or_404(
                Comment,
                pk=parent_id,
                post=post
            )

            comment.parent = parent

        comment.save()

        messages.success(
            request,
            'Comment added successfully.'
        )

    return redirect(
        'post_detail',
        pk=post.pk
    )


# ==========================================================
# EDIT COMMENT
# ==========================================================

@login_required
def edit_comment(request, pk):

    comment = get_object_or_404(
        Comment,
        pk=pk
    )

    if comment.author != request.user:
        messages.error(
            request,
            'You can only edit your own comments.'
        )

        return redirect(
            'post_detail',
            pk=comment.post.pk
        )

    if request.method == 'POST':
        form = CommentForm(
            request.POST,
            instance=comment
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Comment updated successfully.'
            )

    return redirect(
        'post_detail',
        pk=comment.post.pk
    )


# ==========================================================
# DELETE COMMENT
# ==========================================================

@login_required
def delete_comment(request, pk):

    comment = get_object_or_404(
        Comment,
        pk=pk
    )

    post_id = comment.post.pk

    if comment.author != request.user:
        messages.error(
            request,
            'You can only delete your own comments.'
        )

        return redirect(
            'post_detail',
            pk=post_id
        )

    if request.method == 'POST':
        comment.delete()

        messages.success(
            request,
            'Comment deleted successfully.'
        )

    return redirect(
        'post_detail',
        pk=post_id
    )


# ==========================================================
# LIKE / UNLIKE POST
# ==========================================================

@login_required
def toggle_post_like(request, pk):

    post = get_object_or_404(
        BlogPost,
        pk=pk
    )

    if request.method == 'POST':

        like = PostLike.objects.filter(
            post=post,
            user=request.user
        ).first()

        if like:
            like.delete()
            messages.info(
                request,
                'Post unliked.'
            )
        else:
            PostLike.objects.create(
                post=post,
                user=request.user
            )

            messages.success(
                request,
                'Post liked.'
            )

    return redirect(
        'post_detail',
        pk=post.pk
    )


# ==========================================================
# LIKE / UNLIKE COMMENT
# ==========================================================

@login_required
def toggle_comment_like(request, pk):

    comment = get_object_or_404(
        Comment,
        pk=pk
    )

    if request.method == 'POST':

        like = CommentLike.objects.filter(
            comment=comment,
            user=request.user
        ).first()

        if like:
            like.delete()

        else:
            CommentLike.objects.create(
                comment=comment,
                user=request.user
            )

    return redirect(
        'post_detail',
        pk=comment.post.pk
    )


# ==========================================================
# RATE POST
# ==========================================================

@login_required
def rate_post(request, pk):

    post = get_object_or_404(
        BlogPost,
        pk=pk
    )

    if request.method == 'POST':

        rating_value = request.POST.get('rating')

        try:
            rating_value = int(rating_value)
        except (TypeError, ValueError):
            messages.error(
                request,
                'Invalid rating.'
            )

            return redirect(
                'post_detail',
                pk=post.pk
            )

        if rating_value < 1 or rating_value > 5:
            messages.error(
                request,
                'Rating must be between 1 and 5.'
            )

            return redirect(
                'post_detail',
                pk=post.pk
            )

        rating, created = PostRating.objects.update_or_create(
            post=post,
            user=request.user,
            defaults={
                'rating': rating_value
            }
        )

        if created:
            messages.success(
                request,
                'Rating added successfully.'
            )
        else:
            messages.success(
                request,
                'Rating updated successfully.'
            )

    return redirect(
        'post_detail',
        pk=post.pk
    )


# ==========================================================
# SEARCH
# ==========================================================

def search_posts(request):

    query = request.GET.get(
        'q',
        ''
    ).strip()

    posts = (
        BlogPost.objects
        .select_related('author')
        .annotate(
            total_likes=Count(
                'post_likes',
                distinct=True
            ),
            total_comments=Count(
                'comments',
                distinct=True
            ),
            average_rating=Avg(
                'ratings__rating'
            )
        )
    )

    if query:

        posts = posts.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(author__username__icontains=query)
        )

    return render(
        request,
        'search_results.html',
        {
            'posts': posts,
            'query': query,
        }
    )


# ==========================================================
# PROFILE
# ==========================================================

def profile(request, username):

    user = get_object_or_404(
        User,
        username=username
    )

    statistics = BlogPost.objects.filter(
        author=user
    ).aggregate(
        posts=Count('id')
    )

    comment_count = Comment.objects.filter(
        author=user
    ).count()

    likes_given = PostLike.objects.filter(
        user=user
    ).count()

    ratings_given = PostRating.objects.filter(
        user=user
    ).count()

    return render(
        request,
        'profile.html',
        {
            'profile_user': user,
            'posts_count': statistics['posts'],
            'comments_count': comment_count,
            'likes_given': likes_given,
            'ratings_given': ratings_given,
        }
    )


# ==========================================================
# REGISTER
# ==========================================================

def register(request):

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':

        form = UserCreationForm(
            request.POST
        )

        if form.is_valid():

            user = form.save()

            login(
                request,
                user
            )

            messages.success(
                request,
                'Registration successful.'
            )

            return redirect('home')

    else:
        form = UserCreationForm()

    return render(
        request,
        'register.html',
        {
            'form': form
        }
    )
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from .forms import CommentForm, PostForm
# Импортируем модель, чтобы обратиться к ней
from .models import Comment, Follow, Group, Post, User


COUNT_POST = 10


def my_paginator(request, post_list):
    # Показывать по 10 записей на странице.
    paginator = Paginator(post_list, COUNT_POST)
    # Из URL извлекаем номер запрошенной страницы
    # - это значение параметра page
    page_number = request.GET.get('page')
    # Получаем набор записей для страницы с запрошенным номером
    return paginator.get_page(page_number)


@cache_page(20, key_prefix='index_page')
def index(request):
    template = 'posts/index.html'
    # Если порядок сортировки определен в классе Meta модели,
    # запрос будет выглядить так:
    post_list = Post.objects.all()
    page_obj = my_paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    template = 'posts/group_list.html'
    post_list = Post.objects.all()
    page_obj = my_paginator(request, post_list)
    context = {
        'page_obj': page_obj,
        'group': group,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=author)
    post_count = post_list.count()
    page_obj = my_paginator(request, post_list)
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user.id,
            author=author.id
        ).exists()
    else:
        following = False
    context = {
        'author': author,
        'post_count': post_count,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    comments = Comment.objects.filter(post=post)
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES or None)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            new_post.save()
            return redirect('posts:profile', new_post.author)
        return render(request, template, {'form': form, 'is_edit': False})
    form = PostForm()
    return render(request, template, {'form': form, 'is_edit': False})


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    is_edit = True
    if request.method == 'POST':
        form = PostForm(
            request.POST,
            files=request.FILES or None,
            instance=post
        )
        if form.is_valid():
            post.save()
            return redirect('posts:post_detail', post_id)
        return render(request, template)
    else:
        form = PostForm(instance=post)
    context = {'form': form, 'post_id': post_id, 'is_edit': is_edit}
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    # Получаем пост
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    # информация о текущем пользователе доступна в переменной request.user
    template = 'posts/follow.html'
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = my_paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.get_or_create(
            user=user, author=author
        )
    return redirect('posts:profile', username=author.username)


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    author = get_object_or_404(User, username=username)
    user = request.user
    Follow.objects.filter(
        user=user, author=author
    ).delete()
    return redirect('posts:profile', username=author.username)

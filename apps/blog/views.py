from django.shortcuts import render, get_object_or_404
from .models import Post
from django.views.generic import ListView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .form import *
from django.core.mail import send_mail
from taggit.models import Tag
from django.db.models import Count


# Create your views here.
def post_list(request, tag_slug=None):
    posts = Post.objects.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        posts = posts.filter(tags__in=[tag])

    paginator = Paginator(posts, 3)
    page_number = request.GET.get('page')
    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    return render(request, 'blog/post/list.html', {'page': page, 'posts': posts, 'tag': tag})

def post_detail(request, year, month, day, slug):
    post = get_object_or_404(Post, slug=slug, publish__year=year,
                             publish__month=month, publish__day=day)
    # List active comments for this post
    comments = post.comments.filter(active=True)
    new_comment = None
    if request.method == 'POST':
        # user send comment
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            # created comment but until don't save
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.save()
    else:
        comment_form = CommentForm()
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.objects.filter(tags__in=post_tags_ids)\
    .exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags'))\
    .order_by('-same_tags','-publish')[:4]
    return render(request, 'blog/post/detail.html', {'post': post,
                                                     'comments': comments,
                                                     'new_comment': new_comment,
                                                     'comment_form': comment_form,
                                                     'similar_posts': similar_posts,})

def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    sent = False
    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            # Send email
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = '{}({}) recommends you reading "{}"'.format(cd['name'], cd['email'], post.title)
            message = 'Read "{}" at {}\n\n{}\'s comments: {}'.format(post.title, post_url, cd['name'], cd['comments'])
            send_mail(subject, message, 'visvo.lider@gmail.com', [cd['to']])
            sent = True
            return render(request, 'blog/post/share.html', {'post': post, 'form': form, 'sent': sent})
    else:
        form = EmailPostForm()
        return render(request, 'blog/post/share.html',
                      {'post': post, 'form': form, 'sent': sent})

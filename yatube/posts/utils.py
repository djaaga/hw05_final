from django.core.paginator import Paginator

POSTS_PAGINATE = 10


def paginate(request, posts_list):
    paginator = Paginator(posts_list, POSTS_PAGINATE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj

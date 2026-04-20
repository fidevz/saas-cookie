"""
Shared DRF pagination classes.
"""

from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Default pagination for all list endpoints.

    Clients may request a larger page via ?page_size=N (capped at max_page_size).
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 1000

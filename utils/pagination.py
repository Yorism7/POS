"""
Pagination Utilities for POS System
"""

from typing import List, Tuple, Any

def paginate_items(items: List[Any], page: int = 1, items_per_page: int = 10) -> Tuple[List[Any], int, int, int]:
    """
    Paginate a list of items
    
    Args:
        items: List of items to paginate
        page: Current page number (1-indexed)
        items_per_page: Number of items per page
    
    Returns:
        Tuple of (paginated_items, total_items, total_pages, current_page)
    """
    total_items = len(items)
    total_pages = (total_items + items_per_page - 1) // items_per_page if total_items > 0 else 1
    
    # Ensure page is within valid range
    page = max(1, min(page, total_pages))
    
    # Calculate start and end indices
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    
    paginated_items = items[start_idx:end_idx]
    
    return paginated_items, total_items, total_pages, page




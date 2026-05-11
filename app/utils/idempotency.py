"""
Request deduplication and idempotency utilities.
Prevents duplicate API calls when clients retry requests.
"""
import hashlib
import time
from functools import wraps
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)

# In-production, use Redis for this
# For now, simple in-memory cache with TTL
_idempotency_cache = OrderedDict()
IDEMPOTENCY_TTL = 3600  # 1 hour
CACHE_MAX_SIZE = 10000


def _cleanup_expired_entries():
    """Remove expired entries from cache."""
    now = time.time()
    expired_keys = [k for k, (_, expiry) in _idempotency_cache.items() if now > expiry]
    for key in expired_keys:
        del _idempotency_cache[key]
    
    # Keep cache size manageable
    if len(_idempotency_cache) > CACHE_MAX_SIZE:
        # Remove oldest entries
        to_remove = len(_idempotency_cache) - CACHE_MAX_SIZE
        for _ in range(to_remove):
            _idempotency_cache.popitem(last=False)


def _get_request_fingerprint(user_id, method, path, data=None):
    """
    Create a fingerprint of the request to detect duplicates.
    Include user_id, method, path, and request body hash.
    """
    fingerprint_str = f"{user_id}:{method}:{path}"
    
    if data:
        # Hash the request data
        data_str = str(data) if isinstance(data, dict) else str(data)
        data_hash = hashlib.md5(data_str.encode()).hexdigest()
        fingerprint_str += f":{data_hash}"
    
    return hashlib.sha256(fingerprint_str.encode()).hexdigest()


def check_idempotency(user_id, method, path, data=None):
    """
    Check if this request was recently processed.
    Returns: (is_duplicate, cached_response)
    
    Use in POST/PUT endpoints to prevent duplicate processing:
        is_dup, cached = check_idempotency(user_id, 'POST', '/send-message', request.json)
        if is_dup:
            return cached_response
    """
    _cleanup_expired_entries()
    
    fingerprint = _get_request_fingerprint(user_id, method, path, data)
    now = time.time()
    
    if fingerprint in _idempotency_cache:
        response, expiry = _idempotency_cache[fingerprint]
        if now < expiry:
            logger.info(f"⚠️ Duplicate request detected for user {user_id}: {path}")
            return True, response
    
    return False, None


def record_idempotency(user_id, method, path, data=None, response=None):
    """
    Record that this request was processed and cache its response.
    Call after successfully processing a POST/PUT request.
    """
    _cleanup_expired_entries()
    
    fingerprint = _get_request_fingerprint(user_id, method, path, data)
    expiry = time.time() + IDEMPOTENCY_TTL
    _idempotency_cache[fingerprint] = (response, expiry)
    logger.debug(f"Recorded idempotency for user {user_id}: {path}")


def idempotent_post(func):
    """
    Decorator for POST endpoints to prevent duplicate processing.
    
    Usage:
        @bp.route('/send-message', methods=['POST'])
        @login_required
        @idempotent_post
        def send_message():
            # Your endpoint code
    """
    @wraps(func)
    def wrapped(*args, **kwargs):
        from flask import request
        from flask_login import current_user
        
        if not current_user.is_authenticated:
            return func(*args, **kwargs)
        
        # Check for duplicate
        is_duplicate, cached_response = check_idempotency(
            current_user.id,
            request.method,
            request.path,
            request.get_json() if request.is_json else None
        )
        
        if is_duplicate and cached_response:
            logger.warning(f"Returning cached response for duplicate request from user {current_user.id}")
            return cached_response
        
        # Process the request
        result = func(*args, **kwargs)
        
        # Record the response for future duplicates
        record_idempotency(
            current_user.id,
            request.method,
            request.path,
            request.get_json() if request.is_json else None,
            result
        )
        
        return result
    return wrapped


def invalidate_user_cache(user_id):
    """Clear all cached responses for a specific user."""
    _cleanup_expired_entries()
    user_prefix = f"{user_id}:"
    keys_to_delete = [k for k in _idempotency_cache.keys() if k.startswith(user_prefix)]
    for key in keys_to_delete:
        del _idempotency_cache[key]
    logger.debug(f"Cleared idempotency cache for user {user_id}")

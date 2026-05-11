"""
Socket.IO event rate limiting and anti-spam protection.
Prevents DOS attacks on socket events and reconnect storms.
"""
import time
from functools import wraps
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

# Global rate limit tracking: {user_id: {event_name: [timestamps]}}
_socket_event_limits = defaultdict(lambda: defaultdict(list))
_socket_user_limits = defaultdict(list)

# Configuration
SOCKET_EVENT_LIMITS = {
    'typing': {'rate': 10, 'window': 5},          # Max 10 per 5 seconds
    'stop_typing': {'rate': 10, 'window': 5},
    'user_online': {'rate': 5, 'window': 10},
    'user_inactive': {'rate': 5, 'window': 10},
    'get_notifications': {'rate': 20, 'window': 60},
    'mark_notification_read': {'rate': 30, 'window': 60},
    'watch_species': {'rate': 10, 'window': 5},
    'join_conversation': {'rate': 5, 'window': 10},
    # Default for unknown events
    'default': {'rate': 50, 'window': 60}
}

# Per-user global rate limit (prevent spam across all events)
USER_GLOBAL_LIMIT = {'rate': 100, 'window': 60}  # Max 100 events per minute per user


def _cleanup_old_timestamps(timestamps, window_seconds):
    """Remove timestamps older than the window."""
    now = time.time()
    return [ts for ts in timestamps if now - ts < window_seconds]


def check_socket_event_limit(user_id, event_name):
    """
    Check if user has exceeded rate limit for this event.
    Returns: (allowed, remaining, reset_in_seconds)
    """
    now = time.time()
    
    # Check global per-user limit first
    user_global_ts = _socket_user_limits.get(user_id, [])
    user_global_ts = _cleanup_old_timestamps(user_global_ts, USER_GLOBAL_LIMIT['window'])
    _socket_user_limits[user_id] = user_global_ts
    
    if len(user_global_ts) >= USER_GLOBAL_LIMIT['rate']:
        oldest_ts = min(user_global_ts)
        reset_in = USER_GLOBAL_LIMIT['window'] - (now - oldest_ts)
        logger.warning(f"⚠️ User {user_id} exceeded global socket event limit")
        return False, 0, max(1, int(reset_in))
    
    # Check event-specific limit
    limit_config = SOCKET_EVENT_LIMITS.get(event_name, SOCKET_EVENT_LIMITS['default'])
    event_timestamps = _socket_event_limits[user_id][event_name]
    event_timestamps = _cleanup_old_timestamps(event_timestamps, limit_config['window'])
    _socket_event_limits[user_id][event_name] = event_timestamps
    
    remaining = limit_config['rate'] - len(event_timestamps)
    
    if len(event_timestamps) >= limit_config['rate']:
        oldest_ts = min(event_timestamps)
        reset_in = limit_config['window'] - (now - oldest_ts)
        logger.warning(f"⚠️ User {user_id} exceeded rate limit for '{event_name}'")
        return False, 0, max(1, int(reset_in))
    
    # Allow - record timestamp
    event_timestamps.append(now)
    _socket_event_limits[user_id][event_name] = event_timestamps
    _socket_user_limits[user_id].append(now)
    
    return True, remaining, 0


def socket_rate_limit(event_name=None):
    """
    Decorator for socket event handlers to enforce rate limiting.
    Usage:
        @socketio.on('typing')
        @socket_rate_limit('typing')
        def handle_typing(data):
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            from flask_login import current_user
            from flask_socketio import emit
            
            if not current_user.is_authenticated:
                emit('error', {'message': 'Unauthorized'})
                return
            
            event = event_name or f.__name__
            allowed, remaining, reset_in = check_socket_event_limit(current_user.id, event)
            
            if not allowed:
                logger.warning(f"Rate limit exceeded for user {current_user.id} on event '{event}'")
                emit('rate_limited', {
                    'event': event,
                    'reset_in_seconds': reset_in,
                    'message': f'Too many requests. Try again in {reset_in}s.'
                })
                return
            
            return f(*args, **kwargs)
        return wrapped
    return decorator


def clear_socket_limits_for_user(user_id):
    """Clear all rate limit records for a user (e.g., on disconnect)."""
    if user_id in _socket_event_limits:
        del _socket_event_limits[user_id]
    if user_id in _socket_user_limits:
        del _socket_user_limits[user_id]
    logger.debug(f"Cleared socket rate limits for user {user_id}")

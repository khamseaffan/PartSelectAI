# redis_manager.py
import json
import os
import uuid
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional

from redis import Redis
from redis.exceptions import ConnectionError, RedisError


class RedisManager:
    def __init__(self):
        self.redis = self._connect()

    def _connect(self):
        try:
            redis_instance = Redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                health_check_interval=30
            )
            redis_instance.ping()
            print("Redis connection successful.")
            return redis_instance
        except (ConnectionError, RedisError, Exception) as e:
            print(f"Redis connection error: {str(e)}")
            return None

    def _serialize_dict_values(self, data: dict) -> dict:
        """Converts dictionary values to Redis-compatible types (str)."""
        serialized = {}
        for k, v in data.items():
            if isinstance(v, bool): serialized[k] = str(v)
            elif isinstance(v, (int, float)): serialized[k] = str(v)
            elif isinstance(v, (list, dict)): serialized[k] = json.dumps(v)
            elif v is None: serialized[k] = ""
            else: serialized[k] = str(v)
        return serialized

    def check_connection(func):
        """Decorator to check Redis connection before executing a method."""
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.redis:
                print(f"Redis connection not available for {func.__name__}")
                # Return sensible defaults on connection failure
                if "get_cart" in func.__name__: return {}
                if "get_order" in func.__name__: return None # Although get_order isn't directly used by kept tools now
                return False # Default fail for actions
            try:
                return func(self, *args, **kwargs)
            except (ConnectionError, RedisError) as e:
                print(f"Redis Error during {func.__name__}: {e}")
                if "get_cart" in func.__name__: return {}
                if "get_order" in func.__name__: return None
                return False
            except Exception as e:
                print(f"Unexpected Error during Redis op {func.__name__}: {e}")
                if "get_cart" in func.__name__: return {}
                if "get_order" in func.__name__: return None
                return False
        return wrapper

    # --- Session Management (Optional but potentially useful) ---
    @check_connection
    def update_session(self, session_id: str, updates: dict) -> bool:
        key = f"session:{session_id}"
        data_to_store = {"last_active": datetime.now().isoformat(), **updates}
        serialized_data = self._serialize_dict_values(data_to_store)
        self.redis.hset(key, mapping=serialized_data)
        self.redis.expire(key, timedelta(days=7))
        return True

    @check_connection
    def get_session(self, session_id: str) -> Optional[Dict]:
        key = f"session:{session_id}"
        return self.redis.hgetall(key)

    # --- Cart Management (Using Redis Hash) ---
    @check_connection
    def add_to_cart(self, session_id: str, part_number: str, quantity: int, name: str) -> bool:
        """Adds or updates an item in the cart hash. Stores quantity and name as JSON."""
        key = f"cart:{session_id}"
        item_data = {"quantity": quantity, "name": name}
        item_data_json = json.dumps(item_data)
        self.redis.hset(key, part_number, item_data_json)
        self.redis.expire(key, timedelta(days=7))
        return True # Assume success if no exception via decorator

    @check_connection
    def get_cart(self, session_id: str) -> Dict[str, Dict[str, Any]]:
        """Retrieves the cart hash and parses item data from JSON strings."""
        key = f"cart:{session_id}"
        raw_cart_data = self.redis.hgetall(key)
        parsed_cart = {}
        for part_num, item_data_json in raw_cart_data.items():
            try:
                item_data = json.loads(item_data_json)
                parsed_cart[part_num] = {
                    "quantity": int(item_data.get("quantity", 0)),
                    "name": str(item_data.get("name", ""))
                }
            except (json.JSONDecodeError, ValueError, TypeError) as parse_error:
                print(f"[RedisManager Warning] Parsing item data failed for part {part_num} in cart {key}: {parse_error}")
                parsed_cart[part_num] = {"quantity": 0, "name": "[Error Reading Data]"}
        return parsed_cart

    @check_connection
    def clear_cart(self, session_id: str) -> bool:
        """Deletes the entire cart hash."""
        key = f"cart:{session_id}"
        deleted_count = self.redis.delete(key)
        return deleted_count > 0

    # --- Order Management (Only create needed for checkout simulation) ---
    @check_connection
    def create_order(self, session_id: str, order_data: Dict) -> bool:
        """Creates/overwrites a mock order record hash for the session."""
        key = f"order:{session_id}" # This key stores the finalized cart state
        items_dict_to_store = order_data.get("items", {})
        data_to_store = {
            "order_id": order_data.get("order_id", f"REC-{uuid.uuid4().hex[:6].upper()}"),
            "status": order_data.get("status", "Cart Finalized - User Redirected"), # Reflect checkout action
            "items": json.dumps(items_dict_to_store), # Store final cart items as JSON string
            "created_at": order_data.get("created_at", datetime.now().isoformat())
        }
        self.redis.hset(key, mapping=data_to_store)
        # Set expiry for this finalized record (maybe longer than active cart?)
        self.redis.expire(key, timedelta(days=14)) # Example: 2 weeks
        return True # Assume success

# Instantiate Manager
redis_manager = RedisManager()
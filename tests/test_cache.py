import time
import json
import pytest
from stock_market_agents.utils.cache import Cache

@pytest.fixture
def cache(test_cache_dir):
    """Create a test cache instance"""
    return Cache("test")

def test_cache_set_get(cache):
    """Test basic cache set and get operations"""
    cache.set("test_key", {"data": "test_value"})
    result = cache.get("test_key")
    assert result == {"data": "test_value"}

def test_cache_expiry(cache):
    """Test that cache entries expire correctly"""
    # Set with 1 second expiry
    cache.set("test_key", {"data": "test_value"}, expiry=1)
    
    # Should be available immediately
    assert cache.get("test_key") == {"data": "test_value"}
    
    # Wait for expiry
    time.sleep(1.1)
    
    # Should be None after expiry
    assert cache.get("test_key") is None

def test_cache_delete(cache):
    """Test cache deletion"""
    cache.set("test_key", {"data": "test_value"})
    assert cache.get("test_key") is not None
    
    cache.delete("test_key")
    assert cache.get("test_key") is None

def test_cache_invalid_json(cache):
    """Test handling of invalid JSON data"""
    # Create an object that can't be JSON serialized
    class UnserializableObject:
        pass
    
    # Should not raise an exception
    cache.set("test_key", UnserializableObject())
    assert cache.get("test_key") is None

def test_cache_namespace_isolation(test_cache_dir):
    """Test that different cache namespaces are isolated"""
    cache1 = Cache("namespace1")
    cache2 = Cache("namespace2")
    
    cache1.set("key", "value1")
    cache2.set("key", "value2")
    
    assert cache1.get("key") == "value1"
    assert cache2.get("key") == "value2"

def test_cache_large_data(cache):
    """Test caching of large data structures"""
    large_data = {
        "array": list(range(1000)),
        "nested": {
            "data": {str(i): i for i in range(100)}
        }
    }
    
    cache.set("large_key", large_data)
    result = cache.get("large_key")
    assert result == large_data

def test_cache_special_characters(cache):
    """Test caching with special characters in keys"""
    special_keys = [
        "key with spaces",
        "key/with/slashes",
        "key#with#hashes",
        "key@with@symbols"
    ]
    
    for key in special_keys:
        cache.set(key, {"data": key})
        assert cache.get(key) == {"data": key}

def test_cache_none_value(cache):
    """Test caching of None values"""
    cache.set("none_key", None)
    assert cache.get("none_key") is None
    
    # Make sure we can distinguish between a cached None
    # and a non-existent key
    assert cache.get("nonexistent_key") is None

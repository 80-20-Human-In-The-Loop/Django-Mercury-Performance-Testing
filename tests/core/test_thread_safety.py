"""
Unit tests for thread_safety module
"""

import os
import unittest
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock

from django_mercury.python_bindings.thread_safety import (
    ThreadSafeCounter,
    ThreadSafeDict,
    SingletonMeta,
    synchronized,
    thread_safe_operation
)


class TestThreadSafeCounter(unittest.TestCase):
    """Test cases for ThreadSafeCounter class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.counter = ThreadSafeCounter()

    def test_counter_initialization_default(self) -> None:
        """Test counter initializes with default value of 0."""
        counter = ThreadSafeCounter()
        self.assertEqual(counter.value, 0)

    def test_counter_initialization_with_value(self) -> None:
        """Test counter initializes with specified value."""
        counter = ThreadSafeCounter(initial_value=10)
        self.assertEqual(counter.value, 10)

    def test_counter_increment_default(self) -> None:
        """Test counter increment with default amount."""
        result = self.counter.increment()
        self.assertEqual(result, 1)
        self.assertEqual(self.counter.value, 1)

    def test_counter_increment_with_amount(self) -> None:
        """Test counter increment with specified amount."""
        result = self.counter.increment(5)
        self.assertEqual(result, 5)
        self.assertEqual(self.counter.value, 5)

    def test_counter_increment_multiple_times(self) -> None:
        """Test multiple increments."""
        self.counter.increment(3)
        self.counter.increment(2)
        result = self.counter.increment(1)
        self.assertEqual(result, 6)
        self.assertEqual(self.counter.value, 6)

    def test_counter_decrement_default(self) -> None:
        """Test counter decrement with default amount."""
        self.counter.increment(5)  # Start with 5
        result = self.counter.decrement()
        self.assertEqual(result, 4)
        self.assertEqual(self.counter.value, 4)

    def test_counter_decrement_with_amount(self) -> None:
        """Test counter decrement with specified amount."""
        self.counter.increment(10)  # Start with 10
        result = self.counter.decrement(3)
        self.assertEqual(result, 7)
        self.assertEqual(self.counter.value, 7)

    def test_counter_decrement_below_zero(self) -> None:
        """Test counter can go below zero."""
        result = self.counter.decrement(5)
        self.assertEqual(result, -5)
        self.assertEqual(self.counter.value, -5)

    def test_counter_reset_default(self) -> None:
        """Test counter reset to default value."""
        self.counter.increment(10)
        self.counter.reset()
        self.assertEqual(self.counter.value, 0)

    def test_counter_reset_with_value(self) -> None:
        """Test counter reset to specified value."""
        self.counter.increment(10)
        self.counter.reset(100)
        self.assertEqual(self.counter.value, 100)

    def test_counter_thread_safety(self) -> None:
        """Test counter is thread-safe with concurrent access."""
        counter = ThreadSafeCounter()
        num_threads = 10
        increments_per_thread = 100
        
        def increment_worker():
            for _ in range(increments_per_thread):
                counter.increment()
        
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=increment_worker)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Final value should be exactly num_threads * increments_per_thread
        expected_value = num_threads * increments_per_thread
        self.assertEqual(counter.value, expected_value)

    def test_counter_mixed_operations_thread_safety(self) -> None:
        """Test counter with mixed increment/decrement operations."""
        counter = ThreadSafeCounter(1000)  # Start with 1000
        num_threads = 5
        operations_per_thread = 50
        
        def mixed_worker():
            for i in range(operations_per_thread):
                if i % 2 == 0:
                    counter.increment()
                else:
                    counter.decrement()
        
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=mixed_worker)
            threads.append(thread)
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Each thread does 25 increments and 25 decrements (net 0)
        # So final value should still be 1000
        self.assertEqual(counter.value, 1000)


class TestThreadSafeDict(unittest.TestCase):
    """Test cases for ThreadSafeDict class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.safe_dict = ThreadSafeDict()

    def test_dict_initialization_empty(self) -> None:
        """Test dict initializes empty."""
        safe_dict = ThreadSafeDict()
        self.assertEqual(len(safe_dict), 0)

    def test_dict_initialization_with_data(self) -> None:
        """Test dict can be populated after initialization."""
        safe_dict = ThreadSafeDict()
        safe_dict.set('a', 1)
        safe_dict.set('b', 2)
        self.assertEqual(len(safe_dict), 2)
        self.assertEqual(safe_dict.get('a'), 1)
        self.assertEqual(safe_dict.get('b'), 2)

    def test_dict_set_and_get(self) -> None:
        """Test basic set and get operations."""
        self.safe_dict.set('key1', 'value1')
        self.assertEqual(self.safe_dict.get('key1'), 'value1')

    def test_dict_get_with_default(self) -> None:
        """Test get with default value."""
        result = self.safe_dict.get('nonexistent', 'default')
        self.assertEqual(result, 'default')

    def test_dict_get_nonexistent_no_default(self) -> None:
        """Test get nonexistent key without default."""
        result = self.safe_dict.get('nonexistent')
        self.assertIsNone(result)

    def test_dict_contains(self) -> None:
        """Test key containment check."""
        self.safe_dict.set('existing_key', 'value')
        self.assertTrue('existing_key' in self.safe_dict)
        self.assertFalse('nonexistent_key' in self.safe_dict)

    def test_dict_remove(self) -> None:
        """Test key removal."""
        self.safe_dict.set('to_remove', 'value')
        self.assertTrue('to_remove' in self.safe_dict)
        
        removed = self.safe_dict.delete('to_remove')
        self.assertTrue(removed)
        self.assertFalse('to_remove' in self.safe_dict)

    def test_dict_remove_nonexistent(self) -> None:
        """Test removing nonexistent key."""
        result = self.safe_dict.delete('nonexistent')
        self.assertFalse(result)

    def test_dict_clear(self) -> None:
        """Test clearing the dictionary."""
        self.safe_dict.set('key1', 'value1')
        self.safe_dict.set('key2', 'value2')
        self.assertEqual(len(self.safe_dict), 2)
        
        self.safe_dict.clear()
        self.assertEqual(len(self.safe_dict), 0)

    def test_dict_keys(self) -> None:
        """Test getting all keys."""
        self.safe_dict.set('key1', 'value1')
        self.safe_dict.set('key2', 'value2')
        
        keys = self.safe_dict.keys()
        self.assertEqual(set(keys), {'key1', 'key2'})

    def test_dict_values(self) -> None:
        """Test getting all values."""
        self.safe_dict.set('key1', 'value1')
        self.safe_dict.set('key2', 'value2')
        
        values = self.safe_dict.values()
        self.assertEqual(set(values), {'value1', 'value2'})

    def test_dict_items(self) -> None:
        """Test getting all items."""
        self.safe_dict.set('key1', 'value1')
        self.safe_dict.set('key2', 'value2')
        
        items = self.safe_dict.items()
        self.assertEqual(set(items), {('key1', 'value1'), ('key2', 'value2')})

    def test_dict_len(self) -> None:
        """Test dictionary length."""
        self.assertEqual(len(self.safe_dict), 0)
        
        self.safe_dict.set('key1', 'value1')
        self.assertEqual(len(self.safe_dict), 1)
        
        self.safe_dict.set('key2', 'value2')
        self.assertEqual(len(self.safe_dict), 2)
        
        self.safe_dict.delete('key1')
        self.assertEqual(len(self.safe_dict), 1)

    def test_dict_thread_safety(self) -> None:
        """Test dictionary is thread-safe with concurrent access."""
        safe_dict = ThreadSafeDict()
        num_threads = 10
        items_per_thread = 50
        
        def writer_worker(thread_id):
            for i in range(items_per_thread):
                key = f"thread_{thread_id}_item_{i}"
                value = f"value_{thread_id}_{i}"
                safe_dict.set(key, value)
        
        threads = []
        for thread_id in range(num_threads):
            thread = threading.Thread(target=writer_worker, args=(thread_id,))
            threads.append(thread)
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should have all items
        expected_count = num_threads * items_per_thread
        self.assertEqual(len(safe_dict), expected_count)
        
        # Verify all items are present and correct
        for thread_id in range(num_threads):
            for i in range(items_per_thread):
                key = f"thread_{thread_id}_item_{i}"
                expected_value = f"value_{thread_id}_{i}"
                self.assertEqual(safe_dict.get(key), expected_value)


class TestSingletonMeta(unittest.TestCase):
    """Test cases for SingletonMeta metaclass."""

    def test_singleton_single_instance(self) -> None:
        """Test singleton creates only one instance."""
        class TestSingleton(metaclass=SingletonMeta):
            def __init__(self) -> None:
                self.value = 42
        
        instance1 = TestSingleton()
        instance2 = TestSingleton()
        
        self.assertIs(instance1, instance2)
        self.assertEqual(instance1.value, instance2.value)

    def test_singleton_with_arguments(self) -> None:
        """Test singleton with initialization arguments."""
        class TestSingletonWithArgs(metaclass=SingletonMeta):
            def __init__(self, value=0) -> None:
                if not hasattr(self, 'initialized'):
                    self.value = value
                    self.initialized = True
        
        # First instance sets the value
        instance1 = TestSingletonWithArgs(100)
        # Second instance should be the same, arguments ignored
        instance2 = TestSingletonWithArgs(200)
        
        self.assertIs(instance1, instance2)
        self.assertEqual(instance1.value, 100)  # First value is kept
        self.assertEqual(instance2.value, 100)

    def test_singleton_thread_safety(self) -> None:
        """Test singleton is thread-safe."""
        instances = []
        
        class TestThreadSafeSingleton(metaclass=SingletonMeta):
            def __init__(self) -> None:
                self.creation_time = time.time()
        
        def create_instance():
            instance = TestThreadSafeSingleton()
            instances.append(instance)
        
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_instance)
            threads.append(thread)
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All instances should be the same object
        first_instance = instances[0]
        for instance in instances[1:]:
            self.assertIs(instance, first_instance)

    def test_singleton_different_classes(self) -> None:
        """Test different singleton classes are independent."""
        class SingletonA(metaclass=SingletonMeta):
            def __init__(self) -> None:
                self.type = 'A'
        
        class SingletonB(metaclass=SingletonMeta):
            def __init__(self) -> None:
                self.type = 'B'
        
        instance_a1 = SingletonA()
        instance_a2 = SingletonA()
        instance_b1 = SingletonB()
        instance_b2 = SingletonB()
        
        # Same class instances should be identical
        self.assertIs(instance_a1, instance_a2)
        self.assertIs(instance_b1, instance_b2)
        
        # Different class instances should be different
        self.assertIsNot(instance_a1, instance_b1)
        self.assertEqual(instance_a1.type, 'A')
        self.assertEqual(instance_b1.type, 'B')


class TestSynchronizedDecorator(unittest.TestCase):
    """Test cases for synchronized decorator."""

    def test_synchronized_decorator_basic(self) -> None:
        """Test basic functionality of synchronized decorator."""
        class TestClass:
            def __init__(self) -> None:
                self.value = 0
                self._lock = threading.Lock()
            
            @synchronized()
            def increment(self):
                self.value += 1
                return self.value
        
        obj = TestClass()
        result = obj.increment()
        self.assertEqual(result, 1)
        self.assertEqual(obj.value, 1)

    def test_synchronized_decorator_with_arguments(self) -> None:
        """Test synchronized decorator with method arguments."""
        class TestClass:
            def __init__(self) -> None:
                self.value = 0
                self._lock = threading.Lock()
            
            @synchronized()
            def add(self, amount):
                self.value += amount
                return self.value
        
        obj = TestClass()
        result = obj.add(5)
        self.assertEqual(result, 5)
        self.assertEqual(obj.value, 5)

    def test_synchronized_decorator_thread_safety(self) -> None:
        """Test synchronized decorator provides thread safety."""
        class TestClass:
            def __init__(self) -> None:
                self.value = 0
                self._lock = threading.Lock()
            
            @synchronized()
            def increment(self):
                # Simulate some processing time
                current = self.value
                time.sleep(0.001)  # Small delay to increase chance of race condition
                self.value = current + 1
                return self.value
        
        obj = TestClass()
        num_threads = 10
        
        def worker():
            obj.increment()
        
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=worker)
            threads.append(thread)
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # With proper thread safety, final value should be exactly num_threads
        self.assertEqual(obj.value, num_threads)

    def test_synchronized_decorator_custom_lock_attr(self) -> None:
        """Test synchronized decorator with custom lock attribute."""
        class TestClass:
            def __init__(self) -> None:
                self.value = 0
                self.my_lock = threading.Lock()
            
            @synchronized('my_lock')
            def increment(self):
                self.value += 1
                return self.value
        
        obj = TestClass()
        result = obj.increment()
        self.assertEqual(result, 1)
        self.assertEqual(obj.value, 1)

    def test_synchronized_decorator_missing_lock(self) -> None:
        """Test synchronized decorator handles missing lock attribute."""
        class TestClass:
            def __init__(self) -> None:
                self.value = 0
                # No lock attribute
            
            @synchronized()
            def increment(self):
                self.value += 1
                return self.value
        
        obj = TestClass()
        # Should work without lock (warning logged)
        result = obj.increment()
        self.assertEqual(result, 1)
        self.assertEqual(obj.value, 1)


class TestThreadSafeOperation(unittest.TestCase):
    """Test cases for thread_safe_operation context manager."""

    def test_thread_safe_operation_basic(self) -> None:
        """Test basic thread_safe_operation functionality."""
        lock = threading.Lock()
        
        with thread_safe_operation(lock):
            # This should execute without issues
            pass

    def test_thread_safe_operation_actually_locks(self) -> None:
        """Test thread_safe_operation actually provides mutual exclusion."""
        lock = threading.Lock()
        shared_resource = {'value': 0}
        results = []
        
        def worker():
            with thread_safe_operation(lock):
                # Simulate some work that modifies shared resource
                current = shared_resource['value']
                time.sleep(0.01)  # Small delay
                shared_resource['value'] = current + 1
                results.append(shared_resource['value'])
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Results should be sequential (1, 2, 3, 4, 5) if properly locked
        self.assertEqual(sorted(results), [1, 2, 3, 4, 5])
        self.assertEqual(shared_resource['value'], 5)

    def test_thread_safe_operation_timeout(self) -> None:
        """Test thread_safe_operation with timeout."""
        lock = threading.Lock()
        
        # Detect CI environment and adjust timing for reliability
        # CI runners (especially macOS ARM64) need more time for thread scheduling
        is_ci = os.environ.get('CI', '').lower() == 'true' or os.environ.get('GITHUB_ACTIONS', '').lower() == 'true'
        
        # Use longer delays in CI to ensure reliable test execution
        hold_time = 0.25 if is_ci else 0.15  # Hold lock for 250ms in CI, 150ms locally
        setup_delay = 0.05 if is_ci else 0.02  # Wait 50ms in CI, 20ms locally
        timeout = 0.05  # Keep 50ms timeout (must be less than hold_time - setup_delay)
        
        def holder():
            with lock:
                time.sleep(hold_time)  # Hold lock long enough to trigger timeout
        
        # Start thread that holds the lock
        holder_thread = threading.Thread(target=holder)
        holder_thread.start()
        
        time.sleep(setup_delay)  # Ensure holder thread has acquired lock
        
        # Try to acquire with short timeout - should fail and raise TimeoutError
        with self.assertRaises(TimeoutError):
            with thread_safe_operation(lock, timeout=timeout):
                pass
        
        holder_thread.join()

    def test_thread_safe_operation_no_timeout(self) -> None:
        """Test thread_safe_operation without timeout (should wait indefinitely)."""
        lock = threading.Lock()
        acquired = threading.Event()
        
        def holder():
            with lock:
                acquired.set()
                time.sleep(0.05)  # Hold lock briefly
        
        def waiter():
            acquired.wait()  # Wait for holder to acquire lock
            with thread_safe_operation(lock):  # No timeout
                # Should eventually acquire the lock
                pass
        
        holder_thread = threading.Thread(target=holder)
        waiter_thread = threading.Thread(target=waiter)
        
        holder_thread.start()
        waiter_thread.start()
        
        # Both should complete successfully
        holder_thread.join()
        waiter_thread.join()

    def test_thread_safe_operation_exception_handling(self) -> None:
        """Test thread_safe_operation properly releases lock on exception."""
        lock = threading.Lock()
        
        # Should not hang after exception
        with self.assertRaises(ValueError):
            with thread_safe_operation(lock):
                raise ValueError("Test exception")
        
        # Lock should be available again
        with thread_safe_operation(lock):
            # Should acquire successfully
            pass


class TestThreadSafetyEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def test_counter_with_large_numbers(self) -> None:
        """Test counter with large increment/decrement values."""
        counter = ThreadSafeCounter()
        
        large_value = 1000000
        counter.increment(large_value)
        self.assertEqual(counter.value, large_value)
        
        counter.decrement(large_value // 2)
        self.assertEqual(counter.value, large_value // 2)

    def test_dict_with_none_values(self) -> None:
        """Test ThreadSafeDict with None values."""
        safe_dict = ThreadSafeDict()
        
        safe_dict.set('key', None)
        self.assertTrue('key' in safe_dict)
        self.assertIsNone(safe_dict.get('key'))

    def test_dict_with_complex_keys(self) -> None:
        """Test ThreadSafeDict with complex key types."""
        safe_dict = ThreadSafeDict()
        
        # Test with tuple key
        tuple_key = ('a', 'b', 1)
        safe_dict.set(tuple_key, 'tuple_value')
        self.assertEqual(safe_dict.get(tuple_key), 'tuple_value')
        
        # Test with frozen set key
        frozenset_key = frozenset([1, 2, 3])
        safe_dict.set(frozenset_key, 'frozenset_value')
        self.assertEqual(safe_dict.get(frozenset_key), 'frozenset_value')

    def test_thread_safe_operation_with_already_acquired_lock(self) -> None:
        """Test thread_safe_operation behavior when lock is already held."""
        lock = threading.Lock()
        
        # This should cause a timeout since it's the same thread trying to acquire again
        with lock:  # Acquire lock in outer scope
            with self.assertRaises(TimeoutError):
                with thread_safe_operation(lock, timeout=0.1):
                    pass  # Should timeout

    def test_synchronized_method_with_exception(self) -> None:
        """Test synchronized method properly releases lock on exception."""
        class TestClass:
            def __init__(self) -> None:
                self.call_count = 0
                self._lock = threading.Lock()
            
            @synchronized()
            def failing_method(self):
                self.call_count += 1
                if self.call_count == 1:
                    raise ValueError("First call fails")
                return "success"
        
        obj = TestClass()
        
        # First call should raise exception
        with self.assertRaises(ValueError):
            obj.failing_method()
        
        # Second call should work (lock should have been released)
        result = obj.failing_method()
        self.assertEqual(result, "success")
        self.assertEqual(obj.call_count, 2)


if __name__ == '__main__':
    unittest.main()
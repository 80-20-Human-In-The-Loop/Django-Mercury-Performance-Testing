"""
Comprehensive tests for PythonQueryAnalyzer in pure_python.py
Tests SQL query analysis without C extensions.
"""

import unittest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from django_mercury.python_bindings.pure_python import PythonQueryAnalyzer


class TestPythonQueryAnalyzer(unittest.TestCase):
    """Test the PythonQueryAnalyzer class."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.analyzer = PythonQueryAnalyzer()
    
    def test_initialization(self) -> None:
        """Test analyzer initializes correctly."""
        self.assertEqual(self.analyzer.queries, [])
        self.assertEqual(self.analyzer.analysis_cache, {})
    
    def test_analyze_simple_select(self) -> None:
        """Test analyzing a simple SELECT query."""
        sql = "SELECT * FROM users"
        result = self.analyzer.analyze_query(sql)
        
        self.assertEqual(result['type'], 'SELECT')
        self.assertEqual(result['tables'], ['users'])
        self.assertFalse(result['has_join'])
        self.assertFalse(result['has_subquery'])
        self.assertFalse(result['has_order_by'])
        self.assertFalse(result['has_group_by'])
        self.assertEqual(result['estimated_complexity'], 1)
        self.assertEqual(result['implementation'], 'pure_python')
    
    def test_analyze_select_with_limit_recommendation(self) -> None:
        """Test that SELECT without LIMIT gets recommendation."""
        sql = "SELECT * FROM posts"
        result = self.analyzer.analyze_query(sql)
        
        self.assertEqual(result['type'], 'SELECT')
        self.assertIn('Consider adding LIMIT for large result sets', result['recommendations'])
    
    def test_analyze_select_with_limit_no_recommendation(self) -> None:
        """Test that SELECT with LIMIT doesn't get limit recommendation."""
        sql = "SELECT * FROM posts LIMIT 10"
        result = self.analyzer.analyze_query(sql)
        
        self.assertEqual(result['type'], 'SELECT')
        self.assertNotIn('Consider adding LIMIT for large result sets', result['recommendations'])
    
    def test_analyze_insert_query(self) -> None:
        """Test analyzing an INSERT query."""
        sql = "INSERT INTO users (name, email) VALUES ('John', 'john@example.com')"
        result = self.analyzer.analyze_query(sql)
        
        self.assertEqual(result['type'], 'INSERT')
        # INSERT queries are parsed differently, may not extract table from VALUES
        self.assertEqual(result['estimated_complexity'], 1)
    
    def test_analyze_update_query(self) -> None:
        """Test analyzing an UPDATE query."""
        sql = "UPDATE users SET active = 1 WHERE id = 123"
        result = self.analyzer.analyze_query(sql)
        
        self.assertEqual(result['type'], 'UPDATE')
        self.assertEqual(result['estimated_complexity'], 1)
    
    def test_analyze_delete_query(self) -> None:
        """Test analyzing a DELETE query."""
        sql = "DELETE FROM users WHERE created_at < '2020-01-01'"
        result = self.analyzer.analyze_query(sql)
        
        self.assertEqual(result['type'], 'DELETE')
        self.assertEqual(result['tables'], ['users'])
    
    def test_analyze_other_query_type(self) -> None:
        """Test analyzing non-standard query type."""
        sql = "CREATE TABLE test (id INT)"
        result = self.analyzer.analyze_query(sql)
        
        self.assertEqual(result['type'], 'OTHER')
    
    def test_analyze_query_with_join(self) -> None:
        """Test analyzing query with JOIN."""
        sql = "SELECT * FROM users JOIN posts ON users.id = posts.user_id"
        result = self.analyzer.analyze_query(sql)
        
        self.assertEqual(result['type'], 'SELECT')
        self.assertTrue(result['has_join'])
        self.assertIn('users', result['tables'])
        self.assertIn('posts', result['tables'])
        self.assertGreater(result['estimated_complexity'], 1)
    
    def test_analyze_query_with_multiple_joins(self) -> None:
        """Test analyzing query with multiple JOINs."""
        sql = """
            SELECT * FROM users 
            JOIN posts ON users.id = posts.user_id
            JOIN comments ON posts.id = comments.post_id
            LEFT JOIN likes ON posts.id = likes.post_id
        """
        result = self.analyzer.analyze_query(sql)
        
        self.assertTrue(result['has_join'])
        self.assertEqual(len(result['tables']), 4)  # users, posts, comments, likes
        self.assertGreaterEqual(result['estimated_complexity'], 4)  # Base + 3 joins
    
    def test_analyze_query_with_subquery(self) -> None:
        """Test analyzing query with subquery."""
        sql = "SELECT * FROM users WHERE id IN (SELECT user_id FROM posts WHERE active = 1)"
        result = self.analyzer.analyze_query(sql)
        
        self.assertTrue(result['has_subquery'])
        self.assertIn('Consider using JOINs instead of subqueries', result['recommendations'])
        self.assertGreater(result['estimated_complexity'], 2)
    
    def test_analyze_query_with_order_by(self) -> None:
        """Test analyzing query with ORDER BY."""
        sql = "SELECT * FROM posts ORDER BY created_at DESC"
        result = self.analyzer.analyze_query(sql)
        
        self.assertTrue(result['has_order_by'])
        self.assertEqual(result['estimated_complexity'], 2)  # Base + ORDER BY
    
    def test_analyze_query_with_group_by(self) -> None:
        """Test analyzing query with GROUP BY."""
        sql = "SELECT user_id, COUNT(*) FROM posts GROUP BY user_id"
        result = self.analyzer.analyze_query(sql)
        
        self.assertTrue(result['has_group_by'])
        self.assertGreater(result['estimated_complexity'], 1)
    
    def test_analyze_complex_query(self) -> None:
        """Test analyzing a complex query."""
        sql = """
            SELECT DISTINCT u.name, COUNT(p.id) as post_count
            FROM users u
            JOIN posts p ON u.id = p.user_id
            WHERE u.active = 1 AND p.status = 'published'
            GROUP BY u.name
            ORDER BY post_count DESC
        """
        result = self.analyzer.analyze_query(sql)
        
        self.assertEqual(result['type'], 'SELECT')
        self.assertTrue(result['has_join'])
        self.assertTrue(result['has_order_by'])
        self.assertTrue(result['has_group_by'])
        self.assertGreater(result['estimated_complexity'], 4)
        self.assertIn('Query appears complex, consider optimization', result['recommendations'])
    
    def test_analyze_query_with_union(self) -> None:
        """Test analyzing query with UNION."""
        sql = """
            SELECT name FROM users
            UNION
            SELECT title FROM posts
        """
        result = self.analyzer.analyze_query(sql)
        
        complexity = result['estimated_complexity']
        self.assertGreaterEqual(complexity, 3)  # Base + UNION complexity
    
    def test_query_caching(self) -> None:
        """Test that query analysis results are cached."""
        sql = "SELECT * FROM users WHERE id = 1"
        
        # First analysis
        result1 = self.analyzer.analyze_query(sql)
        
        # Mark the result to verify it's from cache
        self.analyzer.analysis_cache[sql]['cached'] = True
        
        # Second analysis should return cached result
        result2 = self.analyzer.analyze_query(sql)
        
        self.assertTrue(result2.get('cached', False))
        self.assertEqual(result1['type'], result2['type'])
    
    def test_query_truncation(self) -> None:
        """Test that long queries are truncated in results."""
        # Create a very long SQL query
        long_sql = "SELECT " + ", ".join([f"column_{i}" for i in range(100)]) + " FROM very_long_table"
        
        result = self.analyzer.analyze_query(long_sql)
        
        # Query should be truncated to 200 characters
        self.assertLessEqual(len(result['query']), 200)
    
    def test_extract_tables_from_clause(self) -> None:
        """Test table extraction from FROM clause."""
        sql = "SELECT * FROM customers WHERE id > 100"
        result = self.analyzer.analyze_query(sql)
        
        self.assertEqual(result['tables'], ['customers'])
    
    def test_extract_tables_multiple_joins(self) -> None:
        """Test table extraction with multiple JOIN types."""
        sql = """
            SELECT * FROM orders o
            INNER JOIN customers c ON o.customer_id = c.id
            LEFT JOIN products p ON o.product_id = p.id
            RIGHT JOIN categories cat ON p.category_id = cat.id
        """
        result = self.analyzer.analyze_query(sql)
        
        tables = result['tables']
        self.assertIn('orders', tables)
        self.assertIn('customers', tables)
        self.assertIn('products', tables)
        self.assertIn('categories', tables)
    
    def test_extract_tables_case_insensitive(self) -> None:
        """Test table extraction is case insensitive."""
        sql = "select * FROM Users join Posts on users.id = posts.user_id"
        result = self.analyzer.analyze_query(sql)
        
        # Should extract tables regardless of case
        self.assertIn('Users', result['tables'])
        self.assertIn('Posts', result['tables'])
    
    def test_get_query_type_various_cases(self) -> None:
        """Test query type detection with various cases and spacing."""
        test_cases = [
            ("  SELECT * FROM users", "SELECT"),
            ("\nSELECT * FROM users", "SELECT"),
            ("select * from users", "SELECT"),
            ("  INSERT INTO users", "INSERT"),
            ("update users set", "UPDATE"),
            ("DELETE from users", "DELETE"),
            ("TRUNCATE TABLE users", "OTHER"),
            ("", "OTHER"),
        ]
        
        for sql, expected_type in test_cases:
            result = self.analyzer.analyze_query(sql)
            self.assertEqual(result['type'], expected_type, f"Failed for SQL: {sql}")
    
    def test_estimate_complexity_cap(self) -> None:
        """Test that complexity is capped at 10."""
        # Create a query that would have complexity > 10
        sql = """
            SELECT DISTINCT * FROM t1
            JOIN t2 ON t1.id = t2.id
            JOIN t3 ON t2.id = t3.id
            JOIN t4 ON t3.id = t4.id
            JOIN t5 ON t4.id = t5.id
            JOIN t6 ON t5.id = t6.id
            WHERE EXISTS (SELECT 1 FROM sub1)
            AND EXISTS (SELECT 1 FROM sub2)
            GROUP BY t1.id
            ORDER BY t1.name
            UNION
            SELECT * FROM t7
        """
        result = self.analyzer.analyze_query(sql)
        
        # Complexity should be capped at 10
        self.assertEqual(result['estimated_complexity'], 10)
    
    def test_recommendations_combinations(self) -> None:
        """Test different recommendation combinations."""
        # Query with subquery but has LIMIT
        sql1 = "SELECT * FROM users WHERE id IN (SELECT user_id FROM posts) LIMIT 10"
        result1 = self.analyzer.analyze_query(sql1)
        self.assertIn('Consider using JOINs instead of subqueries', result1['recommendations'])
        self.assertNotIn('Consider adding LIMIT for large result sets', result1['recommendations'])
        
        # Complex query without subquery
        sql2 = """
            SELECT * FROM users u
            JOIN posts p ON u.id = p.user_id
            JOIN comments c ON p.id = c.post_id
            JOIN likes l ON p.id = l.post_id
            JOIN follows f ON u.id = f.user_id
            GROUP BY u.id
            ORDER BY COUNT(p.id) DESC
        """
        result2 = self.analyzer.analyze_query(sql2)
        self.assertIn('Query appears complex, consider optimization', result2['recommendations'])
        self.assertIn('Consider adding LIMIT for large result sets', result2['recommendations'])
    
    def test_empty_and_whitespace_queries(self) -> None:
        """Test handling of empty and whitespace-only queries."""
        test_cases = ["", "   ", "\n", "\t\n  "]
        
        for sql in test_cases:
            result = self.analyzer.analyze_query(sql)
            self.assertEqual(result['type'], 'OTHER')
            self.assertEqual(result['tables'], [])
            self.assertEqual(result['estimated_complexity'], 1)


if __name__ == '__main__':
    unittest.main()
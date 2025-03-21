"""
Unit tests for config module
"""
import unittest
from deezer_rpc.config.settings import Config


class TestConfig(unittest.TestCase):
    """Test cases for the Config class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
    
    def test_default_values(self):
        """Test default configuration values"""
        self.assertEqual(self.config.update_interval, Config.DEFAULT_UPDATE_INTERVAL)
    
    def test_set_update_interval_valid(self):
        """Test setting a valid update interval"""
        success, _ = self.config.set_update_interval(15)
        self.assertTrue(success)
        self.assertEqual(self.config.update_interval, 15)
    
    def test_set_update_interval_invalid(self):
        """Test setting an invalid update interval"""
        original_interval = self.config.update_interval
        success, _ = self.config.set_update_interval(0)  # Too small
        self.assertFalse(success)
        self.assertEqual(self.config.update_interval, original_interval)
        
        success, _ = self.config.set_update_interval(100)  # Too large
        self.assertFalse(success)
        self.assertEqual(self.config.update_interval, original_interval)
        
        success, _ = self.config.set_update_interval("not a number")
        self.assertFalse(success)
        self.assertEqual(self.config.update_interval, original_interval)


if __name__ == "__main__":
    unittest.main() 
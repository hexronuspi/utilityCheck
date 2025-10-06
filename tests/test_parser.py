# There is no datafile generation for testblock, all results are shown on terminal itself
import unittest
import os
import json
import tempfile
import shutil
from ucheck.utility.parser import parse_code

class TestParser(unittest.TestCase):    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.test_dir, "output")
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    def test_simple_functions(self):
        """Test 1: Parse simple standalone functions."""
        test_code = '''
def hello_world():
    """A simple hello world function."""
    print("Hello, World!")
    return "Hello"

def add_numbers(a, b):
    """Add two numbers together."""
    result = a + b
    return result

def multiply(x, y):
    """Multiply two numbers."""
    return x * y
'''
        
        # Create test file
        test_file = os.path.join(self.test_dir, "simple_functions.py")
        with open(test_file, 'w') as f:
            f.write(test_code)
        
        # Parse the file
        result = parse_code(test_file, self.output_dir)
        
        # Verify results
        self.assertIn("analysisData", result)
        self.assertIn("graphNodes", result["analysisData"])
        
        nodes = result["analysisData"]["graphNodes"]
        self.assertEqual(len(nodes), 3)  # Should find 3 functions
        
        function_names = [node["label"] for node in nodes]
        self.assertIn("hello_world", function_names)
        self.assertIn("add_numbers", function_names)
        self.assertIn("multiply", function_names)
        
        # Check that all nodes have required fields
        for node in nodes:
            self.assertIn("id", node)
            self.assertIn("label", node)
            self.assertIn("code", node)
            self.assertIn("language", node)
            self.assertEqual(node["language"], "py")
    
    def test_class_methods(self):
        """Test 2: Parse class methods as separate functions."""
        test_code = '''
class Calculator:
    """A simple calculator class."""
    
    def __init__(self, name="Calculator"):
        self.name = name
    
    def add(self, a, b):
        """Add two numbers."""
        return a + b
    
    def subtract(self, a, b):
        """Subtract two numbers."""
        return a - b
    
    def get_name(self):
        """Get calculator name."""
        return self.name

def standalone_function():
    """A function outside the class."""
    return "I'm standalone!"
'''
        
        # Create test file
        test_file = os.path.join(self.test_dir, "class_example.py")
        with open(test_file, 'w') as f:
            f.write(test_code)
        
        # Parse the file
        result = parse_code(test_file, self.output_dir)
        
        nodes = result["analysisData"]["graphNodes"]
        self.assertEqual(len(nodes), 5)  # 4 methods + 1 standalone function
        
        # Check for class methods
        method_labels = [node["label"] for node in nodes]
        self.assertIn("Calculator.__init__", method_labels)
        self.assertIn("Calculator.add", method_labels)
        self.assertIn("Calculator.subtract", method_labels)
        self.assertIn("Calculator.get_name", method_labels)
        self.assertIn("standalone_function", method_labels)
    
    def test_directory_parsing(self):
        """Test 3: Parse multiple files in a directory structure."""
        # Create directory structure
        subdir = os.path.join(self.test_dir, "myproject")
        os.makedirs(subdir)
        
        # File 1: utils.py
        utils_code = '''
def helper_function():
    """A helper function."""
    return "helping"

def another_helper():
    """Another helper."""
    pass
'''
        utils_file = os.path.join(subdir, "utils.py")
        with open(utils_file, 'w') as f:
            f.write(utils_code)
        
        # File 2: main.py
        main_code = '''
def main():
    """Main function."""
    print("This is main")
    return 0

class App:
    def run(self):
        """Run the app."""
        return "running"
'''
        main_file = os.path.join(subdir, "main.py")
        with open(main_file, 'w') as f:
            f.write(main_code)
        
        # Parse the directory
        result = parse_code(subdir, self.output_dir)
        
        nodes = result["analysisData"]["graphNodes"]
        self.assertEqual(len(nodes), 4)  # 2 from utils + 2 from main
        
        # Check that we have functions from both files
        labels = [node["label"] for node in nodes]
        self.assertIn("helper_function", labels)
        self.assertIn("another_helper", labels)
        self.assertIn("main", labels)
        self.assertIn("App.run", labels)
        
        # Check that IDs contain correct file paths
        ids = [node["id"] for node in nodes]
        utils_ids = [id for id in ids if "utils.py" in id]
        main_ids = [id for id in ids if "main.py" in id]
        self.assertEqual(len(utils_ids), 2)
        self.assertEqual(len(main_ids), 2)
    
    def test_empty_file(self):
        """Test 4: Handle empty or non-Python files gracefully."""
        # Create empty Python file
        empty_file = os.path.join(self.test_dir, "empty.py")
        with open(empty_file, 'w') as f:
            f.write("# Just a comment\n")
        
        # Create text file (should be ignored)
        text_file = os.path.join(self.test_dir, "readme.txt")
        with open(text_file, 'w') as f:
            f.write("This is not Python code")
        
        # Parse the directory
        result = parse_code(self.test_dir, self.output_dir)
        
        # Should have no functions since files are empty or not Python
        nodes = result["analysisData"]["graphNodes"]
        self.assertEqual(len(nodes), 0)
    
    def test_output_file_creation(self):
        """Test that JSON output file is created correctly."""
        test_code = '''
def test_function():
    return "test"
'''
        
        test_file = os.path.join(self.test_dir, "test_output.py")
        with open(test_file, 'w') as f:
            f.write(test_code)
        
        # Parse and check output file
        parse_code(test_file, self.output_dir)
        
        # Check that output file was created
        expected_output = os.path.join(self.output_dir, "test_output.json")
        self.assertTrue(os.path.exists(expected_output))
        
        # Verify JSON structure
        with open(expected_output, 'r') as f:
            data = json.load(f)
        
        self.assertIn("analysisData", data)
        self.assertIn("graphNodes", data["analysisData"])
        self.assertEqual(len(data["analysisData"]["graphNodes"]), 1)


if __name__ == "__main__":
    unittest.main()


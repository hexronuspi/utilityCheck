import ast
import re
import json
import os
import glob
from typing import Dict, Any, List

# --------------------------
# Global heuristic weights (raw, will be normalized later)
# --------------------------
LINES_LESS_THAN_3 = 0.9
RETURN_LITERAL_OR_ARG = 0.8
SINGLE_STATEMENT_PRINT_LOG = 0.7
MULTI_CALL_LOOP_CONDITIONAL = 0.2
MULTI_OBJECTS_INITIALIZED = 0.2
MULTIPLE_FUNC_CALLS = 0.2
IMPORT_COUNT_FACTOR = 0.05
REGEX_USAGE_FACTOR = 0.1
COMPLEXITY_FACTOR = 0.3
DOCUMENTATION_FACTOR = 0.1

# Default threshold for utility classification
DEFAULT_THRESHOLD = 0.8

# --------------------------
# Helpers
# --------------------------
def is_utility_file_or_folder(file_path: str) -> bool:
    """
    Check if the function is from a utility file or folder.
    Returns True if the file path contains 'util', 'utils', or 'utility' in any part.
    """
    if not file_path:
        return False
    
    # Convert to lowercase for case-insensitive matching
    path_lower = file_path.lower()
    
    # Split the path by common separators to check each component
    path_components = path_lower.replace('\\', '/').split('/')
    
    # Check if any component contains utility-related names
    utility_names = ['util', 'utils', 'utility']
    
    for component in path_components:
        # Remove file extensions for checking
        component_base = component.split('.')[0]
        
        # Check if the component is exactly one of the utility names
        if component_base in utility_names:
            return True
        
        # Check if the component contains utility names as substrings
        for util_name in utility_names:
            if util_name in component_base:
                return True
    
    return False

def is_trivial_return(node: ast.Return) -> bool:
    if isinstance(node.value, (ast.Constant, ast.Name)):
        return True
    if isinstance(node.value, ast.Attribute) and isinstance(node.value.value, ast.Name):
        return node.value.value.id == "self"
    return False

def count_objects_and_calls(tree: ast.AST) -> Dict[str, int]:
    object_inits = 0
    func_calls = 0
    control_structures = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func_calls += 1
        elif isinstance(node, ast.Assign):
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
                object_inits += 1
        elif isinstance(node, (ast.For, ast.While, ast.If, ast.Try, ast.With)):
            control_structures += 1
    return {"object_inits": object_inits, "func_calls": func_calls, "control_structures": control_structures}

def count_import_words(code: str) -> int:
    imports = re.findall(r"^\s*(import|from)\s+.*", code, re.MULTILINE)
    return sum(len(i.split()) for i in imports)

def count_regex_usage(code: str) -> int:
    return len(re.findall(r"\bre\.", code))

def calculate_code_complexity(code: str) -> float:
    """Calculate code complexity based on cyclomatic complexity and nesting."""
    try:
        tree = ast.parse(code)
        complexity = 1  # Base complexity
        max_nesting = 0
        current_nesting = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                complexity += 1
                current_nesting += 1
                max_nesting = max(max_nesting, current_nesting)
            elif isinstance(node, ast.FunctionDef):
                current_nesting = max(0, current_nesting - 1)
        
        # Normalize complexity (higher complexity = more utility-like)
        return min(1.0, (complexity + max_nesting * 0.5) / 10.0)
    except:
        return 0.0

def calculate_documentation_ratio(original_code: str, cleaned_code: str) -> float:
    """Calculate ratio of documentation vs code (higher ratio = less utility-like)."""
    if not original_code.strip():
        return 0.0
    
    original_lines = len([line for line in original_code.split('\n') if line.strip()])
    cleaned_lines = len([line for line in cleaned_code.split('\n') if line.strip()])
    
    if original_lines == 0:
        return 0.0
    
    doc_ratio = 1.0 - (cleaned_lines / original_lines)
    return max(0.0, min(1.0, doc_ratio))

# --------------------------
# Main function scoring
# --------------------------
def score_function(node: Dict[str, Any], threshold: float = DEFAULT_THRESHOLD, original_code: str = "") -> Dict[str, Any]:
    """Score a function and determine if it's a utility function."""
    code = node.get("code", "")
    if code is None:
        code = ""
    lines = code.strip().count("\n") + 1
    
    # ----------------------
    # Check for utility file/folder - bypass heuristics if found
    # ----------------------
    function_id = node.get("id", "")
    if is_utility_file_or_folder(function_id):
        # Auto-assign utility score of 1.0 for functions in util/utils/utility files/folders
        node["rank"] = 1.0
        node["isUtil"] = True
        node["category"] = "utility"
        return node

    # ----------------------
    # Raw heuristic points (weighted scoring)
    # ----------------------
    raw_points: List[float] = []

    # Simple functions (few lines = potentially more utility-like, but not guaranteed)
    if lines <= 3:
        raw_points.append(0.3)  # Reduced from 0.9
    elif lines <= 10:
        raw_points.append(0.1)
    else:
        raw_points.append(-0.1)  # Complex functions less likely to be utilities

    # AST-based analysis
    try:
        tree = ast.parse(code)
        
        # Trivial return check (simple getters/setters)
        returns = [n for n in ast.walk(tree) if isinstance(n, ast.Return)]
        if len(returns) == 1 and is_trivial_return(returns[0]):
            raw_points.append(0.2)  # Reduced from 0.8
        else:
            raw_points.append(0.0)

        # Single statement functions
        statements = [n for n in tree.body if not isinstance(n, (ast.Pass, ast.Expr))]
        if len(statements) <= 1:
            raw_points.append(0.2)  # Simple functions
        else:
            raw_points.append(0.0)

        counts = count_objects_and_calls(tree)
        
        # Control structures (loops, conditionals) - mixed signal
        if counts["control_structures"] > 3:
            raw_points.append(-0.2)  # Too complex for typical utilities
        elif counts["control_structures"] > 0:
            raw_points.append(0.1)   # Some complexity is ok
        else:
            raw_points.append(0.0)   # No control structures

        # Function calls - utilities often call other functions
        if counts["func_calls"] > 5:
            raw_points.append(-0.1)  # Too many calls = complex
        elif counts["func_calls"] > 0:
            raw_points.append(0.2)   # Some calls = good
        else:
            raw_points.append(-0.1)  # No calls = might be too simple

        # Object initializations
        if counts["object_inits"] > 2:
            raw_points.append(-0.1)  # Too many objects = complex
        else:
            raw_points.append(0.0)

        # Code complexity
        complexity_score = calculate_code_complexity(code)
        if complexity_score > 0.5:
            raw_points.append(-0.2)  # High complexity = less utility-like
        else:
            raw_points.append(complexity_score * 0.1)

    except Exception:
        raw_points.extend([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    # Regex usage (utilities sometimes use regex)
    regex_count = count_regex_usage(code)
    if regex_count > 0:
        raw_points.append(0.1)
    else:
        raw_points.append(0.0)

    # Import usage
    import_words = count_import_words(code)
    if import_words > 10:
        raw_points.append(-0.1)  # Too many imports = complex
    elif import_words > 0:
        raw_points.append(0.1)   # Some imports = good
    else:
        raw_points.append(0.0)

    # Documentation ratio (this needs original code to work)
    if original_code:
        doc_ratio = calculate_documentation_ratio(original_code, code)
        raw_points.append((1.0 - doc_ratio) * 0.1)
    else:
        raw_points.append(0.0)

    # ----------------------
    # Proper normalization to 0–1
    # ----------------------
    # Convert to 0-1 scale using sigmoid-like function
    total_score = sum(raw_points)
    
    # Map to 0-1 using a more reasonable approach
    # Expected range is roughly -1 to +1, so we'll map that to 0-1
    normalized_score = (total_score + 1.0) / 2.0
    normalized_score = max(0.0, min(1.0, normalized_score))

    # Add some randomness/variance based on function name patterns
    function_name = node.get("label", "").lower()
    if any(word in function_name for word in ["util", "helper", "get", "set", "convert", "format"]):
        normalized_score += 0.1
    if any(word in function_name for word in ["main", "init", "process", "analyze", "complex"]):
        normalized_score -= 0.1
    
    normalized_score = max(0.0, min(1.0, normalized_score))

    # Assign final score and utility classification
    node["rank"] = round(normalized_score, 3)
    node["isUtil"] = normalized_score >= threshold
    
    # Keep legacy category for compatibility
    if normalized_score >= 0.7:
        node["category"] = "utility"
    elif normalized_score <= 0.4:
        node["category"] = "core"
    else:
        node["category"] = "mixed"

    return node

# --------------------------
# Apply to all functions
# --------------------------
def score_all_functions(graph_nodes: List[Dict[str, Any]], threshold: float = DEFAULT_THRESHOLD) -> List[Dict[str, Any]]:
    """Score all functions in the graph nodes list."""
    for node in graph_nodes:
        score_function(node, threshold)
    return graph_nodes

def process_data_files(data_dir: str = "data", threshold: float = DEFAULT_THRESHOLD) -> Dict[str, Any]:
    """Process all JSON files in the data directory and create ranked versions."""
    if not os.path.isabs(data_dir):
        # Find the project root (where setup.py or README.md exists)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = current_dir
        while project_root != os.path.dirname(project_root):
            if (os.path.exists(os.path.join(project_root, 'setup.py')) or 
                os.path.exists(os.path.join(project_root, 'README.md'))):
                break
            project_root = os.path.dirname(project_root)
        data_dir = os.path.join(project_root, data_dir)
    
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"Data directory does not exist: {data_dir}")
    
    # Find all JSON files in the data directory
    json_files = glob.glob(os.path.join(data_dir, "*.json"))
    
    results: Dict[str, Any] = {
        "processed_files": [],
        "total_functions": 0,
        "utility_functions": 0,
        "threshold_used": threshold
    }
    
    for json_file in json_files:
        # Extract base name (without extension)
        base_name = os.path.splitext(os.path.basename(json_file))[0]
        
        # Skip if it's already a ranked file
        if base_name.endswith("_rank"):
            continue
        
        try:
            # Read the original JSON file
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract graph nodes
            graph_nodes = data.get("analysisData", {}).get("graphNodes", [])
            
            if not graph_nodes:
                print(f"No graph nodes found in {json_file}")
                continue
            
            # Score all functions
            ranked_nodes = score_all_functions(graph_nodes.copy(), threshold)
            
            # Create output data structure
            ranked_data: Dict[str, Any] = {
                "analysisData": {
                    "graphNodes": ranked_nodes
                },
                "rankingInfo": {
                    "threshold": threshold,
                    "totalFunctions": len(ranked_nodes),
                    "utilityFunctions": sum(1 for node in ranked_nodes if node.get("isUtil", False)),
                    "averageRank": sum(node.get("rank", 0) for node in ranked_nodes) / len(ranked_nodes) if ranked_nodes else 0,
                    "processedAt": "2025-10-06"  # Current date
                }
            }
            
            # Save ranked file
            output_file = os.path.join(data_dir, f"{base_name}_rank.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(ranked_data, f, indent=2)
            
            # Update results
            results["processed_files"].append({
                "input_file": json_file,
                "output_file": output_file,
                "total_functions": len(ranked_nodes),
                "utility_functions": sum(1 for node in ranked_nodes if node.get("isUtil", False))
            })
            results["total_functions"] += len(ranked_nodes)
            results["utility_functions"] += sum(1 for node in ranked_nodes if node.get("isUtil", False))
            
            print(f"Processed {json_file} -> {output_file}")
            print(f"  Functions: {len(ranked_nodes)}, Utility: {sum(1 for node in ranked_nodes if node.get('isUtil', False))}")
            
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
    
    return results

def rank_code(data_dir: str = "data", threshold: float = DEFAULT_THRESHOLD) -> Dict[str, Any]:
    """
    Convenience function to rank code functions.
    
    Args:
        data_dir (str): Directory containing JSON files to process
        threshold (float): Threshold for utility classification (default: 0.8)
        
    Returns:
        Dict[str, Any]: Processing results
    """
    return process_data_files(data_dir, threshold)

if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    threshold = float(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_THRESHOLD
    
    print(f"Processing files in '{data_dir}' with threshold {threshold}")
    
    try:
        results = rank_code(data_dir, threshold)
        print("\n" + "="*50)
        print("RANKING COMPLETE")
        print("="*50)
        print(f"Processed {len(results['processed_files'])} files")
        print(f"Total functions: {results['total_functions']}")
        print(f"Utility functions: {results['utility_functions']}")
        print(f"Utility ratio: {results['utility_functions']/results['total_functions']*100:.1f}%" if results['total_functions'] > 0 else "Utility ratio: 0%")
        print(f"Threshold used: {results['threshold_used']}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

#!/usr/bin/env python3
"""
Data transformation utility for converting various JSON formats to utilityCheck format.
Handles missing code fields and normalizes data structure.
"""

import json
import os
import glob
from typing import Dict, Any, List, Optional

def transform_data_file(input_file: str, output_file: str) -> Dict[str, Any]:
    """
    Transform a single data file to the expected format.
    
    Args:
        input_file (str): Path to input JSON file
        output_file (str): Path to output JSON file
        
    Returns:
        Dict[str, Any]: Transformation summary
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data: Any = json.load(f)
        
        graph_nodes: List[Any]
        # Extract graph nodes
        if isinstance(data, dict) and "analysisData" in data:
            analysis_data: Dict[str, Any] = data["analysisData"]
            if isinstance(analysis_data, dict):
                graph_nodes = analysis_data.get("graphNodes", [])
            else:
                graph_nodes = []
        elif isinstance(data, dict) and "graphNodes" in data:
            graph_nodes = data["graphNodes"]
        elif isinstance(data, list):
            graph_nodes = data
        else:
            print(f"Warning: Unexpected data structure in {input_file}")
            return {"status": "error", "message": "Unexpected data structure"}
        
        # Transform nodes
        transformed_nodes: List[Dict[str, Any]] = []
        skipped_count: int = 0
        transformed_count: int = 0
        
        for node in graph_nodes:
            if not isinstance(node, dict):
                continue
            
            # Handle missing or null code
            code: Any = node.get("code")
            if code is None or code == "null":
                # Skip nodes without code or generate placeholder
                skipped_count += 1
                continue
            
            # Ensure code is a string
            if not isinstance(code, str):
                code = str(code)
            
            # Get label with fallbacks
            label = node.get("label")
            if label is None:
                label = node.get("name", "unknown")
                
            # Create standardized node
            transformed_node: Dict[str, Any] = {
                "id": node.get("id", f"unknown_{len(transformed_nodes)}"),
                "label": label,
                "code": code,
                "language": node.get("language", "py")  # Default to Python
            }
            
            # Add optional fields if present
            if "type" in node:
                transformed_node["type"] = node["type"]
            
            transformed_nodes.append(transformed_node)
            transformed_count += 1
        
        # Create output structure
        output_data: Dict[str, Any] = {
            "analysisData": {
                "graphNodes": transformed_nodes
            }
        }
        
        # Write transformed data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        
        return {
            "status": "success",
            "input_file": input_file,
            "output_file": output_file,
            "original_count": len(graph_nodes),
            "transformed_count": transformed_count,
            "skipped_count": skipped_count
        }
        
    except Exception as e:
        return {
            "status": "error",
            "input_file": input_file,
            "message": str(e)
        }

def transform_directory(input_dir: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Transform all JSON files in a directory.
    
    Args:
        input_dir (str): Input directory path
        output_dir (str): Output directory path (defaults to input_dir)
        
    Returns:
        Dict[str, Any]: Summary of transformations
    """
    if output_dir is None:
        output_dir = input_dir
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all JSON files
    json_files: List[str] = glob.glob(os.path.join(input_dir, "*.json"))
    
    results: Dict[str, Any] = {
        "total_files": len(json_files),
        "successful": 0,
        "errors": 0,
        "total_functions": 0,
        "total_skipped": 0,
        "files": []
    }
    
    for json_file in json_files:
        # Skip already processed files (avoid overwriting ranked files)
        if json_file.endswith("_rank.json") or json_file.endswith("_transformed.json"):
            continue
        
        # Create output filename
        base_name: str = os.path.splitext(os.path.basename(json_file))[0]
        output_file: str
        if input_dir == output_dir:
            output_file = os.path.join(output_dir, f"{base_name}_transformed.json")
        else:
            output_file = os.path.join(output_dir, f"{base_name}.json")
        
        # Transform file
        result: Dict[str, Any] = transform_data_file(json_file, output_file)
        results["files"].append(result)
        
        if result["status"] == "success":
            results["successful"] += 1
            results["total_functions"] += result["transformed_count"]
            results["total_skipped"] += result["skipped_count"]
            print(f"✓ Transformed {json_file}")
            print(f"  Functions: {result['transformed_count']}, Skipped: {result['skipped_count']}")
        else:
            results["errors"] += 1
            print(f"✗ Error transforming {json_file}: {result['message']}")
    
    return results

def main() -> None:
    """Main function for command line usage."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python transformData.py <input_directory> [output_directory]")
        print("       python transformData.py <input_file.json> [output_file.json]")
        sys.exit(1)
    
    input_path: str = sys.argv[1]
    
    if os.path.isfile(input_path):
        # Single file transformation
        output_file: str
        if len(sys.argv) > 2:
            output_file = sys.argv[2]
        else:
            base_name: str = os.path.splitext(input_path)[0]
            output_file = f"{base_name}_transformed.json"
        
        print(f"Transforming file: {input_path}")
        result: Dict[str, Any] = transform_data_file(input_path, output_file)
        
        if result["status"] == "success":
            print(f"✓ Success: {result['transformed_count']} functions, {result['skipped_count']} skipped")
            print(f"Output: {result['output_file']}")
        else:
            print(f"✗ Error: {result['message']}")
            sys.exit(1)
    
    elif os.path.isdir(input_path):
        # Directory transformation
        output_dir: str = sys.argv[2] if len(sys.argv) > 2 else input_path
        
        print(f"Transforming directory: {input_path}")
        print(f"Output directory: {output_dir}")
        
        results: Dict[str, Any] = transform_directory(input_path, output_dir)
        
        print("\n" + "="*50)
        print("TRANSFORMATION COMPLETE")
        print("="*50)
        print(f"Files processed: {results['total_files']}")
        print(f"Successful: {results['successful']}")
        print(f"Errors: {results['errors']}")
        print(f"Total functions: {results['total_functions']}")
        print(f"Total skipped: {results['total_skipped']}")
        
        if results['errors'] > 0:
            sys.exit(1)
    
    else:
        print(f"Error: {input_path} is neither a file nor a directory")
        sys.exit(1)

if __name__ == "__main__":
    main()
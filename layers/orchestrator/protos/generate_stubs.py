#!/usr/bin/env python3
"""
Generate Python gRPC stubs from task_service.proto

Usage:
    python generate_stubs.py

Requires grpcio-tools: pip install grpcio-tools
"""

import subprocess
import sys
from pathlib import Path


def main():
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    
    proto_file = script_dir / "task_service.proto"
    output_dir = script_dir
    
    if not proto_file.exists():
        print(f"Error: Proto file not found: {proto_file}")
        return 1
    
    print(f"Generating Python gRPC stubs from {proto_file}...")
    
    # Run protoc via grpc_tools
    cmd = [
        sys.executable, "-m", "grpc_tools.protoc",
        f"-I{script_dir}",
        f"--python_out={output_dir}",
        f"--grpc_python_out={output_dir}",
        str(proto_file),
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error generating stubs:")
        print(result.stderr)
        return 1
    
    print("Successfully generated:")
    print(f"  - {output_dir / 'task_service_pb2.py'}")
    print(f"  - {output_dir / 'task_service_pb2_grpc.py'}")
    
    # Fix the import in the grpc file (known issue with protoc)
    grpc_file = output_dir / "task_service_pb2_grpc.py"
    if grpc_file.exists():
        content = grpc_file.read_text()
        # Change absolute import to relative import
        fixed = content.replace(
            "import task_service_pb2 as task__service__pb2",
            "from . import task_service_pb2 as task__service__pb2"
        )
        if fixed != content:
            grpc_file.write_text(fixed)
            print("  - Fixed imports in task_service_pb2_grpc.py")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

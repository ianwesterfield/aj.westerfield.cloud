"""
Tests for WorkspaceState - External State Tracking

Tests the workspace state manager that maintains ground-truth state
from actual tool outputs (rather than LLM tracking).
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


# Inline minimal implementation for testing
@dataclass
class CompletedStep:
    """Record of a completed step."""
    step_id: str
    tool: str
    params: Dict[str, Any]
    output_summary: str
    success: bool
    timestamp: Optional[str] = None


@dataclass
class WorkspaceState:
    """External state maintained by orchestrator."""
    scanned_paths: Set[str] = field(default_factory=set)
    files: List[str] = field(default_factory=list)
    dirs: List[str] = field(default_factory=list)
    edited_files: Set[str] = field(default_factory=set)
    read_files: Set[str] = field(default_factory=set)
    completed_steps: List[CompletedStep] = field(default_factory=list)
    user_info: Dict[str, str] = field(default_factory=dict)
    
    def update_from_step(self, tool: str, params: Dict[str, Any], output: str, success: bool) -> None:
        step_id = f"S{len(self.completed_steps) + 1:03d}"
        
        if tool == "scan_workspace":
            scan_path = params.get("path", ".")
            self.scanned_paths.add(scan_path)
            self._parse_scan_output(output, scan_path)
            summary = f"scan({scan_path}): {len(self.files)} files, {len(self.dirs)} dirs"
        elif tool == "read_file":
            path = params.get("path", "")
            self.read_files.add(path)
            char_count = len(output) if output else 0
            summary = f"read({path}): {char_count:,} chars"
        elif tool in ("write_file", "replace_in_file", "insert_in_file", "append_to_file"):
            path = params.get("path", "")
            if success:
                self.edited_files.add(path)
            summary = f"{tool}({path}): {'OK' if success else 'FAILED'}"
        elif tool == "execute_shell":
            cmd = params.get("command", "")[:40]
            summary = f"shell({cmd}): {'OK' if success else 'FAILED'}"
        elif tool == "none":
            reason = params.get("reason", "already present")
            path = params.get("path", "")
            summary = f"skipped({path}): {reason}" if path else f"skipped: {reason}"
        else:
            summary = f"{tool}: {'OK' if success else 'FAILED'}"
        
        self.completed_steps.append(CompletedStep(
            step_id=step_id, tool=tool, params=params,
            output_summary=summary, success=success,
        ))
    
    def _parse_scan_output(self, output: str, base_path: str) -> None:
        if not output:
            return
        for line in output.split("\n"):
            line = line.strip()
            if not line or line.startswith("PATH:") or line.startswith("TOTAL:"):
                continue
            if line.startswith("-") or line.startswith("NAME"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0]
                entry_type = parts[1] if len(parts) > 1 else ""
                full_path = name.rstrip("/")
                if entry_type == "dir" or name.endswith("/"):
                    if full_path not in self.dirs:
                        self.dirs.append(full_path)
                elif entry_type == "file":
                    if full_path not in self.files:
                        self.files.append(full_path)
    
    def get_editable_files(self) -> List[str]:
        editable_ext = {'.md', '.py', '.js', '.ts', '.yaml', '.yml', '.json', '.txt'}
        binary_ext = {'.png', '.jpg', '.pyc', '.safetensors'}
        return sorted([
            f for f in self.files
            if f not in self.edited_files
            and not any(f.endswith(ext) for ext in binary_ext)
            and any(f.endswith(ext) for ext in editable_ext)
        ])
    
    def get_unread_files(self) -> List[str]:
        return [f for f in self.files if f not in self.read_files]
    
    def format_for_prompt(self) -> str:
        lines = ["=== WORKSPACE STATE ==="]
        if self.completed_steps:
            lines.append("Completed steps:")
            for step in self.completed_steps[-15:]:
                status = "✓" if step.success else "✗"
                lines.append(f"  {status} {step.output_summary}")
        if self.read_files:
            lines.append(f"Already read ({len(self.read_files)}):")
            for f in sorted(self.read_files)[:10]:
                lines.append(f"  📖 {f}")
        if self.user_info:
            lines.append("User info:")
            for key, value in self.user_info.items():
                lines.append(f"  {key}: {value}")
        lines.append("=== END STATE ===")
        return "\n".join(lines)
    
    def has_scanned(self, path: str = ".") -> bool:
        return path in self.scanned_paths
    
    def has_edited(self, path: str) -> bool:
        return path in self.edited_files
    
    def has_read(self, path: str) -> bool:
        return path in self.read_files
    
    def reset(self) -> None:
        self.scanned_paths.clear()
        self.files.clear()
        self.dirs.clear()
        self.edited_files.clear()
        self.read_files.clear()
        self.completed_steps.clear()


_current_state: Optional[WorkspaceState] = None

def get_workspace_state() -> WorkspaceState:
    global _current_state
    if _current_state is None:
        _current_state = WorkspaceState()
    return _current_state

def reset_workspace_state() -> WorkspaceState:
    global _current_state
    _current_state = WorkspaceState()
    return _current_state


class TestWorkspaceStateBasics:
    """Test basic state operations."""
    
    def test_init_empty_state(self):
        """Fresh state should be empty."""
        state = WorkspaceState()
        assert len(state.scanned_paths) == 0
        assert len(state.files) == 0
        assert len(state.dirs) == 0
        assert len(state.edited_files) == 0
        assert len(state.read_files) == 0
        assert len(state.completed_steps) == 0
        assert len(state.user_info) == 0
    
    def test_reset_clears_state(self):
        """Reset should clear all state except user_info."""
        state = WorkspaceState()
        state.scanned_paths.add(".")
        state.files.append("test.py")
        state.edited_files.add("test.py")
        state.read_files.add("test.py")
        state.user_info["name"] = "Test"
        
        state.reset()
        
        assert len(state.scanned_paths) == 0
        assert len(state.files) == 0
        assert len(state.edited_files) == 0
        assert len(state.read_files) == 0
        # user_info should persist
        assert state.user_info.get("name") == "Test"


class TestUpdateFromStep:
    """Test state updates from tool execution."""
    
    def test_scan_workspace_update(self):
        """Scan workspace should update scanned_paths."""
        state = WorkspaceState()
        
        output = """PATH: /workspace
TOTAL: 3 items (1 dirs, 2 files)

NAME          TYPE   SIZE      MODIFIED
----------------------------------------------
filters/      dir    -         2024-01-01
README.md     file   1.2 KB    2024-01-01
test.py       file   500 B     2024-01-01
"""
        state.update_from_step("scan_workspace", {"path": "."}, output, True)
        
        assert "." in state.scanned_paths
        assert len(state.completed_steps) == 1
        assert state.completed_steps[0].tool == "scan_workspace"
        assert state.completed_steps[0].success is True
    
    def test_read_file_update(self):
        """Read file should add to read_files set."""
        state = WorkspaceState()
        
        state.update_from_step("read_file", {"path": "test.py"}, "content here", True)
        
        assert "test.py" in state.read_files
        assert len(state.completed_steps) == 1
        assert "read(test.py)" in state.completed_steps[0].output_summary
    
    def test_write_file_success_update(self):
        """Successful write should add to edited_files."""
        state = WorkspaceState()
        
        state.update_from_step("write_file", {"path": "new.py"}, "Written 100 bytes", True)
        
        assert "new.py" in state.edited_files
        assert state.completed_steps[0].success is True
    
    def test_write_file_failure_not_edited(self):
        """Failed write should NOT add to edited_files."""
        state = WorkspaceState()
        
        state.update_from_step("write_file", {"path": "fail.py"}, "Error", False)
        
        assert "fail.py" not in state.edited_files
        assert state.completed_steps[0].success is False
    
    def test_replace_in_file_update(self):
        """Replace in file should update edited_files on success."""
        state = WorkspaceState()
        
        state.update_from_step(
            "replace_in_file", 
            {"path": "config.py", "old_text": "old", "new_text": "new"}, 
            "Replaced 1 occurrence", 
            True
        )
        
        assert "config.py" in state.edited_files
    
    def test_insert_in_file_update(self):
        """Insert in file should update edited_files on success."""
        state = WorkspaceState()
        
        state.update_from_step(
            "insert_in_file", 
            {"path": "readme.md", "position": "start", "text": "# Header"}, 
            "Inserted", 
            True
        )
        
        assert "readme.md" in state.edited_files
    
    def test_shell_command_update(self):
        """Shell commands should be recorded in steps."""
        state = WorkspaceState()
        
        state.update_from_step(
            "execute_shell", 
            {"command": "git status"}, 
            "On branch main", 
            True
        )
        
        assert len(state.completed_steps) == 1
        assert "shell(git status)" in state.completed_steps[0].output_summary
    
    def test_none_tool_skip(self):
        """None tool (idempotent skip) should be recorded."""
        state = WorkspaceState()
        
        state.update_from_step(
            "none",
            {"reason": "already present", "path": "test.py"},
            "",
            True
        )
        
        assert "skipped" in state.completed_steps[0].output_summary


class TestParseScanOutput:
    """Test parsing of scan_workspace output."""
    
    def test_parse_standard_format(self):
        """Parse standard ls-style output."""
        state = WorkspaceState()
        
        output = """PATH: /workspace
TOTAL: 4 items (2 dirs, 2 files)

NAME          TYPE   SIZE      MODIFIED
----------------------------------------------
.github/      dir    -         2024-01-01
layers/       dir    -         2024-01-01
README.md     file   1.2 KB    2024-01-01
setup.py      file   500 B     2024-01-01
"""
        state._parse_scan_output(output, ".")
        
        assert ".github" in state.dirs or ".github/" in state.dirs
        assert "layers" in state.dirs or "layers/" in state.dirs
        assert "README.md" in state.files
        assert "setup.py" in state.files
    
    def test_parse_nested_path(self):
        """Parse output with base path."""
        state = WorkspaceState()
        
        output = """PATH: /workspace/layers
NAME          TYPE
-------------------
memory/       dir
executor/     dir
main.py       file
"""
        state._parse_scan_output(output, "layers")
        
        # Should have parsed the dirs (strips trailing /)
        assert "memory" in state.dirs
        assert "executor" in state.dirs
        assert "main.py" in state.files
    
    def test_skip_headers_and_separators(self):
        """Should skip header lines and separators."""
        state = WorkspaceState()
        
        output = """PATH: .
NAME          TYPE
-------------------
test.py       file
"""
        state._parse_scan_output(output, ".")
        
        # Should only have test.py, not headers
        assert len(state.files) == 1
        assert "test.py" in state.files


class TestEditableFiles:
    """Test editable file filtering."""
    
    def test_get_editable_files_filters_binary(self):
        """Should exclude binary files."""
        state = WorkspaceState()
        state.files = ["test.py", "image.png", "model.safetensors", "config.json"]
        
        editable = state.get_editable_files()
        
        assert "test.py" in editable
        assert "config.json" in editable
        assert "image.png" not in editable
        assert "model.safetensors" not in editable
    
    def test_get_editable_files_excludes_edited(self):
        """Should exclude already edited files."""
        state = WorkspaceState()
        state.files = ["a.py", "b.py", "c.py"]
        state.edited_files.add("b.py")
        
        editable = state.get_editable_files()
        
        assert "a.py" in editable
        assert "b.py" not in editable
        assert "c.py" in editable
    
    def test_get_unread_files(self):
        """Should return files not yet read."""
        state = WorkspaceState()
        state.files = ["a.py", "b.py", "c.py"]
        state.read_files.add("a.py")
        
        unread = state.get_unread_files()
        
        assert "a.py" not in unread
        assert "b.py" in unread
        assert "c.py" in unread


class TestFormatForPrompt:
    """Test prompt context formatting."""
    
    def test_format_empty_state(self):
        """Empty state should still produce valid format."""
        state = WorkspaceState()
        
        output = state.format_for_prompt()
        
        assert "WORKSPACE STATE" in output
        assert "END STATE" in output
    
    def test_format_with_completed_steps(self):
        """Should include completed steps."""
        state = WorkspaceState()
        state.update_from_step("scan_workspace", {"path": "."}, "output", True)
        
        output = state.format_for_prompt()
        
        assert "Completed steps" in output
        assert "✓" in output  # Success marker
    
    def test_format_with_read_files(self):
        """Should show already read files."""
        state = WorkspaceState()
        state.read_files.add("test.py")
        
        output = state.format_for_prompt()
        
        assert "Already read" in output
        assert "test.py" in output
    
    def test_format_with_user_info(self):
        """Should include user info."""
        state = WorkspaceState()
        state.user_info["name"] = "Ian"
        
        output = state.format_for_prompt()
        
        assert "User info" in output
        assert "Ian" in output


class TestStateChecks:
    """Test state query methods."""
    
    def test_has_scanned(self):
        """Test scanned path checking."""
        state = WorkspaceState()
        
        assert state.has_scanned(".") is False
        state.scanned_paths.add(".")
        assert state.has_scanned(".") is True
    
    def test_has_edited(self):
        """Test edited file checking."""
        state = WorkspaceState()
        
        assert state.has_edited("test.py") is False
        state.edited_files.add("test.py")
        assert state.has_edited("test.py") is True
    
    def test_has_read(self):
        """Test read file checking."""
        state = WorkspaceState()
        
        assert state.has_read("test.py") is False
        state.read_files.add("test.py")
        assert state.has_read("test.py") is True


class TestSingletonState:
    """Test singleton state management."""
    
    def test_get_workspace_state_returns_same_instance(self):
        """Should return same instance on repeated calls."""
        reset_workspace_state()  # Start fresh
        
        state1 = get_workspace_state()
        state2 = get_workspace_state()
        
        assert state1 is state2
    
    def test_reset_creates_new_instance(self):
        """Reset should create a new instance."""
        state1 = get_workspace_state()
        state1.scanned_paths.add("test")
        
        state2 = reset_workspace_state()
        
        assert "test" not in state2.scanned_paths


class TestMetadataCaching:
    """Tests for metadata caching from command outputs."""
    
    def test_file_metadata_extracted_from_scan(self):
        """File sizes should be cached when scanning workspace."""
        # Import actual implementation
        import sys
        sys.path.insert(0, str(__file__).replace("tests\\test_workspace_state.py", "layers\\orchestrator"))
        from services.workspace_state import WorkspaceState as ActualState, FileMetadata, EnvironmentFacts
        
        state = ActualState()
        
        scan_output = """PATH: .
TOTAL: 5 items (2 dirs, 3 files)

NAME                  TYPE      SIZE      MODIFIED
-------------------------------------------------
src/                  dir       -         2025-01-01
tests/                dir       -         2025-01-01
README.md             file      1.2 KiB   2025-01-01
setup.py              file      500 B     2025-01-01
requirements.txt      file      128 B     2025-01-01
"""
        state.update_from_step("scan_workspace", {"path": "."}, scan_output, True)
        
        # Check file metadata was extracted
        assert "README.md" in state.file_metadata
        assert state.file_metadata["README.md"].size_human == "1.2"
        
        assert "setup.py" in state.file_metadata
        
        # Check environment facts updated
        assert state.environment_facts.total_file_count == 3
        assert state.environment_facts.total_dir_count == 2
        assert "python" in state.environment_facts.project_types  # .py file detected
        assert "pip" in state.environment_facts.package_managers  # requirements.txt detected
    
    def test_shell_facts_extraction(self):
        """Environment facts should be extracted from shell command outputs."""
        import sys
        sys.path.insert(0, str(__file__).replace("tests\\test_workspace_state.py", "layers\\orchestrator"))
        from services.workspace_state import WorkspaceState as ActualState
        
        state = ActualState()
        
        # Git status output
        git_output = """On branch feature/metadata-cache
Your branch is up to date with 'origin/feature/metadata-cache'.

nothing to commit, working tree clean"""
        
        state.update_from_step("execute_shell", {"command": "git status"}, git_output, True)
        
        assert state.environment_facts.git_branch == "feature/metadata-cache"
    
    def test_python_version_extraction(self):
        """Python version should be extracted from python --version."""
        import sys
        sys.path.insert(0, str(__file__).replace("tests\\test_workspace_state.py", "layers\\orchestrator"))
        from services.workspace_state import WorkspaceState as ActualState
        
        state = ActualState()
        state.update_from_step("execute_shell", {"command": "python --version"}, "Python 3.11.5", True)
        
        assert state.environment_facts.python_version == "3.11.5"
    
    def test_size_parsing(self):
        """Human-readable sizes should be converted to bytes."""
        import sys
        sys.path.insert(0, str(__file__).replace("tests\\test_workspace_state.py", "layers\\orchestrator"))
        from services.workspace_state import WorkspaceState as ActualState
        
        state = ActualState()
        
        # Test various size formats
        assert state._parse_size_to_bytes("100 B") == 100
        assert state._parse_size_to_bytes("1 KiB") == 1024
        assert state._parse_size_to_bytes("1.5 MiB") == int(1.5 * 1024 * 1024)
        assert state._parse_size_to_bytes("-") is None
        assert state._parse_size_to_bytes("") is None
    
    def test_read_file_adds_line_count(self):
        """Reading files should cache line count metadata."""
        import sys
        sys.path.insert(0, str(__file__).replace("tests\\test_workspace_state.py", "layers\\orchestrator"))
        from services.workspace_state import WorkspaceState as ActualState
        
        state = ActualState()
        
        file_content = """line 1
line 2
line 3
line 4
line 5"""
        
        state.update_from_step("read_file", {"path": "test.py"}, file_content, True)
        
        assert "test.py" in state.file_metadata
        assert state.file_metadata["test.py"].line_count == 5
    
    def test_format_for_prompt_includes_metadata(self):
        """format_for_prompt should include environment facts and largest files."""
        import sys
        sys.path.insert(0, str(__file__).replace("tests\\test_workspace_state.py", "layers\\orchestrator"))
        from services.workspace_state import WorkspaceState as ActualState, FileMetadata
        
        state = ActualState()
        state.files = ["README.md", "large_file.bin"]
        state.dirs = ["src"]
        state.scanned_paths.add(".")
        
        # Add file metadata
        state.file_metadata["README.md"] = FileMetadata(
            path="README.md", size_bytes=1024, size_human="1.0 KiB"
        )
        state.file_metadata["large_file.bin"] = FileMetadata(
            path="large_file.bin", size_bytes=10*1024*1024, size_human="10.0 MiB"
        )
        
        # Add environment facts
        state.environment_facts.project_types.add("python")
        state.environment_facts.git_branch = "main"
        state.environment_facts.add_observation("Found 42 Python packages")
        
        output = state.format_for_prompt()
        
        # Check sections present
        assert "ENVIRONMENT FACTS" in output
        assert "python" in output.lower()
        assert "Git branch: main" in output
        assert "OBSERVATIONS" in output
        assert "42 Python packages" in output
        assert "LARGEST FILES" in output
        assert "large_file.bin" in output


class TestConversationLedger:
    """Tests for the conversation ledger feature."""
    
    def test_user_requests_tracked(self):
        """User requests should be logged to the ledger."""
        import sys
        sys.path.insert(0, str(__file__).replace("tests\\test_workspace_state.py", "layers\\orchestrator"))
        from services.workspace_state import WorkspaceState as ActualState
        
        state = ActualState()
        state.add_user_request("List all files in the workspace")
        state.add_user_request("How much space does it consume?")
        
        assert len(state.ledger.user_requests) == 2
        assert "List all files" in state.ledger.user_requests[0]
        assert "space" in state.ledger.user_requests[1]
    
    def test_ip_addresses_extracted(self):
        """IP addresses should be extracted from command outputs."""
        import sys
        sys.path.insert(0, str(__file__).replace("tests\\test_workspace_state.py", "layers\\orchestrator"))
        from services.workspace_state import WorkspaceState as ActualState
        
        state = ActualState()
        output = "Server started at 192.168.1.100:8080"
        state.update_from_step("execute_shell", {"command": "start server"}, output, True)
        
        assert "IP address" in state.ledger.extracted_values
        assert "192.168.1.100" in state.ledger.extracted_values["IP address"]
    
    def test_urls_extracted(self):
        """URLs should be extracted from command outputs."""
        import sys
        sys.path.insert(0, str(__file__).replace("tests\\test_workspace_state.py", "layers\\orchestrator"))
        from services.workspace_state import WorkspaceState as ActualState
        
        state = ActualState()
        output = "API docs available at https://api.example.com/docs"
        state.update_from_step("execute_shell", {"command": "curl"}, output, True)
        
        assert "URL" in state.ledger.extracted_values
        assert "https://api.example.com/docs" in state.ledger.extracted_values["URL"]
    
    def test_ports_extracted(self):
        """Port numbers should be extracted from command outputs."""
        import sys
        sys.path.insert(0, str(__file__).replace("tests\\test_workspace_state.py", "layers\\orchestrator"))
        from services.workspace_state import WorkspaceState as ActualState
        
        state = ActualState()
        output = "Server listening on port 8443"
        state.update_from_step("execute_shell", {"command": "start"}, output, True)
        
        assert "Port" in state.ledger.extracted_values
        assert "8443" in state.ledger.extracted_values["Port"]
    
    def test_ledger_in_prompt_output(self):
        """Ledger should appear in format_for_prompt output."""
        import sys
        sys.path.insert(0, str(__file__).replace("tests\\test_workspace_state.py", "layers\\orchestrator"))
        from services.workspace_state import WorkspaceState as ActualState
        
        state = ActualState()
        state.add_user_request("Deploy to production")
        state.ledger.extract_value("Server IP", "10.0.0.5", "deploy")
        
        output = state.format_for_prompt()
        
        assert "QUICK REFERENCE" in output
        assert "10.0.0.5" in output
        assert "USER REQUESTS" in output
        assert "Deploy" in output
    
    def test_ledger_preserved_across_reset(self):
        """Ledger should be preserved when reset() is called."""
        import sys
        sys.path.insert(0, str(__file__).replace("tests\\test_workspace_state.py", "layers\\orchestrator"))
        from services.workspace_state import WorkspaceState as ActualState
        
        state = ActualState()
        state.add_user_request("First request")
        state.files = ["test.py"]
        
        state.reset()
        
        # Files cleared, but ledger preserved
        assert len(state.files) == 0
        assert len(state.ledger.user_requests) == 1
        assert "First request" in state.ledger.user_requests[0]
    
    def test_actions_logged(self):
        """Tool actions should be logged to the ledger."""
        import sys
        sys.path.insert(0, str(__file__).replace("tests\\test_workspace_state.py", "layers\\orchestrator"))
        from services.workspace_state import WorkspaceState as ActualState
        
        state = ActualState()
        state.update_from_step("read_file", {"path": "config.yaml"}, "content here", True)
        
        action_entries = [e for e in state.ledger.entries if e.entry_type == "action"]
        assert len(action_entries) == 1
        assert "read_file" in action_entries[0].summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

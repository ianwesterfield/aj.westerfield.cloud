"""
Tests for AgentTargetExtractor and CommandRedirector - 100% coverage target.
"""

import pytest
import sys
import os

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "layers", "orchestrator")
)

from services.helpers.agent_utils import AgentTargetExtractor, CommandRedirector


class TestAgentTargetExtractor:
    AGENTS = ["ians-r16", "domain01", "domain02", "exchange01", "r730xd"]

    def test_empty_request(self):
        assert AgentTargetExtractor.extract_target_agent("", self.AGENTS) is None

    def test_empty_agents(self):
        assert AgentTargetExtractor.extract_target_agent("hello", []) is None

    def test_both_empty(self):
        assert AgentTargetExtractor.extract_target_agent("", []) is None

    # Contextual references
    def test_my_workstation(self):
        result = AgentTargetExtractor.extract_target_agent(
            "check my workstation", self.AGENTS
        )
        assert result == "ians-r16"  # matches workstation indicator pattern

    def test_my_pc(self):
        result = AgentTargetExtractor.extract_target_agent("reboot my pc", self.AGENTS)
        assert result is not None

    def test_my_machine(self):
        result = AgentTargetExtractor.extract_target_agent(
            "update my machine", self.AGENTS
        )
        assert result is not None

    def test_my_computer(self):
        result = AgentTargetExtractor.extract_target_agent(
            "what's on my computer", self.AGENTS
        )
        assert result is not None

    def test_my_desktop(self):
        result = AgentTargetExtractor.extract_target_agent(
            "check my desktop", self.AGENTS
        )
        assert result is not None

    def test_my_laptop(self):
        result = AgentTargetExtractor.extract_target_agent(
            "scan my laptop", self.AGENTS
        )
        assert result is not None

    def test_workstation_keyword(self):
        result = AgentTargetExtractor.extract_target_agent(
            "check the workstation", self.AGENTS
        )
        assert result is not None

    def test_personal_machine(self):
        result = AgentTargetExtractor.extract_target_agent(
            "check personal machine", self.AGENTS
        )
        assert result is not None

    def test_contextual_user_pattern_fallback(self):
        # No workstation indicator matches, fall back to user-pattern regex
        agents = ["janes-ws01", "server01"]
        result = AgentTargetExtractor.extract_target_agent(
            "check my workstation", agents
        )
        assert result is not None

    # Exact match
    def test_exact_match(self):
        result = AgentTargetExtractor.extract_target_agent(
            "reboot domain01", self.AGENTS
        )
        assert result == "domain01"

    def test_exact_match_case_insensitive(self):
        result = AgentTargetExtractor.extract_target_agent(
            "check DOMAIN01 status", self.AGENTS
        )
        assert result == "domain01"

    # Quoted target
    def test_quoted_target_single(self):
        result = AgentTargetExtractor.extract_target_agent(
            "restart 'domain02'", self.AGENTS
        )
        assert result == "domain02"

    def test_quoted_target_double(self):
        result = AgentTargetExtractor.extract_target_agent(
            'restart "exchange01"', self.AGENTS
        )
        assert result == "exchange01"

    def test_quoted_partial_match(self):
        result = AgentTargetExtractor.extract_target_agent(
            "check 'domain'", self.AGENTS
        )
        assert result in ("domain01", "domain02")

    def test_quoted_no_match(self):
        result = AgentTargetExtractor.extract_target_agent(
            "check 'nonexistent'", self.AGENTS
        )
        # Falls through to action patterns or no match
        assert result is None or result in self.AGENTS

    # Action patterns
    def test_action_reboot(self):
        result = AgentTargetExtractor.extract_target_agent(
            "reboot r730xd now", self.AGENTS
        )
        assert result == "r730xd"

    def test_action_on_preposition(self):
        result = AgentTargetExtractor.extract_target_agent(
            "run command on domain01", self.AGENTS
        )
        assert result == "domain01"

    def test_action_to_preposition(self):
        result = AgentTargetExtractor.extract_target_agent(
            "send data to exchange01", self.AGENTS
        )
        assert result == "exchange01"

    def test_action_check(self):
        result = AgentTargetExtractor.extract_target_agent(
            "check r730xd status", self.AGENTS
        )
        assert result == "r730xd"

    # No match
    def test_no_match(self):
        result = AgentTargetExtractor.extract_target_agent(
            "what is the weather today", self.AGENTS
        )
        assert result is None


class TestCommandRedirector:
    def test_python_code_redirect(self):
        result = CommandRedirector.redirect_workspace_command(
            "", code="import os\ndef main():\n    pass"
        )
        assert result is not None
        assert result.tool == "write_file"
        assert result.params["path"] == "app.py"

    def test_flask_code_redirect(self):
        result = CommandRedirector.redirect_workspace_command(
            "", code="from flask import Flask\napp = Flask(__name__)"
        )
        assert result is not None
        assert result.params["path"] == "app.py"

    def test_django_code_redirect(self):
        result = CommandRedirector.redirect_workspace_command(
            "", code="import django\nclass MyModel:\n    pass"
        )
        assert result is not None
        assert result.params["path"] == "manage.py"

    def test_class_code_redirect(self):
        result = CommandRedirector.redirect_workspace_command(
            "", code="class MyClass:\n    def method(self):\n        pass"
        )
        assert result is not None
        assert result.tool == "write_file"

    def test_touch_redirect(self):
        result = CommandRedirector.redirect_workspace_command("touch newfile.txt")
        assert result is not None
        assert result.tool == "write_file"
        assert result.params["path"] == "newfile.txt"
        assert result.params["content"] == ""

    def test_touch_with_workspace_prefix(self):
        result = CommandRedirector.redirect_workspace_command(
            "touch /workspace/newfile.txt"
        )
        assert result is not None
        assert result.params["path"] == "newfile.txt"

    def test_touch_no_filename(self):
        result = CommandRedirector.redirect_workspace_command("touch ")
        assert result is not None
        assert result.params["path"] == "unnamed.txt"

    def test_echo_redirect(self):
        result = CommandRedirector.redirect_workspace_command(
            'echo "hello world" > output.txt'
        )
        assert result is not None
        assert result.tool == "write_file"
        assert result.params["path"] == "output.txt"
        assert result.params["content"] == "hello world"

    def test_echo_with_n_flag(self):
        result = CommandRedirector.redirect_workspace_command(
            "echo -n 'test' > file.txt"
        )
        assert result is not None
        assert result.params["content"] == "test"

    def test_echo_with_workspace_prefix(self):
        result = CommandRedirector.redirect_workspace_command(
            'echo "data" > /workspace/file.txt'
        )
        assert result is not None
        assert result.params["path"] == "file.txt"

    def test_cat_redirect(self):
        result = CommandRedirector.redirect_workspace_command("cat README.md")
        assert result is not None
        assert result.tool == "read_file"
        assert result.params["path"] == "README.md"

    def test_cat_with_workspace_prefix(self):
        result = CommandRedirector.redirect_workspace_command(
            "cat /workspace/README.md"
        )
        assert result is not None
        assert result.params["path"] == "README.md"

    def test_find_redirect(self):
        result = CommandRedirector.redirect_workspace_command("find . -name '*.py'")
        assert result is not None
        assert result.tool == "scan_workspace"

    def test_ls_redirect(self):
        result = CommandRedirector.redirect_workspace_command("ls -la")
        assert result is not None
        assert result.tool == "scan_workspace"

    def test_mkdir_redirect(self):
        result = CommandRedirector.redirect_workspace_command("mkdir src")
        assert result is not None
        assert result.tool == "execute_shell"

    def test_unknown_command_returns_none(self):
        result = CommandRedirector.redirect_workspace_command("whoami")
        assert result is None

    def test_no_code_no_command(self):
        result = CommandRedirector.redirect_workspace_command("")
        assert result is None


class TestAgentTargetExtractorMissedPaths:
    """Cover lines 56-59: user-pattern match when no workstation indicator found."""

    def test_personal_phrase_user_pattern_match(self):
        # Agents with no workstation-like indicators but matching user-pattern regex
        agents = ["bobs-dev1", "alices-box2"]
        result = AgentTargetExtractor.extract_target_agent("check my computer", agents)
        # "my computer" triggers personal_phrases. No workstation indicator match.
        # Falls to user-pattern regex: ^[a-z]+s?-[a-z0-9]+$ which matches "bobs-dev1"
        assert result == "bobs-dev1"

    def test_action_pattern_on_target(self):
        """Cover lines 86-87: second action pattern (on|to|from) match."""
        # Agent name must NOT appear as substring of request (to avoid Strategy 1).
        # The word captured after "to" must be a substring of the agent name.
        # request: "deploy to prod now" → captures "prod" → matches "prod-server"
        agents = ["prod-server"]
        result = AgentTargetExtractor.extract_target_agent("deploy to prod now", agents)
        assert result == "prod-server"

    def test_action_pattern_from_target(self):
        agents = ["staging-host"]
        result = AgentTargetExtractor.extract_target_agent(
            "get info from staging now", agents
        )
        assert result == "staging-host"

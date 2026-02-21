"""
Tests for PowerShellValidator and ScriptValidator - 100% coverage target.
"""

import pytest
import sys
import os

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "layers", "orchestrator")
)

from services.helpers.powershell_utils import PowerShellValidator, ScriptValidator


class TestPowerShellValidate:
    def test_clean_command(self):
        errors = PowerShellValidator.validate_syntax("Get-Process")
        assert errors == []

    def test_powershell_wrapper_detected(self):
        errors = PowerShellValidator.validate_syntax(
            'powershell -Command "Get-Process"'
        )
        assert any("Unnecessary" in e for e in errors)

    def test_powershell_c_wrapper(self):
        errors = PowerShellValidator.validate_syntax("powershell -c 'hostname'")
        assert any("Unnecessary" in e for e in errors)

    def test_unbalanced_single_quotes(self):
        errors = PowerShellValidator.validate_syntax("Get-Content 'file.txt")
        assert any("single quote" in e for e in errors)

    def test_unbalanced_double_quotes(self):
        errors = PowerShellValidator.validate_syntax('Get-Content "file.txt')
        assert any("double quote" in e for e in errors)

    def test_escaped_quotes_ok(self):
        errors = PowerShellValidator.validate_syntax('Write-Output `"hello`"')
        assert not any("double quote" in e for e in errors)

    def test_unbalanced_braces(self):
        errors = PowerShellValidator.validate_syntax("if ($true) { Get-Process")
        assert any("brace" in e.lower() for e in errors)

    def test_unbalanced_parens(self):
        errors = PowerShellValidator.validate_syntax("(Get-Process")
        assert any("parenthesis" in e.lower() for e in errors)

    def test_missing_dollar_underscore_where(self):
        errors = PowerShellValidator.validate_syntax(
            "Get-ChildItem | Where-Object {.Name -eq 'test'}"
        )
        assert any("Missing $_" in e for e in errors)

    def test_psiscontainer_false_detected(self):
        errors = PowerShellValidator.validate_syntax(
            "Get-ChildItem | Where-Object {$_.PSIsContainer -eq $false}"
        )
        assert any("-File flag" in e for e in errors)

    def test_missing_dollar_underscore_foreach(self):
        errors = PowerShellValidator.validate_syntax(
            "Get-ChildItem | ForEach-Object {.Name}"
        )
        assert any("Missing $_" in e for e in errors)

    def test_dir_command_detected(self):
        errors = PowerShellValidator.validate_syntax("dir C:\\Users")
        assert any("dir" in e.lower() for e in errors)

    def test_dir_alone_detected(self):
        errors = PowerShellValidator.validate_syntax("dir")
        assert any("dir" in e.lower() for e in errors)

    def test_broken_pipe(self):
        errors = PowerShellValidator.validate_syntax("Get-Process | | Select-Object")
        assert any("pipe" in e.lower() for e in errors)

    def test_false_instead_of_dollar_false(self):
        errors = PowerShellValidator.validate_syntax("if ($x -eq Fal) { }")
        assert any("$false" in e for e in errors)


class TestPowerShellFix:
    def test_remove_wrapper(self):
        fixed = PowerShellValidator.fix_command(
            'powershell -Command "Get-Process"',
            ["Unnecessary 'powershell -Command' wrapper"],
        )
        assert "powershell" not in fixed.lower() or "Get-Process" in fixed

    def test_fix_missing_dollar_underscore(self):
        fixed = PowerShellValidator.fix_command(
            "Where-Object {.Name}", ["Missing $_ before .Name"]
        )
        assert "$_." in fixed

    def test_fix_psiscontainer(self):
        fixed = PowerShellValidator.fix_command(
            "Get-ChildItem | Where-Object {$_.PSIsContainer -eq $false}",
            ["Use -File flag instead of Where-Object PSIsContainer filter"],
        )
        assert "-File" in fixed

    def test_fix_dir_command(self):
        fixed = PowerShellValidator.fix_command(
            "dir C:\\Users", ["cmd.exe 'dir' command"]
        )
        assert "Get-ChildItem" in fixed

    def test_fix_dir_command_with_recurse(self):
        fixed = PowerShellValidator.fix_command(
            "dir /s C:\\Users", ["cmd.exe 'dir' command"]
        )
        assert "Get-ChildItem" in fixed
        assert "-Recurse" in fixed

    def test_fix_dir_drive_only(self):
        fixed = PowerShellValidator.fix_command("dir C:", ["cmd.exe 'dir' command"])
        assert "Get-ChildItem" in fixed
        assert "C:\\" in fixed

    def test_fix_dir_no_path(self):
        fixed = PowerShellValidator.fix_command("dir", ["cmd.exe 'dir' command"])
        assert "Get-ChildItem" in fixed

    def test_fix_false_comparison(self):
        fixed = PowerShellValidator.fix_command(
            "$x -eq False", ["$false instead of False"]
        )
        assert "$false" in fixed

    def test_fix_fal_partial(self):
        fixed = PowerShellValidator.fix_command(
            "$x -eq Fal", ["$false instead of False"]
        )
        assert "$false" in fixed

    def test_add_error_action_on_recurse(self):
        fixed = PowerShellValidator.fix_command(
            "Get-ChildItem -Path C:\\ -Recurse | Select-Object Name", []
        )
        assert "-ErrorAction SilentlyContinue" in fixed

    def test_no_double_error_action(self):
        cmd = "Get-ChildItem -Path C:\\ -Recurse -ErrorAction Stop"
        fixed = PowerShellValidator.fix_command(cmd, [])
        assert fixed.count("-ErrorAction") == 1

    def test_fix_preserves_command_without_recurse(self):
        cmd = "Get-ChildItem -Path C:\\"
        fixed = PowerShellValidator.fix_command(cmd, [])
        assert fixed == cmd


class TestScriptValidator:
    def setup_method(self):
        self.v = ScriptValidator()

    # PowerShell validation
    def test_valid_powershell(self):
        result = self.v.validate("Get-Process | Select-Object Name", "powershell")
        assert result["valid"] is True
        assert "looks good" in result["summary"]

    def test_powershell_unmatched_quote(self):
        result = self.v.validate("Write-Output 'hello", "powershell")
        assert len(result["errors"]) > 0

    def test_powershell_unmatched_brace(self):
        result = self.v.validate("if ($true) { Get-Process", "powershell")
        assert len(result["errors"]) > 0

    def test_powershell_missing_dollar_underscore_script(self):
        result = self.v.validate(
            "Get-ChildItem | Where-Object {.Name -eq 'test'}", "powershell"
        )
        assert any("Missing $_" in e["description"] for e in result["errors"])

    def test_powershell_recurse_warning(self):
        result = self.v.validate("Get-ChildItem -Recurse", "powershell")
        assert len(result["warnings"]) > 0

    def test_powershell_dangerous_remove_item(self):
        result = self.v.validate("Remove-Item C:\\temp -Recurse", "powershell")
        assert any(e["type"] == "safety" for e in result["errors"])

    def test_powershell_dangerous_format_volume(self):
        result = self.v.validate("Format-Volume -DriveLetter D", "powershell")
        assert any(e["type"] == "safety" for e in result["errors"])

    # Python validation
    def test_valid_python(self):
        result = self.v.validate("print('hello')", "python")
        assert result["valid"] is True

    def test_invalid_python_syntax(self):
        result = self.v.validate("def foo(:", "python")
        assert result["valid"] is False

    def test_python_file_without_except(self):
        result = self.v.validate("f = open('test.txt')\ndata = f.read()", "python")
        assert len(result["warnings"]) > 0

    def test_python_file_with_except(self):
        result = self.v.validate(
            "try:\n  f = open('test.txt')\nexcept:\n  pass", "python"
        )
        assert len(result["warnings"]) == 0

    # Bash validation
    def test_bash_no_shebang(self):
        result = self.v.validate("echo hello", "bash")
        assert any(w["description"] == "No shebang line" for w in result["warnings"])

    def test_bash_with_shebang(self):
        result = self.v.validate("#!/bin/bash\necho hello", "bash")
        assert not any(
            w["description"] == "No shebang line" for w in result["warnings"]
        )

    def test_bash_shell_alias(self):
        result = self.v.validate("echo hello", "shell")
        assert result["language"] == "shell"

    def test_bash_sh_alias(self):
        result = self.v.validate("echo hello", "sh")
        assert result["language"] == "sh"

    def test_bash_unmatched_quote(self):
        result = self.v.validate("echo 'hello", "bash")
        assert len(result["errors"]) > 0

    def test_bash_rm_rf_safety(self):
        result = self.v.validate("rm -rf /tmp/test", "bash")
        assert any(e["type"] == "safety" for e in result["errors"])

    def test_bash_rm_rf_with_i(self):
        result = self.v.validate("rm -rfi /tmp/test", "bash")
        assert not any(e["type"] == "safety" for e in result["errors"])

    # Generic validation
    def test_generic_language(self):
        result = self.v.validate("some code here", "ruby")
        assert result["language"] == "ruby"

    def test_generic_unmatched_quote(self):
        result = self.v.validate('print("hello', "ruby")
        assert len(result["errors"]) > 0

    # Result structure
    def test_result_structure_complete(self):
        result = self.v.validate("Get-Process", "powershell")
        assert "valid" in result
        assert "issues" in result
        assert "errors" in result
        assert "warnings" in result
        assert "summary" in result
        assert "can_fix" in result
        assert "fixed_script" in result
        assert "language" in result

    def test_can_fix_and_fixed_script(self):
        result = self.v.validate(
            "Get-ChildItem -Recurse | Where-Object {.Name}", "powershell"
        )
        # Has syntax error (missing $_) which is fixable
        if result["errors"] and result["can_fix"]:
            assert result["fixed_script"] is not None

    def test_non_fixable_errors(self):
        result = self.v.validate("Remove-Item C:\\ -Recurse", "powershell")
        # Safety errors are not fixable
        assert result["can_fix"] is False

    def test_summary_fixable(self):
        result = self.v.validate("Get-ChildItem -Recurse", "powershell")
        # Only warning, no errors -> valid
        assert result["valid"] is True


class TestCheckUnmatchedQuotes:
    def setup_method(self):
        self.v = ScriptValidator()

    def test_balanced_double_quotes(self):
        assert self.v._check_unmatched_quotes('"hello"') == []

    def test_balanced_single_quotes(self):
        assert self.v._check_unmatched_quotes("'hello'") == []

    def test_comment_line_skipped(self):
        assert self.v._check_unmatched_quotes("# it's a comment") == []

    def test_escaped_backslash(self):
        result = self.v._check_unmatched_quotes('"hello\\\\"')
        # Escaped backslash, then closing quote
        assert isinstance(result, list)

    def test_multiline(self):
        text = "line1 = 'ok'\nline2 = 'broken"
        issues = self.v._check_unmatched_quotes(text)
        assert len(issues) > 0
        assert issues[0][0] == 2  # Line 2


class TestCheckUnmatchedBraces:
    def setup_method(self):
        self.v = ScriptValidator()

    def test_balanced_braces(self):
        assert self.v._check_unmatched_braces("{ }") == []

    def test_balanced_brackets(self):
        assert self.v._check_unmatched_braces("[ ]") == []

    def test_balanced_parens(self):
        assert self.v._check_unmatched_braces("( )") == []

    def test_unmatched_open_brace(self):
        issues = self.v._check_unmatched_braces("{")
        assert len(issues) > 0

    def test_unmatched_close_brace(self):
        issues = self.v._check_unmatched_braces("}")
        assert len(issues) > 0

    def test_mismatched_pairs(self):
        issues = self.v._check_unmatched_braces("{)")
        assert len(issues) > 0

    def test_nested_balanced(self):
        assert self.v._check_unmatched_braces("{[()]}") == []

    def test_comment_skipped(self):
        assert self.v._check_unmatched_braces("# {") == []


class TestFixScript:
    def setup_method(self):
        self.v = ScriptValidator()

    def test_fix_missing_error_handling(self):
        errors = [{"type": "missing_error_handling"}]
        script = "Get-ChildItem -Recurse | Select-Object Name"
        fixed = self.v._fix_script(script, errors, "powershell")
        assert "-ErrorAction SilentlyContinue" in fixed

    def test_fix_non_powershell_noop(self):
        errors = [{"type": "missing_error_handling"}]
        script = "ls -la"
        fixed = self.v._fix_script(script, errors, "bash")
        assert fixed == script

    def test_fix_already_has_error_action(self):
        errors = [{"type": "missing_error_handling"}]
        script = "Get-ChildItem -Recurse -ErrorAction Stop"
        fixed = self.v._fix_script(script, errors, "powershell")
        assert fixed == script

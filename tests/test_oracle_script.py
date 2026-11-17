"""Regression tests for optional oracle discovery and execution failures."""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "oracle_cross_check", Path(__file__).resolve().parents[1] / "scripts/oracle-cross-check.py"
)
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)


class OracleDiscoveryTests(unittest.TestCase):
    def test_argument_overrides_environment_and_path(self):
        with patch.dict(os.environ, {"BEAN_ORACLE_DIR": "/env-oracle"}, clear=True), \
             patch.object(Path, "is_file", return_value=True), \
             patch.object(oracle.os, "access", return_value=True), \
             patch.object(oracle.shutil, "which") as lookup:
            self.assertEqual(oracle.find_tools(Path("/arg-oracle")),
                             (Path("/arg-oracle/bean-check"), Path("/arg-oracle/bean-query")))
            lookup.assert_not_called()

    def test_environment_overrides_path(self):
        with patch.dict(os.environ, {"BEAN_ORACLE_DIR": "/env-oracle"}, clear=True), \
             patch.object(Path, "is_file", return_value=True), \
             patch.object(oracle.os, "access", return_value=True), \
             patch.object(oracle.shutil, "which") as lookup:
            self.assertEqual(oracle.find_tools(None),
                             (Path("/env-oracle/bean-check"), Path("/env-oracle/bean-query")))
            lookup.assert_not_called()

    def test_path_tools_can_be_in_separate_directories(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(oracle.shutil, "which", side_effect=["/check/bean-check", "/query/bean-query"]):
            self.assertEqual(oracle.find_tools(None),
                             (Path("/check/bean-check"), Path("/query/bean-query")))

    def test_empty_environment_uses_path(self):
        with patch.dict(os.environ, {"BEAN_ORACLE_DIR": ""}, clear=True), \
             patch.object(oracle.shutil, "which", side_effect=["/bin/bean-check", "/bin/bean-query"]):
            self.assertIsNotNone(oracle.find_tools(None))

    def test_truly_absent_tools_skip_without_running_commands(self):
        output = io.StringIO()
        with patch.dict(os.environ, {"PATH": "/absent"}, clear=True), \
             patch.object(oracle.shutil, "which", return_value=None), \
             patch.object(Path, "lstat", side_effect=FileNotFoundError), \
             patch.object(oracle, "run") as run, contextlib.redirect_stdout(output):
            self.assertEqual(oracle.main([]), 0)
            run.assert_not_called()
        self.assertIn("SKIP:", output.getvalue())
        self.assertIn("bean-check, bean-query", output.getvalue())

    def test_partial_absence_names_the_missing_tool(self):
        output = io.StringIO()
        with patch.dict(os.environ, {"PATH": "/absent"}, clear=True), \
             patch.object(oracle.shutil, "which", side_effect=["/bin/bean-check", None]), \
             patch.object(Path, "lstat", side_effect=FileNotFoundError), \
             contextlib.redirect_stdout(output):
            self.assertIsNone(oracle.find_tools(None))
        self.assertIn("SKIP: optional oracle tools absent from PATH: bean-query", output.getvalue())

    def test_missing_configured_tool_is_an_error(self):
        with patch.object(Path, "is_file", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "configured oracle tool"):
                oracle.find_tools(Path("/missing"))

    def test_non_executable_configured_tool_is_an_error(self):
        with patch.object(Path, "is_file", return_value=True), \
             patch.object(oracle.os, "access", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "not executable"):
                oracle.find_tools(Path("/broken"))

    def test_non_executable_path_tool_is_an_error(self):
        with patch.dict(os.environ, {"PATH": "/broken"}, clear=True), \
             patch.object(oracle.shutil, "which", return_value=None), \
             patch.object(Path, "lstat"):
            with self.assertRaisesRegex(RuntimeError, "not executable"):
                oracle.find_tools(None)

    def test_inaccessible_path_is_an_error_not_a_skip(self):
        with patch.dict(os.environ, {"PATH": "/inaccessible"}, clear=True), \
             patch.object(oracle.shutil, "which", return_value=None), \
             patch.object(Path, "lstat", side_effect=PermissionError("access denied")):
            with self.assertRaises(PermissionError):
                oracle.find_tools(None)

    def test_existing_tool_failure_is_an_error(self):
        failed = subprocess.CompletedProcess(["bean-check"], 7, "", "synthetic tool failure")
        with patch.object(oracle.subprocess, "run", return_value=failed):
            with self.assertRaisesRegex(RuntimeError, r"failed \(7\).*synthetic tool failure"):
                oracle.run(["bean-check", "sample/ledger.beancount"])


if __name__ == "__main__":
    unittest.main()

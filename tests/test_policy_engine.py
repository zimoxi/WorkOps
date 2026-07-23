"""
WorkOps Policy Engine Tests
Sprint044: Policy Engine Foundation

覆盖：
- PolicyEffect enum
- PolicyType enum
- PolicyRule model
- Policy model
- PolicyEvaluationRequest model
- PolicyEvaluationResult model
- PolicyEvaluator contract
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.policy.rule import PolicyEffect, PolicyType
from backup_manager.policy.model import PolicyRule, Policy
from backup_manager.policy.request import PolicyEvaluationRequest
from backup_manager.policy.result import PolicyEvaluationResult
from backup_manager.policy.evaluator import PolicyEvaluator
from backup_manager.policy.errors import (
    PolicyError,
    InvalidPolicyError,
    PolicyConflictError,
    PolicyNotFoundError,
)


# ============================================================================
# PolicyEffect
# ============================================================================

class TestPolicyEffect(unittest.TestCase):
    """策略效果测试"""

    def test_allow(self):
        self.assertEqual(PolicyEffect.ALLOW.value, "allow")

    def test_deny(self):
        self.assertEqual(PolicyEffect.DENY.value, "deny")

    def test_two_effects(self):
        self.assertEqual(len(PolicyEffect), 2)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            PolicyEffect("nonexistent")


# ============================================================================
# PolicyType
# ============================================================================

class TestPolicyType(unittest.TestCase):
    """策略类型测试"""

    def test_operation(self):
        self.assertEqual(PolicyType.OPERATION.value, "operation")

    def test_device(self):
        self.assertEqual(PolicyType.DEVICE.value, "device")

    def test_health(self):
        self.assertEqual(PolicyType.HEALTH.value, "health")

    def test_three_types(self):
        self.assertEqual(len(PolicyType), 3)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            PolicyType("nonexistent")


# ============================================================================
# PolicyRule
# ============================================================================

class TestPolicyRule(unittest.TestCase):
    """策略规则测试"""

    def _make_rule(self, **kwargs):
        defaults = {
            "rule_id": "rule-001",
            "policy_type": PolicyType.OPERATION,
            "effect": PolicyEffect.ALLOW,
            "description": "Allow backup operations",
        }
        defaults.update(kwargs)
        return PolicyRule(**defaults)

    def test_valid_rule(self):
        rule = self._make_rule()
        self.assertEqual(rule.rule_id, "rule-001")
        self.assertEqual(rule.effect, PolicyEffect.ALLOW)

    def test_frozen(self):
        rule = self._make_rule()
        with self.assertRaises(AttributeError):
            rule.rule_id = "other"

    def test_slots(self):
        rule = self._make_rule()
        with self.assertRaises(AttributeError):
            rule.__dict__

    def test_empty_rule_id_rejected(self):
        with self.assertRaises(InvalidPolicyError):
            self._make_rule(rule_id="")

    def test_empty_description_rejected(self):
        with self.assertRaises(InvalidPolicyError):
            self._make_rule(description="")

    def test_invalid_policy_type_rejected(self):
        with self.assertRaises(InvalidPolicyError):
            self._make_rule(policy_type="operation")

    def test_invalid_effect_rejected(self):
        with self.assertRaises(InvalidPolicyError):
            self._make_rule(effect="allow")

    def test_deny_effect(self):
        rule = self._make_rule(effect=PolicyEffect.DENY)
        self.assertEqual(rule.effect, PolicyEffect.DENY)

    def test_no_forbidden_fields(self):
        rule = self._make_rule()
        for attr in ["password", "credential", "secret", "token", "ssh", "command", "condition_script"]:
            self.assertFalse(hasattr(rule, attr))


# ============================================================================
# Policy
# ============================================================================

class TestPolicy(unittest.TestCase):
    """策略测试"""

    def _make_policy(self, **kwargs):
        rule = PolicyRule(
            rule_id="rule-001", policy_type=PolicyType.OPERATION,
            effect=PolicyEffect.ALLOW, description="Allow",
        )
        defaults = {
            "policy_id": "pol-001",
            "name": "Backup Policy",
            "rules": (rule,),
        }
        defaults.update(kwargs)
        return Policy(**defaults)

    def test_valid_policy(self):
        policy = self._make_policy()
        self.assertEqual(policy.policy_id, "pol-001")
        self.assertEqual(policy.name, "Backup Policy")
        self.assertTrue(policy.enabled)

    def test_frozen(self):
        policy = self._make_policy()
        with self.assertRaises(AttributeError):
            policy.policy_id = "other"

    def test_slots(self):
        policy = self._make_policy()
        with self.assertRaises(AttributeError):
            policy.__dict__

    def test_empty_policy_id_rejected(self):
        with self.assertRaises(InvalidPolicyError):
            self._make_policy(policy_id="")

    def test_empty_name_rejected(self):
        with self.assertRaises(InvalidPolicyError):
            self._make_policy(name="")

    def test_rules_must_be_tuple(self):
        rule = PolicyRule(
            rule_id="r1", policy_type=PolicyType.OPERATION,
            effect=PolicyEffect.ALLOW, description="Allow",
        )
        with self.assertRaises(InvalidPolicyError):
            Policy(policy_id="p1", name="P", rules=[rule])

    def test_invalid_rule_rejected(self):
        with self.assertRaises(InvalidPolicyError):
            Policy(policy_id="p1", name="P", rules=("not_a_rule",))

    def test_empty_rules_allowed(self):
        policy = Policy(policy_id="p1", name="P", rules=())
        self.assertEqual(len(policy.rules), 0)

    def test_timezone_aware(self):
        policy = self._make_policy()
        self.assertIsNotNone(policy.created_at.tzinfo)

    def test_enabled_must_be_bool(self):
        with self.assertRaises(InvalidPolicyError):
            self._make_policy(enabled=1)

    def test_multiple_rules(self):
        r1 = PolicyRule(rule_id="r1", policy_type=PolicyType.OPERATION, effect=PolicyEffect.ALLOW, description="A")
        r2 = PolicyRule(rule_id="r2", policy_type=PolicyType.DEVICE, effect=PolicyEffect.DENY, description="D")
        policy = Policy(policy_id="p1", name="P", rules=(r1, r2))
        self.assertEqual(len(policy.rules), 2)

    def test_no_forbidden_fields(self):
        policy = self._make_policy()
        for attr in ["password", "credential", "secret", "token", "ssh"]:
            self.assertFalse(hasattr(policy, attr))


# ============================================================================
# PolicyEvaluationRequest
# ============================================================================

class TestPolicyEvaluationRequest(unittest.TestCase):
    """策略评估请求测试"""

    def test_valid_request(self):
        req = PolicyEvaluationRequest(
            request_id="req-001", operation_type="backup",
        )
        self.assertEqual(req.request_id, "req-001")
        self.assertEqual(req.operation_type, "backup")

    def test_frozen(self):
        req = PolicyEvaluationRequest(request_id="req-001", operation_type="backup")
        with self.assertRaises(AttributeError):
            req.request_id = "other"

    def test_slots(self):
        req = PolicyEvaluationRequest(request_id="req-001", operation_type="backup")
        with self.assertRaises(AttributeError):
            req.__dict__

    def test_empty_request_id_rejected(self):
        with self.assertRaises(InvalidPolicyError):
            PolicyEvaluationRequest(request_id="", operation_type="backup")

    def test_empty_operation_type_rejected(self):
        with self.assertRaises(InvalidPolicyError):
            PolicyEvaluationRequest(request_id="req-001", operation_type="")

    def test_timezone_aware(self):
        req = PolicyEvaluationRequest(request_id="req-001", operation_type="backup")
        self.assertIsNotNone(req.created_at.tzinfo)

    def test_device_id_none_default(self):
        req = PolicyEvaluationRequest(request_id="req-001", operation_type="backup")
        self.assertIsNone(req.device_id)

    def test_with_device_id(self):
        req = PolicyEvaluationRequest(
            request_id="req-001", operation_type="backup", device_id="dev-001",
        )
        self.assertEqual(req.device_id, "dev-001")

    def test_no_forbidden_fields(self):
        req = PolicyEvaluationRequest(request_id="req-001", operation_type="backup")
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(req, attr))


# ============================================================================
# PolicyEvaluationResult
# ============================================================================

class TestPolicyEvaluationResult(unittest.TestCase):
    """策略评估结果测试"""

    def test_valid_result(self):
        result = PolicyEvaluationResult(
            request_id="req-001", allowed=True,
            effect=PolicyEffect.ALLOW, message="ok",
        )
        self.assertEqual(result.request_id, "req-001")
        self.assertTrue(result.allowed)
        self.assertEqual(result.effect, PolicyEffect.ALLOW)

    def test_frozen(self):
        result = PolicyEvaluationResult(
            request_id="req-001", allowed=True,
            effect=PolicyEffect.ALLOW, message="ok",
        )
        with self.assertRaises(AttributeError):
            result.request_id = "other"

    def test_slots(self):
        result = PolicyEvaluationResult(
            request_id="req-001", allowed=True,
            effect=PolicyEffect.ALLOW, message="ok",
        )
        with self.assertRaises(AttributeError):
            result.__dict__

    def test_empty_request_id_rejected(self):
        with self.assertRaises(InvalidPolicyError):
            PolicyEvaluationResult(
                request_id="", allowed=True,
                effect=PolicyEffect.ALLOW, message="ok",
            )

    def test_allowed_must_be_bool(self):
        with self.assertRaises(InvalidPolicyError):
            PolicyEvaluationResult(
                request_id="req-001", allowed=1,
                effect=PolicyEffect.ALLOW, message="ok",
            )

    def test_invalid_effect_rejected(self):
        with self.assertRaises(InvalidPolicyError):
            PolicyEvaluationResult(
                request_id="req-001", allowed=True,
                effect="allow", message="ok",
            )

    def test_message_must_be_str(self):
        with self.assertRaises(InvalidPolicyError):
            PolicyEvaluationResult(
                request_id="req-001", allowed=True,
                effect=PolicyEffect.ALLOW, message=123,
            )

    def test_timezone_aware(self):
        result = PolicyEvaluationResult(
            request_id="req-001", allowed=True,
            effect=PolicyEffect.ALLOW, message="ok",
        )
        self.assertIsNotNone(result.evaluated_at.tzinfo)

    def test_deny_result(self):
        result = PolicyEvaluationResult(
            request_id="req-001", allowed=False,
            effect=PolicyEffect.DENY, message="denied",
        )
        self.assertFalse(result.allowed)
        self.assertEqual(result.effect, PolicyEffect.DENY)

    def test_no_forbidden_fields(self):
        result = PolicyEvaluationResult(
            request_id="req-001", allowed=True,
            effect=PolicyEffect.ALLOW, message="ok",
        )
        for attr in ["secret", "credential", "password", "token"]:
            self.assertFalse(hasattr(result, attr))


# ============================================================================
# PolicyEvaluator Contract
# ============================================================================

class TestPolicyEvaluatorContract(unittest.TestCase):
    """策略评估器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(PolicyEvaluator, ABC))

    def test_has_evaluate(self):
        self.assertTrue(hasattr(PolicyEvaluator, "evaluate"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            PolicyEvaluator()

    def test_concrete_subclass(self):
        class MockEvaluator(PolicyEvaluator):
            def evaluate(self, request, policy):
                return PolicyEvaluationResult(
                    request_id=request.request_id,
                    allowed=True, effect=PolicyEffect.ALLOW,
                    message="ok",
                )
        evaluator = MockEvaluator()
        req = PolicyEvaluationRequest(request_id="req-001", operation_type="backup")
        policy = Policy(policy_id="p1", name="P", rules=())
        result = evaluator.evaluate(req, policy)
        self.assertTrue(result.allowed)

    def test_missing_evaluate(self):
        class BadEvaluator(PolicyEvaluator):
            pass
        with self.assertRaises(TypeError):
            BadEvaluator()


# ============================================================================
# Error Model
# ============================================================================

class TestPolicyErrors(unittest.TestCase):
    """错误模型测试"""

    def test_policy_error(self):
        with self.assertRaises(PolicyError):
            raise PolicyError("test")

    def test_invalid_policy_error(self):
        with self.assertRaises(PolicyError):
            raise InvalidPolicyError("test")

    def test_conflict_error(self):
        exc = PolicyConflictError("p1")
        self.assertIn("p1", str(exc))

    def test_not_found_error(self):
        exc = PolicyNotFoundError("p1")
        self.assertIn("p1", str(exc))

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (PolicyError, ("test",)),
            (InvalidPolicyError, ("test",)),
            (PolicyConflictError, ("p1",)),
            (PolicyNotFoundError, ("p1",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential", "ssh"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_rule_no_credentials(self):
        rule = PolicyRule(
            rule_id="r1", policy_type=PolicyType.OPERATION,
            effect=PolicyEffect.ALLOW, description="Allow",
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(rule, attr))

    def test_policy_no_credentials(self):
        policy = Policy(policy_id="p1", name="P", rules=())
        for attr in ["password", "credential", "secret", "token", "ssh"]:
            self.assertFalse(hasattr(policy, attr))

    def test_request_no_credentials(self):
        req = PolicyEvaluationRequest(request_id="req-001", operation_type="backup")
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(req, attr))

    def test_result_no_credentials(self):
        result = PolicyEvaluationResult(
            request_id="req-001", allowed=True,
            effect=PolicyEffect.ALLOW, message="ok",
        )
        for attr in ["secret", "credential", "password", "token"]:
            self.assertFalse(hasattr(result, attr))

    def test_no_subprocess(self):
        import ast
        import os
        policy_dir = os.path.join("backup_manager", "policy")
        for filename in os.listdir(policy_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(policy_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotEqual(alias.name, "subprocess")
                elif isinstance(node, ast.ImportFrom):
                    if node.module and "subprocess" in node.module:
                        self.fail(f"subprocess imported in {filename}")

    def test_no_exec_eval(self):
        import ast
        import os
        policy_dir = os.path.join("backup_manager", "policy")
        for filename in os.listdir(policy_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(policy_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_evaluator_lifecycle(self):
        """完整评估器生命周期"""
        class MockEvaluator(PolicyEvaluator):
            def evaluate(self, request, policy):
                return PolicyEvaluationResult(
                    request_id=request.request_id,
                    allowed=True, effect=PolicyEffect.ALLOW,
                    message="ok",
                )
        evaluator = MockEvaluator()
        req = PolicyEvaluationRequest(request_id="req-001", operation_type="backup")
        rule = PolicyRule(
            rule_id="r1", policy_type=PolicyType.OPERATION,
            effect=PolicyEffect.ALLOW, description="Allow",
        )
        policy = Policy(policy_id="p1", name="P", rules=(rule,))
        result = evaluator.evaluate(req, policy)
        self.assertTrue(result.allowed)
        self.assertEqual(result.effect, PolicyEffect.ALLOW)


# ============================================================================
# Extended Tests
# ============================================================================

class TestPolicyExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidPolicyError, PolicyError))
        self.assertTrue(issubclass(PolicyConflictError, PolicyError))
        self.assertTrue(issubclass(PolicyNotFoundError, PolicyError))

    def test_rule_repr_no_secrets(self):
        rule = PolicyRule(
            rule_id="r1", policy_type=PolicyType.OPERATION,
            effect=PolicyEffect.ALLOW, description="Allow",
        )
        r = repr(rule)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_policy_repr_no_secrets(self):
        policy = Policy(policy_id="p1", name="P", rules=())
        r = repr(policy)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_request_repr_no_secrets(self):
        req = PolicyEvaluationRequest(request_id="req-001", operation_type="backup")
        r = repr(req)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_result_repr_no_secrets(self):
        result = PolicyEvaluationResult(
            request_id="req-001", allowed=True,
            effect=PolicyEffect.ALLOW, message="ok",
        )
        r = repr(result)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())


if __name__ == "__main__":
    unittest.main()

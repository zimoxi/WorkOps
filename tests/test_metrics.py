"""
WorkOps Monitoring Metrics Tests
Sprint063: Monitoring Metrics Foundation

覆盖：
- MetricType enum
- MetricRecord validation
- MetricQuery validation
- MetricsCollector contract
- MetricsQueryService contract
- validate_metric_record
- validate_metric_query
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.metrics.model import (
    MetricType,
    MetricRecord,
    MetricQuery,
    validate_metric_record,
    validate_metric_query,
)
from backup_manager.metrics.collector import MetricsCollector
from backup_manager.metrics.query import MetricsQueryService
from backup_manager.metrics.errors import (
    MetricsError,
    InvalidMetricError,
    MetricsUnavailableError,
    MetricsQueryError,
)


# ============================================================================
# MetricType
# ============================================================================

class TestMetricType(unittest.TestCase):
    """指标类型测试"""

    def test_execution_count(self):
        self.assertEqual(MetricType.EXECUTION_COUNT.value, "execution_count")

    def test_execution_duration(self):
        self.assertEqual(MetricType.EXECUTION_DURATION.value, "execution_duration")

    def test_backup_duration(self):
        self.assertEqual(MetricType.BACKUP_DURATION.value, "backup_duration")

    def test_restore_duration(self):
        self.assertEqual(MetricType.RESTORE_DURATION.value, "restore_duration")

    def test_health_status(self):
        self.assertEqual(MetricType.HEALTH_STATUS.value, "health_status")

    def test_runtime_latency(self):
        self.assertEqual(MetricType.RUNTIME_LATENCY.value, "runtime_latency")

    def test_six_types(self):
        self.assertEqual(len(MetricType), 6)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            MetricType("nonexistent")


# ============================================================================
# MetricRecord
# ============================================================================

class TestMetricRecord(unittest.TestCase):
    """指标记录测试"""

    def _make_record(self, **kwargs):
        defaults = {
            "metric_id": "m-001",
            "metric_type": MetricType.EXECUTION_COUNT,
            "value": 42.0,
            "source_id": "exec-001",
        }
        defaults.update(kwargs)
        return MetricRecord(**defaults)

    def test_valid_record(self):
        record = self._make_record()
        self.assertEqual(record.metric_id, "m-001")
        self.assertEqual(record.metric_type, MetricType.EXECUTION_COUNT)
        self.assertEqual(record.value, 42.0)
        self.assertEqual(record.source_id, "exec-001")

    def test_frozen(self):
        record = self._make_record()
        with self.assertRaises(AttributeError):
            record.metric_id = "other"

    def test_slots(self):
        record = self._make_record()
        with self.assertRaises(AttributeError):
            record.__dict__

    def test_empty_metric_id_rejected(self):
        with self.assertRaises(InvalidMetricError):
            self._make_record(metric_id="")

    def test_invalid_metric_type_rejected(self):
        with self.assertRaises(InvalidMetricError):
            self._make_record(metric_type="execution_count")

    def test_invalid_value_rejected(self):
        with self.assertRaises(InvalidMetricError):
            self._make_record(value="not_a_number")

    def test_empty_source_id_rejected(self):
        with self.assertRaises(InvalidMetricError):
            self._make_record(source_id="")

    def test_timezone_aware(self):
        record = self._make_record()
        self.assertIsNotNone(record.created_at.tzinfo)

    def test_int_value_allowed(self):
        record = self._make_record(value=42)
        self.assertEqual(record.value, 42)

    def test_float_value_allowed(self):
        record = self._make_record(value=42.5)
        self.assertEqual(record.value, 42.5)

    def test_zero_value_allowed(self):
        record = self._make_record(value=0.0)
        self.assertEqual(record.value, 0.0)

    def test_negative_value_allowed(self):
        record = self._make_record(value=-1.5)
        self.assertEqual(record.value, -1.5)

    def test_all_metric_types(self):
        for mt in MetricType:
            record = self._make_record(metric_type=mt)
            self.assertEqual(record.metric_type, mt)

    def test_no_forbidden_fields(self):
        record = self._make_record()
        for attr in ["password", "credential", "secret", "token", "command", "ssh"]:
            self.assertFalse(hasattr(record, attr))

    def test_repr_no_secrets(self):
        record = self._make_record()
        r = repr(record)
        for term in ["password", "secret", "token", "credential"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# MetricQuery
# ============================================================================

class TestMetricQuery(unittest.TestCase):
    """指标查询测试"""

    def test_valid_query(self):
        query = MetricQuery(metric_type=MetricType.EXECUTION_COUNT)
        self.assertEqual(query.metric_type, MetricType.EXECUTION_COUNT)
        self.assertIsNone(query.source_id)

    def test_frozen(self):
        query = MetricQuery(metric_type=MetricType.EXECUTION_COUNT)
        with self.assertRaises(AttributeError):
            query.metric_type = MetricType.EXECUTION_DURATION

    def test_slots(self):
        query = MetricQuery(metric_type=MetricType.EXECUTION_COUNT)
        with self.assertRaises(AttributeError):
            query.__dict__

    def test_invalid_metric_type_rejected(self):
        with self.assertRaises(InvalidMetricError):
            MetricQuery(metric_type="execution_count")

    def test_with_source_id(self):
        query = MetricQuery(
            metric_type=MetricType.EXECUTION_COUNT,
            source_id="exec-001",
        )
        self.assertEqual(query.source_id, "exec-001")

    def test_all_metric_types(self):
        for mt in MetricType:
            query = MetricQuery(metric_type=mt)
            self.assertEqual(query.metric_type, mt)

    def test_no_forbidden_fields(self):
        query = MetricQuery(metric_type=MetricType.EXECUTION_COUNT)
        for attr in ["secret", "credential", "token"]:
            self.assertFalse(hasattr(query, attr))


# ============================================================================
# MetricsCollector Contract
# ============================================================================

class TestMetricsCollectorContract(unittest.TestCase):
    """指标收集器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(MetricsCollector, ABC))

    def test_has_collect(self):
        self.assertTrue(hasattr(MetricsCollector, "collect"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            MetricsCollector()

    def test_concrete_subclass(self):
        class MockCollector(MetricsCollector):
            def __init__(self):
                self.records = []
            def collect(self, record):
                self.records.append(record)
        collector = MockCollector()
        record = MetricRecord(
            metric_id="m-001", metric_type=MetricType.EXECUTION_COUNT,
            value=42.0, source_id="exec-001",
        )
        collector.collect(record)
        self.assertEqual(len(collector.records), 1)

    def test_missing_collect(self):
        class BadCollector(MetricsCollector):
            pass
        with self.assertRaises(TypeError):
            BadCollector()


# ============================================================================
# MetricsQueryService Contract
# ============================================================================

class TestMetricsQueryServiceContract(unittest.TestCase):
    """指标查询服务契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(MetricsQueryService, ABC))

    def test_has_query(self):
        self.assertTrue(hasattr(MetricsQueryService, "query"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            MetricsQueryService()

    def test_concrete_subclass(self):
        class MockQueryService(MetricsQueryService):
            def __init__(self, records):
                self._records = records
            def query(self, query):
                return [r for r in self._records if r.metric_type == query.metric_type]
        record = MetricRecord(
            metric_id="m-001", metric_type=MetricType.EXECUTION_COUNT,
            value=42.0, source_id="exec-001",
        )
        service = MockQueryService([record])
        query = MetricQuery(metric_type=MetricType.EXECUTION_COUNT)
        results = service.query(query)
        self.assertEqual(len(results), 1)

    def test_missing_query(self):
        class BadService(MetricsQueryService):
            pass
        with self.assertRaises(TypeError):
            BadService()


# ============================================================================
# validate_metric_record
# ============================================================================

class TestValidateMetricRecord(unittest.TestCase):
    """验证指标记录测试"""

    def test_valid_record(self):
        record = MetricRecord(
            metric_id="m-001", metric_type=MetricType.EXECUTION_COUNT,
            value=42.0, source_id="exec-001",
        )
        validate_metric_record(record)

    def test_invalid_type_rejected(self):
        with self.assertRaises(InvalidMetricError):
            validate_metric_record("not_a_record")


# ============================================================================
# validate_metric_query
# ============================================================================

class TestValidateMetricQuery(unittest.TestCase):
    """验证指标查询测试"""

    def test_valid_query(self):
        query = MetricQuery(metric_type=MetricType.EXECUTION_COUNT)
        validate_metric_query(query)

    def test_invalid_type_rejected(self):
        with self.assertRaises(InvalidMetricError):
            validate_metric_query("not_a_query")


# ============================================================================
# Error Model
# ============================================================================

class TestMetricsErrors(unittest.TestCase):
    """错误模型测试"""

    def test_metrics_error(self):
        with self.assertRaises(MetricsError):
            raise MetricsError("test")

    def test_invalid_metric_error(self):
        with self.assertRaises(MetricsError):
            raise InvalidMetricError("test")

    def test_unavailable_error(self):
        with self.assertRaises(MetricsError):
            raise MetricsUnavailableError("test")

    def test_query_error(self):
        with self.assertRaises(MetricsError):
            raise MetricsQueryError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (MetricsError, ("test",)),
            (InvalidMetricError, ("test",)),
            (MetricsUnavailableError, ("test",)),
            (MetricsQueryError, ("test",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential", "ssh"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_record_no_credentials(self):
        record = MetricRecord(
            metric_id="m-001", metric_type=MetricType.EXECUTION_COUNT,
            value=42.0, source_id="exec-001",
        )
        for attr in ["password", "credential", "secret", "token", "command", "ssh"]:
            self.assertFalse(hasattr(record, attr))

    def test_query_no_credentials(self):
        query = MetricQuery(metric_type=MetricType.EXECUTION_COUNT)
        for attr in ["secret", "credential", "token"]:
            self.assertFalse(hasattr(query, attr))

    def test_no_subprocess(self):
        import ast
        import os
        metrics_dir = os.path.join("backup_manager", "metrics")
        for filename in os.listdir(metrics_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(metrics_dir, filename)
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
        metrics_dir = os.path.join("backup_manager", "metrics")
        for filename in os.listdir(metrics_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(metrics_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_collector_lifecycle(self):
        """完整收集器生命周期"""
        class MockCollector(MetricsCollector):
            def __init__(self):
                self.records = []
            def collect(self, record):
                self.records.append(record)
        collector = MockCollector()
        record = MetricRecord(
            metric_id="m-001", metric_type=MetricType.EXECUTION_COUNT,
            value=42.0, source_id="exec-001",
        )
        collector.collect(record)
        self.assertEqual(len(collector.records), 1)
        self.assertEqual(collector.records[0].metric_id, "m-001")

    def test_query_service_lifecycle(self):
        """完整查询服务生命周期"""
        class MockQueryService(MetricsQueryService):
            def __init__(self, records):
                self._records = records
            def query(self, query):
                return [r for r in self._records if r.metric_type == query.metric_type]
        records = [
            MetricRecord(
                metric_id="m-001", metric_type=MetricType.EXECUTION_COUNT,
                value=42.0, source_id="exec-001",
            ),
            MetricRecord(
                metric_id="m-002", metric_type=MetricType.EXECUTION_DURATION,
                value=1.5, source_id="exec-001",
            ),
        ]
        service = MockQueryService(records)
        query = MetricQuery(metric_type=MetricType.EXECUTION_COUNT)
        results = service.query(query)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].metric_id, "m-001")


# ============================================================================
# Extended Tests
# ============================================================================

class TestMetricsExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidMetricError, MetricsError))
        self.assertTrue(issubclass(MetricsUnavailableError, MetricsError))
        self.assertTrue(issubclass(MetricsQueryError, MetricsError))

    def test_record_repr_no_secrets(self):
        record = MetricRecord(
            metric_id="m-001", metric_type=MetricType.EXECUTION_COUNT,
            value=42.0, source_id="exec-001",
        )
        r = repr(record)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_query_repr_no_secrets(self):
        query = MetricQuery(metric_type=MetricType.EXECUTION_COUNT)
        r = repr(query)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_record_preserves_all_fields(self):
        record = MetricRecord(
            metric_id="m-001", metric_type=MetricType.EXECUTION_COUNT,
            value=42.0, source_id="exec-001",
        )
        self.assertEqual(record.metric_id, "m-001")
        self.assertEqual(record.metric_type, MetricType.EXECUTION_COUNT)
        self.assertEqual(record.value, 42.0)
        self.assertEqual(record.source_id, "exec-001")

    def test_query_preserves_all_fields(self):
        query = MetricQuery(
            metric_type=MetricType.EXECUTION_COUNT,
            source_id="exec-001",
        )
        self.assertEqual(query.metric_type, MetricType.EXECUTION_COUNT)
        self.assertEqual(query.source_id, "exec-001")

    def test_collector_returns_none(self):
        class MockCollector(MetricsCollector):
            def collect(self, record):
                pass
        collector = MockCollector()
        record = MetricRecord(
            metric_id="m-001", metric_type=MetricType.EXECUTION_COUNT,
            value=42.0, source_id="exec-001",
        )
        result = collector.collect(record)
        self.assertIsNone(result)

    def test_query_service_returns_list(self):
        class MockQueryService(MetricsQueryService):
            def query(self, query):
                return []
        service = MockQueryService()
        query = MetricQuery(metric_type=MetricType.EXECUTION_COUNT)
        results = service.query(query)
        self.assertIsInstance(results, list)

    def test_record_whitespace_id_rejected(self):
        with self.assertRaises(InvalidMetricError):
            MetricRecord(
                metric_id="   ", metric_type=MetricType.EXECUTION_COUNT,
                value=42.0, source_id="exec-001",
            )

    def test_record_whitespace_source_id_rejected(self):
        with self.assertRaises(InvalidMetricError):
            MetricRecord(
                metric_id="m-001", metric_type=MetricType.EXECUTION_COUNT,
                value=42.0, source_id="   ",
            )

    def test_record_no_command(self):
        record = MetricRecord(
            metric_id="m-001", metric_type=MetricType.EXECUTION_COUNT,
            value=42.0, source_id="exec-001",
        )
        self.assertFalse(hasattr(record, "command"))

    def test_record_no_ssh(self):
        record = MetricRecord(
            metric_id="m-001", metric_type=MetricType.EXECUTION_COUNT,
            value=42.0, source_id="exec-001",
        )
        self.assertFalse(hasattr(record, "ssh"))

    def test_query_no_secret(self):
        query = MetricQuery(metric_type=MetricType.EXECUTION_COUNT)
        self.assertFalse(hasattr(query, "secret"))

    def test_error_messages_safe(self):
        try:
            raise MetricsError("test")
        except MetricsError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "command"]:
                self.assertNotIn(term, msg.lower())

    def test_unavailable_error_message(self):
        exc = MetricsUnavailableError("service down")
        self.assertIn("service down", str(exc))

    def test_query_error_message(self):
        exc = MetricsQueryError("query failed")
        self.assertIn("query failed", str(exc))

    def test_collector_multiple_records(self):
        class MockCollector(MetricsCollector):
            def __init__(self):
                self.records = []
            def collect(self, record):
                self.records.append(record)
        collector = MockCollector()
        for i in range(5):
            record = MetricRecord(
                metric_id=f"m-{i:03d}", metric_type=MetricType.EXECUTION_COUNT,
                value=float(i), source_id="exec-001",
            )
            collector.collect(record)
        self.assertEqual(len(collector.records), 5)

    def test_query_service_filter_by_source(self):
        class MockQueryService(MetricsQueryService):
            def __init__(self, records):
                self._records = records
            def query(self, query):
                results = [r for r in self._records if r.metric_type == query.metric_type]
                if query.source_id:
                    results = [r for r in results if r.source_id == query.source_id]
                return results
        records = [
            MetricRecord(
                metric_id="m-001", metric_type=MetricType.EXECUTION_COUNT,
                value=42.0, source_id="exec-001",
            ),
            MetricRecord(
                metric_id="m-002", metric_type=MetricType.EXECUTION_COUNT,
                value=10.0, source_id="exec-002",
            ),
        ]
        service = MockQueryService(records)
        query = MetricQuery(
            metric_type=MetricType.EXECUTION_COUNT,
            source_id="exec-001",
        )
        results = service.query(query)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].source_id, "exec-001")

    def test_record_all_fields_present(self):
        record = MetricRecord(
            metric_id="m-001", metric_type=MetricType.EXECUTION_COUNT,
            value=42.0, source_id="exec-001",
        )
        self.assertTrue(hasattr(record, "metric_id"))
        self.assertTrue(hasattr(record, "metric_type"))
        self.assertTrue(hasattr(record, "value"))
        self.assertTrue(hasattr(record, "source_id"))
        self.assertTrue(hasattr(record, "created_at"))

    def test_query_all_fields_present(self):
        query = MetricQuery(
            metric_type=MetricType.EXECUTION_COUNT,
            source_id="exec-001",
        )
        self.assertTrue(hasattr(query, "metric_type"))
        self.assertTrue(hasattr(query, "source_id"))

    def test_record_no_password(self):
        record = MetricRecord(
            metric_id="m-001", metric_type=MetricType.EXECUTION_COUNT,
            value=42.0, source_id="exec-001",
        )
        self.assertFalse(hasattr(record, "password"))

    def test_record_no_secret(self):
        record = MetricRecord(
            metric_id="m-001", metric_type=MetricType.EXECUTION_COUNT,
            value=42.0, source_id="exec-001",
        )
        self.assertFalse(hasattr(record, "secret"))

    def test_record_no_token(self):
        record = MetricRecord(
            metric_id="m-001", metric_type=MetricType.EXECUTION_COUNT,
            value=42.0, source_id="exec-001",
        )
        self.assertFalse(hasattr(record, "token"))

    def test_query_no_credential(self):
        query = MetricQuery(metric_type=MetricType.EXECUTION_COUNT)
        self.assertFalse(hasattr(query, "credential"))

    def test_query_no_token(self):
        query = MetricQuery(metric_type=MetricType.EXECUTION_COUNT)
        self.assertFalse(hasattr(query, "token"))

    def test_record_no_credential(self):
        record = MetricRecord(
            metric_id="m-001", metric_type=MetricType.EXECUTION_COUNT,
            value=42.0, source_id="exec-001",
        )
        self.assertFalse(hasattr(record, "credential"))


if __name__ == "__main__":
    unittest.main()

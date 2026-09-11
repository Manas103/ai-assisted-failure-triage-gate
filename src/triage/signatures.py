"""The 40 ground-truth failure signatures.

Signatures 1-12 are backed by a real, small, genuinely buggy Python module
and its real fix under fixtures/<key>/{buggy,fixed}.py (see README for the
disclosure of which is which). Signatures 13-40 are textual-pattern-only:
a plausible CI/production failure shape with no backing implementation,
used only to exercise clustering and attribution at the full 4,000-record
scale, exactly as disclosed in the README.

Each signature record has:
  id            int, 1..40, the ground-truth label (never given to the
                clustering or attribution code, only used to score them)
  key           short slug
  name          human label
  real_fixture  bool
  module        fixtures package name, or None for textual-only
  error_type    exception / failure class name
  file          synthetic source file path used in the fake stack trace
  function      synthetic function name for the top frame
  base_line     nominal line number for the top frame (jittered per record)
  message_template
                a template string using {id} for an identifier-with-digits
                token, {num} for a bare integer token, and optionally
                {addr} for a fake memory address token. These are exactly
                the tokens generate_records.py fills with per-record noise
                and cluster.py's normalizer strips back out.
  weight        relative frequency used when sampling 4,000 records
"""

REAL_SIGNATURES = [
    dict(
        id=1, key="sig01_pagination_off_by_one", name="Pagination fencepost error",
        real_fixture=True, module="sig01_pagination_off_by_one",
        target_function="page_slice",
        error_type="AssertionError", file="services/catalog/pagination.py",
        function="test_page_slice", base_line=41,
        message_template="page_slice({id}, page={num}, size={num}) is missing the last item of the page",
        weight=14,
    ),
    dict(
        id=2, key="sig02_tz_naive_compare", name="Timezone-naive comparison",
        real_fixture=True, module="sig02_tz_naive_compare",
        target_function="is_expired",
        error_type="TypeError", file="services/billing/expiry.py",
        function="is_expired", base_line=13,
        message_template="can't compare offset-naive and offset-aware datetimes for {id}",
        weight=11,
    ),
    dict(
        id=3, key="sig03_boundary_inclusive", name="Exclusive/inclusive boundary bug",
        real_fixture=True, module="sig03_boundary_inclusive",
        target_function="ranges_overlap",
        error_type="AssertionError", file="services/scheduling/ranges.py",
        function="test_ranges_overlap", base_line=9,
        message_template="ranges_overlap({id}) returned False for touching ranges, expected True ({num})",
        weight=10,
    ),
    dict(
        id=4, key="sig04_stale_cache", name="Stale cache invalidation",
        real_fixture=True, module="sig04_stale_cache",
        target_function="get_or_compute",
        error_type="AssertionError", file="services/pricing/cache.py",
        function="test_get_or_compute_expires", base_line=8,
        message_template="get_or_compute({id}) returned a value {num}s past ttl expiry, cache never invalidated",
        weight=13,
    ),
    dict(
        id=5, key="sig05_float_epsilon", name="Float equality instead of tolerance",
        real_fixture=True, module="sig05_float_epsilon",
        target_function="is_close_enough",
        error_type="AssertionError", file="services/analytics/compare.py",
        function="test_is_close_enough", base_line=8,
        message_template="is_close_enough({id}) is False for values within {num}e-9 of each other",
        weight=9,
    ),
    dict(
        id=6, key="sig06_mutable_default_arg", name="Mutable default argument",
        real_fixture=True, module="sig06_mutable_default_arg",
        target_function="add_item",
        error_type="AssertionError", file="services/checkout/cart.py",
        function="test_add_item_fresh_cart", base_line=6,
        message_template="add_item({id}) leaked {num} item(s) from a previous unrelated call",
        weight=12,
    ),
    dict(
        id=7, key="sig07_int_division_truncation", name="Integer division truncation",
        real_fixture=True, module="sig07_int_division_truncation",
        target_function="average_batch_size",
        error_type="AssertionError", file="services/capacity/planning.py",
        function="test_average_batch_size", base_line=8,
        message_template="average_batch_size({id}) truncated to {num}, fractional remainder lost",
        weight=10,
    ),
    dict(
        id=8, key="sig08_unicode_truncate", name="Byte-length truncation bug",
        real_fixture=True, module="sig08_unicode_truncate",
        target_function="truncate_message",
        error_type="AssertionError", file="services/notify/format.py",
        function="test_truncate_message", base_line=6,
        message_template="truncate_message({id}) exceeded the {num}-byte budget after encoding",
        weight=8,
    ),
    dict(
        id=9, key="sig09_sort_tiebreak", name="Missing sort tie-break key",
        real_fixture=True, module="sig09_sort_tiebreak",
        target_function="rank_candidates",
        error_type="AssertionError", file="services/hiring/rank.py",
        function="test_rank_candidates_tiebreak", base_line=6,
        message_template="rank_candidates({id}) ordered {num} tied candidates arbitrarily",
        weight=9,
    ),
    dict(
        id=10, key="sig10_dedupe_collision", name="Dedupe key collision",
        real_fixture=True, module="sig10_dedupe_collision",
        target_function="dedupe_events",
        error_type="AssertionError", file="services/telemetry/dedupe.py",
        function="test_dedupe_events_distinct", base_line=7,
        message_template="dedupe_events({id}) collapsed {num} distinct events into one",
        weight=11,
    ),
    dict(
        id=11, key="sig11_retry_backoff_offbyone", name="Retry loop off-by-one",
        real_fixture=True, module="sig11_retry_backoff_offbyone",
        target_function="retry_with_backoff",
        error_type="RuntimeError", file="services/integrations/retry.py",
        function="retry_with_backoff", base_line=9,
        message_template="transient failure for {id} after {num} attempts, one short of max_retries",
        weight=12,
    ),
    dict(
        id=12, key="sig12_broad_exception_swallow", name="Overly broad except clause",
        real_fixture=True, module="sig12_broad_exception_swallow",
        target_function="parse_config_value",
        error_type="Failed", file="services/config/parse.py",
        function="test_parse_config_value_raises_on_bad_type", base_line=10,
        message_template="parse_config_value({id}) silently returned default {num} instead of raising",
        weight=8,
    ),
]

# 28 textual-pattern-only signatures: a plausible CI/production failure
# shape, no backing implementation. See README "Honest framing" for the
# disclosure that these do not have real fixtures.
_TEXTUAL_DEFS = [
    ("Database connection timeout", "TimeoutError", "infra/db/pool.py", "acquire_connection",
     "timed out after {num}ms waiting for a connection for {id}"),
    ("Null attribute access", "AttributeError", "services/orders/handler.py", "process_order",
     "'NoneType' object has no attribute 'total' while handling {id} (order {num})"),
    ("Worker out of memory", "MemoryError", "workers/batch/runner.py", "load_partition",
     "unable to allocate buffer of {num} bytes for {id}"),
    ("Connection reset by peer", "ConnectionResetError", "infra/net/client.py", "send_request",
     "connection reset by peer while sending to {id} (errno {num})"),
    ("Permission denied on artifact store", "PermissionError", "infra/storage/uploader.py", "put_object",
     "[Errno 13] Permission denied: '{id}' (attempt {num})"),
    ("Malformed JSON payload", "JSONDecodeError", "services/api/parse.py", "parse_body",
     "Expecting ',' delimiter at char {num} in payload {id}"),
    ("Upstream HTTP 500", "HTTPError", "services/api/gateway.py", "call_upstream",
     "upstream {id} returned 500 after {num}ms"),
    ("Disk full during write", "OSError", "infra/storage/writer.py", "flush_segment",
     "[Errno 28] No space left on device writing {id} ({num} bytes pending)"),
    ("DNS resolution failure", "socket.gaierror", "infra/net/resolver.py", "resolve_host",
     "Name or service not known: {id} (attempt {num})"),
    ("Deadlock detected", "DeadlockError", "infra/db/txn.py", "commit_transaction",
     "deadlock detected involving transaction {id}, retried {num} time(s)"),
    ("Schema validation error", "ValidationError", "services/api/schema.py", "validate_payload",
     "field {id} failed schema check, code {num}"),
    ("Expired auth token", "AuthError", "services/auth/session.py", "verify_token",
     "token {id} expired {num}s ago"),
    ("Rate limit exceeded", "RateLimitError", "services/api/throttle.py", "check_quota",
     "quota exceeded for {id}, {num} requests over limit"),
    ("Missing input file", "FileNotFoundError", "workers/etl/loader.py", "open_input",
     "[Errno 2] No such file or directory: '{id}' (job {num})"),
    ("Recursion limit exceeded", "RecursionError", "services/tree/walker.py", "walk_nested",
     "maximum recursion depth exceeded while walking {id}, depth {num}"),
    ("CI assertion failure, unrelated flake", "AssertionError", "tests/integration/test_flow.py", "test_end_to_end",
     "expected status 'ready' for {id}, got 'pending' after {num}ms"),
    ("Flaky test timeout", "TimeoutError", "tests/integration/test_slow.py", "test_batch_completes",
     "{id} did not complete within {num}ms"),
    ("Container OOM killed", "OOMKilled", "infra/docker/container.py", "healthcheck",
     "container {id} killed by OOM after using {num}MB"),
    ("Pod crash loop", "CrashLoopBackOff", "infra/k8s/pod.py", "watch_pod",
     "pod {id} restarted {num} times in the last 5 minutes"),
    ("Merge conflict in CI checkout", "GitMergeError", "ci/checkout.py", "merge_base",
     "conflict merging {id} into base, {num} conflicting file(s)"),
    ("Dependency install failure", "InstallError", "ci/deps/install.py", "npm_install",
     "failed to install package {id}, exit code {num}"),
    ("Build tool failure", "BuildError", "ci/build/gradle.py", "run_build",
     "task {id} failed with exit code {num}"),
    ("TLS certificate verification failed", "SSLCertVerificationError", "infra/net/tls.py", "verify_cert",
     "certificate verify failed for {id}, error code {num}"),
    ("Missing required environment variable", "ConfigError", "services/bootstrap/env.py", "require_env",
     "environment variable {id} is not set (check {num})"),
    ("Port already in use", "OSError", "services/bootstrap/server.py", "bind_socket",
     "[Errno 98] Address already in use: {id}:{num}"),
    ("Disk quota exceeded for tenant", "QuotaExceededError", "services/storage/quota.py", "check_quota",
     "tenant {id} exceeded disk quota by {num}MB"),
    ("Message queue consumer lag", "ConsumerLagError", "infra/mq/consumer.py", "poll_batch",
     "consumer group {id} lagging by {num} messages"),
    ("GPU out of memory", "CUDAOutOfMemoryError", "workers/ml/train.py", "forward_pass",
     "CUDA out of memory trying to allocate {num}MiB for {id}"),
]

TEXTUAL_SIGNATURES = []
for _offset, (_name, _err, _file, _func, _tmpl) in enumerate(_TEXTUAL_DEFS):
    _sid = 13 + _offset
    TEXTUAL_SIGNATURES.append(dict(
        id=_sid,
        key=f"sig{_sid:02d}_textual",
        name=_name,
        real_fixture=False,
        module=None,
        error_type=_err,
        file=_file,
        function=_func,
        base_line=20 + (_offset * 7) % 180,
        message_template=_tmpl,
        weight=6 + (_offset % 5) * 3,
    ))

ALL_SIGNATURES = REAL_SIGNATURES + TEXTUAL_SIGNATURES
assert len(ALL_SIGNATURES) == 40, f"expected 40 signatures, got {len(ALL_SIGNATURES)}"
assert sum(1 for s in ALL_SIGNATURES if s["real_fixture"]) == 12

SIGNATURES_BY_ID = {s["id"]: s for s in ALL_SIGNATURES}

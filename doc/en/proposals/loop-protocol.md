# Proposal: a marker-driven loop/rerun protocol

Status: **draft for discussion** — no implementation yet.
File/line anchors refer to `main` at the time of writing (9.2.0.dev,
around `344c23787`).

## Motivation

pytest has no first-class way to run *one test item multiple times under a
controller*. Every project that needs it works around the protocol instead of
through it:

- **hypothesis** runs its whole example loop *inside* a single
  `pytest_runtest_call`. pytest sees one setup, one call, one teardown —
  function-scoped fixtures are created once and shared by every example, the
  classic mutable-fixture footgun of
  [#916](https://github.com/pytest-dev/pytest/issues/916) and
  [hypothesis#377](https://github.com/HypothesisWorks/hypothesis/issues/377).
- **pytest-repeat** / **pytest-flakefinder** fake looping via collection-time
  parametrization — impossible when the iteration count is dynamic (hypothesis
  generates and shrinks at runtime; retry policies decide per outcome).
- **pytest-rerunfailures** re-drives `runtestprotocol` off an informal
  contract: the `item._request` falsy guard re-initializes the request on
  re-entry (`src/_pytest/runner.py:126-130`) and a `finally` clause nulls
  `_request`/`funcargs` (`runner.py:148-150`). It works, but it is the whole
  extent of core's rerun support and it can only rerun *entire* protocols.
- [#12596](https://github.com/pytest-dev/pytest/issues/12596) (prototype in
  #12597) proposed the missing fixture primitive — resetting function-scoped
  fixtures between in-item executions — but deliberately kept "the test item
  should still be failed/passed and reported as a unit". That loses exactly
  the thing CI consumers keep asking for: *per-iteration visibility*.
- [#12939](https://github.com/pytest-dev/pytest/issues/12939) asks for
  retry-with-fresh-fixtures (growing timeouts): today's retry plugins cannot
  rebuild fixtures per attempt without relying on implementation details.

The common shape underneath all of these: a **loop controller** wants to
execute a test item N times, with N unknown at collection time, with **fresh
function-scoped fixtures per iteration**, and with each iteration carrying a
**loop key** that is **reportable and useful** — in the terminal, in
junitxml/xunit, and in machine-readable report streams.

This proposal makes that a core protocol.

## Prior art

- `runtestprotocol` rerun contract (`runner.py:123-151`) — reused verbatim as
  the per-iteration reset mechanism (§ Fixture mechanics).
- **subtests** (now in-tree, `src/_pytest/subtests.py`) — the established
  pattern for *runtime sub-identity*: extra call-phase reports for a stable
  nodeid, identity in a structured report field (`SubtestReport.context`),
  custom `pytest_report_teststatus` categories, own serialization hooks.
  Subtests do **not** re-run fixtures and currently collapse into the parent
  testcase in junitxml — both gaps this proposal addresses for loops (and
  builds the machinery subtests could later reuse, § Relationship to
  subtests).
- **#12596/#12597** — the fixture-reset mechanics (reset method, teardown
  ordering via a sequence counter, an `item` scope). This proposal subsumes
  the first two with existing machinery and defers the third (§ Fixture
  mechanics).
- **pytest-repeat / pytest-flakefinder** — collection-time fan-out; stays
  valid, but both could migrate to the loop protocol and gain dynamic counts.

## Goals

1. A **marker-carried loop controller** drives repeated executions of one
   item; plugins (hypothesis, repeat, retry) apply the marker themselves.
2. **Inversion of control**: the controller decides how many iterations run
   and when to stop — required by hypothesis's generate + shrink phases.
3. **Fresh function-scoped fixtures every iteration**, torn down and set up
   through the normal `SetupState`/`FixtureDef` paths.
4. Intermediate iterations tear down **only the function/item scope**; the
   final teardown honors the real `nextitem` so higher scopes behave exactly
   as today.
5. **Per-iteration `TestReport`s** carrying a structured loop key, usable by
   junitxml (distinct testcases), terminal, and machine-readable consumers.
6. **Deferrable reporting**: a controller may run iterations silently and
   decide later what to emit (hypothesis reports only the shrunk failure).
7. **Zero cost and byte-identical behavior** for unmarked tests.

### Non-goals (v1)

- Controller composition (`repeat × hypothesis`) — multiple `loop` marks on
  one item are a collection error.
- Per-iteration *fixture parametrization* (injecting `request.param` per
  iteration) — only direct function-argument injection is in scope.
- unittest `TestCase` items — collection error with a clear message.
- Changing subtests — a subtest inside an iteration simply carries both
  identities.

## The marker and controller API

```python
@pytest.mark.loop(controller)
def test_foo(db, tmp_path): ...
```

`controller` is any callable implementing the `LoopController` protocol.
Plugins normally apply the mark themselves: hypothesis on `@given`-decorated
functions, pytest-repeat via `pytest_collection_modifyitems`. The closest mark
wins (`item.get_closest_marker("loop")`); more than one distinct `loop` mark
is a collection error. The controller is invoked fresh on every protocol run
of the item, so a pytest-rerunfailures rerun restarts the loop from scratch;
stateful controller instances must be re-entrant.

```python
class LoopController(Protocol):
    def __call__(self, loop: LoopContext) -> None: ...


LoopKey = str | int | tuple["LoopKey", ...]  # JSON-round-trippable (xdist)


@final
class LoopContext:
    item: Item  # the item being looped
    iteration_count: int  # iterations executed so far

    def run_iteration(
        self,
        key: LoopKey | None = None,  # default: running counter 0, 1, 2, ...
        *,
        funcargs: Mapping[str, object] | None = None,
        report: Literal["live", "defer", "discard"] = "live",
    ) -> IterationResult: ...

    def emit(self, result: IterationResult) -> None: ...


@final
@dataclasses.dataclass(frozen=True)
class IterationResult:
    key: LoopKey
    reports: tuple[TestReport, ...]  # setup[, call], teardown
    excinfo: ExceptionInfo[BaseException] | None
    when_failed: Literal["setup", "call", "teardown"] | None
    duration: float

    def emit(self) -> None: ...  # convenience for LoopContext.emit
    @property
    def passed(self) -> bool: ...
    @property
    def failed(self) -> bool: ...
    @property
    def skipped(self) -> bool: ...
```

`LoopContext`, `IterationResult` and the `LoopController` typing protocol are
exported as `pytest.LoopContext` etc.; the implementation lives in a new
`src/_pytest/loop.py`.

### Loop keys

Every iteration is identified by a `LoopKey` attached to all of its reports as
a structured field (§ Reporting). The item's **nodeid is never mutated** — the
item stays one item, selection/`--lf`/cache semantics are untouched. Keys may
repeat across `run_iteration` calls (a shrink pass may revisit a key), but
keys of **emitted** iterations must be unique per item — `LoopContext` raises
otherwise — because junitxml keys testcases by them. `]` is stripped from key
reprs at construction so the derived `[key]` suffix stays parseable.
Controllers should use meaningful keys: `("gen", 17)`, `("shrink", 3)`,
`("attempt", 2)`.

### Reporting modes

- `report="live"` — the iteration's setup/call/teardown reports go through
  `pytest_runtest_logreport` immediately (the pytest-repeat mode; also what
  subtests does for its extra reports, `subtests.py` emit path).
- `report="defer"` — reports are fully constructed (real timing, captured
  output, longrepr) but buffered on the `IterationResult`; calling
  `result.emit()` later replays setup → call → teardown in original internal
  order. Un-emitted deferred results are discarded when the loop finishes.
- `report="discard"` — never reportable; only counted in the loop summary
  (hypothesis's 99 silent passing examples).

### Per-iteration data injection

`run_iteration(funcargs={"x": 3})` overlays values onto the test call for this
iteration only: `pytest_pyfunc_call` (`src/_pytest/python.py:180-197`) builds
`testargs` from `pyfuncitem.funcargs` filtered by `_fixtureinfo.argnames` and
then applies the overlay. Injected names may be function parameters that are
*not* fixtures; to make collection accept them, the mark grows `provides=`:

```python
@pytest.mark.loop(controller, provides=("x", "y"))
def test_foo(x, y, db): ...
```

Names in `provides` are excluded from fixture resolution when
`FixtureManager.getfixtureinfo` computes `_fixtureinfo.argnames` (the same
class of mechanism as the existing indirect-parametrization `ignore_args`
handling). Hypothesis can keep its signature-wrapping during a transition and
eventually drop the wrapper. Overlay entries for names that *are* fixtures
shadow the fixture value for that iteration; the fixture is still set up and
torn down (shadow-without-setup is a non-goal).

### Outcomes and error propagation

`run_iteration` **never raises for test outcomes** — setup errors, failures,
skips, xfails, teardown errors are captured via the normal
`CallInfo.from_call` path and surfaced on the `IterationResult`. Exceptions in
the reraise set (`KeyboardInterrupt`, `bdb.BdbQuit`, session-stop outcomes —
see `get_reraise_exceptions`, `runner.py`) propagate through the controller
and are handled by the loop's finalization (§ Protocol integration). Calling
`run_iteration` on an escaped `LoopContext` raises `RuntimeError`.

## Protocol integration

### Mount point

The loop mounts as a dispatch branch inside `runtestprotocol`
(`runner.py:123-151`) — deliberately *not* as a competing firstresult
`pytest_runtest_protocol` impl — so both halves of the rerunfailures contract
(the `_request` re-init guard and the `finally` cleanup) wrap the loop without
duplication:

```python
def runtestprotocol(item, log=True, nextitem=None):
    hasrequest = hasattr(item, "_request")
    if hasrequest and not item._request:
        item._initrequest()  # rerun contract, unchanged
    loop_mark = item.get_closest_marker("loop")
    try:
        if loop_mark is not None:
            return _loop_runtestprotocol(item, loop_mark, log=log, nextitem=nextitem)
        ...  # existing body unchanged
    finally:
        if hasrequest:
            item._request = False  # unchanged
            item.funcargs = None
```

**Zero-cost path**: with no marker, the only new work is one
`get_closest_marker` call; the report stream is byte-identical to today.

### Per-iteration sequencing

`_loop_runtestprotocol` builds a `LoopContext` and calls `controller(ctx)`.
Each `run_iteration` executes the existing single-item cycle
(`runner.py:132-144`) with two twists:

```text
1. if not first iteration: item._initrequest()     # fresh funcargs + TopRequest
2. rep_setup    = call_and_report(item, "setup",    log=<mode>)
3. if rep_setup.passed:
       rep_call = call_and_report(item, "call",     log=<mode>)
4. rep_teardown = call_and_report(item, "teardown", log=<mode>, nextitem=item)
5. stamp the loop key on all reports; return IterationResult
```

All standard per-phase hooks — `pytest_runtest_setup/call/teardown`,
`pytest_runtest_makereport`, fixture hooks, capture hookwrappers, and (when
live) `pytest_runtest_logreport`/`pytest_exception_interact` — fire **once
per iteration**. `pytest_runtest_protocol` and
`pytest_runtest_logstart/logfinish` fire once per item.
`PYTEST_CURRENT_TEST` updates per phase for free.

### The `nextitem` problem: `nextitem is item` sentinel + `teardown_item_frame`

The controller only knows it is done *after* the last iteration, so "last
iteration" cannot get special teardown treatment. Instead there are two
teardown flavors:

**Intermediate teardown** (every iteration, including the one that turns out
to be last) passes the sentinel `nextitem=item` — a value impossible today,
hence backward compatible. The runner impl routes it:

```python
def pytest_runtest_teardown(item, nextitem):
    if nextitem is item:
        item.session._setupstate.teardown_item_frame(item)
    else:
        item.session._setupstate.teardown_exact(nextitem)
```

`SetupState.teardown_item_frame(item)` is the one new `SetupState` API — the
currently missing "pop just the item frame": assert the top of the stack is
`item`, pop it, run its finalizers LIFO with the same exception grouping as
`teardown_exact` (`runner.py:551-583`). Higher frames (class/module/session)
are untouched. This cannot be expressed through `teardown_exact` — its prefix
rule (`runner.py:558-562`) would *keep* the item frame.

The sentinel doubles as a precise signal for teardown-hooking plugins:
"iteration boundary, not item end".

**Final teardown** runs after the controller returns or raises:

```python
if item.session.shouldfail or item.session.shouldstop:
    nextitem = None  # existing rule, #11706 (runner.py:140-143)
rep = call_and_report(item, "teardown", log, nextitem=nextitem)
```

The item frame is already popped; `teardown_exact(nextitem)` handles that
gracefully — it pops collector frames until the stack is a prefix of
`nextitem.listchain()`, i.e. higher scopes tear down **exactly as today**.

This deliberately carries pytest's existing runtest-loop design: setup and
teardown of higher scopes happen lazily inside item phases. Consequently the
**first iteration's setup runs the full setup chain** (higher scopes included,
via normal `SetupState.setup` laziness, `runner.py:520-539`) and the **final
loop-less teardown tears down toward the real `nextitem`**. A broken module
fixture therefore surfaces on iteration 0's (loop-keyed) setup report; the
stored frame exception replays identically on every later iteration
(`runner.py:526-529`), so well-behaved controllers stop on
`when_failed == "setup"`.

### Controller exceptions and the item verdict

`controller(ctx)` is wrapped in `CallInfo.from_call(when="call", reraise=...)`:

- **Reraise set** (`KeyboardInterrupt`, `BdbQuit`, session stop): final
  teardown runs (`nextitem=None` per the shouldstop rule), then the exception
  propagates — session behavior identical to today.
- **Outcome exceptions** (`pytest.fail()` / `pytest.skip()` / xfail): captured
  into the item-level call report — the sanctioned channel for a controller to
  state the item's summary verdict (hypothesis calls `fail()` with the shrunk
  counterexample's repr).
- **Any other exception** (controller bug): item-level *error* report — loud,
  never swallowed.
- **Zero iterations and nothing emitted or raised**: a synthesized item-level
  error report, `"loop controller executed no iterations"` — a silent pass
  would hide controller bugs. Controllers that legitimately have nothing to
  run call `pytest.skip()`.

## Fixture mechanics — no new reset API

Fresh function scope per iteration composes three existing, battle-tested
mechanisms; #12596's new primitives are subsumed:

1. **Frame teardown = fixture teardown.** Function-scoped fixture finalizers
   are registered on the item node (`request.node.addfinalizer`,
   `fixtures.py:1238` → `SetupState.addfinalizer`, `runner.py:541-549`).
   `teardown_item_frame` runs them LIFO — reverse original execution order,
   which is what #12596's sequence counter existed to guarantee.
   `FixtureDef.finish()` (`fixtures.py:1147`) clears `cached_result` and
   `_finalizers` along the way, so no stale cache survives.
2. **`_initrequest()` = fixture reset.** Recreating `item.funcargs` and
   `TopRequest` per iteration (the rerunfailures path,
   `python.py:1737-1741`) replaces #12596's `FixtureRequest.reset()`. One
   mechanism, two callers.
3. **Differential re-setup.** `SetupState.setup(item)` re-pushes only the
   missing item frame (`runner.py:531-534`); `Function.setup()` →
   `TopRequest._fillfixtures` (`fixtures.py:803`) → `FixtureDef.execute`
   re-runs function-scoped fixtures and **cache-hits every higher-scoped
   fixture** (`cached_result` intact, param `cache_key` comparison unchanged,
   `fixtures.py:1202-1211`). Higher-scoped fixtures are shared across
   iterations by construction; their finalizers live on higher frames and run
   at the real final teardown.

**#12596's `item` scope** (a fixture shared across iterations but torn down at
item end) is *deferred, not rejected*: in this design "function scope" *is*
"per-iteration scope"; an `item` scope needs a second per-item stack frame
(`[..., item-persistent, item-iteration]`) so its finalizers survive
`teardown_item_frame`. Clean follow-up on top of this proposal.

**The tmp_path incompatibility #12596 hit resolves itself**: each iteration
goes through `call_and_report`, so `pytest_runtest_makereport` runs *before*
that iteration's teardown — tmp_path's report-driven retention logic sees a
report per iteration and each iteration gets its own numbered directory.

## Reporting model

### The `loop` field

```python
@dataclasses.dataclass(frozen=True, kw_only=True)
class LoopIteration:
    key: LoopKey  # controller-chosen; unique among emitted iterations
    index: int  # 0-based true execution counter (gaps show discards)
    controller: str  # "hypothesis", "repeat", "retry", ... machine-filterable
    data: Mapping[str, str] = (
        {}
    )  # optional payload, saferepr'd like SubtestContext.kwargs
```

`TestReport` gains `loop: LoopIteration | None = None`, stamped (via a
makereport hookwrapper in `_pytest/loop.py`) on every report produced inside
`run_iteration` — including the per-iteration **setup and teardown** reports,
so a fixture failing on iteration 57 surfaces as a keyed *error*, preserving
the error/failure split everywhere downstream.

A field, **not** a `TestReport` subclass: reports keep flowing through the
normal `from_item_and_call`/`pytest_runtest_makereport` machinery, third-party
`isinstance(report, TestReport)` checks keep working, and it composes — a
`SubtestReport` raised inside an iteration simply also carries `loop`. Because
this is core, `_report_to_json`/`_report_kwargs_from_json`
(`reports.py:541-611`) learn to round-trip `loop` natively (exactly like
`longrepr`), so **xdist and report-log consumers work with no new hooks** —
no `_report_type` stamping dance as subclasses need (`reports.py:527-538`,
cf. `subtests.py` serialization hooks).

### The parent report contract

**Unchanged and guaranteed: exactly one loop-less `when="call"` report per
item**, emitted **after** all iteration reports. Its outcome is the
controller's verdict (via `fail()`/`skip()`/normal return; default if the
controller doesn't decide: failed if any iteration failed). It carries a
`loop_summary` field — `{controller, iterations_run, emitted, outcomes:
{"passed": 99, "failed": 1}}` — so deferred/discarded work is visible in every
downstream output without emitting hundreds of reports.

This ordering is load-bearing for `--lf`: `LFPlugin` keys off `report.nodeid`
and last-writer-wins, so the parent verdict decides —
**zero cacheprovider changes**.

The compat contract for report consumers, spelled out:

- *Unchanged*: one loop-less call report per item; `report.nodeid` is the
  collection-time nodeid on every report; unmarked suites are byte-identical.
- *Changed for marked items only*: "one call report per nodeid" is gone
  (de-facto already broken by subtests and rerunfailures; now
  core-sanctioned). Per-execution consumers key on
  `(report.nodeid, report.loop and report.loop.key)`; per-test consumers
  filter `report.loop is None`.
- *No global feature flag*: the marker on the test is the opt-in.

### Summary counts and terminal

`BaseReport.count_towards_summary` is a property (`reports.py:167-177`);
`TestReport` overrides it as `self.loop is None` — iterations never inflate
"1 failed" into "101 failed".

A `tryfirst pytest_report_teststatus` impl in the loop plugin classifies loop
reports (subtests' hook must keep winning for `SubtestReport`s; the loop hook
returns `None` for them):

| condition                          | category       | letter | verbose word     |
|------------------------------------|----------------|--------|------------------|
| iteration failed                   | `loop failed`  | `i`    | `ITERFAIL[key]`  |
| iteration errored (setup/teardown) | `loop error`   | `I`    | `ITERERROR[key]` |
| iteration passed (default verbosity) | *(suppressed)* |      |                  |
| iteration skipped                  | `loop skipped` | `-`    | `ITERSKIP[key]`  |

Letters `u`/`y` are taken by subtests, `R` by rerunfailures. Category strings
surface in the summary line the way `rerun` does today ("2 loop failed"
alongside "1 failed") without touching exit-status-relevant totals. A
`VERBOSITY_LOOP` ini knob mirrors subtests' `VERBOSITY_SUBTESTS` fine-grained
verbosity. Controllers may override wording with their own tryfirst hook
(rerunfailures keeps `rerun`/`R` when it migrates onto the protocol).

Deferred iterations produce no live terminal output by design (hypothesis
shows nothing today either). An optional lightweight notification hook —
`pytest_loop_iteration(item, iteration, outcome)`, historic, no reports
attached — would give progress-hungry plugins (pytest-sugar, IDE runners)
liveness under deferral; whether it ships in v1 is an open question.

### junitxml

The stated pain point — loop keys must be useful in xunit — and the hardest
consumer, because everything is keyed today by `(nodeid, workernode)`
(`junitxml.py:502-518`), collapsing same-nodeid reports into one `<testcase>`.

- Extend the `_NodeReporter` cache key to `(nodeid, workernode, loop_key)`
  (`loop_key = report.loop.key if report.loop else None`); `finalize()` pops
  the same triple. Iterations become distinct `<testcase>` elements; the
  parent keeps `(nodeid, workernode, None)`.
- Iteration testcase names gain a second bracket group after the
  collection-time param suffix: `test_foo[p1][gen-17]` — derived purely from
  `report.loop` in `record_testreport`/`mangle_test_address`
  (`junitxml.py:114-142, 445-453`); the nodeid itself is untouched.
  Emitted-key uniqueness (enforced by `LoopContext`) keeps this sound without
  mangling heuristics.
- The `open_reports` / double-fail reconciliation machinery
  (`junitxml.py:562-620, 655-661`) — which assumes one call report per
  `(nodeid, worker)` — extends its matchers with the loop key, so
  "failed call + errored teardown" resolves correctly *per iteration*.
- **The parent testcase is always written**; iterations are additional
  entries. CI dashboards keyed on the stable `classname/name` keep an
  unbroken history — iterations become visible *in addition*, never
  *instead*.
- Loop identity also lands as `<property name="loop:key">` etc., except under
  strict `xunit2` (testcase properties violate the schema — same policy as
  `record_property`), where the `[key]` name suffix carries the identity
  alone. Deferred/unreported iterations appear only via the parent's
  `loop_summary` properties.
- Accepted, documented quirks: testsuite totals count parent + emitted
  iterations (a looped item with one emitted failing iteration reports
  `tests=2 failures=2`); the parent call duration spans the whole loop and
  overlaps the iteration sum (duration semantics are already fuzzy under
  reruns today).

### Relationship to subtests

Both features attach runtime sub-identity to a stable nodeid
(`SubtestReport.context` vs `TestReport.loop`); they can co-occur (a
`subtests.test()` block inside a hypothesis example → a `SubtestReport`
carrying both). **Don't unify now**: a later follow-up can define a small
shared `SubIdentity` rendering protocol (a `describe()` for headlines and
junitxml suffixes plus JSON round-trip), at which point the junitxml keying
built here gives subtests their missing per-subtest testcase story. Unifying
eagerly would couple this proposal to redesigning subtests' junitxml
behavior.

## Flagship consumers (sketches)

### hypothesis (#916)

```python
def hypothesis_controller(loop: LoopContext) -> None:
    engine = build_engine(loop.item)  # from @given metadata
    for n, example in enumerate(engine.generate()):  # generate phase
        res = loop.run_iteration(("gen", n), funcargs=example.kwargs, report="discard")
        if res.skipped:
            return  # static skip
        engine.record(example, res)  # excinfo feeds shrinking
        if engine.done:
            break
    if engine.has_failure:
        for k, ex in enumerate(engine.shrink()):  # shrink phase, silent
            engine.record(
                ex,
                loop.run_iteration(("shrink", k), funcargs=ex.kwargs, report="discard"),
            )
        loop.run_iteration(
            ("minimal", 0),  # replay minimal example
            funcargs=engine.minimal.kwargs,
            report="live",
        )
        # live: --pdb / pytest_exception_interact fire HERE, on the shrunk example
```

Every example gets fresh function-scoped fixtures — the
`function_scoped_fixture` health check problem disappears. pytest owns the
loop; hypothesis owns the policy. Reports: N discarded generate/shrink
iterations, one live `[minimal-0]` failure, one loop-less parent failure with
`loop_summary`.

### pytest-repeat

```python
def make_repeat_controller(count: int) -> LoopController:
    def controller(loop: LoopContext) -> None:
        for i in range(count):
            if loop.run_iteration(i).skipped:  # live per-iteration reports
                break

    return controller
```

### retry with growing timeout (#12939)

```python
def make_retry_controller(base_timeout: float, retries: int) -> LoopController:
    def controller(loop: LoopContext) -> None:
        timeout, last = base_timeout, None
        for attempt in range(retries + 1):
            last = loop.run_iteration(
                ("attempt", attempt),
                funcargs={"service_timeout": timeout},
                report="defer",
            )
            if not last.failed:
                break
            timeout *= 2
        last.emit()  # only the deciding attempt

    return controller
```

Fresh fixtures per attempt is the entire point of #12939 — the flaky-service
fixture is rebuilt with each new timeout, which no rerun-inside-call plugin
can do today.

## Edge cases

- **Iteration setup failure**: keyed setup error report; intermediate teardown
  still finalizes partial setup (today's error path). Higher-collector setup
  failure replays on every iteration (`runner.py:526-529`) — controllers stop
  on `when_failed == "setup"`.
- **KeyboardInterrupt / `session.shouldstop`**: propagates through
  `run_iteration` and the controller; final teardown runs with
  `nextitem=None`, then re-raise. No iteration teardown is skipped because it
  lives inside `run_iteration`'s own phase sequence.
- **`--setup-only`**: the loop is bypassed entirely — one plain
  setup(+show)+teardown, as if unmarked. **`--setup-show`** during a real run
  shows fixture setup per iteration — truthful, they *are* set up N times.
- **`--pdb` / `pytest_exception_interact`**: fires only for live iterations
  (triggered from `call_and_report`). Deferral-mode controllers get
  post-mortem by re-running the deciding iteration live — hypothesis's
  minimal-example replay does exactly this.
- **Capture**: the capture plugin's per-phase hookwrappers run per iteration;
  every iteration's reports carry their own captured output, buffered ones
  included.
- **xdist**: the whole protocol including the loop runs on one worker; only
  reports travel, and `loop`/`loop_summary` serialize natively.
- **unittest items**: collection error in v1 (`TestCase` runs
  setUp/tearDown inside its own machinery and has no `funcargs`).

## Open questions

1. **`pytest_loop_iteration` progress hook** — ship in v1 or defer? Cheap,
   but hook surface is forever.
2. **`item` scope** (#12596) — the two-frame `SetupState` follow-up: separate
   proposal or fold in?
3. **Controller composition** — nesting (`run_iteration` accepting a
   sub-controller) vs an ordering rule; v1 errors on multiple marks.
4. **Fixture-aware injection** — per-iteration `request.param` injection
   (hypothesis strategies drawing through fixtures); `cache_key`
   implications. Deliberately excluded from v1.
5. **Iteration-boundary hooks** — is the `nextitem is item` sentinel enough
   for pytest-timeout budgets / coverage contexts, or are explicit
   `pytest_loop_iteration_start/finish` hooks needed?
6. **`--setup-plan` / `--collect-only` presentation** of looped items
   (iteration count is dynamic by nature).
7. **Per-key `--lf` replay** — rerunning only failing loop keys requires
   key→execution replay only the controller can do (hypothesis's example
   database is prior art); propose exposing `lastfailed` keys to controllers
   as a follow-up.
8. **junitxml double-counting** — testsuite totals (parent + iterations,
   `failures=2` for one logical failure) and duration overlap: document (as
   proposed) or suppress/derive?
9. **Terminal bikeshed** — letters `i`/`I`, category names, and whether
   `rerun`/`R` becomes the core default for retry-flavored controllers.
10. **Field name** — `loop` vs `iteration` vs a future generic sub-identity
    `context`; `loop` could collide with plugins abusing `TestReport`'s
    `**extra` (`reports.py:335, 378`) — needs a plugin-ecosystem survey.
11. **Subtest parent-flip inside discarded iterations** — subtests' failed
    counter is per-nodeid; a failed subtest in a discarded iteration would
    flip the parent, contradicting deferral. The counter likely needs to
    become loop-aware.

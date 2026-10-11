// Publication versus kernel retirement
scenario("1A", "fatal failure with a prepared unpublished request")
  .given("a RequestLease in PreparedUnpublished holding a ResourceLease")
  .when("CleanupStarted disables normal producers")
  .then("the request is proven unpublished and becomes AbandonedUnpublished")
  .and("cleanup does not flush that application SQE")
  .and("the ResourceLease is released only after all other retaining requests retire");

scenario("1B", "enter fails after shared SQ tail publication")
  .given("a RequestLease made Published before io_uring_enter")
  .when("enter reports an error during fatal unwind")
  .then("the lease remains Published or PublicationUncertain, never PreparedUnpublished")
  .and("its ResourceLease remains live until correlated TerminalCompletion");

// Pending targets and independent cancellation outcomes
scenario("2A", "drain pending one-shot operations without restarting HTTP work")
  .given("published RequestLease instances for ACCEPT, RECV, heap READ and SEND")
  .when("CleanupStarted disables normal completion callbacks and rearming")
  .then("cleanup consumes each correlated TerminalCompletion without producing HTTP work")
  .and("each ResourceLease stays live through every retaining target retirement")
  .and("only then can CleanupSettled permit deferred resource destruction");

scenario("2B", "cancellation receipt is not target acknowledgment")
  .given("a published RequestLease with an unread target completion or an unresolved target")
  .when("a CancellationReceipt reports success, a nonnegative count or no match")
  .then("only separately observed TerminalCompletion establishes TargetRetired; it is not consumed twice")
  .and("no control tag or submit count substitutes for TargetRetired");

scenario("2C", "failed timed-out or noncancelable target preserves ownership")
  .given("an unresolved published RequestLease retaining application memory")
  .when("cancellation fails, times out or cannot retire the target")
  .then("CleanupStalled preserves the ResourceLease and access to outstanding results")
  .and("cleanup does not return through defers that free referenced memory")
  .and("the verifier requires an explicit safe escalation policy before acceptance");

// Successful resource-producing results
scenario("3A", "successful ACCEPT completion remains unread during fatal cleanup")
  .given("an ACCEPT TerminalCompletion in ReadyUnread with a nonnegative descriptor")
  .when("cleanup drains that completion despite cancel no-match")
  .then("AcceptDescriptorClaimed creates a ResourceLease and ResourceReleased closes it")
  .and("owned peer EOF and whole descriptor census are observed before process exit");

scenario("3B", "copied acknowledged ACCEPT result has not reached a client owner")
  .given("an ACCEPT result in CopiedUndispatched after CQ advancement")
  .when("fatal cleanup starts before the result is transferred to a ClientSlot")
  .then("cleanup claims and releases its ResourceLease exactly once")
  .and("an empty CQ or copied-result discard cannot substitute for release");

scenario("3C", "descriptor zero is a successful ACCEPT resource")
  .given("an ACCEPT TerminalCompletion whose result is descriptor zero")
  .when("cleanup claims successful resource results")
  .then("descriptor zero receives a ResourceLease and is closed exactly once")
  .and("zero is not classified as EOF or a failed ACCEPT");

scenario("3D", "idle phase does not erase an already claimed accepted descriptor")
  .given("a ClientSlot still in idle owns an accepted ResourceLease")
  .when("configuration fails before reception is queued")
  .then("cleanup releases that owned descriptor despite the idle phase")
  .and("phase filtering cannot discard descriptor ownership");

// Bounds and preserved normal teaching behavior
scenario("4A", "cleanup control admission respects a finite SQ")
  .given("up to thirty-three unresolved application leases and a requested sixty-four-entry SQ")
  .when("cleanup needs up to thirty-three cancellation requests")
  .then("control admission accounts for remaining SQ occupancy, not just controller count")
  .and("cleanup does not assume all sixty-six application and control entries fit at once")
  .and("backpressure or admission failure cannot trigger early operand release");

scenario("4B", "fatal observer output failure with a late loopback peer")
  .given("an idle receiver and next ACCEPT are published while another response is active")
  .when("observer output fails and a late peer connects")
  .then("cleanup retires published requests and claims every successful ACCEPT resource")
  .and("pre-exit census and peer EOF prove cleanup, not operating-system process exit");

scenario("4C", "normal partial I/O and per-client errors remain unchanged")
  .given("CleanupSession is inactive during normal HTTP operation")
  .when("a request fragments, SEND completes short or a peer abandons its response")
  .then("whole wire bytes and per-client progress preserve the existing public contracts")
  .and("another client can finish while one client waits")
  .and("normal producer rearming remains enabled outside fatal cleanup");

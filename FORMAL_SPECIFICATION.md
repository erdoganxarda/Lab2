# Formal Specification - Distributed Request Processing System

## 1. System Overview

This document provides a formal specification for a distributed request processing system consisting of client nodes, queue nodes, service nodes, and a high-performance distribution device.

## 2. Components

### 2.1 Node Types

**Definition 2.1.1**: The system consists of three primary node types:
- **Q-nodes**: Queue and request distribution nodes
- **P-nodes**: Request processing (service) nodes
- **QP-nodes**: Mixed nodes with both queue and processing capabilities

### 2.2 Component Inventory

Let **N** be the set of all nodes in the system:

```
N = {K₁, K₂, Q₁, P₁₁, P₁₂, P₁₃, D, Q₂₁, Q₂₂, Q₂₃, P₂₁, P₂₂, P₂₃}
```

Where:
- **K** = {K₁, K₂}: Set of client nodes
- **Q₁**: Primary cyclic distribution queue
- **P₁ˣ** = {P₁₁, P₁₂, P₁₃}: First-tier service nodes with priority queues
- **D**: High-performance query distribution device
- **Q₂ˣ** = {Q₂₁, Q₂₂, Q₂₃}: Second-tier queue nodes
- **P₂ˣ** = {P₂₁, P₂₂, P₂₃}: Second-tier service nodes with failure capability

## 3. Request Types and Priorities

### 3.1 Request Definition

**Definition 3.1.1**: A request r is a tuple:
```
r = (id, type, client_id, priority, timestamp, hops)
```

Where:
- `id ∈ String`: Unique request identifier
- `type ∈ Z = {z₁, z₂, z₃}`: Request type
- `client_id ∈ K`: Originating client
- `priority ∈ ℕ`: Priority level
- `timestamp ∈ ℝ⁺`: Creation time
- `hops ∈ N*`: Ordered sequence of nodes visited

### 3.2 Priority Ordering

**Axiom 3.2.1**: Priority ordering is defined as:
```
priority(z₃) > priority(z₂) > priority(z₁)
```

Specifically:
```
priority(z₃) = 3
priority(z₂) = 2
priority(z₁) = 1
```

## 4. Queue Specifications

### 4.1 Queue Properties

**Definition 4.1.1**: A priority queue Q_p at node n is defined as:
```
Q_p = {(r, t_entry) | r.priority = p, t_entry ∈ ℝ⁺}
```

Where t_entry is the time when request r entered the queue.

**Property 4.1.2** (FIFO within priority): For any two requests r₁, r₂ ∈ Q_p:
```
If t_entry(r₁) < t_entry(r₂), then r₁ is processed before r₂
```

### 4.2 Multi-Priority Queue

**Definition 4.2.1**: A multi-priority queue MPQ is defined as:
```
MPQ = ⋃(p∈{1,2,3}) Q_p
```

**Algorithm 4.2.2** (Priority Queue Processing):
```
function GET_NEXT_REQUEST(MPQ):
    for p in {3, 2, 1}:  // Check highest priority first
        if Q_p is not empty:
            return DEQUEUE(Q_p)
    return NULL
```

### 4.3 Queue Configuration Parameters

**Definition 4.3.1**: Queue configuration parameters:
- `max_length ∈ ℕ`: Maximum queue capacity
- `max_wait_time ∈ ℝ⁺`: Maximum allowable wait time
- `avg_wait_threshold ∈ ℝ⁺`: Average wait time threshold for scaling

## 5. Distribution Strategies

### 5.1 Cyclic Distribution (Q₁)

**Definition 5.1.1**: Q₁ implements cyclic (round-robin) distribution to P₁ˣ nodes.

**Algorithm 5.1.2** (Cyclic Distribution):
```
Let m = |P₁ˣ| = 3  // Number of service devices
Let i = current_index  // Last device that received request

function DISTRIBUTE_CYCLICALLY(request):
    j = (i mod m) + 1  // Next device index (1-based)
    FORWARD(request, P₁ⱼ)
    i = j
    return j
```

**Property 5.1.3** (Load Balancing): Over n requests, each P₁ˣ node receives approximately n/3 requests.

### 5.2 Type-Based Distribution (D)

**Definition 5.2.1**: Node D implements type-based distribution to Q₂ˣ nodes.

**Algorithm 5.2.2** (Type-Based Distribution):
```
function DISTRIBUTE_BY_TYPE(request):
    match request.type:
        case z₁: FORWARD(request, Q₂₁)
        case z₂: FORWARD(request, Q₂₂)
        case z₃: FORWARD(request, Q₂₃)
```

**Mapping 5.2.3**:
```
φ: Z → Q₂ˣ
φ(z₁) = Q₂₁
φ(z₂) = Q₂₂
φ(z₃) = Q₂₃
```

## 6. Service Time Specifications

### 6.1 Service Time Distribution

**Definition 6.1.1**: Service time S for a request at node n follows a uniform distribution:
```
S_n ~ U[a_n, b_n]
```

Where [a_n, b_n] is the service time interval for node n.

### 6.2 Specific Service Times

**Parameter 6.2.1**: Service time intervals:
```
P₁ˣ nodes: S ~ U[0.1, 0.3] seconds
P₂ˣ nodes: S ~ U[0.2, 0.5] seconds
```

## 7. Wait Time Metrics

### 7.1 Wait Time Definition

**Definition 7.1.1**: Wait time W(r) for request r at node n:
```
W(r) = t_process(r) - t_entry(r)
```

Where:
- `t_entry(r)`: Time when r entered the queue
- `t_process(r)`: Time when r began processing

### 7.2 Average Wait Time

**Definition 7.2.1**: Average wait time at node n over window of k requests:
```
W̄_n = (1/k) Σ(i=1 to k) W(r_i)
```

## 8. Failure Model

### 8.1 P₂ˣ Node Failures

**Definition 8.1.1**: A P₂ˣ node n can be in one of two states:
```
state(n) ∈ {AVAILABLE, FAILED}
```

**Property 8.1.2** (Failure Transition):
```
P(state(n, t+Δt) = FAILED | state(n, t) = AVAILABLE) = p_fail
```

Where p_fail is the failure probability (default: 0.1).

**Property 8.1.3** (Recovery Transition):
After failure duration d ~ U[d_min, d_max]:
```
state(n, t+d) = AVAILABLE
```

Where d ∈ [3, 8] seconds.

### 8.2 Request Success Criteria

**Definition 8.2.1**: A request r is successful if and only if:
```
SUCCESS(r) ⟺ |responses(r)| = 3 ∧ ∀resp ∈ responses(r): resp.success = true
```

Where responses(r) is the set of responses received for request r from {P₂₁, P₂₂, P₂₃}.

## 9. Dynamic Scaling

### 9.1 Scaling Trigger

**Definition 9.1.1**: Scaling condition for P₁ˣ node n:
```
SCALE_UP(n) ⟺ W̄_n > θ_wait × α_scale
```

Where:
- `θ_wait`: Average wait time threshold (default: 2.0s)
- `α_scale`: Scale-up multiplier (default: 1.5)
- `W̄_n`: Current average wait time at node n

### 9.2 Scaling Action

**Algorithm 9.2.1** (Dynamic Scaling):
```
function CHECK_AND_SCALE(n):
    W̄_n = CALCULATE_AVG_WAIT_TIME(n)
    if W̄_n > θ_wait × α_scale:
        if |instances(n)| < max_instances:
            START_NEW_INSTANCE(n)
            UPDATE_ROUTING_TABLE(Q₁, n)
```

## 10. Communication Protocol

### 10.1 Message Structure

**Definition 10.1.1**: Messages are transmitted over TCP/IP with the following structure:
```
Message = Length_Prefix || JSON_Payload
```

Where:
- `Length_Prefix`: 4-byte integer (big-endian) indicating payload size
- `JSON_Payload`: UTF-8 encoded JSON string

### 10.2 Message Types

**Definition 10.2.1**: Message type enumeration:
```
MessageType = {REQUEST, RESPONSE, ACK, HEARTBEAT}
```

## 11. System Properties

### 11.1 Liveness

**Property 11.1.1** (Request Progress): Every request r will eventually either:
1. Complete successfully with all responses, or
2. Timeout and be marked as failed

**Proof sketch**: Each queue has finite capacity, each service has bounded time, and timeout ensures termination.

### 11.2 Fairness

**Property 11.2.1** (Priority Fairness): Requests of higher priority are always processed before requests of lower priority at P₁ˣ nodes.

**Property 11.2.2** (Cyclic Fairness): Over a sequence of n requests at Q₁, each P₁ˣ node receives ⌊n/3⌋ or ⌈n/3⌉ requests.

### 11.3 Reliability

**Property 11.3.1** (Partial Reliability): The system continues to operate with reduced capacity even when some P₂ˣ nodes fail.

**Property 11.3.2** (State Recovery): Failed P₂ˣ nodes automatically recover after failure duration.

## 12. Performance Metrics

### 12.1 Client-Level Metrics

**Definition 12.1.1**: Client success rate:
```
SR_k = (|{r ∈ R_k | SUCCESS(r)}|) / |R_k|
```

Where R_k is the set of requests from client k.

### 12.2 System-Level Metrics

**Definition 12.2.1**: System throughput:
```
Θ = |{r ∈ R | SUCCESS(r)}| / T
```

Where T is the total observation time.

**Definition 12.2.2**: Average end-to-end latency:
```
L̄ = (1/|R|) Σ(r∈R) (t_response(r) - t_submit(r))
```

## 13. Configuration Constraints

### 13.1 Network Constraints

**Constraint 13.1.1**: Port assignments must be unique:
```
∀n₁, n₂ ∈ N: n₁ ≠ n₂ ⟹ port(n₁) ≠ port(n₂)
```

### 13.2 Scaling Constraints

**Constraint 13.2.1**: Maximum instance limit:
```
∀n ∈ P₁ˣ: |instances(n)| ≤ max_instances
```

### 13.3 Timeout Constraints

**Constraint 13.3.1**: Client timeout must exceed maximum possible processing time:
```
timeout_client > 2 × (max(S_P₁ˣ) + max(S_P₂ˣ)) + max(W̄)
```

## 14. Formal Verification Points

### 14.1 Correctness Criteria

1. **Priority Ordering**: Higher priority requests processed first ✓
2. **Cyclic Distribution**: Even distribution across P₁ˣ nodes ✓
3. **Type Routing**: Correct mapping from request type to Q₂ˣ ✓
4. **Success Tracking**: Accurate identification of successful/failed requests ✓
5. **Scaling Trigger**: Automatic scaling based on wait time threshold ✓

### 14.2 Safety Properties

1. **No Request Loss**: Every request is either completed or explicitly marked as failed
2. **No Deadlock**: System cannot enter a state where no progress is possible
3. **Bounded Queues**: Queue lengths remain within configured limits

### 14.3 Liveness Properties

1. **Request Completion**: Every submitted request eventually completes (success or failure)
2. **Failure Recovery**: Failed P₂ˣ nodes eventually recover
3. **Scaling Response**: System scales up when overload detected

---

## Appendix A: Notation Summary

| Symbol | Meaning |
|--------|---------|
| N | Set of all nodes |
| K | Set of client nodes |
| Z | Set of request types {z₁, z₂, z₃} |
| r | A request |
| Q_p | Priority queue with priority p |
| MPQ | Multi-priority queue |
| W(r) | Wait time for request r |
| W̄_n | Average wait time at node n |
| S_n | Service time at node n |
| θ_wait | Wait time threshold |
| α_scale | Scaling multiplier |
| SR_k | Success rate for client k |
| Θ | System throughput |
| L̄ | Average latency |

---

**Document Version**: 1.0  
**Date**: December 3, 2025  
**Course**: Distributed Systems Laboratory  
**Institution**: Kaunas Technical University

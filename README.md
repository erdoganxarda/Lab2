# Distributed System Simulation - Lab 2

## System Architecture

This project implements a distributed queuing and processing system with dynamic scaling capabilities based on the laboratory task requirements.

## System Components

### 1. Client Nodes (K1, K2)
- **Purpose**: Generate and send requests to the system
- **Request Types**: z1, z2, z3 (with different priorities)
- **Functionality**: 
  - Sends requests to Q1
  - Receives responses from P21, P22, P23
  - Tracks successful and failed requests
  - A request is **successful** if all 3 responses are received from P2x devices
  - A request is **failed** if not all 3 responses are received (due to P2x failures)

### 2. Q1 Node (Cyclic Distributor)
- **Purpose**: Distribute incoming requests cyclically to P1x service devices
- **Distribution Strategy**: Round-robin (cyclic)
- **Formula**: `j = (i mod m) + 1` where:
  - `m` = number of serving devices (3)
  - `i` = index of last device that received request
  - `j` = index of device that will receive request
- **Target Nodes**: P11, P12, P13

### 3. P1x Service Nodes (P11, P12, P13)
- **Purpose**: Process requests based on priority
- **Priority Order**: z3 > z2 > z1
- **Queue Management**: Multiple priority queues (FIFO within each priority)
- **Processing**: 
  - Simulates service time (random uniform distribution)
  - Tracks queue wait times
  - Forwards processed requests to D

### 4. D Node (High-Performance Distributor)
- **Purpose**: Route requests to appropriate Q2x queues based on request type
- **Routing Strategy**:
  - z1 requests → Q21
  - z2 requests → Q22
  - z3 requests → Q23

### 5. Q2x Nodes (Q21, Q22, Q23)
- **Purpose**: Queue and forward requests to corresponding P2x service devices
- **Mapping**:
  - Q21 → P21
  - Q22 → P22
  - Q23 → P23

### 6. P2x Service Nodes (P21, P22, P23)
- **Purpose**: Final processing and response generation
- **Failure Simulation**: Can randomly go down and recover
- **Response**: Send processed requests back to original clients (K1 or K2)

## Communication Protocol

- **Protocol**: TCP/IP (Socket-based)
- **Message Format**: JSON
- **Message Types**:
  - Request: Contains request_id, type, priority, client_id, timestamp, hops
  - Response: Contains request_id, processed_by, success status

## Dynamic Scaling

The system monitors average queue wait times for P1x nodes. When the average wait time exceeds the threshold, the system triggers scaling:

- **Trigger**: Average wait time > threshold × scale_up_threshold
- **Action**: Increase number of P1x processing units
- **Configuration**: See `SCALING_CONFIG` in `config.py`

## Request Flow

```
K1, K2 (Clients)
    ↓
    → Q1 (Cyclic Distribution)
        ↓
        → P11, P12, P13 (Priority Processing: z3>z2>z1)
            ↓
            → D (High-Performance Distributor)
                ↓
                → Q21, Q22, Q23 (Type-based Queues)
                    ↓
                    → P21, P22, P23 (Final Processing, can fail)
                        ↓
                        ← Back to K1, K2 (Responses)
```

## Installation & Setup

### Prerequisites
- Python 3.7 or higher
- No external dependencies required (uses standard library)

### Running the System

#### Option 1: Run All Components (Recommended)
```powershell
python run_system.py
```

This will start all nodes automatically in the correct order.

#### Option 2: Run Components Individually

Start each component in a separate terminal:

```powershell
# Start Q1
python q1_node.py Q1

# Start D
python d_node.py

# Start P1x nodes
python p1x_service.py P11
python p1x_service.py P12
python p1x_service.py P13

# Start Q2x nodes
python q2x_node.py Q21
python q2x_node.py Q22
python q2x_node.py Q23

# Start P2x nodes
python p2x_service.py P21
python p2x_service.py P22
python p2x_service.py P23

# Start clients (after all services are running)
python client.py K1
python client.py K2
```

## Configuration

Edit `config.py` to adjust:

- **PORT assignments**: Change port numbers for each node
- **Service times**: Adjust processing time ranges
- **Queue parameters**: Max length, wait time thresholds
- **Client behavior**: Request interval, timeout, number of requests
- **Failure simulation**: Probability and duration of P2x failures
- **Scaling parameters**: Thresholds and maximum instances

## Key Features

### 1. Priority Queue Implementation
- Multiple priority levels (z3 highest, z1 lowest)
- FIFO ordering within each priority level
- Higher priority requests processed first

### 2. Cyclic Load Balancing
- Round-robin distribution at Q1
- Ensures even load distribution across P1x nodes

### 3. Fault Tolerance
- P2x nodes can fail and recover
- Clients track failed requests
- System continues operating with reduced capacity

### 4. Dynamic Scaling
- Monitors queue wait times
- Automatically scales up P1x nodes when needed
- Prevents overload situations

### 5. Request Tracking
- Each request tracks its path (hops) through the system
- Clients verify all responses received
- Statistics collected at each node

## Success Criteria

A client request is considered **SUCCESSFUL** if:
1. All 3 P2x devices (P21, P22, P23) return a response
2. All responses indicate successful processing
3. Response received within timeout period

A client request is considered **FAILED** if:
1. Not all 3 responses received (some P2x nodes down)
2. Timeout exceeded
3. Any processing error occurred

## Testing

The system includes:
- Simulated failures (P2x nodes)
- Load testing (multiple concurrent clients)
- Priority queue testing (mixed request types)
- Scaling verification (high load scenarios)

## Grading Components

1. **Formal Specification** (2 points): See `FORMAL_SPECIFICATION.md`
2. **System Implementation** (6 points):
   - All nodes implemented with TCP/IP
   - Priority queues working correctly
   - Cyclic distribution functioning
   - Fault tolerance (P2x failures)
   - Client success/failure tracking
3. **Dynamic Scaling** (2 points):
   - Wait time monitoring
   - Automatic scaling triggers
   - P1x instance management

## Logging

The system provides detailed logging:
- INFO level: Key events (requests received, forwarded, processed)
- WARNING level: Failures, scaling events
- ERROR level: Connection issues, processing errors

Logs are output to console with timestamps and node names.

## Architecture Diagram

```
        K1 (Client)
         |
         | z1,z2,z3
         |
        Q1 (Cyclic)
       / | \
      /  |  \
   P11 P12 P13 (Priority: z3>z2>z1)
      \  |  /
       \ | /
         D (High-Perf)
       / | \
      /  |  \
    Q21 Q22 Q23
     |   |   |
    P21 P22 P23 (Can Fail)
      \  |  /
       \ | /
        K1, K2 (Responses)
```

## License

Academic project for KTU Distributed Systems Lab 2

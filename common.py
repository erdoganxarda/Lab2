"""
Common utilities and message structures for the distributed system
"""

import json
import time
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Optional, List
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class MessageType(Enum):
    """Types of messages in the system"""
    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"
    ACK = "ACK"
    HEARTBEAT = "HEARTBEAT"
    REGISTER = "REGISTER"


@dataclass
class Request:
    """Request structure"""
    request_id: str
    request_type: str  # z1, z2, z3
    client_id: str
    timestamp: float
    priority: int
    hops: List[str]  # Track the path through the system
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))
    
    @staticmethod
    def from_json(json_str: str) -> 'Request':
        data = json.loads(json_str)
        return Request(**data)
    
    def add_hop(self, node_name: str):
        """Add a node to the request's path"""
        self.hops.append(node_name)


@dataclass
class Response:
    """Response structure"""
    request_id: str
    request_type: str
    client_id: str
    processed_by: List[str]  # List of nodes that processed this
    timestamp: float
    success: bool
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))
    
    @staticmethod
    def from_json(json_str: str) -> 'Response':
        data = json.loads(json_str)
        return Response(**data)


@dataclass
class Message:
    """Generic message wrapper"""
    msg_type: str
    payload: dict
    
    def to_json(self) -> str:
        return json.dumps({
            'msg_type': self.msg_type,
            'payload': self.payload
        })
    
    @staticmethod
    def from_json(json_str: str) -> 'Message':
        data = json.loads(json_str)
        return Message(
            msg_type=data['msg_type'],
            payload=data['payload']
        )


def send_message(sock, message: str) -> bool:
    """
    Send a message through a socket with length prefix
    Returns True if successful, False otherwise
    """
    try:
        # Add length prefix
        msg_bytes = message.encode('utf-8')
        length = len(msg_bytes)
        length_prefix = length.to_bytes(4, byteorder='big')
        
        sock.sendall(length_prefix + msg_bytes)
        return True
    except Exception as e:
        logging.error(f"Error sending message: {e}")
        return False


def receive_message(sock, timeout: Optional[float] = None) -> Optional[str]:
    """
    Receive a message from a socket with length prefix
    Returns the message string or None if error/timeout
    """
    try:
        if timeout:
            sock.settimeout(timeout)
        
        # Read length prefix (4 bytes)
        length_bytes = sock.recv(4)
        if not length_bytes or len(length_bytes) < 4:
            return None
        
        length = int.from_bytes(length_bytes, byteorder='big')
        
        # Read the actual message
        chunks = []
        bytes_received = 0
        
        while bytes_received < length:
            chunk = sock.recv(min(length - bytes_received, 4096))
            if not chunk:
                return None
            chunks.append(chunk)
            bytes_received += len(chunk)
        
        message = b''.join(chunks).decode('utf-8')
        return message
        
    except Exception as e:
        logging.error(f"Error receiving message: {e}")
        return None


def create_request_id(client_id: str, sequence: int) -> str:
    """Create a unique request ID"""
    return f"{client_id}_{sequence}_{int(time.time() * 1000)}"


class Statistics:
    """Track statistics for a node"""
    def __init__(self, node_name: str):
        self.node_name = node_name
        self.requests_received = 0
        self.requests_processed = 0
        self.requests_forwarded = 0
        self.total_wait_time = 0.0
        self.queue_lengths = []
        
    def add_request(self):
        self.requests_received += 1
    
    def process_request(self, wait_time: float):
        self.requests_processed += 1
        self.total_wait_time += wait_time
    
    def forward_request(self):
        self.requests_forwarded += 1
    
    def record_queue_length(self, length: int):
        self.queue_lengths.append(length)
    
    def get_average_wait_time(self) -> float:
        if self.requests_processed == 0:
            return 0.0
        return self.total_wait_time / self.requests_processed
    
    def get_average_queue_length(self) -> float:
        if not self.queue_lengths:
            return 0.0
        return sum(self.queue_lengths) / len(self.queue_lengths)
    
    def __str__(self) -> str:
        return (f"Statistics for {self.node_name}:\n"
                f"  Received: {self.requests_received}\n"
                f"  Processed: {self.requests_processed}\n"
                f"  Forwarded: {self.requests_forwarded}\n"
                f"  Avg Wait Time: {self.get_average_wait_time():.3f}s\n"
                f"  Avg Queue Length: {self.get_average_queue_length():.2f}")

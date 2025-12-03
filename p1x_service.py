"""
P1x Service Nodes (P11, P12, P13)
Process requests with priority queues (z3 > z2 > z1) and forward to D
"""

import socket
import threading
import queue
import time
import random
import logging
from typing import Dict
from common import Request, send_message, receive_message, Statistics
from config import HOST, PORTS, SERVICE_TIME, PRIORITIES


class P1xServiceNode:
    def __init__(self, node_name: str):
        self.node_name = node_name
        self.port = PORTS[node_name]
        
        # Priority queues for different request types
        self.queues: Dict[int, queue.Queue] = {
            PRIORITIES['z3']: queue.Queue(),  # Priority 3 (highest)
            PRIORITIES['z2']: queue.Queue(),  # Priority 2
            PRIORITIES['z1']: queue.Queue(),  # Priority 1 (lowest)
        }
        
        # Track when requests entered queue (for wait time calculation)
        self.queue_entry_times: Dict[str, float] = {}
        
        self.running = False
        self.server_socket = None
        self.stats = Statistics(self.node_name)
        
        self.d_address = (HOST, PORTS['D'])
        
        self.logger = logging.getLogger(self.node_name)
        
    def start(self):
        """Start P1x service node"""
        self.running = True
        self.logger.info(f"{self.node_name} starting on port {self.port}")
        
        # Start processing thread
        processing_thread = threading.Thread(target=self._process_queue, daemon=True)
        processing_thread.start()
        
        # Start server
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((HOST, self.port))
        self.server_socket.listen(10)
        
        self.logger.info(f"{self.node_name} listening for requests...")
        
        try:
            while self.running:
                try:
                    self.server_socket.settimeout(1.0)
                    conn, addr = self.server_socket.accept()
                    threading.Thread(target=self._handle_request, args=(conn,), daemon=True).start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.logger.error(f"Error accepting connection: {e}")
        finally:
            self.stop()
            
    def _handle_request(self, conn: socket.socket):
        """Handle incoming request from Q1"""
        try:
            self.logger.debug(f"Connection received from {conn.getpeername()}")
            msg = receive_message(conn)
            if not msg:
                self.logger.warning("No message received")
                return
            
            self.logger.debug(f"Received message: {msg[:100]}")
            request = Request.from_json(msg)
            self.stats.add_request()
            
            request.add_hop(self.node_name)
            self.logger.info(f"Received {request.request_type} request {request.request_id}")
            
            # Add to appropriate priority queue
            priority = request.priority
            self.queue_entry_times[request.request_id] = time.time()
            self.queues[priority].put(request)
            
            # Record queue length for statistics
            total_queue_length = sum(q.qsize() for q in self.queues.values())
            self.stats.record_queue_length(total_queue_length)
            
            self.logger.debug(f"Queue lengths - z3:{self.queues[3].qsize()} "
                            f"z2:{self.queues[2].qsize()} z1:{self.queues[1].qsize()}")
                
        except Exception as e:
            self.logger.error(f"Error handling request: {e}")
        finally:
            conn.close()
            
    def _process_queue(self):
        """Process requests from queues based on priority"""
        while self.running:
            request = None
            
            # Check queues in priority order (highest to lowest)
            for priority in sorted(self.queues.keys(), reverse=True):
                try:
                    request = self.queues[priority].get_nowait()
                    break
                except queue.Empty:
                    continue
            
            if request:
                # Calculate wait time
                wait_time = time.time() - self.queue_entry_times.get(request.request_id, time.time())
                
                # Simulate processing time
                service_time = random.uniform(
                    SERVICE_TIME[self.node_name]['min'],
                    SERVICE_TIME[self.node_name]['max']
                )
                time.sleep(service_time)
                
                self.stats.process_request(wait_time)
                self.logger.info(f"Processed {request.request_id} (wait: {wait_time:.3f}s, "
                               f"service: {service_time:.3f}s)")
                
                # Forward to D
                if self._forward_to_d(request):
                    self.stats.forward_request()
                    self.logger.info(f"Forwarded {request.request_id} to D")
                else:
                    self.logger.error(f"Failed to forward {request.request_id} to D")
                    
                # Clean up
                if request.request_id in self.queue_entry_times:
                    del self.queue_entry_times[request.request_id]
            else:
                time.sleep(0.01)  # Small sleep to avoid busy waiting
                
    def _forward_to_d(self, request: Request) -> bool:
        """Forward processed request to D"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(self.d_address)
            
            success = send_message(sock, request.to_json())
            sock.close()
            
            return success
        except Exception as e:
            self.logger.error(f"Error forwarding to D: {e}")
            return False
            
    def get_average_wait_time(self, request_type: str) -> float:
        """Get average wait time for specific request type"""
        # This is simplified - in production, you'd track per-type statistics
        return self.stats.get_average_wait_time()
        
    def stop(self):
        """Stop P1x service node"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        
        self.logger.info(f"\n{self.stats}")


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python p1x_service.py <P11|P12|P13>")
        sys.exit(1)
    
    node_name = sys.argv[1]
    if node_name not in ['P11', 'P12', 'P13']:
        print("Node name must be P11, P12, or P13")
        sys.exit(1)
    
    node = P1xServiceNode(node_name)
    
    try:
        node.start()
    except KeyboardInterrupt:
        print(f"\nShutting down {node_name}...")
        node.stop()


if __name__ == '__main__':
    main()

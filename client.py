"""
Client node (K1, K2) - Sends requests and tracks responses
"""

import socket
import time
import threading
import logging
from typing import Dict, List
from common import Request, Response, send_message, receive_message, create_request_id
from config import HOST, PORTS, CLIENT_CONFIG, PRIORITIES


class Client:
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.port = PORTS[client_id]
        self.q1_address = (HOST, PORTS['Q1'])
        
        self.pending_requests: Dict[str, Request] = {}
        self.successful_requests = 0
        self.failed_requests = 0
        self.responses_received: Dict[str, List[Response]] = {}
        
        self.running = False
        self.server_socket = None
        
        self.logger = logging.getLogger(f"Client-{client_id}")
        
    def start(self):
        """Start the client"""
        self.running = True
        
        # Start server thread to receive responses
        server_thread = threading.Thread(target=self._run_server, daemon=True)
        server_thread.start()
        
        time.sleep(0.5)  # Give server time to start
        
        # Start sending requests
        self._send_requests()
        
    def _run_server(self):
        """Run server to receive responses from P2x nodes"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((HOST, self.port))
        self.server_socket.listen(5)
        self.logger.info(f"Client {self.client_id} listening on port {self.port}")
        
        while self.running:
            try:
                self.server_socket.settimeout(1.0)
                conn, addr = self.server_socket.accept()
                threading.Thread(target=self._handle_response, args=(conn,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.logger.error(f"Server error: {e}")
                break
                
    def _handle_response(self, conn: socket.socket):
        """Handle incoming response from P2x nodes"""
        try:
            msg = receive_message(conn)
            if msg:
                response = Response.from_json(msg)
                request_id = response.request_id
                
                if request_id not in self.responses_received:
                    self.responses_received[request_id] = []
                
                self.responses_received[request_id].append(response)
                self.logger.info(f"Received response for {request_id} from {response.processed_by[-1]}")
                
        except Exception as e:
            self.logger.error(f"Error handling response: {e}")
        finally:
            conn.close()
            
    def _send_requests(self):
        """Send requests to Q1"""
        request_types = ['z1', 'z2', 'z3']
        sequence = 0
        
        for i in range(CLIENT_CONFIG['num_requests']):
            if not self.running:
                break
                
            # Rotate through request types
            req_type = request_types[i % len(request_types)]
            request_id = create_request_id(self.client_id, sequence)
            sequence += 1
            
            request = Request(
                request_id=request_id,
                request_type=req_type,
                client_id=self.client_id,
                timestamp=time.time(),
                priority=PRIORITIES[req_type],
                hops=[]
            )
            
            self.pending_requests[request_id] = request
            
            if self._send_to_q1(request):
                self.logger.info(f"Sent {req_type} request {request_id}")
            else:
                self.logger.error(f"Failed to send request {request_id}")
                self.failed_requests += 1
                
            time.sleep(CLIENT_CONFIG['request_interval'])
        
        # Wait for responses
        self._wait_for_responses()
        
    def _send_to_q1(self, request: Request) -> bool:
        """Send request to Q1"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(self.q1_address)
            
            success = send_message(sock, request.to_json())
            sock.close()
            
            return success
        except Exception as e:
            self.logger.error(f"Error connecting to Q1: {e}")
            return False
            
    def _wait_for_responses(self):
        """Wait for all responses with timeout"""
        self.logger.info("Waiting for responses...")
        timeout = CLIENT_CONFIG['response_timeout']
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check if we've received all expected responses
            all_received = True
            for request_id in self.pending_requests:
                # We expect 3 responses (from P21, P22, P23)
                if request_id not in self.responses_received or \
                   len(self.responses_received[request_id]) < 3:
                    all_received = False
                    break
            
            if all_received:
                break
                
            time.sleep(0.1)
        
        # Calculate results
        self._calculate_results()
        
    def _calculate_results(self):
        """Calculate successful and failed requests"""
        for request_id, request in self.pending_requests.items():
            if request_id in self.responses_received:
                responses = self.responses_received[request_id]
                
                # Check if we got all 3 responses
                if len(responses) == 3:
                    # Check if all are successful
                    all_successful = all(r.success for r in responses)
                    if all_successful:
                        self.successful_requests += 1
                        self.logger.info(f"✓ Request {request_id} successful")
                    else:
                        self.failed_requests += 1
                        self.logger.warning(f"✗ Request {request_id} partially failed")
                else:
                    self.failed_requests += 1
                    self.logger.warning(f"✗ Request {request_id} incomplete ({len(responses)}/3 responses)")
            else:
                self.failed_requests += 1
                self.logger.warning(f"✗ Request {request_id} no responses")
        
        self.print_summary()
        
    def print_summary(self):
        """Print summary of results"""
        total = self.successful_requests + self.failed_requests
        success_rate = (self.successful_requests / total * 100) if total > 0 else 0
        
        print(f"\n{'='*50}")
        print(f"Client {self.client_id} Summary")
        print(f"{'='*50}")
        print(f"Total Requests Sent: {total}")
        print(f"Successful Requests: {self.successful_requests}")
        print(f"Failed Requests: {self.failed_requests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"{'='*50}\n")
        
    def stop(self):
        """Stop the client"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python client.py <K1|K2>")
        sys.exit(1)
    
    client_id = sys.argv[1]
    if client_id not in ['K1', 'K2']:
        print("Client ID must be K1 or K2")
        sys.exit(1)
    
    client = Client(client_id)
    
    try:
        client.start()
    except KeyboardInterrupt:
        print("\nShutting down client...")
        client.stop()


if __name__ == '__main__':
    main()

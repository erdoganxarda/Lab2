"""
D - High-Performance Query Distribution Device
Distributes requests to Q21, Q22, Q23 based on request type
"""

import socket
import threading
import logging
from common import Request, send_message, receive_message, Statistics
from config import HOST, PORTS


class DNode:
    def __init__(self):
        self.node_name = "D"
        self.port = PORTS['D']
        
        # Map request types to Q2x queues
        self.request_type_mapping = {
            'z1': 'Q21',
            'z2': 'Q22',
            'z3': 'Q23',
        }
        
        self.running = False
        self.server_socket = None
        self.stats = Statistics(self.node_name)
        
        self.logger = logging.getLogger(self.node_name)
        
    def start(self):
        """Start D node"""
        self.running = True
        self.logger.info(f"{self.node_name} starting on port {self.port}")
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((HOST, self.port))
        self.server_socket.listen(20)
        
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
        """Handle incoming request from P1x nodes"""
        try:
            msg = receive_message(conn)
            if not msg:
                return
            
            request = Request.from_json(msg)
            self.stats.add_request()
            
            request.add_hop(self.node_name)
            self.logger.info(f"Received {request.request_type} request {request.request_id}")
            
            # IMPORTANT: Broadcast to ALL Q2x nodes!
            # Client expects responses from all 3 P2x nodes
            all_queues = ['Q21', 'Q22', 'Q23']
            
            for target_queue in all_queues:
                if self._forward_to_queue(request, target_queue):
                    self.stats.forward_request()
                    self.logger.info(f"Forwarded {request.request_id} to {target_queue}")
                else:
                    self.logger.error(f"Failed to forward {request.request_id} to {target_queue}")
                
        except Exception as e:
            self.logger.error(f"Error handling request: {e}")
        finally:
            conn.close()
            
    def _forward_to_queue(self, request: Request, queue_name: str) -> bool:
        """Forward request to Q2x queue"""
        try:
            target_address = (HOST, PORTS[queue_name])
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(target_address)
            
            success = send_message(sock, request.to_json())
            sock.close()
            
            return success
        except Exception as e:
            self.logger.error(f"Error forwarding to {queue_name}: {e}")
            return False
            
    def stop(self):
        """Stop D node"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        
        self.logger.info(f"\n{self.stats}")


def main():
    d_node = DNode()
    
    try:
        d_node.start()
    except KeyboardInterrupt:
        print("\nShutting down D...")
        d_node.stop()


if __name__ == '__main__':
    main()

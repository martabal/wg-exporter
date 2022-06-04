import subprocess
from argparse import ArgumentParser
from http.server import BaseHTTPRequestHandler, HTTPServer

class wg_metrics_handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if(self.path == '/metrics'):
            result = subprocess.run(['wg', 'show', 'all', 'dump'], capture_output=True, text=True)
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            message = self.parse_wg_output(result.stdout)
            self.wfile.write(bytes(message, 'utf-8'))
    
    def parse_wg_output(self, wg_output):
        # Check the doc for the output format: https://manpages.debian.org/unstable/wireguard-tools/wg.8.en.html#show
        self.wg_interface = ''
        lines = wg_output.splitlines()
        parsed_result = self.parse_server_info(lines[0].split('\t'))
        for peer_info in lines[1:]: # will be empty if no peers
            parsed_result += self.parse_peer_info(peer_info.split('\t'))
        return parsed_result
    
    def parse_server_info(self, server_info):
        self.wg_interface = server_info[0]
        return f'wg_server_info{{pkey="{server_info[2]}", interface="{server_info[0]}"}} {server_info[3]}\n'
    
    def parse_peer_info(self, peer_info):
        peer_latest_handshake = f'wg_peer_latest_handshake{{pkey="{peer_info[1]}", interface="{peer_info[0]}"}} {peer_info[5]}\n'
        peer_latest_transfer_rx = f'wg_peer_transfer_rx{{pkey="{peer_info[1]}", interface="{peer_info[0]}"}} {peer_info[6]}\n'
        peer_latest_transfer_tx = f'wg_peer_transfer_tx{{pkey="{peer_info[1]}", interface="{peer_info[0]}"}} {peer_info[7]}\n'
        return peer_latest_handshake + peer_latest_transfer_rx + peer_latest_transfer_tx


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--bind', type=str, help='The interface to bind the server to. Defaults to localhost', default='')
    parser.add_argument('--port', type=int, help='The port to listen to', default=8400)
    args = parser.parse_args()
    with HTTPServer((args.bind, args.port), wg_metrics_handler) as server:
        server.serve_forever()

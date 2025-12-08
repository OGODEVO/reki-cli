from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import random

class MockHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/v1/chat/completions':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Print received data for debugging
            try:
                data = json.loads(post_data)
                print(f"Server received messages: {len(data.get('messages', []))}")
            except:
                print("Server received malformed JSON")

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # OpenAI Chat Completion Response Format
            action = random.choice(["BUY", "SELL", "HOLD"])
            response = {
                "id": "chatcmpl-mock",
                "object": "chat.completion",
                "created": 1677652288,
                "model": "reki-0.2",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"PREDICT: {action}\nREASON: Mock model reasoning."
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 50,
                    "completion_tokens": 10,
                    "total_tokens": 60
                }
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

def run(server_class=HTTPServer, handler_class=MockHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting mock model server on port {port}...')
    httpd.serve_forever()

if __name__ == "__main__":
    run()

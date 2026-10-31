import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 8000))
    s.listen(1)
    print("SUCCESS: Bound and listening on 127.0.0.1:8000")
    s.close()
except Exception as e:
    print(f"FAILED: {e}")


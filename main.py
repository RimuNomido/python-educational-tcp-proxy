import sys
import selectors
import socket

session = {'r': None, 'r2l': b'', 'l': None, 'l2r': b''}

LOCAL_HOST = '127.0.0.1'
LOCAL_PORT = 3232

sel = selectors.DefaultSelector()

def accept(sock, mask):
    remote_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_host = sys.argv[1]
    remote_port = int(sys.argv[2])
    remote_client.connect((remote_host, remote_port))
    remote_client.setblocking(False)
    session['r'] = remote_client
    sel.register(remote_client, selectors.EVENT_READ, read)

    conn, addr = sock.accept()
    conn.setblocking(False)
    print(f'Новое входящее соединение {addr[0]}:{addr[1]}')
    session['l'] = conn
    sel.register(conn, selectors.EVENT_READ, read)

def read(conn, mask):
    if conn == session['l']:
        data = conn.recv(1024)
        if data:
            session['l2r'] += data
            if session['l2r']:
                sel.modify(session['r'], selectors.EVENT_WRITE, write)
        else:
            close_both()
            return
    elif conn == session['r']:
        data = conn.recv(1024)
        if data:
            session['r2l'] += data
            if session['r2l']:
                sel.modify(session['l'], selectors.EVENT_WRITE, write)
        else:
            close_both()
            return
        
def write(conn, mask):
    try:
        if conn == session['r']:
            sent = conn.send(session['l2r'])
            if sent == 0:
                close_both()
                return
            hexdump(session['l2r'][:sent], 'local -> remote')
            session['l2r'] = session['l2r'][sent:]
            if not session['l2r']:
                sel.modify(session['r'], selectors.EVENT_READ, read)
            else:
                sel.modify(session['r'], selectors.EVENT_WRITE, write)
        elif conn == session['l']:
            sent = conn.send(session['r2l'])
            if sent == 0:
                close_both()
                return
            hexdump(session['r2l'][:sent], 'remote -> local')
            session['r2l'] = session['r2l'][sent:]
            if not session['r2l']:
                sel.modify(session['l'], selectors.EVENT_READ, read)
            else:
                sel.modify(session['l'], selectors.EVENT_WRITE, write)
    except Exception as e:
        print(f'Failed: {e}.')

def conn_close(conn):
    if not conn:
        return
    try:
        conn.close()
    except Exception:
        pass

def close_both():
    l = session.get('l')
    r = session.get('r')
    try:
        sel.unregister(l)
        sel.unregister(r)
    except Exception:
        pass
    conn_close(l)
    conn_close(r)
    print('Соединение разорвано')
    session['l'] = session['r'] = None
    session['l2r'] = session['r2l'] = b''

def hexdump(src: bytes, prefix, length=16, max_bytes=256):
    if src is None:
        return
    if max_bytes is not None:
        src = src[:max_bytes]

    print(prefix)       
    for i in range(0, len(src), length):
        chunk = src[i: i + length]
        hexa = ' '.join(f'{b:02x}' for b in chunk)
        printable = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print(f'{i:04x} {hexa:<{length*3}} {printable}')

def main(): 

    if len(sys.argv) != 3:
        print("Usage: python proxy.py <remote_host> <remote_port>")
        sys.exit(1)

    proxy_server = socket.socket()
    proxy_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    proxy_server.bind((LOCAL_HOST, LOCAL_PORT))
    proxy_server.setblocking(False)
    proxy_server.listen(5)    

    sel.register(proxy_server, selectors.EVENT_READ, accept)

    try:
        while True:
            events = sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)
    except KeyboardInterrupt:
        print('Завершение работы...')
        close_both()
        sys.exit(1)
    except Exception as e:
        print(f'Failed: {e}')

if __name__ == '__main__':
    main()
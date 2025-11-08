README — Chicken Gun (Python Windows prototype)

Files included in this single-file prototype (below):

- chicken_gun.py      -> main game + optional simple network (server/client)

- requirements.txt    -> python packages to install



Overview

This is a compact prototype of a "Chicken Gun"-style multiplayer demo written in Python using pygame.

It supports:

- Local single-player mode (default)

- Simple remote multiplayer (server/client) using TCP with JSON lines

- Building a Windows .exe via PyInstaller (instructions below)



Quick start (Windows)

1) Install Python 3.10+ from python.org and add to PATH.

2) Create a virtual environment and activate it:

python -m venv venv

venv\Scripts\activate

3) Install requirements:

pip install -r requirements.txt

4) Run locally:

python chicken_gun.py

5) To run a server (host matches IPv4 of machine):

python chicken_gun.py --server --bind 0.0.0.0 --port 5000

6) To run as client connecting to server:

python chicken_gun.py --client --host 192.168.1.5 --port 5000



Build Windows .exe with PyInstaller

1) Install PyInstaller in the venv: pip install pyinstaller

2) Build a single executable:

pyinstaller --onefile --noconsole chicken_gun.py

3) The EXE will be in the dist folder (dist\chicken_gun.exe).

4) Test the exe locally.



Publish to GitHub (basic)

1) git init

2) git add .

3) git commit -m "Add chicken gun python prototype"

4) Create a new repo on GitHub web and follow instructions to push.

5) Add a Releases section and upload the built dist\chicken_gun.exe if you want to share an exe.



Notes & caveats

- This is a small demo, not a production-ready multiplayer server.

- For reliable multiplayer consider using libraries like ENet, WebSockets, or a proper authoritative server.

- Opening ports on Windows requires firewall rules and router port forwarding for internet play.

- Respect copyright: do not distribute proprietary assets. Use your own art/audio.



----------

requirements.txt content (included below):

pygame==2.1.3



----------

Below: the single-file python script chicken_gun.py.

""" Simple Chicken Gun prototype

Controls: WASD to move, Mouse to aim, LMB to shoot

Modes:

single-player: spawn AI chickens

--server: run minimal TCP relay server

--client --host IP: connect to server and exchange positions



This is intentionally compact and commented for learning. """

import pygame import sys import math import random import json import socket import threading import argparse import time from dataclasses import dataclass, field from typing import Dict, Tuple

Game constants

WIDTH, HEIGHT = 800, 600 PLAYER_SPEED = 220.0  # px/sec BULLET_SPEED = 600.0 CHICKEN_SPEED = 100.0 FPS = 60

Networking constants

NET_TICK = 0.05  # 20 Hz

@dataclass class Entity: id: str x: float y: float ang: float = 0.0 vx: float = 0.0 vy: float = 0.0 hp: int = 100

class SimpleServer: """Very small TCP server that accepts clients and relays JSON state messages. Protocol: clients send JSON lines like {"type":"state","id":...,"x":...,"y":...} Server keeps a dict of last-known states and forwards other clients' states. Not secure. For LAN testing only. """ def init(self, bind='0.0.0.0', port=5000): self.bind = bind self.port = port self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) self.sock.bind((bind, port)) self.sock.listen(8) self.clients = []  # list of (conn, addr) self.lock = threading.Lock() self.running = True print(f"[Server] Listening on {bind}:{port}")

def start(self):
    threading.Thread(target=self._accept_loop, daemon=True).start()
    threading.Thread(target=self._broadcast_loop, daemon=True).start()

def _accept_loop(self):
    while self.running:
        try:
            conn, addr = self.sock.accept()
            conn.settimeout(1.0)
            with self.lock:
                self.clients.append((conn, addr))
            print(f"[Server] Client connected {addr}")
            threading.Thread(target=self._client_reader, args=(conn,addr), daemon=True).start()
        except Exception as e:
            continue

def _client_reader(self, conn, addr):
    buf = b""
    while self.running:
        try:
            data = conn.recv(4096)
            if not data:
                break
            buf += data
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                # naive validation
                try:
                    msg = json.loads(line.decode('utf-8'))
                    # attach last_received to client socket object
                    conn.last_msg = msg
                except Exception:
                    pass
        except socket.timeout:
            continue
        except Exception:
            break
    print(f"[Server] Client disconnected {addr}")
    with self.lock:
        self.clients = [(c,a) for (c,a) in self.clients if c is not conn]
    try:
        conn.close()
    except:
        pass

def _broadcast_loop(self):
    while self.running:
        time.sleep(NET_TICK)
        with self.lock:
            # collect all client messages
            messages = []
            for (c,a) in list(self.clients):
                if hasattr(c, 'last_msg'):
                    messages.append(c.last_msg)
            if not messages:
                continue
            data = (json.dumps({"type":"batch","messages":messages}) + "\n").encode('utf-8')
            for (c,a) in list(self.clients):
                try:
                    c.sendall(data)
                except Exception:
                    # drop bad client
                    try:
                        c.close()
                    except:
                        pass
                    self.clients = [(cc,aa) for (cc,aa) in self.clients if cc is not c]

def stop(self):
    self.running = False
    try:
        self.sock.close()
    except:
        pass
    with self.lock:
        for c,a in self.clients:
            try: c.close()
            except: pass
        self.clients = []

class SimpleClient: """Client connects to server, sends local state and receives batches of other states. Client runs a receiver thread that updates others dict with Entity-like dicts. """ def init(self, host='127.0.0.1', port=5000, id='p1'): self.host = host self.port = port self.id = id self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) self.sock.settimeout(3.0) self.others = {}  # id -> state self.running = True try: self.sock.connect((host, port)) self.sock.settimeout(0.5) threading.Thread(target=self._recv_loop, daemon=True).start() print(f"[Client] Connected to {host}:{port}") except Exception as e: print(f"[Client] Connect failed: {e}") raise

def send_state(self, x, y, ang):
    msg = {"type":"state","id":self.id,"x":x,"y":y,"ang":ang}
    try:
        self.sock.sendall((json.dumps(msg) + "\n").encode('utf-8'))
    except Exception:
        pass

def _recv_loop(self):
    buf = b""
    while self.running:
        try:
            data = self.sock.recv(4096)
            if not data:
                break
            buf += data
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                try:
                    msg = json.loads(line.decode('utf-8'))
                    if msg.get('type') == 'batch':
                        for m in msg.get('messages', []):
                            if m.get('id') == self.id:
                                continue
                            self.others[m['id']] = m
                except Exception:
                    pass
        except socket.timeout:
            continue
        except Exception:
            break
    self.running = False
    try:
        self.sock.close()
    except:
        pass
    print("[Client] Receiver thread ended")

def stop(self):
    self.running = False
    try:
        self.sock.close()
    except:
        pass

---------- Game code (pygame)

class Player: def init(self, id, x, y, color=(255,200,0)): self.id = id self.x = x self.y = y self.ang = 0.0 self.color = color self.size = 22 self.hp = 100

def draw(self, surf):
    rect = pygame.Rect(0,0,self.size,self.size)
    rect.center = (int(self.x), int(self.y))
    pygame.draw.rect(surf, self.color, rect)
    # draw barrel
    bx = self.x + math.cos(self.ang) * (self.size)
    by = self.y + math.sin(self.ang) * (self.size)
    pygame.draw.line(surf, (0,0,0), (self.x,self.y),(bx,by),3)

class Bullet: def init(self, x, y, ang): self.x = x self.y = y self.ang = ang self.alive = True

def update(self, dt):
    self.x += math.cos(self.ang) * BULLET_SPEED * dt
    self.y += math.sin(self.ang) * BULLET_SPEED * dt
    if self.x < -50 or self.x > WIDTH+50 or self.y < -50 or self.y > HEIGHT+50:
        self.alive = False

def draw(self, surf):
    pygame.draw.circle(surf, (20,20,20), (int(self.x), int(self.y)), 4)

class Chicken: def init(self, x, y): self.x = x self.y = y self.dir = random.random()*math.tau if hasattr(math,'tau') else random.random()2math.pi self.size = 20 self.hp = 50

def update(self, dt):
    self.x += math.cos(self.dir) * CHICKEN_SPEED * dt
    self.y += math.sin(self.dir) * CHICKEN_SPEED * dt
    # bounce
    if self.x < 0 or self.x > WIDTH:
        self.dir = math.pi - self.dir
    if self.y < 0 or self.y > HEIGHT:
        self.dir = -self.dir

def draw(self, surf):
    pygame.draw.rect(surf, (200,100,50), pygame.Rect(self.x-10,self.y-10,20,20))

def run_game(args): pygame.init() screen = pygame.display.set_mode((WIDTH, HEIGHT)) clock = pygame.time.Clock() myid = f"p-{random.randint(1000,9999)}"

# Networking
server = None
client = None
if args.server:
    server = SimpleServer(bind=args.bind, port=args.port)
    server.start()
if args.client:
    try:
        client = SimpleClient(host=args.host, port=args.port, id=myid)
    except Exception:
        print("Failed to connect to server. Starting in local mode.")
        client = None

player = Player(myid, WIDTH/2, HEIGHT/2)
bullets = []
chickens = [Chicken(random.randint(50, WIDTH-50), random.randint(50, HEIGHT-50)) for _ in range(6)]
others = {}  # id -> Player-like

shoot_cool = 0.0

running = True
while running:
    dt = clock.tick(FPS)/1000.0
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False
    keys = pygame.key.get_pressed()
    mx, my = pygame.mouse.get_pos()
    # movement
    vx = vy = 0.0
    if keys[pygame.K_w]: vy -= 1
    if keys[pygame.K_s]: vy += 1
    if keys[pygame.K_a]: vx -= 1
    if keys[pygame.K_d]: vx += 1
    norm = math.hypot(vx, vy)
    if norm > 0:
        vx /= norm; vy /= norm
        player.x += vx * PLAYER_SPEED * dt
        player.y += vy * PLAYER_SPEED * dt
    # aim
    player.ang = math.atan2(my - player.y, mx - player.x)
    # shooting
    shoot_cool -= dt
    if pygame.mouse.get_pressed()[0] and shoot_cool <= 0:
        bx = player.x + math.cos(player.ang) * 20
        by = player.y + math.sin(player.ang) * 20
        bullets.append(Bullet(bx, by, player.ang))
        shoot_cool = 0.15
    # update bullets
    for b in bullets:
        b.update(dt)
    bullets = [b for b in bullets if b.alive]
    # update chickens
    for c in chickens:
        c.update(dt)
    # bullet-chicken collisions
    for b in bullets:
        for c in chickens:
            if math.hypot(b.x-c.x,b.y-c.y) < 18:
                c.hp -= 50
                b.alive = False
    chickens = [c for c in chickens if c.hp > 0]
    # spawn chickens slowly
    if random.random() < 0.01:
        chickens.append(Chicken(random.randint(20, WIDTH-20), random.randint(20, HEIGHT-20)))

    # Networking: send state and read others (local client object holds others)
    if client:
        client.send_state(player.x, player.y, player.ang)
        # copy client.others to local others
        others = {}
        for oid, st in client.others.items():
            try:
                others[oid] = Player(oid, st['x'], st['y'], color=(100,180,255))
            except Exception:
                pass

    # draw
    screen.fill((135,206,235))
    for c in chickens:
        c.draw(screen)
    player.draw(screen)
    for o in others.values():
        o.draw(screen)
    for b in bullets:
        b.draw(screen)

    # HUD
    font = pygame.font.SysFont(None, 24)
    txt = font.render(f"Mode: {'Server' if server else ('Client' if client else 'Local')}  ID:{player.id}", True, (0,0,0))
    screen.blit(txt, (8,8))
    pygame.display.flip()

# cleanup
if client:
    client.stop()
if server:
    server.stop()
pygame.quit()

if name == 'main': parser = argparse.ArgumentParser() parser.add_argument('--server', action='store_true', help='Run relay server') parser.add_argument('--bind', default='0.0.0.0') parser.add_argument('--port', type=int, default=5000) parser.add_argument('--client', action='store_true', help='Run as client connecting to server') parser.add_argument('--host', default='127.0.0.1') args = parser.parse_args() # requirements: pygame run_game(args)

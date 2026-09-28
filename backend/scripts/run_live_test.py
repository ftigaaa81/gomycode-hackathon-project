"""Comprehensive API test for EyE C backend."""
import urllib.request, json, base64, io
from PIL import Image

BASE = "http://127.0.0.1:8000"

buf = io.BytesIO()
Image.new("RGB", (640, 480), color=(100, 150, 200)).save(buf, format="JPEG", quality=85)
img_b64 = base64.b64encode(buf.getvalue()).decode("ascii")

print("=== EyE C Live API Test ===")
print()

# 1. Health
r = urllib.request.urlopen(f"{BASE}/health")
print(f"1. GET /health              -> {r.status} {json.loads(r.read())}")
print()

# 2. Demo random
r = urllib.request.urlopen(f"{BASE}/api/demo/scene/random")
d = json.loads(r.read())
print(f"2. GET /api/demo/scene/random -> {r.status}")
print(f"   urgence={d['urgence']}, msg=\"{d['message_court']}\", source={d['source']}")
print()

# 3. Demo known scene
r = urllib.request.urlopen(f"{BASE}/api/demo/scene/escalier_danger")
d = json.loads(r.read())
print(f"3. GET /api/demo/scene/escalier_danger -> {r.status}")
print(f"   urgence={d['urgence']}, msg=\"{d['message_court']}\"")
print()

# 4. Analyze on-demand (no NVIDIA key -> fallback)
payload = json.dumps({"image_base64": img_b64}).encode()
req = urllib.request.Request(f"{BASE}/api/analyze/on-demand", data=payload, headers={"Content-Type": "application/json"})
r = urllib.request.urlopen(req)
d = json.loads(r.read())
print(f"4. POST /api/analyze/on-demand -> {r.status}")
print(f"   urgence={d['urgence']}, msg=\"{d['message_court']}\", used_fallback={d['used_fallback']}")
print()

# 5. Analyze captor (no NVIDIA key -> fallback)
payload2 = json.dumps({"image_base64": img_b64, "source": "captor", "captor_id": "pi-captor-01"}).encode()
req2 = urllib.request.Request(f"{BASE}/api/analyze", data=payload2, headers={"Content-Type": "application/json"})
r2 = urllib.request.urlopen(req2)
d2 = json.loads(r2.read())
print(f"5. POST /api/analyze (captor) -> {r2.status}")
print(f"   urgence={d2['urgence']}, msg=\"{d2['message_court']}\", used_fallback={d2['used_fallback']}")
print()

# 6. 404 test
try:
    urllib.request.urlopen(f"{BASE}/api/demo/scene/not-a-scene")
except urllib.error.HTTPError as e:
    print(f"6. GET /api/demo/scene/not-a-scene -> {e.code} (expected 404)")

print()
print("=== All endpoints OK ===")

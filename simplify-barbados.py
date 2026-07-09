import re
import math

# Read the SVG file
with open('barbados-source.svg', 'r') as f:
    content = f.read()

# Extract the path d attribute for the island outline (clipPath)
match = re.search(r'<path[^>]*id="path3796"[^>]*d="([^"]*)"', content)
if not match:
    print("Path not found!")
    exit()

d = match.group(1)

# Parse relative path: starts with 'm' then series of relative coordinates
# Remove newlines and extra spaces
d = ' '.join(d.split())

# Parse the path - it starts with 'm x,y' then all subsequent are relative lineto
parts = d.strip().split()

points = []
i = 0
cx, cy = 0, 0

while i < len(parts):
    token = parts[i]
    if token == 'm':
        i += 1
        coords = parts[i].split(',')
        cx += float(coords[0])
        cy += float(coords[1])
        points.append((cx, cy))
        i += 1
        # Subsequent coordinates after m are implicit relative lineto
        while i < len(parts) and not parts[i].isalpha() and parts[i] not in ('m', 'M', 'l', 'L', 'c', 'C', 'z', 'Z'):
            coords = parts[i].split(',')
            if len(coords) == 2:
                cx += float(coords[0])
                cy += float(coords[1])
                points.append((cx, cy))
            i += 1
    elif token in ('z', 'Z'):
        i += 1
    else:
        # Try parsing as coordinate pair
        coords = token.split(',')
        if len(coords) == 2:
            try:
                cx += float(coords[0])
                cy += float(coords[1])
                points.append((cx, cy))
            except ValueError:
                pass
        i += 1

print(f"Total points: {len(points)}")

# Find bounding box
min_x = min(p[0] for p in points)
max_x = max(p[0] for p in points)
min_y = min(p[1] for p in points)
max_y = max(p[1] for p in points)
print(f"Bounding box: x=[{min_x:.0f}, {max_x:.0f}], y=[{min_y:.0f}, {max_y:.0f}]")
print(f"Size: {max_x - min_x:.0f} x {max_y - min_y:.0f}")

# Normalize to fit in a 200x300 viewBox with some padding
target_w, target_h = 180, 280
pad = 10
src_w = max_x - min_x
src_h = max_y - min_y
scale = min(target_w / src_w, target_h / src_h)

normalized = []
for x, y in points:
    nx = (x - min_x) * scale + pad
    ny = (y - min_y) * scale + pad
    normalized.append((nx, ny))

# Simplify using Ramer-Douglas-Peucker algorithm
def rdp(points, epsilon):
    if len(points) <= 2:
        return points

    # Find the point farthest from the line between first and last
    start, end = points[0], points[-1]
    max_dist = 0
    max_idx = 0

    for i in range(1, len(points) - 1):
        # Distance from point to line
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        line_len = math.sqrt(dx*dx + dy*dy)
        if line_len == 0:
            dist = math.sqrt((points[i][0]-start[0])**2 + (points[i][1]-start[1])**2)
        else:
            dist = abs(dy * points[i][0] - dx * points[i][1] + end[0]*start[1] - end[1]*start[0]) / line_len
        if dist > max_dist:
            max_dist = dist
            max_idx = i

    if max_dist > epsilon:
        left = rdp(points[:max_idx+1], epsilon)
        right = rdp(points[max_idx:], epsilon)
        return left[:-1] + right
    else:
        return [start, end]

# Try different epsilon values
for eps in [1.0, 2.0, 3.0, 5.0]:
    simplified = rdp(normalized, eps)
    print(f"Epsilon {eps}: {len(simplified)} points")

# Use epsilon=2 for smoother curves
simplified = rdp(normalized, 2.0)
print(f"\nUsing {len(simplified)} points")

# Generate SVG path
path_parts = []
for i, (x, y) in enumerate(simplified):
    if i == 0:
        path_parts.append(f"M {x:.1f},{y:.1f}")
    else:
        path_parts.append(f"L {x:.1f},{y:.1f}")
path_parts.append("Z")

path_d = " ".join(path_parts)

# Write test HTML
vb_w = target_w + 2*pad
vb_h = target_h + 2*pad
html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Barbados - Simplified from Wikimedia</title></head>
<body style="background:#e8e8e8; display:flex; justify-content:center; align-items:center; min-height:100vh; margin:0; gap:40px; flex-wrap:wrap;">

<!-- Simplified outline -->
<svg viewBox="0 0 {vb_w} {vb_h}" style="width:350px; border:1px solid #ccc;">
  <rect width="{vb_w}" height="{vb_h}" fill="white"/>
  <path d="{path_d}" fill="#0a9396" stroke="#064e3b" stroke-width="1.5"/>
</svg>

<!-- Dark version -->
<svg viewBox="0 0 {vb_w} {vb_h}" style="width:200px; border:1px solid #ccc;">
  <rect width="{vb_w}" height="{vb_h}" fill="#0b132b"/>
  <path d="{path_d}" fill="#0a9396" stroke="none"/>
</svg>

<!-- Reference -->
<div style="text-align:center; font-family:sans-serif; color:#666; font-size:14px;">
  <img src="Images/Barbados outline 1.jpg" style="width:220px; border:1px solid #ccc;">
  <p>Reference</p>
</div>

</body></html>
'''

with open('barbados-test.html', 'w') as f:
    f.write(html)

# Also write the path data to a separate file for easy copy
with open('barbados-path.txt', 'w') as f:
    f.write(f"viewBox: 0 0 {vb_w} {vb_h}\n\n")
    f.write(path_d)

print(f"\nWrote barbados-test.html and barbados-path.txt")
print(f"viewBox: 0 0 {vb_w} {vb_h}")

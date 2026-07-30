"""
Test harness for a Web Mercator projection pair.

Point the import below at your own module, then run:

    python test_projection.py

Four independent checks, because no single one catches everything:

  1. ANCHORS      absolute known values. Catches a wrong `n` (the 2^z bug),
                  swapped return order, and sign errors.
  2. ROUND-TRIP   f(g(x)) == x. Catches formula typos. Does NOT catch a
                  consistently-wrong scale -- see the demo at the bottom.
  3. MONOTONIC    north -> smaller y, east -> larger x. Catches flipped axes.
  4. ALIGNMENT    tile corners land on exact multiples of 256.
"""

import math

# ============================================================================
# EDIT THIS: import your own functions instead of the reference ones below.
#
#   from projection import world_to_latlon, latlon_to_world
#
# Your signatures must be:
#   world_to_latlon(px, py, z) -> (lat, lon)
#   latlon_to_world(lat, lon, z) -> (px, py)
#
# If yours return (lon, lat) or take tiles instead of pixels, write a small
# adapter here rather than editing the tests.
# ============================================================================

TILE = 256




from main import world_to_latlon, latlon_to_world
# ============================================================================
# test machinery
# ============================================================================

PASS = 0
FAIL = 0


def check(label, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  PASS  {label}")
    else:
        FAIL += 1
        print(f"  FAIL  {label}   {detail}")


def close(a, b, tol):
    return abs(a - b) <= tol


# ============================================================================
# 1. ANCHORS -- absolute values you can verify by hand
# ============================================================================


def test_anchors(f_fwd, f_inv):
    print("\n[1] ANCHORS (absolute ground truth)")

    # At any zoom, the world is (256 * 2**z) pixels square.
    for z in (0, 10, 16):
        size = TILE * 2**z

        # Null Island sits at the exact center of the Mercator square.
        px, py = f_inv(0.0, 0.0, z)
        check(
            f"z{z}: (0,0) -> world center {size/2:,.0f}",
            close(px, size / 2, 1e-6) and close(py, size / 2, 1e-6),
            f"got {px:,.3f}, {py:,.3f}",
        )

        # The antimeridian is the left edge.
        px, py = f_inv(0.0, -180.0, z)
        check(f"z{z}: lon -180 -> x = 0", close(px, 0.0, 1e-6), f"got x={px}")

        # The right edge.
        px, py = f_inv(0.0, 180.0, z)
        check(
            f"z{z}: lon +180 -> x = {size:,}",
            close(px, size, 1e-6),
            f"got x={px:,.3f}",
        )

        # Mercator's top clip latitude -> y = 0.
        px, py = f_inv(85.0511287798066, 0.0, z)
        check(
            f"z{z}: lat 85.0511 -> y = 0",
            close(py, 0.0, 1e-3),
            f"got y={py}",
        )

    # A concrete Tucson tile, hand-verifiable against any slippy-map tool.
    px, py = f_inv(32.2319, -110.9501, 16)
    tx, ty = int(px // TILE), int(py // TILE)
    check(
        "UA campus @ z16 -> tile 12570/26563",
        (tx, ty) == (12570, 26563),
        f"got {tx}/{ty}",
    )

    # Return order: lat must come back first and be ~32, not ~-110.
    lat, lon = f_fwd(3217958.6, 6800355.9, 16)
    check(
        "return order is (lat, lon) not (lon, lat)",
        30 < lat < 34 and -113 < lon < -109,
        f"got lat={lat:.4f}, lon={lon:.4f}",
    )


# ============================================================================
# 2. ROUND-TRIP
# ============================================================================

PLACES = [
    ("UA campus", 32.2319, -110.9501),
    ("Tucson City Hall", 32.2217, -110.9747),
    ("Saguaro NP East", 32.1800, -110.7300),
    ("Marana", 32.4367, -111.2255),
    ("equator/prime mer.", 0.0, 0.0),
    ("high north", 70.0, 25.0),
    ("southern hemi", -33.8688, 151.2093),
]


def test_round_trip(f_fwd, f_inv):
    print("\n[2] ROUND-TRIP (lat/lon -> world -> lat/lon)")
    worst = 0.0
    for name, lat, lon in PLACES:
        px, py = f_inv(lat, lon, 16)
        lat2, lon2 = f_fwd(px, py, 16)
        dlat = abs(lat - lat2) * 111_320
        dlon = abs(lon - lon2) * 111_320 * math.cos(math.radians(lat))
        err = math.hypot(dlat, dlon)
        worst = max(worst, err)
        check(f"{name:<20} error {err:.3e} m", err < 1e-3, f"{err} m")
    print(f"        worst case: {worst:.3e} m")


# ============================================================================
# 3. MONOTONICITY -- catches flipped or swapped axes
# ============================================================================


def test_monotonic(f_fwd, f_inv):
    print("\n[3] MONOTONICITY")

    south = f_inv(32.10, -110.95, 16)
    north = f_inv(32.30, -110.95, 16)
    check(
        "further north -> smaller y",
        north[1] < south[1],
        f"north y={north[1]:,.1f} south y={south[1]:,.1f}",
    )

    west = f_inv(32.20, -111.10, 16)
    east = f_inv(32.20, -110.70, 16)
    check(
        "further east -> larger x",
        east[0] > west[0],
        f"west x={west[0]:,.1f} east x={east[0]:,.1f}",
    )

    # Latitude must not affect x, longitude must not affect y.
    a = f_inv(32.10, -110.95, 16)
    b = f_inv(32.30, -110.95, 16)
    check("same lon -> same x", close(a[0], b[0], 1e-6), f"{a[0]} vs {b[0]}")

    a = f_inv(32.20, -111.10, 16)
    b = f_inv(32.20, -110.70, 16)
    check("same lat -> same y", close(a[1], b[1], 1e-6), f"{a[1]} vs {b[1]}")


# ============================================================================
# 4. SCALE / TILE ALIGNMENT
# ============================================================================


def test_scale(f_fwd, f_inv):
    print("\n[4] SCALE & TILE ALIGNMENT")

    # Zooming in one level must exactly double world pixel coordinates.
    a = f_inv(32.2319, -110.9501, 15)
    b = f_inv(32.2319, -110.9501, 16)
    check(
        "z15 -> z16 doubles coordinates",
        close(a[0] * 2, b[0], 1e-6) and close(a[1] * 2, b[1], 1e-6),
        f"{a[0]*2:,.3f} vs {b[0]:,.3f}",
    )

    # Ground resolution at Tucson's latitude should be ~2.02 m/px at z16.
    p1 = f_inv(32.2319, -110.9501, 16)
    p2 = f_inv(32.2319, -110.9401, 16)  # 0.01 deg east
    dx_px = p2[0] - p1[0]
    meters = 0.01 * 111_320 * math.cos(math.radians(32.2319))
    res = meters / dx_px
    check(
        f"resolution ~2.02 m/px  (got {res:.3f})",
        close(res, 2.021, 0.01),
        f"{res}",
    )


# ============================================================================
# demo: why round-trip alone is not enough
# ============================================================================


def broken_fwd(px, py, z):
    n = 2 ^ z  # XOR, not exponent
    tx, ty = px / TILE, py / TILE
    lon = tx / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1.0 - 2.0 * ty / n))))
    return lat, lon


def broken_inv(lat, lon, z):
    n = 2 ^ z  # XOR, not exponent
    tx = (lon + 180.0) / 360.0 * n
    ty = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    return tx * TILE, ty * TILE


def demo_round_trip_is_insufficient():
    print("\n" + "=" * 68)
    print("DEMO: round-trip passes even with the 2^z bug")
    print("=" * 68)
    lat, lon = 32.2319, -110.9501
    px, py = broken_inv(lat, lon, 16)
    lat2, lon2 = broken_fwd(px, py, 16)
    err = math.hypot((lat - lat2) * 111_320, (lon - lon2) * 111_320)
    print(f"  broken round-trip error : {err:.3e} m   <-- looks perfect!")
    print(f"  but world pixel is      : {px:,.1f}, {py:,.1f}")
    print(f"  correct value is        : 3,217,958.6, 6,800,355.9")
    print("  Only the ANCHOR tests catch this.")


if __name__ == "__main__":
    test_anchors(world_to_latlon, latlon_to_world)
    test_round_trip(world_to_latlon, latlon_to_world)
    test_monotonic(world_to_latlon, latlon_to_world)
    test_scale(world_to_latlon, latlon_to_world)

    print("\n" + "-" * 68)
    print(f"  {PASS} passed, {FAIL} failed")
    print("-" * 68)

    demo_round_trip_is_insufficient()
"""Headless multiscale acoustic guitar generator for Fusion.

All dimensions in mm (converted to Fusion's internal cm via MM).
Layout: nut centre at x=0, strings along +X, bass side +Y, top surface z=0.
"""
import adsk.core, adsk.fusion, math

MM = 0.1

# ---- Scale / strings ----
LB, LT = 647.7, 635.0          # bass / treble scale (25.5" / 25")
PERP = 9                       # perpendicular fret
NUT_SP, BR_SP = 35.0, 52.5     # outer string spacing at nut / bridge (Strandberg 10.5 mm bridge)
NS = 6
GAUGES = [1.19, 0.97, 0.71, 0.56, 0.38, 0.28]   # D'Addario silk & steel 11-47 (.047-.011), bass -> treble, mm
COMP_BASS, COMP_TREBLE = 3.4, 1.6                # acoustic saddle compensation (~1/8" slant from ~1/16")

# ---- Fretboard / action ----
FB_T, FB_R = 6.5, 508.0        # fretboard thickness, 20" radius
FRET_H, FRET_W = 1.3, 2.4

# ---- EndurNeck-style neck (published figures: ~41.9 mm nut, ~52.6 mm at the end of the
# board, ~21.6 / 22.9 mm deep at frets 1 / 12 incl. fretboard; V shaved to a ~15 mm flat) ----
NUT_MARGIN, BRIDGE_MARGIN = 3.45, 1.75     # board edge outside the outer strings (at nut / projected to bridge)
NECK_FLAT, NECK_SHOULDER, NECK_FACET_R = 15.0, 2.0, 4.0
# x, depth under the board at the bass / treble edge of the flat (bass fuller near the nut)
NECK_STATIONS = [(-75, 15.6, 14.4), (0, 15.6, 14.4), (150, 15.8, 15.0), (320, 16.5, 16.2), (450, 16.9, 16.8)]
# ---- Setup (standard acoustic values) ----
# Neck angle: a straightedge on the frets lands on the top of the bridge.
# Action at the 12th fret (bass -> treble) and string clearance over the frets at the nut.
BRIDGE_H = 9.5
ACTION_12 = (2.2, 1.7)          # silk & steel: low tension, a touch higher than bronze
NUT_CLEAR = (0.5, 0.35)
FRET_TOP = FB_T + FRET_H           # fret crowns at the board centre, neck frame
BRIDGE_FRONT, BRIDGE_BACK = -9.0, 30.0   # along x from the bridge line; the back carries the headless tuners
BRIDGE_HALF, BRIDGE_CORNER_R = 40.0, 7.0
SADDLE_HALF, SADDLE_W = 30.0, 2.4

# ---- Body ----
WALL = 3.0                     # top, back and side thickness
DEPTH = 100.0                  # interior depth
KERF_W, KERF_H = 5.0, 12.0
Z_RIM = -(WALL + DEPTH)        # bottom of rim / top of back
POCKET_D = 18.0
# Side sound port in the bass-side wall of the upper horn, facing the player: centre near this
# outline point, axes along the wall and vertical, cut only through the outer wall.
SIDE_PORT_AT, SIDE_PORT_Z, SIDE_PORT_AXES = (400.0, 131.0), -53.0, (36.0, 21.0)
EDGE_R = 3.5                              # top edge roundover all round: > WALL for the shell, < the 4 mm horn tip
BLOCK_BACK = 500.0
TRANSVERSE_BRACE_X = 512.0
BACK_BRACES_X = (525, 595, 648)   # last one clear of the tail block in the tuning notch

# Right-handed: geometry below is written bass-side +Y; P() mirrors it so that, seen from
# the front with the neck pointing right, the bass side is on top.
HAND = -1

# Heel sculpt: an ellipsoid carved out of the back around the neck joint so the body
# falls away from the neck instead of standing as a flat wall.
HEEL_SCULPT = False                        # off: back runs flat up to the neck joint
HEEL_CENTER = (410.0, -170.0)              # x, z
HEEL_AXES = (110.0, 100.0, 135.0)          # along neck, across, vertical
HEEL_SEAM_R, HEEL_EDGE_R, BACK_EDGE_R = 25.0, 6.0, 3.5   # back edge < the ~4 mm bass horn tip

# Body outline: exact copy of the three splines in Sketch1 of the reference document (the
# cleaned-up redraw), scaled 12.6 mm per sketch unit (from the photo's 52.5 mm bridge string
# spread), aligned to the string centre line, with the bridge ~22 mm further back than the
# photo's so the treble side keeps a usable neck pocket. Geometry coords in mm, bass side +Y.
# Order: neck joint -> bass horn tip; bass horn -> bass edge -> butt; butt -> leg rest ->
# treble horn -> neck joint. The neck joint is wherever this outline crosses the neck.
SKETCH_SPLINES = [
    dict(degree=5,
         knots=[0, 0, 0, 0, 0, 0, 0.04, 0.08, 0.12, 0.16, 0.2, 0.24, 0.28, 0.32, 0.36, 0.4, 0.44, 0.48, 0.52, 0.56, 0.6, 0.64, 0.68, 0.72, 0.76, 0.8, 0.84, 0.88, 0.92, 0.96, 1, 1, 1, 1, 1, 1],
         points=[(417.5260, 12.6000), (417.1382, 14.8170), (416.3425, 19.1949), (415.0881, 25.5933), (413.2940, 33.7868), (410.8421, 43.4605), (408.1656, 52.5593), (405.2357, 61.0770), (402.0065, 69.0093), (398.4115, 76.3562), (394.3586, 83.1243), (389.7281, 89.3294), (384.4054, 94.9946), (378.3101, 100.1500), (371.4287, 104.8313), (363.8441, 109.0798), (355.7727, 112.9419), (347.5867, 116.4686), (339.7380, 119.7114), (332.6970, 122.7193), (326.8814, 125.5343), (322.5975, 128.1893), (319.9546, 130.7030), (318.8522, 133.0796), (319.0997, 135.3162), (320.5159, 137.4082), (322.5118, 138.9654), (324.4771, 140.0680), (325.9951, 140.7742), (326.8060, 141.1200)]),
    dict(degree=5,
         knots=[0, 0, 0, 0, 0, 0, 0.02222222222, 0.04444444444, 0.06666666667, 0.08888888889, 0.1111111111, 0.1333333333, 0.1555555556, 0.1777777778, 0.2, 0.2222222222, 0.2444444444, 0.2666666667, 0.2888888889, 0.3111111111, 0.3333333333, 0.3555555556, 0.3777777778, 0.4, 0.4222222222, 0.4444444444, 0.4666666667, 0.4888888889, 0.5111111111, 0.5333333333, 0.5555555556, 0.5777777778, 0.6, 0.6222222222, 0.6444444444, 0.6666666667, 0.6888888889, 0.7111111111, 0.7333333333, 0.7555555556, 0.7777777778, 0.8, 0.8222222222, 0.8444444444, 0.8666666667, 0.8888888889, 0.9111111111, 0.9333333333, 0.9555555556, 0.9777777778, 1, 1, 1, 1, 1, 1],
         points=[(326.8060, 141.1200), (329.0504, 141.7497), (333.5398, 142.8609), (340.2753, 144.0832), (349.2589, 144.8231), (360.4924, 144.2816), (371.7271, 142.3318), (382.9576, 139.0937), (394.1746, 134.7762), (405.3653, 129.6856), (416.5191, 124.1840), (427.6325, 118.6580), (438.7137, 113.4841), (449.7887, 108.9933), (460.9035, 105.4425), (472.1110, 103.0179), (483.4602, 101.8334), (494.9855, 101.9311), (506.6930, 103.2787), (518.5571, 105.7755), (530.5313, 109.2728), (542.5566, 113.5920), (554.5704, 118.5411), (566.5155, 123.9360), (578.3480, 129.6078), (590.0409, 135.3727), (601.5892, 141.0101), (613.0142, 146.2368), (624.3677, 150.6835), (635.7382, 153.8661), (647.2183, 155.2832), (658.8701, 154.5221), (670.6922, 151.3597), (682.5836, 145.8723), (694.3143, 138.5222), (705.5689, 129.9858), (715.9826, 121.0075), (725.1812, 112.2361), (732.8171, 104.0868), (738.6133, 96.5460), (742.3670, 89.2372), (743.9327, 81.6139), (743.2115, 73.1062), (740.1388, 63.3010), (734.6762, 51.9307), (726.8059, 38.8373), (718.5798, 26.9240), (711.3257, 17.1699), (706.0080, 10.3033), (703.2288, 6.7791)]),
    dict(degree=5,
         knots=[0, 0, 0, 0, 0, 0, 0.01666666667, 0.03333333333, 0.05, 0.06666666667, 0.08333333333, 0.1, 0.1166666667, 0.1333333333, 0.15, 0.1666666667, 0.1833333333, 0.2, 0.2166666667, 0.2333333333, 0.25, 0.2666666667, 0.2833333333, 0.3, 0.3166666667, 0.3333333333, 0.35, 0.3666666667, 0.3833333333, 0.4, 0.4166666667, 0.4333333333, 0.45, 0.4666666667, 0.4833333333, 0.5, 0.5166666667, 0.5333333333, 0.55, 0.5666666667, 0.5833333333, 0.6, 0.6166666667, 0.6333333333, 0.65, 0.6666666667, 0.6833333333, 0.7, 0.7166666667, 0.7333333333, 0.75, 0.7666666667, 0.7833333333, 0.8, 0.8166666667, 0.8333333333, 0.85, 0.8666666667, 0.8833333333, 0.9, 0.9166666667, 0.9333333333, 0.95, 0.9666666667, 0.9833333333, 1, 1, 1, 1, 1, 1],
         points=[(703.2288, 6.7791), (701.6673, 4.4216), (698.6000, -0.2267), (694.1658, -6.9991), (688.5872, -15.6287), (682.1703, -25.7625), (676.3085, -35.2880), (670.9979, -44.2950), (666.2317, -52.9367), (661.9978, -61.4398), (658.2796, -70.1345), (655.0473, -79.3923), (652.2456, -89.5192), (649.7824, -100.6648), (647.5165, -112.7202), (645.2477, -125.2313), (642.6998, -137.2737), (639.5669, -147.6656), (635.5680, -155.2260), (630.5021, -159.0302), (624.2959, -158.6374), (617.0723, -154.4043), (609.1086, -147.3361), (600.7538, -138.7694), (592.3577, -130.1023), (584.1992, -122.5236), (576.4051, -116.6984), (568.9054, -112.6084), (561.5076, -109.8546), (553.9502, -107.8911), (545.9619, -106.2602), (537.3247, -104.8879), (527.9100, -104.1137), (517.6856, -104.4348), (506.7301, -106.3285), (495.2448, -110.0412), (483.5666, -115.3946), (472.1818, -121.5768), (461.6536, -127.4285), (452.5502, -131.7223), (445.3706, -133.4657), (440.4762, -132.1442), (438.0059, -128.1138), (437.8493, -122.5104), (439.7106, -116.5247), (443.1523, -110.6695), (447.6435, -104.6539), (452.6020, -97.8833), (457.4384, -89.7646), (461.6001, -80.1212), (464.6129, -69.4743), (466.1084, -58.7209), (465.8520, -48.8813), (463.7733, -40.8113), (459.9909, -34.9500), (454.8524, -30.9989), (448.8487, -28.1385), (442.5097, -25.3311), (436.3044, -21.5953), (430.5428, -16.2848), (425.4105, -9.0129), (421.8813, -1.4742), (419.5723, 5.1758), (418.1831, 10.0515), (417.5260, 12.6000)]),
]

# Refined outline (proposal): your v12 curves with two stretches redrawn: the treble cutaway
# under the neck shallower (~10 mm less 'chin') into a shorter, blunter ~11 mm horn tip, and
# the tail as one even
# hollow (same 16 mm depth). Fit points for a single closed spline, bass side +Y.
USE_REFINED_OUTLINE = True
# Thigh draft: where the waist scoop rests on the left thigh, the side wall leans so the soundboard
# edge is inset and the back edge outset; resting on the thigh then draws the body toward the
# player. Full angle over +/-FULL mm of outline around the contact, easing to zero over TAPER mm.
THIGH_DRAFT_DEG = 5.0
THIGH_DRAFT_AT = (532.0, -105.0)
THIGH_DRAFT_FULL, THIGH_DRAFT_TAPER = 40.0, 50.0
OUTLINE_REFINED = [
    (492.0, 102.1), (501.2, 102.8), (509.1, 104.0), (517.1, 105.7), (525.2, 107.8), (533.2, 110.4), (541.4, 113.3), (549.5, 116.5),
    (557.5, 120.0), (565.6, 123.6), (573.6, 127.4), (581.5, 131.2), (589.4, 135.1), (597.2, 138.9), (605.0, 142.5), (612.7, 145.9),
    (620.4, 149.0), (628.1, 151.5), (637.1, 153.7), (646.1, 154.7), (655.3, 154.4), (663.2, 153.1), (671.2, 150.6), (679.1, 147.2),
    (687.1, 142.8), (694.9, 137.7), (702.5, 132.1), (709.7, 126.3), (716.5, 120.3), (722.8, 114.4), (729.2, 107.8), (734.5, 101.6),
    (739.2, 94.8), (742.4, 87.3), (743.4, 79.2), (742.3, 71.3), (735.5, 62.4), (729.2, 54.5), (723.1, 46.4), (717.1, 38.3),
    (711.4, 29.9), (705.8, 21.5), (700.4, 12.9), (695.2, 4.2), (690.1, -4.5), (685.3, -13.4), (680.7, -22.5), (676.3, -31.6),
    (672.0, -40.8), (668.0, -50.1), (664.2, -59.4), (660.6, -68.9), (657.2, -78.4), (654.0, -88.0), (651.0, -97.7), (648.3, -107.5),
    (645.7, -117.3), (643.4, -127.1), (641.2, -137.0), (639.4, -147.0), (635.1, -154.6), (627.9, -158.3), (619.9, -155.7), (613.0, -150.6),
    (607.0, -145.0), (600.7, -138.7), (594.5, -132.4), (588.3, -126.5), (581.1, -120.4), (574.2, -115.7), (566.3, -111.8), (558.5, -109.2),
    (550.3, -107.2), (541.6, -105.6), (533.5, -104.7), (524.7, -104.4), (515.4, -105.1), (507.2, -106.6), (498.7, -109.2), (484.0, -114.0),
    (474.0, -118.0), (464.5, -122.0), (451.0, -127.0), (445.2, -124.7), (441.7, -119.8), (441.2, -113.7), (443.6, -108.9), (446.0, -102.5),
    (449.5, -93.0), (452.8, -83.0), (455.2, -72.5), (456.3, -62.0), (456.0, -50.0), (454.0, -40.0), (450.5, -31.5), (444.1, -25.9),
    (436.7, -21.4), (430.7, -15.8), (425.4, -8.1), (421.4, 0.4), (418.5, 8.9), (416.8, 16.7), (415.2, 24.7), (413.4, 33.0),
    (411.4, 41.0), (409.1, 49.1), (406.7, 56.7), (403.8, 64.5), (400.4, 72.1), (396.6, 79.2), (392.0, 86.2), (386.6, 92.4),
    (380.5, 98.2), (373.9, 103.0), (366.6, 107.4), (359.3, 111.2), (351.7, 114.7), (344.2, 117.9), (336.8, 121.0), (329.3, 124.5),
    (322.4, 128.6), (319.5, 135.5), (325.6, 140.6), (334.4, 142.9), (343.2, 144.1), (352.1, 144.5), (360.9, 143.9), (369.8, 142.4),
    (378.6, 140.2), (387.4, 137.2), (395.0, 134.2), (402.6, 130.9), (410.1, 127.3), (417.6, 123.6), (425.1, 120.0), (432.6, 116.4),
    (440.1, 113.1), (447.6, 110.0), (456.3, 107.0), (465.1, 104.7), (474.0, 103.1), (482.9, 102.2)]



# ======================= geometry =======================
def f(n):
    return 1 - 2 ** (-n / 12.0)


def make_strings():
    res = []
    for i in range(NS):
        t = i / (NS - 1)
        L = LB + (LT - LB) * t
        ny = NUT_SP / 2 - NUT_SP * t
        by = BR_SP / 2 - BR_SP * t
        dx = math.sqrt(L * L - (by - ny) ** 2)
        nx = -f(PERP) * dx
        res.append(((nx, ny), (nx + dx, by)))
    sh = -(res[0][0][0] + res[-1][0][0]) / 2
    return [((a[0] + sh, a[1]), (b[0] + sh, b[1])) for a, b in res]


S = make_strings()


def on_string(i, n):
    (nx, ny), (bx, by) = S[i]
    k = f(n)
    return (nx + k * (bx - nx), ny + k * (by - ny))


def line_int(p1, p2, p3, p4):
    x1, y1 = p1; x2, y2 = p2; x3, y3 = p3; x4, y4 = p4
    d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    a = x1 * y2 - y1 * x2; b = x3 * y4 - y3 * x4
    return ((a * (x3 - x4) - (x1 - x2) * b) / d, (a * (y3 - y4) - (y1 - y2) * b) / d)


EDGE_B = ((S[0][0][0], S[0][0][1] + NUT_MARGIN), (S[0][1][0], S[0][1][1] + BRIDGE_MARGIN))
EDGE_T = ((S[-1][0][0], S[-1][0][1] - NUT_MARGIN), (S[-1][1][0], S[-1][1][1] - BRIDGE_MARGIN))


def edge_y(edge, x):
    (x1, y1), (x2, y2) = edge
    return y1 + (x - x1) * (y2 - y1) / (x2 - x1)


def shift(line, dx):
    return ((line[0][0] + dx, line[0][1]), (line[1][0] + dx, line[1][1]))


def fret_line(n):
    return (on_string(0, n), on_string(NS - 1, n))


def across(line, inset=0.0):
    pb = line_int(line[0], line[1], *EDGE_B)
    pt = line_int(line[0], line[1], *EDGE_T)
    if inset:
        vx, vy = pt[0] - pb[0], pt[1] - pb[1]
        l = math.hypot(vx, vy); ux, uy = vx / l, vy / l
        pb = (pb[0] + ux * inset, pb[1] + uy * inset)
        pt = (pt[0] - ux * inset, pt[1] - uy * inset)
    return pb, pt


def band(l1, l2, inset=0.0):
    a, b = across(l1, inset)
    c, d = across(l2, inset)
    return [a, c, d, b]


def x_on(line, dx, y):
    (x1, y1), (x2, y2) = line
    return x1 + (y - y1) * (x2 - x1) / (y2 - y1) + dx


def strip(line, dx0, dx1, ymax):
    return [(x_on(line, dx0, ymax), ymax), (x_on(line, dx1, ymax), ymax),
            (x_on(line, dx1, -ymax), -ymax), (x_on(line, dx0, -ymax), -ymax)]


def joint_curve(design):
    """The built outline where it crosses the neck: bass edge point -> treble edge point.

    Sampled from the body outline spline, so the neck end matches the body exactly.
    """
    pts = outline_samples(design, 6000)
    inside = lambda p: p[0] < 480 and edge_y(EDGE_T, p[0]) <= p[1] <= edge_y(EDGE_B, p[0])
    n = len(pts)
    start = next(i for i in range(n) if inside(pts[i]) and not inside(pts[i - 1]))
    run = [pts[start - 1]]
    i = start
    while inside(pts[i % n]):
        run.append(pts[i % n]); i += 1
    run.append(pts[i % n])
    if run[0][1] < run[-1][1]:
        run.reverse()                                   # bass (+y) first

    def on_edge(a, b, edge):
        # point on segment a-b where it meets the neck edge line
        fa, fb = a[1] - edge_y(edge, a[0]), b[1] - edge_y(edge, b[0])
        t = fa / (fa - fb)
        return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
    jb = on_edge(run[0], run[1], EDGE_B)
    jt = on_edge(run[-2], run[-1], EDGE_T)
    mid = run[1:-1]
    step = max(1, len(mid) // 12)
    return [jb] + mid[step // 2::step] + [jt]


def outline_samples(design, n):
    """Dense points (geometry coords) round the built body outline, in loop order."""
    sk = comp(design, 'Body Master').sketches.itemByName('Body Outline')
    fitted = sk.sketchCurves.sketchFittedSplines
    curves = fitted if fitted.count else sk.sketchCurves.sketchFixedSplines
    total = sum(curves.item(i).length for i in range(curves.count))
    out = []
    for i in range(curves.count):
        c = curves.item(i)
        ev = c.geometry.evaluator
        ok, p0, p1 = ev.getParameterExtents()
        m = max(2, int(n * c.length / total))
        out += [geo(ev.getPointAtParameter(p0 + (p1 - p0) * k / m)[1]) for k in range(m)]
    return out


def bar(cx, cy, ang_deg, length, width):
    a = math.radians(ang_deg)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    hl, hw = length / 2, width / 2
    return [(cx - ux * hl - nx * hw, cy - uy * hl - ny * hw), (cx + ux * hl - nx * hw, cy + uy * hl - ny * hw),
            (cx + ux * hl + nx * hw, cy + uy * hl + ny * hw), (cx - ux * hl + nx * hw, cy - uy * hl + ny * hw)]


NUT_LINE = (S[0][0], S[-1][0])
END_LINE = shift(NUT_LINE, -40)
POCKET_END = fret_line(24)
FB_END = shift(fret_line(24), 6)
BRIDGE_LINE = (S[0][1], S[-1][1])
SADDLE_LINE = ((S[0][1][0] + COMP_BASS, S[0][1][1]), (S[-1][1][0] + COMP_TREBLE, S[-1][1][1]))
NECK_PIVOT_X = x_on(fret_line(24), 0, 0)       # neck rotates about the pocket end (fretboard extension stays on the top)
NECK_ANGLE = math.atan2(BRIDGE_H - FRET_TOP, x_on(BRIDGE_LINE, 0, 0) - NECK_PIVOT_X)


def rot(x, y, z):
    """Neck frame -> body frame: tilt back (nut end down) by NECK_ANGLE about the pivot."""
    dx = x - NECK_PIVOT_X
    ca, sa = math.cos(NECK_ANGLE), math.sin(NECK_ANGLE)
    return (NECK_PIVOT_X + dx * ca - z * sa, y, z * ca + dx * sa)


def fret_top_z(y):
    """Fret crown height across the radius (neck frame)."""
    r = FB_R + FRET_H
    return FB_T - FB_R + math.sqrt(r * r - y * y)


def string_geometry():
    """Per string: (nut contact, saddle contact) in body frame, from action and clearance targets."""
    out = []
    for i in range(NS):
        t = i / (NS - 1)
        a12 = ACTION_12[0] + (ACTION_12[1] - ACTION_12[0]) * t
        clr = NUT_CLEAR[0] + (NUT_CLEAR[1] - NUT_CLEAR[0]) * t
        (nx, ny), (bx, by) = S[i]
        n = rot(nx, ny, fret_top_z(ny) + clr)
        x12, y12 = on_string(i, 12)
        a = rot(x12, y12, fret_top_z(y12) + a12)
        sx = x_on(SADDLE_LINE, 0, by)
        sz = n[2] + (a[2] - n[2]) * (sx - n[0]) / (a[0] - n[0])
        out.append((n, (sx, by, sz)))
    return out
X_POCKET_END = x_on(POCKET_END, 0, 0)


def joint_line(design):
    """Straight chord between the neck-joint ends (bass, treble), from the built outline."""
    jc = joint_curve(design)
    return (jc[0], jc[-1])


def neck_block_poly(design):
    # Front sits well ahead of the (curved) joint; clipping to the cavity gives the real face.
    (bx, by), (tx, ty) = joint_line(design)
    xj_ = lambda y: bx + (by - y) * (tx - bx) / (by - ty)
    return [(xj_(50) - 15, 50), (xj_(-50) - 15, -50), (BLOCK_BACK, -50), (BLOCK_BACK, 50)]


def tail_block_poly(design):
    """Block along the butt, centred where the outline crosses the centre line at the rear."""
    pts = outline_samples(design, 6000)
    n = len(pts)
    i = max((k for k in range(n) if pts[k][0] > 600 and (pts[k][1] >= 0) != (pts[(k + 1) % n][1] >= 0)),
            key=lambda k: pts[k][0])
    a, b = pts[i], pts[(i + 1) % n]
    t = a[1] / (a[1] - b[1])
    cx, cy = a[0] + t * (b[0] - a[0]), 0.0
    p, q = pts[(i - 20) % n], pts[(i + 20) % n]
    l = math.hypot(q[0] - p[0], q[1] - p[1])
    ux, uy = (q[0] - p[0]) / l, (q[1] - p[1]) / l
    if uy > 0:
        ux, uy = -ux, -uy                  # run toward the treble side
    nx, ny = uy, -ux                       # inward normal (toward the neck)
    if nx > 0:
        nx, ny = -nx, -ny
    return [(cx + ux * s + nx * t, cy + uy * s + ny * t) for s, t in ((25, -8), (-25, -8), (-25, 14), (25, 14))]


# ======================= Fusion helpers =======================
NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
CUT = adsk.fusion.FeatureOperations.CutFeatureOperation
JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
INTERSECT = adsk.fusion.FeatureOperations.IntersectFeatureOperation


def P(x, y, z=0.0):
    return adsk.core.Point3D.create(x * MM, HAND * y * MM, z * MM)


def VI(v):
    return adsk.core.ValueInput.createByReal(v)


def coll(items):
    c = adsk.core.ObjectCollection.create()
    for i in items:
        c.add(i)
    return c


def setup(design):
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits


def new_comp(design, name):
    occ = design.rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occ.component.name = name
    return occ.component


def comp(design, name):
    for c in design.allComponents:
        if c.name == name:
            return c
    raise ValueError('no component ' + name)


def bodies_of(c):
    return [c.bRepBodies.item(i) for i in range(c.bRepBodies.count)]


def poly_sketch(c, polys, name):
    sk = c.sketches.add(c.xYConstructionPlane)
    sk.name = name
    lines = sk.sketchCurves.sketchLines
    for pts in polys:
        first = lines.addByTwoPoints(P(*pts[0]), P(*pts[1]))
        prev = first
        for p in pts[2:]:
            prev = lines.addByTwoPoints(prev.endSketchPoint, P(*p))
        lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)
    return sk


def all_profiles(sk):
    return coll([sk.profiles.item(i) for i in range(sk.profiles.count)])


def extrude(c, profs, z0, h, op=NEW, bodies=None):
    ext = c.features.extrudeFeatures
    inp = ext.createInput(profs, op)
    inp.startExtent = adsk.fusion.OffsetStartDefinition.create(VI(z0 * MM))
    inp.setDistanceExtent(False, VI(h * MM))
    if bodies is not None:
        inp.participantBodies = bodies
    return ext.add(inp)


def poly_extrude(c, polys, name, z0, h, op=NEW, bodies=None):
    sk = poly_sketch(c, polys, name)
    return extrude(c, all_profiles(sk), z0, h, op, bodies)


def combine(c, target, tool, op, keep):
    ci = c.features.combineFeatures.createInput(target, coll([tool]))
    ci.operation = op
    ci.isKeepToolBodies = keep
    return c.features.combineFeatures.add(ci)


def yz_sketch(c, x, name):
    pi = c.constructionPlanes.createInput()
    pi.setByOffset(c.yZConstructionPlane, VI(x * MM))
    pl = c.constructionPlanes.add(pi)
    pl.isLightBulbOn = False
    sk = c.sketches.add(pl)
    sk.name = name
    return sk


def radius_cylinder(c, r, name):
    sk = yz_sketch(c, 250, name)
    sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P(250, 0, FB_T - FB_R)), r * MM)
    ext = c.features.extrudeFeatures
    inp = ext.createInput(sk.profiles.item(0), NEW)
    inp.setSymmetricExtent(VI(700 * MM), True)
    return ext.add(inp).bodies.item(0)


def drawn_splines(sk, z=0.0):
    """Exact copies of the hand-drawn splines (SKETCH_SPLINES) in sketch sk, at height z."""
    out = []
    for s in SKETCH_SPLINES:
        nurbs = adsk.core.NurbsCurve3D.createNonRational([P(x, y, z) for x, y in s['points']], s['degree'],
                                                         s['knots'], False)
        out.append(sk.sketchCurves.sketchFixedSplines.addByNurbsCurve(nurbs))
    return out


def reference_overlay(design):
    """Your drawn outline as a visible sketch just above the top, for comparison."""
    c = new_comp(design, 'Reference Outline (as drawn)')
    sk = c.sketches.add(c.xYConstructionPlane)
    sk.name = 'As Drawn'
    drawn_splines(sk, 1.0)
    return sk


def outline_sketch(c, offsets, name='Body Outline'):
    """Sketch the body outline (refined proposal, or exact copies of the drawn splines);
    returns (sketch, first curve)."""
    sk = c.sketches.add(c.xYConstructionPlane)
    sk.name = name
    if USE_REFINED_OUTLINE:
        sp = sk.sketchCurves.sketchFittedSplines.add(coll([P(*p) for p in body_outline()]))
        sp.isClosed = True
        curves = [sp]
    else:
        curves = drawn_splines(sk)
    for o in offsets:
        sk.offset(coll(curves), P(600, 0), o * MM)
    return sk, curves[0]


def inner_profile(sk):
    for i in range(sk.profiles.count):
        p = sk.profiles.item(i)
        if p.profileLoops.count == 1:
            return p


def ring_profile(sk, sp, touches_outline):
    for i in range(sk.profiles.count):
        p = sk.profiles.item(i)
        if p.profileLoops.count != 2:
            continue
        toks = set()
        for li in range(p.profileLoops.count):
            loop = p.profileLoops.item(li)
            for ci in range(loop.profileCurves.count):
                toks.add(loop.profileCurves.item(ci).sketchEntity.entityToken)
        if (sp.entityToken in toks) == touches_outline:
            return p


def paste(c, body):
    return c.features.copyPasteBodies.add(body).bodies.item(0)


def clip_to_void(c, void, bodies):
    """Keep only the parts of `bodies` that lie inside the body cavity."""
    tool = paste(c, void)
    for b in bodies:
        try:
            combine(c, b, tool, INTERSECT, True)
        except RuntimeError:
            # Empty intersection: the piece lies wholly outside the cavity (e.g. inside the heel carve).
            c.features.removeFeatures.add(b)
    c.features.removeFeatures.add(tool)


def cut_with_copies(c, bodies, tools):
    """Cut every body in component c with a copy of each tool. Re-reads the component's bodies for
    each tool, because a cut can split a body into new pieces that the next tool must also see."""
    for t in tools:
        tool = paste(c, t)
        for b in [x for x in bodies_of(c) if x != tool]:
            combine(c, b, tool, CUT, True)
        c.features.removeFeatures.add(tool)


def z_plane(c, z, name):
    pi = c.constructionPlanes.createInput()
    pi.setByOffset(c.xYConstructionPlane, VI(z * MM))
    pl = c.constructionPlanes.add(pi)
    pl.name = name
    pl.isLightBulbOn = False
    return pl


def top_face(body):
    best = None
    for i in range(body.faces.count):
        fc = body.faces.item(i)
        if best is None or fc.centroid.z > best.centroid.z:
            best = fc
    return best


def fillet_long_top_edges(c, body, r, min_len):
    fc = top_face(body)
    edges = coll([fc.edges.item(i) for i in range(fc.edges.count) if fc.edges.item(i).length > min_len * MM])
    fi = c.features.filletFeatures.createInput()
    fi.edgeSetInputs.addConstantRadiusEdgeSet(edges, VI(r * MM), True)
    return c.features.filletFeatures.add(fi)


def lib_item(app, attr, name):
    for lib in app.materialLibraries:
        items = getattr(lib, attr)
        for i in range(items.count):
            if items.item(i).name == name:
                return items.item(i)
    raise ValueError('not found: ' + name)


# ======================= builders =======================
def geo(pt):
    """Fusion point (cm) -> geometry coordinates (mm, bass side +Y)."""
    return (pt.x / MM, HAND * pt.y / MM)


def face_nz(face, pt):
    ok, n = face.evaluator.getNormalAtPoint(pt)
    return n.z


def vertical_edges(body):
    out = []
    for i in range(body.edges.count):
        e = body.edges.item(i)
        a, b = e.startVertex.geometry, e.endVertex.geometry
        if abs(a.x - b.x) < 1e-6 and abs(a.y - b.y) < 1e-6:
            out.append(e)
    return out


def fillet_edges(c, edges, r):
    if not edges:
        return
    fi = c.features.filletFeatures.createInput()
    fi.edgeSetInputs.addConstantRadiusEdgeSet(coll(edges), VI(r * MM), True)
    return c.features.filletFeatures.add(fi)


def sculpt_heel(c, env):
    """Carve an ellipsoid out of the back around the neck joint (if HEEL_SCULPT), blend its
    seams, and round the back perimeter."""
    def edges_where(test):
        out = []
        for i in range(env.edges.count):
            e = env.edges.item(i)
            if e.faces.count != 2:
                continue
            pt = e.pointOnEdge
            nz = sorted(face_nz(e.faces.item(k), pt) for k in range(2))
            if test(nz, pt):
                out.append(e)
        return out

    is_bottom = lambda n: n < -0.99
    is_wall = lambda n: abs(n) < 0.15          # side walls, including the drafted thigh rest
    if HEEL_SCULPT:
        cx, cz = HEEL_CENTER
        ax, ay, az = HEEL_AXES
        R = 100.0
        sk = c.sketches.add(c.xZConstructionPlane); sk.name = 'Heel Sculpt'
        m = lambda x, z: sk.modelToSketchSpace(P(x, 0, z))
        axis = sk.sketchCurves.sketchLines.addByTwoPoints(m(cx - R, cz), m(cx + R, cz))
        sk.sketchCurves.sketchArcs.addByThreePoints(axis.startSketchPoint, m(cx, cz + R), axis.endSketchPoint)
        centre = sk.sketchPoints.add(m(cx, cz))
        rv = c.features.revolveFeatures
        ri = rv.createInput(sk.profiles.item(0), axis, NEW)
        ri.setAngleExtent(False, VI(2 * math.pi))
        ball = rv.add(ri).bodies.item(0)
        si = c.features.scaleFeatures.createInput(coll([ball]), centre, VI(1.0))
        si.setToNonUniform(VI(ax / R), VI(ay / R), VI(az / R))
        c.features.scaleFeatures.add(si)
        combine(c, env, ball, CUT, False)
        # scoop meets the back, then scoop meets the side walls
        fillet_edges(c, edges_where(lambda nz, pt: is_bottom(nz[0]) and not is_bottom(nz[1]) and not is_wall(nz[1])),
                     HEEL_SEAM_R)
        fillet_edges(c, edges_where(lambda nz, pt: pt.z < -10 * MM and pt.x < 560 * MM and
                                    any(is_wall(n) for n in nz) and not all(is_wall(n) for n in nz) and
                                    not any(is_bottom(n) for n in nz)), HEEL_EDGE_R)
    # back perimeter
    fillet_edges(c, edges_where(lambda nz, pt: is_bottom(nz[0]) and is_wall(nz[1])), BACK_EDGE_R)



def drafted_outlines():
    """(top, back) fit points: OUTLINE_REFINED moved along its normal by -/+ half the draft offset."""
    pts = body_outline()
    n = len(pts)
    half = math.tan(math.radians(THIGH_DRAFT_DEG)) * (DEPTH + 2 * WALL) / 2
    # arc length of each point from the draft centre
    k0 = min(range(n), key=lambda i: math.hypot(pts[i][0] - THIGH_DRAFT_AT[0], pts[i][1] - THIGH_DRAFT_AT[1]))
    fwd = [0.0] * n
    for k in range(1, n):
        i, j = (k0 + k - 1) % n, (k0 + k) % n
        fwd[j] = fwd[i] + math.hypot(pts[j][0] - pts[i][0], pts[j][1] - pts[i][1])
    total = fwd[(k0 - 1) % n] + math.hypot(pts[k0][0] - pts[k0 - 1][0], pts[k0][1] - pts[k0 - 1][1])
    s = [min(f, total - f) for f in fwd]          # distance along the outline from the draft centre
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    top, back = [], []
    for i, (x, y) in enumerate(pts):
        a, b = pts[i - 1], pts[(i + 1) % n]
        l = math.hypot(b[0] - a[0], b[1] - a[1])
        tx, ty = (b[0] - a[0]) / l, (b[1] - a[1]) / l
        nx, ny = (-ty, tx) if area > 0 else (ty, -tx)          # inward normal
        d = abs(s[i])
        if d <= THIGH_DRAFT_FULL:
            w = 1.0
        elif d <= THIGH_DRAFT_FULL + THIGH_DRAFT_TAPER:
            w = 0.5 * (1 + math.cos(math.pi * (d - THIGH_DRAFT_FULL) / THIGH_DRAFT_TAPER))
        else:
            w = 0.0
        top.append((x + nx * half * w, y + ny * half * w))
        back.append((x - nx * half * w, y - ny * half * w))
    return top, back


def lofted_envelope(c):
    """Body envelope as a loft from the (drafted) soundboard outline down to the back outline."""
    top, back = drafted_outlines()
    profs = []
    for z, pts, nm in ((0.0, top, 'Top Outline'), (Z_RIM - WALL, back, 'Back Outline')):
        pl = c.xYConstructionPlane if z == 0 else z_plane(c, z, nm + ' Plane')
        sk = c.sketches.add(pl); sk.name = nm
        sp = sk.sketchCurves.sketchFittedSplines.add(coll([sk.modelToSketchSpace(P(x, y, z)) for x, y in pts]))
        sp.isClosed = True
        profs.append(sk.profiles.item(0))
    li = c.features.loftFeatures.createInput(NEW)
    for p in profs:
        li.loftSections.add(p)
    li.isSolid = True
    return c.features.loftFeatures.add(li).bodies.item(0)

# Wedge body: the player-facing (bass) side is BACK_TAPER mm shallower than the treble side that
# rests on the leg. The soundboard stays flat; the back tilts across the width.
BACK_TAPER = 10.0
_Y_TREBLE = min(y for x, y in OUTLINE_REFINED)
_Y_BASS = max(y for x, y in OUTLINE_REFINED)


def back_z(y, dz=0.0):
    """Height (mm) of the outer back surface at geometry y; dz raises it (dz = WALL: inner surface)."""
    f = (y - _Y_TREBLE) / (_Y_BASS - _Y_TREBLE)
    return Z_RIM - WALL + BACK_TAPER * f + dz


def back_plane(c, dz, name):
    ref = c.sketches.add(c.xYConstructionPlane)
    ref.name = name + ' Points'
    pts = [(0.0, _Y_TREBLE), (900.0, _Y_TREBLE), (0.0, _Y_BASS)]
    rp = [ref.sketchPoints.add(ref.modelToSketchSpace(P(x, y, back_z(y, dz)))) for x, y in pts]
    ref.isVisible = False
    pi = c.constructionPlanes.createInput()
    pi.setByThreePoints(*rp)
    pl = c.constructionPlanes.add(pi)
    pl.name = name
    pl.isLightBulbOn = False
    return pl


def trim_at_back(c, bodies, dz, keep_above, name):
    """Split bodies on the tilted back plane (raised by dz) and remove the unwanted side."""
    pl = back_plane(c, dz, name)
    for b in bodies:
        fe = c.features.splitBodyFeatures.add(c.features.splitBodyFeatures.createInput(b, pl, True))
        pieces = [fe.bodies.item(i) for i in range(fe.bodies.count)]
        unwanted = []
        for piece in pieces:
            cm = piece.physicalProperties.centerOfMass
            if (cm.z / MM > back_z(HAND * cm.y / MM, dz)) != keep_above:
                unwanted.append(piece)
        for piece in unwanted:
            c.features.removeFeatures.add(piece)



# ---- bracing for D'Addario silk & steel 11-47 (light, low tension) ----
X_CROSS, X_LEG_ANGLE = (575.0, 0.0), 50.0          # crossing ~57 mm ahead of the bridge; legs +/-50 deg
X_W, X_H, X_END_H = 6.0, 11.0, 4.0                 # scalloped: tall at the crossing, low toward the rim
TONE_BAR_STARTS = [(614.0, -52.0)]   # one bar: the treble lower bout is small on this outline
TONE_DIR_DEG = -20.0                                # run toward the lower treble rim
TONE_W, TONE_H, TONE_END_H = 5.0, 7.0, 3.0
UPPER_BAR_X, UPPER_W, UPPER_H, UPPER_END_H = 512.0, 6.0, 8.0, 5.0
PLATE_T = 2.5
BACK_BRACE_W, BACK_BRACE_H = 6.0, 8.0              # light, so the back stays live against the chest
RIM_INSET = 6.0                                    # braces stop this far inside the rim (into the linings)


def _inside(pt, poly):
    x, y = pt
    inside = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def ray_to_rim(design, start, direction):
    """Distance from start along direction to just inside the rim (geometry coords, mm)."""
    poly = outline_samples(design, 1500)
    l = math.hypot(*direction)
    dx, dy = direction[0] / l, direction[1] / l
    t = 0.0
    while _inside((start[0] + dx * t, start[1] + dy * t), poly) and t < 1000:
        t += 1.0
    return max(t - RIM_INSET, 0.0)


def scalloped_brace(c, p0, p1, width, h_peak, h_end, peak_at, name, flat=0.3, join_to=None):
    """Brace from p0 to p1 (plan, mm): flat top glued under the soundboard, underside scalloped from
    h_peak (around peak_at of its length, over a `flat` fraction) down to h_end at both ends."""
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    ux, uy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
    ref = c.sketches.add(c.xYConstructionPlane)
    ref.name = name + ' Plane Points'
    rp = [ref.sketchPoints.add(ref.modelToSketchSpace(P(x, y, z)))
          for x, y, z in ((p0[0], p0[1], -WALL), (p1[0], p1[1], -WALL), (p0[0], p0[1], -WALL - 10))]
    ref.isVisible = False
    pi = c.constructionPlanes.createInput()
    pi.setByThreePoints(*rp)
    pl = c.constructionPlanes.add(pi)
    pl.isLightBulbOn = False
    sk = c.sketches.add(pl)
    sk.name = name
    def h(s):
        lo, hi = peak_at - flat / 2, peak_at + flat / 2
        if lo <= s <= hi:
            return h_peak
        t = (lo - s) / lo if s < lo else (s - hi) / (1 - hi)
        return h_end + (h_peak - h_end) * 0.5 * (1 + math.cos(math.pi * min(max(t, 0.0), 1.0)))
    n = 24
    bottom = [(p0[0] + ux * L * k / n, p0[1] + uy * L * k / n, -WALL - h(k / n)) for k in range(n + 1)]
    pts = [(p0[0], p0[1], -WALL), (p1[0], p1[1], -WALL)] + bottom[::-1]
    m = [sk.modelToSketchSpace(P(*p)) for p in pts]
    lines = sk.sketchCurves.sketchLines
    first = prev = lines.addByTwoPoints(m[0], m[1])
    for q in m[2:]:
        prev = lines.addByTwoPoints(prev.endSketchPoint, q)
    lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)
    ext = c.features.extrudeFeatures
    inp = ext.createInput(sk.profiles.item(0), JOIN if join_to else NEW)
    inp.setSymmetricExtent(VI(width * MM), True)
    if join_to:
        inp.participantBodies = [join_to]
    body = ext.add(inp).bodies.item(0)
    if not join_to:
        body.name = name
    return body


def butt_brace_joints(design):
    """Brace joints as built: the X's front arms stop at the upper bar, and the tone bar butts
    against the treble X leg (no braces passing through one another)."""
    tbr = comp(design, 'Top Bracing')
    named = lambda n: [b for b in bodies_of(tbr) if b.name == n]
    upper = named('Upper Bar')[0]
    xb = named('X Brace')[0]
    # everything of the X on the neck side of the upper bar's back face goes
    stop = UPPER_BAR_X + UPPER_W / 2
    box = poly_extrude(tbr, [[(stop - 400, -300), (stop, -300), (stop, 300), (stop - 400, 300)]],
                       'X Arm Stop', -WALL - 30, 30).bodies.item(0)
    combine(tbr, xb, box, CUT, False)
    xb = [b for b in bodies_of(tbr) if b.name.startswith('X Brace')][0]
    xb.name = 'X Brace'
    for t in named('Tone Bar 1'):
        combine(tbr, t, xb, CUT, True)
    tones = sorted([b for b in bodies_of(tbr) if b.name.startswith('Tone Bar 1')], key=lambda b: -b.volume)
    for b in tones[1:]:
        tbr.features.removeFeatures.add(b)                 # sliver on the far side of the X leg
    tones[0].name = 'Tone Bar 1'


# ---- headless tuners on the bridge, and a tuning notch in the tail so the knobs can be reached ----
TAIL_NOTCH = True
NOTCH_BEHIND = 34.0                        # body edge this far behind the bridge line, across the strings
TUNER_HOUSING = (9.0, 28.0, 9.6, 12.0)     # from / to behind the bridge line, width, height (mm)
TUNER_KNOB = (28.0, 12.0, 4.75)            # starts at, length, radius (9.5 mm: fits 10.5 mm spacing)
TUNER_AXIS_H = 6.0                         # knob axis / string clamp height above the bridge top
TUNER_CLAMP = 8.5                          # strings end at the front of each tuner housing
TUNER_STRING_H = 0.5                       # ...this far above the bridge top: below the saddle crown, for break angle


def body_outline():
    """OUTLINE_REFINED, with the tuning notch cut into the butt behind the bridge if enabled."""
    pts = list(OUTLINE_REFINED)
    if not TAIL_NOTCH:
        return pts
    xn = lambda y: x_on(BRIDGE_LINE, NOTCH_BEHIND, y)
    keep, notch_at = [], None
    for i, (x, y) in enumerate(pts):
        if x > 640 and -40.0 <= y <= 44.0 and x > xn(y) + 0.5:
            if notch_at is None:
                notch_at = len(keep)
            continue
        keep.append((x, y))
    if notch_at is None:
        return pts
    # bass-side wall into a rounded inside corner, then the notch floor down to where the slanted
    # butt already meets it on the treble side
    notch = [(xn(40.0) + 28.0, 41.5), (xn(37.5) + 14.0, 38.0), (xn(35.0) + 5.0, 34.8), (xn(31.0) + 1.0, 30.5)]
    notch += [(xn(y), y) for y in (22.0, 12.0, 2.0, -8.0, -18.0, -28.0)]
    return keep[:notch_at] + notch + keep[notch_at:]


def add_corner_jack(design, comp_name, preamp):
    """Endpin jack (optionally with an endpin preamp barrel) through a small jack block at the tail's
    upper point, between the linings. Returns (wall point, tangent, outward normal, height)."""
    sides = comp(design, 'Sides')
    jo, jt, jn, zc = jack_frame(design)
    jb = new_comp(design, 'Jack Block')
    Lb, Tb = JACK_BLOCK
    (ox, oy), (tx, ty), (nx, ny) = jo, jt, jn
    corners = [(ox + tx * s * Lb / 2 + nx * t, oy + ty * s * Lb / 2 + ny * t)
               for s, t in ((-1, 2), (1, 2), (1, -Tb - WALL), (-1, -Tb - WALL))]
    ys = [p[1] for p in corners]
    z_lo, z_hi = back_z(max(ys), WALL + KERF_H) + 0.5, -WALL - KERF_H - 0.5   # clear of both linings
    block = poly_extrude(jb, [corners], 'Jack Block', z_lo, z_hi - z_lo).bodies.item(0)
    clip_to_void(jb, void_body(design), [block])
    jb.bRepBodies.item(0).name = 'Jack Block'
    wall_cut(jb, jo, jt, jn, zc, 'Jack Bore', (JACK_HOLE_D / 2,), JACK_LEN + 5)
    wall_cut(sides, jo, jt, jn, zc, 'Jack Bore', (JACK_HOLE_D / 2,), JACK_LEN + 5)
    jack = new_comp(design, comp_name)
    r_pre, l_pre = ENDPIN_PREAMP
    parts = [('Jack Barrel', JACK_HOLE_D / 2 - 0.2, -JACK_LEN, JACK_LEN)]
    if preamp:
        parts.append(('Endpin Preamp', r_pre, -JACK_LEN - l_pre, l_pre))
    parts += [('Jack Flange', 11.0, 0.8, 3.0), ('Strap Button', 6.0, 3.8, 9.0), ('Strap Button Cap', 9.0, 12.8, 2.5)]
    for nm, r, start, dist in parts:
        sk = wall_sketch(jack, jo, jt, jn, zc, nm)
        wall_circle(sk, jo, jt, zc, r)
        extrude_from(jack, sk.profiles.item(0), start, dist).bodies.item(0).name = nm
    return jo, jt, jn, zc


def add_tuners(design):
    """Six headless tuners on the back of the bridge, one behind each string's saddle point."""
    c = new_comp(design, 'Headless Tuners')
    x0, x1, w, h = TUNER_HOUSING
    ks, kl, kr = TUNER_KNOB
    for i in range(NS):
        y = S[i][1][1]
        a, b = x_on(BRIDGE_LINE, x0, y), x_on(BRIDGE_LINE, x1, y)
        fe = poly_extrude(c, [[(a, y - w / 2), (b, y - w / 2), (b, y + w / 2), (a, y + w / 2)]],
                          'Tuner %d Housing' % (6 - i), BRIDGE_H, h)
        fe.bodies.item(0).name = 'Tuner %d' % (6 - i)
        kx = x_on(BRIDGE_LINE, ks, y)
        sk = yz_sketch(c, kx, 'Tuner %d Knob' % (6 - i))
        sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P(kx, y, BRIDGE_H + TUNER_AXIS_H)), kr * MM)
        extrude(c, sk.profiles.item(0), 0, kl).bodies.item(0).name = 'Tuner %d Knob' % (6 - i)
        sk.isVisible = False
    app = adsk.core.Application.get()
    steel = lib_item(app, 'materials', 'Stainless Steel')
    satin = lib_item(app, 'appearances', 'Stainless Steel - Satin')
    for bdy in bodies_of(c):
        bdy.material, bdy.appearance = steel, satin

def build_shell(design):
    """One filleted body envelope, shelled to WALL and split into top / sides / back.

    The arm-side roundover lives in this envelope, so every wall keeps full thickness
    around the curve. Returns the cavity ('Void') body used to clip interior parts.
    """
    master = new_comp(design, 'Body Master')
    sk, sp = outline_sketch(master, [])
    if USE_REFINED_OUTLINE and THIGH_DRAFT_DEG:
        env = lofted_envelope(master)
    else:
        env = extrude(master, all_profiles(sk), Z_RIM - WALL, DEPTH + 2 * WALL).bodies.item(0)
    env.name = 'Shell'
    tf = top_face(env)
    fillet_edges(master, [tf.edges.item(i) for i in range(tf.edges.count)], EDGE_R)
    if BACK_TAPER:
        trim_at_back(master, [env], 0.0, True, 'Back Taper')
        env = bodies_of(master)[0]
        env.name = 'Shell'
    sculpt_heel(master, env)

    void = paste(master, env)
    void.name = 'Void'
    si = master.features.shellFeatures.createInput(coll([env]), False)
    si.insideThickness = VI(WALL * MM)
    master.features.shellFeatures.add(si)
    shell = [b for b in bodies_of(master) if b.name == 'Shell'][0]
    combine(master, void, shell, CUT, True)
    void = [b for b in bodies_of(master) if b.name == 'Void'][0]

    target = [b for b in bodies_of(master) if b.name != 'Void'][0]
    si = master.features.splitBodyFeatures.createInput(target, z_plane(master, -WALL, 'Top Split'), True)
    master.features.splitBodyFeatures.add(si)
    lower = min((b for b in bodies_of(master) if b.name != 'Void'), key=lambda b: b.boundingBox.minPoint.z)
    si = master.features.splitBodyFeatures.createInput(lower, back_plane(master, WALL, 'Back Split'), True)
    master.features.splitBodyFeatures.add(si)

    # The heel carve can leave a part in several pieces (e.g. the back behind each horn).
    parts = {'Top': [], 'Sides': [], 'Back': []}
    for b in bodies_of(master):
        if b.name == 'Void':
            continue
        lo, hi = b.boundingBox.minPoint.z / MM, b.boundingBox.maxPoint.z / MM
        parts['Top' if lo > -WALL - 0.5 else ('Back' if hi < -WALL - 10 else 'Sides')].append(b)
    for key, pieces in parts.items():
        c = new_comp(design, key)
        for i, b in enumerate(sorted(pieces, key=lambda b: -b.volume)):
            paste(c, b).name = key if i == 0 else '%s %d' % (key, i + 1)
    for i in range(design.rootComponent.occurrences.count):
        occ = design.rootComponent.occurrences.item(i)
        if occ.component == master:
            occ.isLightBulbOn = False
    return void


def build_body(design):
    void = build_shell(design)
    top, sides = comp(design, 'Top'), comp(design, 'Sides')

    # Side sound port in the upper-horn wall, facing the player: on a plane tangent to the wall,
    # cut only a few mm either side so the inner horn wall is untouched.
    wall = outline_samples(design, 6000)
    k = min(range(len(wall)), key=lambda i: math.hypot(wall[i][0] - SIDE_PORT_AT[0], wall[i][1] - SIDE_PORT_AT[1]))
    (cx, cy), (ax_, ay_), (bx_, by_) = wall[k], wall[k - 15], wall[(k + 15) % len(wall)]
    tl = math.hypot(bx_ - ax_, by_ - ay_)
    tx, ty = (bx_ - ax_) / tl, (by_ - ay_) / tl
    a, b = SIDE_PORT_AXES
    zc = SIDE_PORT_Z
    ref = sides.sketches.add(sides.xYConstructionPlane); ref.name = 'Side Port Plane'
    rp = [ref.sketchPoints.add(ref.modelToSketchSpace(P(*p)))
          for p in ((cx, cy, zc), (cx + tx * a, cy + ty * a, zc), (cx, cy, zc + b))]
    ref.isVisible = False
    pi = sides.constructionPlanes.createInput()
    pi.setByThreePoints(*rp)
    pl = sides.constructionPlanes.add(pi)
    pl.isLightBulbOn = False
    sk = sides.sketches.add(pl); sk.name = 'Side Port'
    m = lambda x, y, z: sk.modelToSketchSpace(P(x, y, z))
    sk.sketchCurves.sketchEllipses.add(m(cx, cy, zc), m(cx + tx * a, cy + ty * a, zc), m(cx, cy, zc + b))
    ext = sides.features.extrudeFeatures
    inp = ext.createInput(sk.profiles.item(0), CUT)
    inp.setSymmetricExtent(VI(16 * MM), True)
    inp.participantBodies = bodies_of(sides)
    ext.add(inp)

    # Neck block (with truss-rod access tunnel, reached through the side port)
    nb = new_comp(design, 'Neck Block')
    neck_poly, tail_poly = neck_block_poly(design), tail_block_poly(design)
    b = poly_extrude(nb, [neck_poly], 'Neck Block', Z_RIM, DEPTH).bodies.item(0)
    clip_to_void(nb, void, [b])
    nb.bRepBodies.item(0).name = 'Neck Block'

    # Tail block
    tbk = new_comp(design, 'Tail Block')
    b = poly_extrude(tbk, [tail_poly], 'Tail Block', Z_RIM, DEPTH).bodies.item(0)
    clip_to_void(tbk, void, [b])
    tbk.bRepBodies.item(0).name = 'Tail Block'

    # Kerfed linings top and back, interrupted by the blocks, following the cavity
    kf = new_comp(design, 'Kerfing')
    sk, sp = outline_sketch(kf, [WALL - 1, WALL + KERF_W], 'Kerfing')
    ring = ring_profile(sk, sp, False)
    extrude(kf, ring, -WALL - KERF_H, KERF_H)
    back_lining = extrude(kf, ring, Z_RIM - 20, KERF_H + 30).bodies.item(0)
    trim_at_back(kf, [back_lining], WALL + KERF_H, False, 'Back Lining Top')
    poly_extrude(kf, [neck_poly, tail_poly], 'Block Reliefs', Z_RIM, DEPTH, CUT, bodies_of(kf))
    clip_to_void(kf, void, bodies_of(kf))
    for i, b in enumerate(bodies_of(kf)):
        b.name = 'Kerfing %d' % (i + 1)
    kerfs = bodies_of(kf)

    # (The neck pocket itself is cut in cut_pocket(), from the tilted heel.)
    poly_extrude(nb, [[(X_POCKET_END - 12, 6), (X_POCKET_END - 12, -6), (BLOCK_BACK + 2, -6), (BLOCK_BACK + 2, 6)]],
                 'Truss Rod Access', -14, 11, CUT, bodies_of(nb))

    # Top bracing for light silk & steel: scalloped X crossing ahead of the bridge (no soundhole to
    # work around), two tone bars behind the bridge on the treble side, a light upper bar near the neck.
    tbr = new_comp(design, 'Top Bracing')
    cx, cy = X_CROSS
    a = math.radians(X_LEG_ANGLE)
    legs = []
    for sgn in (1, -1):
        d = (math.cos(a), sgn * math.sin(a))
        e0 = ray_to_rim(design, (cx, cy), (-d[0], -d[1]))
        e1 = ray_to_rim(design, (cx, cy), d)
        legs.append(((cx - d[0] * e0, cy - d[1] * e0), (cx + d[0] * e1, cy + d[1] * e1), e0 / (e0 + e1)))
    xb = scalloped_brace(tbr, legs[0][0], legs[0][1], X_W, X_H, X_END_H, legs[0][2], 'X Brace')
    scalloped_brace(tbr, legs[1][0], legs[1][1], X_W, X_H, X_END_H, legs[1][2], 'X Brace (treble leg)', join_to=xb)
    tdir = (math.cos(math.radians(TONE_DIR_DEG)), math.sin(math.radians(TONE_DIR_DEG)))
    for i, start in enumerate(TONE_BAR_STARTS):
        e = ray_to_rim(design, start, tdir)
        end = (start[0] + tdir[0] * e, start[1] + tdir[1] * e)
        scalloped_brace(tbr, start, end, TONE_W, TONE_H, TONE_END_H, 0.4, 'Tone Bar %d' % (i + 1))
    up = ray_to_rim(design, (UPPER_BAR_X, 0.0), (0.0, 1.0))
    dn = ray_to_rim(design, (UPPER_BAR_X, 0.0), (0.0, -1.0))
    scalloped_brace(tbr, (UPPER_BAR_X, -dn), (UPPER_BAR_X, up), UPPER_W, UPPER_H, UPPER_END_H,
                    dn / (up + dn), 'Upper Bar', flat=0.6)
    butt_brace_joints(design)
    clip_to_void(tbr, void, bodies_of(tbr))
    cut_with_copies(tbr, bodies_of(tbr), kerfs)

    # Thin maple bridge plate under the bridge, between the X legs
    bp = new_comp(design, 'Bridge Plate')
    poly_extrude(bp, [strip(BRIDGE_LINE, BRIDGE_FRONT - 3, BRIDGE_BACK + 6, 45)], 'Bridge Plate',
                 -WALL - PLATE_T, PLATE_T)
    clip_to_void(bp, void, bodies_of(bp))
    cut_with_copies(bp, bodies_of(bp), kerfs + bodies_of(tbr) + bodies_of(tbk))
    bp.bRepBodies.item(0).name = 'Bridge Plate'

    # Back bracing: ladder braces
    bbr = new_comp(design, 'Back Bracing')
    poly_extrude(bbr, [bar(x, 0, 90, 400, BACK_BRACE_W) for x in BACK_BRACES_X], 'Back Braces', Z_RIM - 20, 40)
    trim_at_back(bbr, bodies_of(bbr), WALL + BACK_BRACE_H, False, 'Back Brace Top')
    clip_to_void(bbr, void, bodies_of(bbr))
    cut_with_copies(bbr, bodies_of(bbr), kerfs)


def build_neck(design):
    # Neck: EndurNeck-style faceted carve (V shaved to a flat back, three flats), lofted to the
    # body and trimmed to the fanned plan, then a flat heel into the pocket.
    neck = new_comp(design, 'Neck')
    li = neck.features.loftFeatures.createInput(NEW)
    for x, tb, tt in NECK_STATIONS:
        yb = edge_y(EDGE_B, x) + 1.5
        yt = edge_y(EDGE_T, x) - 1.5
        c = (yb + yt) / 2
        h = NECK_FLAT / 2
        pts = [(yb, 0), (yb, -NECK_SHOULDER), (c + h, -tb), (c - h, -tt), (yt, -NECK_SHOULDER), (yt, 0)]
        sk = yz_sketch(neck, x, 'Neck Section %d' % x)
        lines = sk.sketchCurves.sketchLines
        m = [sk.modelToSketchSpace(P(x, y, z)) for y, z in pts]
        first = prev = lines.addByTwoPoints(m[0], m[1])
        for p in m[2:]:
            prev = lines.addByTwoPoints(prev.endSketchPoint, p)
        lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)
        li.loftSections.add(sk.profiles.item(0))
    li.isSolid = True
    carve = neck.features.loftFeatures.add(li).bodies.item(0)
    eb, et = across(END_LINE)
    pb, pt = across(POCKET_END)
    jc = joint_curve(design)
    plan = poly_extrude(neck, [[eb] + jc + [et]], 'Neck Plan', -40, 41).bodies.item(0)
    combine(neck, carve, plan, INTERSECT, False)
    # Soften the facet edges running along the neck: small at the shoulders, larger on the back.
    nbody = neck.bRepBodies.item(0)
    long_edges = [nbody.edges.item(i) for i in range(nbody.edges.count)
                  if nbody.edges.item(i).length > 150 * MM]
    fillet_edges(neck, [e for e in long_edges if -NECK_SHOULDER * 2 * MM < e.pointOnEdge.z < -0.5 * MM], 1.0)
    nbody = neck.bRepBodies.item(0)
    fillet_edges(neck, [nbody.edges.item(i) for i in range(nbody.edges.count)
                        if nbody.edges.item(i).length > 150 * MM and nbody.edges.item(i).pointOnEdge.z < -8 * MM],
                 NECK_FACET_R)
    poly_extrude(neck, [jc + [pt, pb]], 'Heel', -POCKET_D, POCKET_D, JOIN, bodies_of(neck))
    poly_extrude(neck, [[(12, 3.2), (12, -3.2), (X_POCKET_END + 2, -3.2), (X_POCKET_END + 2, 3.2)]],
                 'Truss Rod Channel', -10, 10, CUT, bodies_of(neck))
    neck.bRepBodies.item(0).name = 'Neck'

    # Truss rod (adjusts at the heel, through the soundhole)
    tr = new_comp(design, 'Truss Rod')
    poly_extrude(tr, [[(14, 3), (14, -3), (X_POCKET_END - 1, -3), (X_POCKET_END - 1, 3)]],
                 'Truss Rod', -9.8, 9.5).bodies.item(0).name = 'Truss Rod'

    # Fretboard
    fb = new_comp(design, 'Fretboard')
    board = poly_extrude(fb, [band(NUT_LINE, FB_END)], 'Fretboard Plan', 0, FB_T).bodies.item(0)
    combine(fb, board, radius_cylinder(fb, FB_R, 'Radius'), INTERSECT, False)
    fb.bRepBodies.item(0).name = 'Fretboard'

    # Frets: fanned, seated on the radius, rounded crowns
    fr = new_comp(design, 'Frets')
    outer = radius_cylinder(fr, FB_R + FRET_H, 'Crown Radius')
    inner = radius_cylinder(fr, FB_R, 'Seat Radius')
    for n in range(1, 25):
        pb, pt = across(fret_line(n), 0.3)
        vx, vy = pt[0] - pb[0], pt[1] - pb[1]
        l = math.hypot(vx, vy)
        nx, ny = -vy / l * FRET_W / 2, vx / l * FRET_W / 2
        poly = [(pb[0] - nx, pb[1] - ny), (pt[0] - nx, pt[1] - ny), (pt[0] + nx, pt[1] + ny), (pb[0] + nx, pb[1] + ny)]
        b = poly_extrude(fr, [poly], 'Fret %d' % n, 3, 7).bodies.item(0)
        b = combine(fr, b, outer, INTERSECT, True).bodies.item(0)
        b = combine(fr, b, inner, CUT, True).bodies.item(0)
        b.name = 'Fret %d' % n
        fillet_long_top_edges(fr, b, 1.0, 20)
    fr.features.removeFeatures.add(outer)
    fr.features.removeFeatures.add(inner)

    # Nut: top follows the board radius at the nut clearance
    nut = new_comp(design, 'Nut')
    clr = sum(NUT_CLEAR) / 2
    nb_ = poly_extrude(nut, [band(shift(NUT_LINE, -5), NUT_LINE)], 'Nut', 0, FRET_TOP + clr + 2).bodies.item(0)
    combine(nut, nb_, radius_cylinder(nut, FB_R + FRET_H + clr, 'Nut Radius'), INTERSECT, False)
    nut.bRepBodies.item(0).name = 'Nut'

    # Pocket tool: the heel footprint, from ahead of the joint to the pocket end, through the top.
    # It tilts with the neck, so the pocket cut from it matches the heel exactly.
    pocket_tool = poly_extrude(neck, [band(shift(joint_line(design), -20), POCKET_END)], 'Pocket Tool',
                               -POCKET_D, POCKET_D + 6).bodies.item(0)
    pocket_tool.name = 'Pocket Tool'
    pocket_tool.isLightBulbOn = False

    # Headless string anchor
    sa = new_comp(design, 'String Anchor')
    ab = poly_extrude(sa, [band(shift(END_LINE, 2), shift(NUT_LINE, -6), 0.8)], 'Anchor', 0, 10).bodies.item(0)
    ab.name = 'String Anchor'
    fillet_edges(sa, vertical_edges(ab), 3.0)
    hs = sa.sketches.add(sa.xYConstructionPlane); hs.name = 'String Holes'
    for i in range(NS):
        hs.sketchCurves.sketchCircles.addByCenterRadius(P(S[i][0][0] - 15, S[i][0][1]), 1.6 * MM)
    extrude(sa, all_profiles(hs), 0, 10, CUT, [ab])


NECK_PARTS = ('Neck', 'Truss Rod', 'Fretboard', 'Frets', 'Nut', 'String Anchor')


def occurrence(design, name):
    for i in range(design.rootComponent.occurrences.count):
        occ = design.rootComponent.occurrences.item(i)
        if occ.component.name == name:
            return occ
    raise ValueError('no occurrence ' + name)


def tilt_neck(design):
    """Set the neck angle: rotate every neck part about the pivot (nut end down)."""
    m = adsk.core.Matrix3D.create()
    m.setToRotation(-NECK_ANGLE, adsk.core.Vector3D.create(0, 1, 0), P(NECK_PIVOT_X, 0, 0))
    for name in NECK_PARTS:
        occurrence(design, name).transform2 = m
    if design.snapshots.hasPendingSnapshot:
        design.snapshots.add()


def cut_pocket(design):
    """Cut the neck pocket through top, sides, kerfing and neck block from the tilted heel tool."""
    neck_occ = occurrence(design, 'Neck')
    tool = [neck_occ.bRepBodies.item(i) for i in range(neck_occ.bRepBodies.count)
            if neck_occ.bRepBodies.item(i).name == 'Pocket Tool'][0]
    root = design.rootComponent
    for name in ('Top', 'Sides', 'Kerfing', 'Neck Block'):
        occ = occurrence(design, name)
        for i in range(occ.bRepBodies.count):
            target = occ.bRepBodies.item(i)
            ci = root.features.combineFeatures.createInput(target, coll([tool]))
            ci.operation = CUT
            ci.isKeepToolBodies = True
            root.features.combineFeatures.add(ci)
    comp(design, 'Neck').features.removeFeatures.add(tool.nativeObject)


def build_bridge(design):
    br = new_comp(design, 'Bridge')
    bb = poly_extrude(br, [strip(BRIDGE_LINE, BRIDGE_FRONT, BRIDGE_BACK, BRIDGE_HALF)], 'Bridge Plan',
                      0, BRIDGE_H).bodies.item(0)
    bb.name = 'Bridge'
    fillet_edges(br, vertical_edges(bb), BRIDGE_CORNER_R)

    # Tapered wings: flat across the saddle, easing down to 5 mm at the ends
    xc = x_on(BRIDGE_LINE, (BRIDGE_FRONT + BRIDGE_BACK) / 2, 0)
    sk = yz_sketch(br, xc, 'Wing Taper')
    m = lambda y, z: sk.modelToSketchSpace(P(xc, y, z))
    splines, lines = sk.sketchCurves.sketchFittedSplines, sk.sketchCurves.sketchLines
    flat, end = SADDLE_HALF + 3, BRIDGE_HALF + 8
    wing = [(flat + t * (end - flat), z) for t, z in ((1.0, 4.8), (0.6, 6.3), (0.3, 8.0), (0.0, BRIDGE_H + 0.4))]
    left = splines.add(coll([m(-y, z) for y, z in wing]))
    right = splines.add(coll([m(y, z) for y, z in reversed(wing)]))
    lines.addByTwoPoints(left.endSketchPoint, right.startSketchPoint)
    up_r = lines.addByTwoPoints(right.endSketchPoint, m(end, 20))
    top_l = lines.addByTwoPoints(up_r.endSketchPoint, m(-end, 20))
    lines.addByTwoPoints(top_l.endSketchPoint, left.startSketchPoint)
    ext = br.features.extrudeFeatures
    inp = ext.createInput(sk.profiles.item(0), CUT)
    inp.setSymmetricExtent(VI(120 * MM), True)
    inp.participantBodies = bodies_of(br)
    ext.add(inp)

    # Compensated saddle slot + saddle
    slot = strip(SADDLE_LINE, -SADDLE_W / 2, SADDLE_W / 2, SADDLE_HALF)
    poly_extrude(br, [slot], 'Saddle Slot', 3, BRIDGE_H - 3, CUT, bodies_of(br))
    # Saddle: plan from the slot, crown through each string's computed height (follows the radius
    # and the bass/treble action difference)
    geom = string_geometry()
    sd = new_comp(design, 'Saddle')
    top_z = max(s[2] for n, s in geom)
    sb = poly_extrude(sd, [slot], 'Saddle', 3, top_z + 3 - 3).bodies.item(0)
    xs = x_on(SADDLE_LINE, 0, 0)
    sk = yz_sketch(sd, xs, 'Saddle Crown')
    m = lambda y, z: sk.modelToSketchSpace(P(xs, y, z))
    pts = [(s[1], s[2]) for n, s in geom]                      # bass (+y) -> treble
    (y0, z0), (y1, z1) = pts[0], pts[1]
    (y4, z4), (y5, z5) = pts[-2], pts[-1]
    ext_b = (SADDLE_HALF + 2, z0 + (z0 - z1) / (y0 - y1) * (SADDLE_HALF + 2 - y0))
    ext_t = (-SADDLE_HALF - 2, z5 + (z5 - z4) / (y5 - y4) * (-SADDLE_HALF - 2 - y5))
    crown = sk.sketchCurves.sketchFittedSplines.add(coll([m(*p) for p in [ext_b] + pts + [ext_t]]))
    lines = sk.sketchCurves.sketchLines
    l1 = lines.addByTwoPoints(crown.endSketchPoint, m(ext_t[0], 0))
    l2 = lines.addByTwoPoints(l1.endSketchPoint, m(ext_b[0], 0))
    lines.addByTwoPoints(l2.endSketchPoint, crown.startSketchPoint)
    ext = sd.features.extrudeFeatures
    inp = ext.createInput(sk.profiles.item(0), NEW)
    inp.setSymmetricExtent(VI(40 * MM), True)
    shape = ext.add(inp).bodies.item(0)
    combine(sd, sb, shape, INTERSECT, False)
    sb = sd.bRepBodies.item(0)
    sb.name = 'Saddle'
    fillet_long_top_edges(sd, sb, SADDLE_W / 2 - 0.1, 20)

    build_strings(design)


def build_strings(design):
    """Strings: anchor -> nut -> saddle -> tuner area on bridge (nut end follows the neck angle)."""
    geom = string_geometry()
    st = new_comp(design, 'Strings')
    sk = st.sketches.add(st.xYConstructionPlane); sk.name = 'String Paths'
    lines = sk.sketchCurves.sketchLines
    for i, (n, s) in enumerate(geom):
        r = GAUGES[i] / 2
        (nx, ny), (bx, by) = S[i]
        anchor = rot(nx - 15, ny, 9.5 + r)
        a = lines.addByTwoPoints(P(*anchor), P(n[0], n[1], n[2] + r))
        b = lines.addByTwoPoints(a.endSketchPoint, P(s[0], s[1], s[2] + r))
        c = lines.addByTwoPoints(b.endSketchPoint, P(x_on(BRIDGE_LINE, TUNER_CLAMP, by), by, BRIDGE_H + TUNER_STRING_H + r))
        pin = st.features.pipeFeatures.createInput(st.features.createPath(coll([a, b, c]), False), NEW)
        pin.sectionType = adsk.fusion.PipeSectionTypes.CircularPipeSectionType
        pin.sectionSize = VI(GAUGES[i] * MM)
        st.features.pipeFeatures.add(pin).bodies.item(0).name = 'String %d' % (6 - i)


def split_neck_laminates(design):
    """Split the neck into three equal-width laminations following the taper (glue lines at 1/3, 2/3)."""
    neck = comp(design, 'Neck')
    ref = neck.sketches.add(neck.xYConstructionPlane); ref.name = 'Lamination Lines'
    ref.isVisible = False
    for k in (1 / 3.0, 2 / 3.0):
        pts = []
        for x, z in ((-60, 0), (520, 0), (-60, -30)):
            y = edge_y(EDGE_T, x) + k * (edge_y(EDGE_B, x) - edge_y(EDGE_T, x))
            pts.append(ref.sketchPoints.add(ref.modelToSketchSpace(P(x, y, z))))
        pi = neck.constructionPlanes.createInput()
        pi.setByThreePoints(*pts)
        pl = neck.constructionPlanes.add(pi)
        pl.isLightBulbOn = False
        # first cut splits the whole neck; the second applies to the larger (two-thirds) piece
        target = max((b for b in bodies_of(neck) if b.name.startswith('Neck')), key=lambda b: b.volume)
        si = neck.features.splitBodyFeatures.createInput(target, pl, True)
        neck.features.splitBodyFeatures.add(si)
    strips = sorted([b for b in bodies_of(neck) if b.name.startswith('Neck')],
                    key=lambda b: HAND * (b.boundingBox.minPoint.y + b.boundingBox.maxPoint.y))
    for b, nm in zip(strips, ('Neck (treble lamination)', 'Neck (centre lamination)', 'Neck (bass lamination)')):
        b.name = nm


def apply_materials(design):
    app = adsk.core.Application.get()

    def custom(base, name, density):
        m = design.materials.itemByName(name)
        if not m:
            m = design.materials.addByCopy(lib_item(app, 'materials', base), name)
        m.materialProperties.itemById('structural_Density').value = density   # kg/m^3
        return m

    steel = lib_item(app, 'materials', 'Stainless Steel')
    cedar = custom('Redwood', 'Cedar, Western Red', 370)
    rosewood = custom('Walnut', 'Rosewood, Indian', 830)
    richlite = custom('Phenolic Resin', 'Richlite', 1420)
    roasted_maple = custom('Maple', 'Maple, Roasted', 650)
    bone = custom('Plastic, Opaque White', 'Bone', 1900)
    mahogany = lib_item(app, 'materials', 'Mahogany')
    walnut = lib_item(app, 'materials', 'Walnut')                     # black walnut back, sides and bridge
    spruce = lib_item(app, 'materials', 'Spruce')
    maple = lib_item(app, 'materials', 'Maple')
    nylon = lib_item(app, 'materials', 'Nylon 6/6')
    polished, satin = 'Stainless Steel - Polished', 'Stainless Steel - Satin'
    plan = [('Frets', steel, polished), ('String Anchor', steel, satin), ('Truss Rod', steel, satin),
            ('Top', cedar, 'Cherry'), ('Sides', walnut, 'Walnut'), ('Back', walnut, 'Walnut'),
            ('Bridge', walnut, 'Walnut'), ('Fretboard', richlite, 'Plastic - Matte (Black)'),
            ('Neck', roasted_maple, 'Mahogany'),           # deep roasted-maple brown ('Nut', bone, 'Acetal Resin (White)'),
            ('Saddle', bone, 'Acetal Resin (White)'), ('Neck Block', mahogany, 'Mahogany'),
            ('Tail Block', mahogany, 'Mahogany'), ('Kerfing', mahogany, 'Mahogany'),
            ('Top Bracing', spruce, None), ('Back Bracing', spruce, None), ('Bridge Plate', maple, None),
            ('Strings', lib_item(app, 'materials', 'Steel'), 'Stainless Steel - Satin')]   # silk & steel
    for cname, mat, appr in plan:
        a = lib_item(app, 'appearances', appr) if appr else None
        for b in bodies_of(comp(design, cname)):
            if cname == 'Fretboard' and b.name != 'Fretboard':
                continue                       # inlays and side dots keep their own materials
            b.material = mat
            if a:
                b.appearance = a


def tidy(design):
    for c in design.allComponents:
        for i in range(c.sketches.count):
            c.sketches.item(i).isVisible = False
        for i in range(c.constructionPlanes.count):
            c.constructionPlanes.item(i).isLightBulbOn = False


def view(eye, target, perspective=True, fit=True):
    vp = adsk.core.Application.get().activeViewport
    cam = vp.camera
    cam.cameraType = (adsk.core.CameraTypes.PerspectiveCameraType if perspective
                      else adsk.core.CameraTypes.OrthographicCameraType)
    cam.target = P(*target)
    cam.eye = P(*eye)
    cam.upVector = adsk.core.Vector3D.create(0, 1, 0) if not perspective else adsk.core.Vector3D.create(0, 0, 1)
    cam.isFitView = fit
    vp.camera = cam
    vp.refresh()


# ======================= scale reference: seated player =======================
# Player frame (mm): origin on the seat between the hips, +X forward, +Y player's left, +Z up.
# Roughly 50th-percentile adult; classical position with the left foot on a ~150 mm footstool.
SEAT_H = 450.0
THIGH_R, SHIN_R, UPPER_ARM_R, FOREARM_R = 75.0, 55.0, 45.0, 38.0
HIP_L, KNEE_L, ANKLE_L, TOE_L = (0, 100, 75), (440, 110, 225), (470, 120, -250), (580, 120, -300)
HIP_R, KNEE_R, ANKLE_R, TOE_R = (0, -100, 75), (450, -130, 75), (480, -140, -400), (590, -140, -450)
SHOULDER_L, SHOULDER_R = (-20, 185, 540), (-20, -185, 540)
CHEST_FRONT_X = 90.0
LEG_REST_PT = (545.0, -106.0)       # geometry coords: deepest point of the treble-side leg scoop


def PP(x, y, z):
    """Player-frame point, mm -> cm, no handedness mirror."""
    return adsk.core.Point3D.create(x * MM, y * MM, z * MM)


def _guitar_axes(theta):
    c, s = math.cos(theta), math.sin(theta)
    # guitar axes in player frame: neck (-x_g) up to the player's left, face (+z_g) forward
    return (0.0, -c, -s), (0.0, s, -c), (1.0, 0.0, 0.0)


def place_guitar(design, theta_deg):
    """Hang the guitar in front of the chest at the given neck angle and let it settle onto the
    thighs: slide sideways until it rests on both. Returns (T, contacts) in the player frame (mm)."""
    th = math.radians(theta_deg)
    xg, yg, zg = _guitar_axes(th)
    edge = [(x, HAND * y) for x, y in outline_samples(design, 1500)]          # model coords
    mid_z = -(WALL + DEPTH / 2)
    tx = CHEST_FRONT_X + (2 * WALL + DEPTH)                                   # back of the body on the chest
    px_mid = tx + mid_z
    def thigh(hip, knee):
        k = (px_mid - hip[0]) / (knee[0] - hip[0])
        return (hip[1] + k * (knee[1] - hip[1]), hip[2] + k * (knee[2] - hip[2]))
    thighs = (('left thigh', thigh(HIP_L, KNEE_L)), ('right thigh', thigh(HIP_R, KNEE_R)))
    def gaps(ty, tz):
        out = []
        for name, (cy, cz) in thighs:
            best = None
            for p in edge:
                u, v = ty + p[0] * xg[1] + p[1] * yg[1], tz + p[0] * xg[2] + p[1] * yg[2]
                dd = math.hypot(u - cy, v - cz) - THIGH_R
                if best is None or dd < best[0]:
                    best = (dd, p)
            out.append(best)
        return out
    def settle(ty):
        # lower from well above until the edge first touches a thigh, then refine
        tz = 1500.0
        while min(g[0] for g in gaps(ty, tz)) > 0 and tz > -500:
            tz -= 10.0
        lo, hi = tz, tz + 10.0
        for _ in range(20):
            mid = (lo + hi) / 2
            if min(g[0] for g in gaps(ty, mid)) > 0:
                hi = mid
            else:
                lo = mid
        return hi
    best = None
    for ty in range(200, 801, 10):
        tz = settle(ty)
        gl, gr = gaps(ty, tz)
        score = max(gl[0], gr[0])                     # resting on both thighs -> both gaps ~0
        if best is None or score < best[0]:
            best = (score, ty, tz, gl, gr)
    score, ty, tz, gl, gr = best
    contacts = [(thighs[0][0], (gl[1][0], HAND * gl[1][1]), gl[0]), (thighs[1][0], (gr[1][0], HAND * gr[1][1]), gr[0])]
    return (tx, float(ty), tz), contacts


def build_player(design, theta_deg):
    """Add a to-scale seated player (and chair + footstool) positioned around the guitar."""
    T, contacts = place_guitar(design, theta_deg)
    c = new_comp(design, 'Player (scale reference)')
    sk = c.sketches.add(c.xYConstructionPlane); sk.name = 'Limbs'
    lines = sk.sketchCurves.sketchLines
    xg, yg, zg = _guitar_axes(math.radians(theta_deg))
    def g2p(x, y, z):
        return tuple(T[i] + x * xg[i] + y * yg[i] + z * zg[i] for i in range(3))
    # hands: left behind the neck at the 4th fret, right over the strings ahead of the bridge
    f4 = x_on(fret_line(4), 0, 0)
    hand_l = g2p(f4, 0, -30)
    hand_r = g2p(560, 0, 40)
    rest_r = g2p(640, HAND * 150, -20)            # right forearm over the bass edge of the lower bout
    elbow_l = tuple((SHOULDER_L[i] + hand_l[i]) / 2 + (40, 60, -150)[i] for i in range(3))
    elbow_r = tuple((SHOULDER_R[i] + rest_r[i]) / 2 + (-40, -40, -120)[i] for i in range(3))
    limbs = [(HIP_L, KNEE_L, THIGH_R), (KNEE_L, ANKLE_L, SHIN_R), (ANKLE_L, TOE_L, 40),
             (HIP_R, KNEE_R, THIGH_R), (KNEE_R, ANKLE_R, SHIN_R), (ANKLE_R, TOE_R, 40),
             (SHOULDER_L, elbow_l, UPPER_ARM_R), (elbow_l, hand_l, FOREARM_R),
             (SHOULDER_R, elbow_r, UPPER_ARM_R), (elbow_r, rest_r, FOREARM_R), (rest_r, hand_r, FOREARM_R)]
    for a, b, r in limbs:
        ln = lines.addByTwoPoints(PP(*a), PP(*b))
        pin = c.features.pipeFeatures.createInput(c.features.createPath(ln, False), NEW)
        pin.sectionType = adsk.fusion.PipeSectionTypes.CircularPipeSectionType
        pin.sectionSize = VI(2 * r * MM)
        c.features.pipeFeatures.add(pin)
    # torso (ellipse prism), neck, head
    tsk = c.sketches.add(c.xYConstructionPlane); tsk.name = 'Torso'
    tsk.sketchCurves.sketchEllipses.add(PP(-20, 0, 0), PP(-20, 175, 0), PP(CHEST_FRONT_X, 0, 0))
    extrude(c, tsk.profiles.item(0), 0, 560)
    nsk = c.sketches.add(c.xYConstructionPlane); nsk.name = 'Neck'
    nsk.sketchCurves.sketchCircles.addByCenterRadius(PP(-20, 0, 0), 55 * MM)
    extrude(c, nsk.profiles.item(0), 560, 90)
    hsk = c.sketches.add(c.xZConstructionPlane); hsk.name = 'Head'
    m = lambda x, z: hsk.modelToSketchSpace(PP(x, 0, z))
    axis = hsk.sketchCurves.sketchLines.addByTwoPoints(m(-20, 640), m(-20, 860))
    hsk.sketchCurves.sketchArcs.addByThreePoints(axis.startSketchPoint, m(90, 750), axis.endSketchPoint)
    ri = c.features.revolveFeatures.createInput(hsk.profiles.item(0), axis, NEW)
    ri.setAngleExtent(False, VI(2 * math.pi))
    c.features.revolveFeatures.add(ri)
    # chair seat + footstool
    seat = poly_sketch_raw(c, [(-250, -230), (230, -230), (230, 230), (-250, 230)], 'Seat')
    extrude(c, seat.profiles.item(0), -40, 40)
    stool = poly_sketch_raw(c, [(420, 40), (650, 40), (650, 200), (420, 200)], 'Footstool')
    extrude(c, stool.profiles.item(0), -SEAT_H, SEAT_H - 300)
    for i in range(c.sketches.count):
        c.sketches.item(i).isVisible = False
    # place the player around the guitar: player frame -> model frame is g = R^T (P - T)
    rows = (xg, yg, zg)
    arr = []
    for r in rows:
        arr += [r[0], r[1], r[2], -sum(r[i] * T[i] for i in range(3)) * MM]
    arr += [0, 0, 0, 1]
    mtx = adsk.core.Matrix3D.create()
    mtx.setWithArray(arr)
    occurrence(design, 'Player (scale reference)').transform2 = mtx
    if design.snapshots.hasPendingSnapshot:
        design.snapshots.add()
    skin = lib_item(adsk.core.Application.get(), 'appearances', 'Plastic - Matte (White)')
    for b in bodies_of(c):
        b.appearance = skin
    return T, contacts


def poly_sketch_raw(c, pts, name):
    sk = c.sketches.add(c.xYConstructionPlane)
    sk.name = name
    lines = sk.sketchCurves.sketchLines
    first = prev = lines.addByTwoPoints(PP(pts[0][0], pts[0][1], 0), PP(pts[1][0], pts[1][1], 0))
    for p in pts[2:]:
        prev = lines.addByTwoPoints(prev.endSketchPoint, PP(p[0], p[1], 0))
    lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)
    return sk


# ======================= glow-in-the-dark side markers =======================
# Strandberg-style luminous side dots on the bass (player-facing) edge of the fretboard only.
SIDE_DOT_FRETS = (3, 5, 7, 9, 12, 15, 17, 19, 21, 24)
SIDE_DOT_DOUBLE = (12, 24)
SIDE_DOT_D, SIDE_DOT_DEPTH, SIDE_DOT_Z = 2.0, 3.0, 3.4     # mm; Z = height of dot centre above the board's base
SIDE_DOT_PAIR = 3.5                                        # spacing of the double dots along the edge


def add_side_markers(design):
    """Drill the bass edge of the fretboard and fill it with glow dots (bodies in the Fretboard component)."""
    fb = comp(design, 'Fretboard')
    board = [b for b in bodies_of(fb) if b.name == 'Fretboard'][0]
    (x1, y1), (x2, y2) = EDGE_B
    l = math.hypot(x2 - x1, y2 - y1)
    ex, ey = (x2 - x1) / l, (y2 - y1) / l                    # along the edge (nut -> bridge)
    def on_edge(n):
        a = across(fret_line(n - 1))[0]
        b = across(fret_line(n))[0]
        return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    centres = []
    for n in SIDE_DOT_FRETS:
        mx, my = on_edge(n)
        offs = (-SIDE_DOT_PAIR / 2, SIDE_DOT_PAIR / 2) if n in SIDE_DOT_DOUBLE else (0.0,)
        centres += [(mx + ex * o, my + ey * o) for o in offs]
    # one sketch on the (planar, vertical) bass edge face
    ref = fb.sketches.add(fb.xYConstructionPlane); ref.name = 'Side Dot Plane'
    ref.isVisible = False
    rp = [ref.sketchPoints.add(ref.modelToSketchSpace(P(*p))) for p in
          ((x1, y1, SIDE_DOT_Z), (x2, y2, SIDE_DOT_Z), (x1, y1, SIDE_DOT_Z + 1))]
    pi = fb.constructionPlanes.createInput()
    pi.setByThreePoints(*rp)
    pl = fb.constructionPlanes.add(pi)
    pl.isLightBulbOn = False
    sk = fb.sketches.add(pl); sk.name = 'Side Dots'
    for cx, cy in centres:
        sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P(cx, cy, SIDE_DOT_Z)),
                                                        SIDE_DOT_D / 2 * MM)
    ext = fb.features.extrudeFeatures
    inp = ext.createInput(all_profiles(sk), NEW)
    inp.setSymmetricExtent(VI(2 * SIDE_DOT_DEPTH * MM), True)
    pins = ext.add(inp)
    dots = [pins.bodies.item(i) for i in range(pins.bodies.count)]
    # keep only the part inside the board, then seat each dot in its own hole
    for i, d in enumerate(dots):
        tool = paste(fb, board)
        d = combine(fb, d, tool, INTERSECT, False).bodies.item(0)
        combine(fb, board, d, CUT, True)
        d.name = 'Side Dot %d' % (i + 1)
    return len(dots)


def apply_marker_material(design):
    app = adsk.core.Application.get()
    m = design.materials.itemByName('Glow Resin (Luminlay-type)')
    if not m:
        m = design.materials.addByCopy(lib_item(app, 'materials', 'Epoxy Resin'), 'Glow Resin (Luminlay-type)')
    m.materialProperties.itemById('structural_Density').value = 1700
    glow = lib_item(app, 'appearances', 'LED (Green)')
    for b in bodies_of(comp(design, 'Fretboard')):
        if b.name.startswith('Side Dot'):
            b.material = m
            b.appearance = glow


# ======================= electronics: piezo, side preamp/tuner, endpin jack =======================
PREAMP_AT = (560.0, 121.0)                  # bass-side wall, toward the neck from the strumming forearm
PREAMP_Z = -53.0
PREAMP_CUTOUT = (70.0, 35.0)                # compact preamp + tuner side-mount cutout
PREAMP_PLATE = (78.0, 42.0, 2.5)
PREAMP_BOX = (60.0, 32.0, 22.0)            # just over a 9 V battery (48.5 x 26.5 x 17.5)
PIEZO_T = 1.2                               # under-saddle strip thickness (saddle shortened by this)
PIEZO_HOLE_Y, PIEZO_HOLE_D = 17.0, 3.2      # cable hole along the saddle, clear of the X-brace legs
JACK_HOLE_D, JACK_LEN = 12.7, 35.0
WIRE_D = 3.0


def wall_frame(design, at):
    """Point on the outline nearest `at`, unit tangent and outward normal (geometry coords)."""
    pts = outline_samples(design, 6000)
    n = len(pts)
    k = min(range(n), key=lambda i: math.hypot(pts[i][0] - at[0], pts[i][1] - at[1]))
    a, b = pts[k - 15], pts[(k + 15) % n]
    l = math.hypot(b[0] - a[0], b[1] - a[1])
    tx, ty = (b[0] - a[0]) / l, (b[1] - a[1]) / l
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    ix, iy = (-ty, tx) if area > 0 else (ty, -tx)
    return pts[k], (tx, ty), (-ix, -iy)


def wall_sketch(c, origin, tangent, outward, z, name):
    """Sketch on the vertical plane tangent to the wall, normal pointing outward."""
    (cx, cy), (tx, ty), (ox, oy) = origin, tangent, outward
    ref = c.sketches.add(c.xYConstructionPlane)
    ref.name = name + ' Plane Points'
    p1, p2, p3 = P(cx, cy, z), P(cx + tx * 10, cy + ty * 10, z), P(cx, cy, z + 10)
    # plane normal (p2-p1) x (p3-p1) = (t_y, -t_x, 0) in model coords; it must point outward
    t_m = (tx, HAND * ty)
    o_m = (ox, HAND * oy)
    if t_m[1] * o_m[0] - t_m[0] * o_m[1] < 0:
        p2, p3 = p3, p2
    rp = [ref.sketchPoints.add(ref.modelToSketchSpace(p)) for p in (p1, p2, p3)]
    ref.isVisible = False
    pi = c.constructionPlanes.createInput()
    pi.setByThreePoints(*rp)
    pl = c.constructionPlanes.add(pi)
    pl.isLightBulbOn = False
    sk = c.sketches.add(pl)
    sk.name = name
    return sk


def wall_rect(sk, origin, tangent, z, w, h, du=0.0, dv=0.0):
    (cx, cy), (tx, ty) = origin, tangent
    m = lambda u, v: sk.modelToSketchSpace(P(cx + tx * u, cy + ty * u, z + v))
    lines = sk.sketchCurves.sketchLines
    corners = [(du - w / 2, dv - h / 2), (du + w / 2, dv - h / 2), (du + w / 2, dv + h / 2), (du - w / 2, dv + h / 2)]
    first = prev = lines.addByTwoPoints(m(*corners[0]), m(*corners[1]))
    for u, v in corners[2:]:
        prev = lines.addByTwoPoints(prev.endSketchPoint, m(u, v))
    lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)


def wall_circle(sk, origin, tangent, z, r, du=0.0, dv=0.0):
    (cx, cy), (tx, ty) = origin, tangent
    sk.sketchCurves.sketchCircles.addByCenterRadius(
        sk.modelToSketchSpace(P(cx + tx * du, cy + ty * du, z + dv)), r * MM)


def extrude_from(c, prof, start, dist, op=NEW, bodies=None):
    """Extrude from `start` mm along the sketch normal (outward) by `dist` mm (negative = inward)."""
    ext = c.features.extrudeFeatures
    inp = ext.createInput(prof, op)
    inp.startExtent = adsk.fusion.OffsetStartDefinition.create(VI(start * MM))
    direction = (adsk.fusion.ExtentDirections.PositiveExtentDirection if dist >= 0
                 else adsk.fusion.ExtentDirections.NegativeExtentDirection)
    inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(VI(abs(dist) * MM)), direction)
    if bodies is not None:
        inp.participantBodies = bodies
    return ext.add(inp)


def wall_cut(c, origin, tangent, outward, z, name, shape, half_depth):
    """Cut a rectangle (w, h) or circle (r,) through a wall, half_depth mm either side of the plane."""
    sk = wall_sketch(c, origin, tangent, outward, z, name)
    if len(shape) == 2:
        wall_rect(sk, origin, tangent, z, *shape)
    else:
        wall_circle(sk, origin, tangent, z, shape[0])
    ext = c.features.extrudeFeatures
    inp = ext.createInput(sk.profiles.item(0), CUT)
    inp.setSymmetricExtent(VI(2 * half_depth * MM), True)
    inp.participantBodies = bodies_of(c)
    ext.add(inp)


def pipe_path(c, pts, d, name):
    sk = c.sketches.add(c.xYConstructionPlane)
    sk.name = name
    lines = sk.sketchCurves.sketchLines
    segs = [lines.addByTwoPoints(P(*pts[0]), P(*pts[1]))]
    for p in pts[2:]:
        segs.append(lines.addByTwoPoints(segs[-1].endSketchPoint, P(*p)))
    pin = c.features.pipeFeatures.createInput(c.features.createPath(coll(segs), False), NEW)
    pin.sectionType = adsk.fusion.PipeSectionTypes.CircularPipeSectionType
    pin.sectionSize = VI(d * MM)
    b = c.features.pipeFeatures.add(pin).bodies.item(0)
    b.name = name
    sk.isVisible = False
    return b



def wall_deviation(design, o, t, n):
    """dev(u): how far the wall surface sits outward of the tangent plane at distance u along it."""
    pts = outline_samples(design, 6000)
    near = []
    for p in pts:
        u = (p[0] - o[0]) * t[0] + (p[1] - o[1]) * t[1]
        w = (p[0] - o[0]) * n[0] + (p[1] - o[1]) * n[1]
        if abs(u) < 90 and abs(w) < 30:
            near.append((u, w))
    near.sort()
    def dev(u):
        best = min(near, key=lambda q: abs(q[0] - u))
        return best[1]
    return dev


def conformal_plate(c, o, t, n, z, plate, name):
    """A plate that follows the curved wall: (outline offset outward by thickness) ring, clipped to a rectangle."""
    w, h, thick = plate
    sk, sp = outline_sketch(c, [], name + ' Wall')
    far = (o[0] + n[0] * 300, o[1] + n[1] * 300)
    sk.offset(coll([sp]), P(*far), thick * MM)
    ring = ring_profile(sk, sp, True)
    slab = extrude(c, ring, z - h / 2, h).bodies.item(0)
    rs = wall_sketch(c, o, t, n, z, name + ' Outline')
    wall_rect(rs, o, t, z, w, h)
    ext = c.features.extrudeFeatures
    inp = ext.createInput(rs.profiles.item(0), NEW)
    inp.setSymmetricExtent(VI(80 * MM), True)
    prism = ext.add(inp).bodies.item(0)
    combine(c, slab, prism, INTERSECT, False)
    body = [b for b in bodies_of(c)][-1]
    body.name = name
    sk.isVisible = False
    return body

def add_electronics(design):
    sides, tail = comp(design, 'Sides'), comp(design, 'Tail Block')

    # --- side-mount preamp with tuner, facing the player ---
    o, t, n = wall_frame(design, PREAMP_AT)
    wall_cut(sides, o, t, n, PREAMP_Z, 'Preamp Cutout', PREAMP_CUTOUT, 8.0)
    pre = new_comp(design, 'Preamp + Tuner')
    conformal_plate(pre, o, t, n, PREAMP_Z, PREAMP_PLATE, 'Faceplate')
    dev = wall_deviation(design, o, t, n)
    sk = wall_sketch(pre, o, t, n, PREAMP_Z, 'Electronics Box')
    wall_rect(sk, o, t, PREAMP_Z, PREAMP_BOX[0], PREAMP_BOX[1])
    extrude_from(pre, sk.profiles.item(0), -WALL, -PREAMP_BOX[2]).bodies.item(0).name = 'Electronics Box'
    sk = wall_sketch(pre, o, t, n, PREAMP_Z, 'Tuner Screen')
    wall_rect(sk, o, t, PREAMP_Z, 18.0, 11.0, du=-18.0, dv=4.0)
    seat = max(dev(u) for u in range(-27, -8)) + PREAMP_PLATE[2]
    extrude_from(pre, sk.profiles.item(0), seat, 0.4).bodies.item(0).name = 'Tuner Screen'
    controls = [('Volume', 6.0, 3.0, 3.5), ('Bass', 17.0, 3.0, 3.5), ('Treble', 28.0, 3.0, 3.5),
                ('Tuner Button', -30.0, -12.0, 2.2)]
    for nm, du, dv, r in controls:
        sk = wall_sketch(pre, o, t, n, PREAMP_Z, nm)
        wall_circle(sk, o, t, PREAMP_Z, r, du=du, dv=dv)
        seat = max(dev(du + k) for k in (-r, 0, r)) + PREAMP_PLATE[2]
        extrude_from(pre, sk.profiles.item(0), seat, 5.0).bodies.item(0).name = nm
    gap = WALL + PREAMP_BOX[2] + 1.5                                    # cables stop just short of the box
    box_back = (o[0] - n[0] * gap, o[1] - n[1] * gap)

    # --- endpin jack / strap button at the tail's upper point (the butt centre is the tuning notch) ---
    jo, jt, jn, zc = add_corner_jack(design, 'Endpin Jack', preamp=False)
    jack_inner = (jo[0] - jn[0] * (JACK_LEN + 1.5), jo[1] - jn[1] * (JACK_LEN + 1.5))

    # --- under-saddle piezo: strip in the slot bottom, saddle shortened to keep the action ---
    pz = new_comp(design, 'Piezo Pickup')
    slot = strip(SADDLE_LINE, -SADDLE_W / 2, SADDLE_W / 2, SADDLE_HALF)
    poly_extrude(pz, [slot], 'Piezo Strip', 3, PIEZO_T).bodies.item(0).name = 'Piezo Strip'
    sd = comp(design, 'Saddle')
    poly_extrude(sd, [slot], 'Piezo Relief', 3, PIEZO_T, CUT, bodies_of(sd))
    hx, hy = x_on(SADDLE_LINE, 0, PIEZO_HOLE_Y), PIEZO_HOLE_Y
    for cname in ('Bridge', 'Top', 'Bridge Plate'):
        cc = comp(design, cname)
        hs = cc.sketches.add(cc.xYConstructionPlane)
        hs.name = 'Piezo Cable Hole'
        hs.sketchCurves.sketchCircles.addByCenterRadius(P(hx, hy), PIEZO_HOLE_D / 2 * MM)
        extrude(cc, hs.profiles.item(0), -WALL - 4, WALL + 7.1, CUT, bodies_of(cc))
        hs.isVisible = False

    # --- wiring through the open middle of the body ---
    wr = new_comp(design, 'Wiring')
    zw = -50.0
    pipe_path(wr, [(hx, hy, 2.9), (hx, hy, -WALL - 6), (hx, hy, zw), (box_back[0], box_back[1], zw)],
              2.0, 'Piezo Cable')
    pipe_path(wr, [(box_back[0], box_back[1], zw - 8), (jack_inner[0], jack_inner[1], zw - 8),
                   (jack_inner[0], jack_inner[1], zc)], WIRE_D, 'Output Cable')
    return {'preamp_at': o, 'jack_at': jo, 'piezo_hole': (hx, hy)}


def apply_electronics_materials(design):
    app = adsk.core.Application.get()
    steel = lib_item(app, 'materials', 'Stainless Steel')
    satin = lib_item(app, 'appearances', 'Stainless Steel - Satin')
    copper = lib_item(app, 'materials', 'Copper')
    abs_mat = lib_item(app, 'materials', 'Acetal Resin, Black')
    black = lib_item(app, 'appearances', 'Plastic - Matte (Black)')
    glossy = lib_item(app, 'appearances', 'Plastic - Glossy (Black)')
    pz = design.materials.itemByName('Piezo Element')
    if not pz:
        pz = design.materials.addByCopy(lib_item(app, 'materials', 'Stainless Steel'), 'Piezo Element')
    pz.materialProperties.itemById('structural_Density').value = 7500     # PZT ceramic in a stainless sleeve
    for b in bodies_of(comp(design, 'Preamp + Tuner')):
        b.material = abs_mat
        b.appearance = glossy if b.name == 'Tuner Screen' else black
    for b in bodies_of(comp(design, 'Endpin Jack')):
        b.material = steel
        b.appearance = satin
    for b in bodies_of(comp(design, 'Wiring')):
        b.material = copper                      # copper conductor, black insulation
        b.appearance = black
    for b in bodies_of(comp(design, 'Piezo Pickup')):
        b.material = pz
        b.appearance = satin


# ======================= 12th-fret sparrowhawk inlay =======================
# Stylised Eurasian sparrowhawk from above, flying toward the headless end: broad rounded
# wings with fingered primaries and a long square-cut tail (the accipiter silhouette).
# Right half (v >= 0) in mm: u along the neck (negative = toward the nut), v across the board.
SPARROWHAWK_HALF = [(-7.5, 0.0), (-7.2, 0.9), (-6.5, 1.4), (-5.6, 1.3), (-5.0, 1.8), (-5.6, 5.0),
                    (-5.9, 9.0), (-5.6, 13.0), (-4.8, 16.5), (-3.6, 18.8), (-2.2, 20.0), (-1.0, 19.6),
                    (-0.6, 18.2), (0.4, 18.6), (0.8, 17.0), (1.6, 17.2), (1.9, 15.4), (2.6, 15.0),
                    (2.4, 12.0), (2.2, 8.0), (1.6, 4.0), (1.2, 2.2), (2.0, 1.5), (6.8, 2.2), (7.5, 1.9),
                    (7.2, 0.0)]
INLAY_SCALE = 0.88            # -> ~35 mm wingspan, ~13 mm beak to tail
INLAY_DEPTH = 1.5


GLIDE_FRET_SPACE = 11         # between frets 10 and 11 (toward the headless end from the 11th)


def fan_axes(fret_space):
    """Unit vectors (u toward the bridge, v toward the bass edge) aligned with the frets of a space."""
    a1, b1 = fret_line(fret_space - 1)
    a2, b2 = fret_line(fret_space)
    dx, dy = ((b1[0] - a1[0]) + (b2[0] - a2[0])) / 2, ((b1[1] - a1[1]) + (b2[1] - a2[1])) / 2
    l = math.hypot(dx, dy)
    vx, vy = -dx / l, -dy / l
    ux, uy = vy, -vx
    if ux < 0:
        ux, uy = -ux, -uy
    return (ux, uy), (vx, vy)


def fit_inlay(shape, fret_space, band, max_scale, clear=1.5, align_to_fan=False):
    """Place shape [(u, v)] in a fret space at the largest scale (<= max_scale) that stays `clear` mm
    from both fret crowns and inside band(x) -> (y_low, y_high)."""
    us, vs = [u for u, v in shape], [v for u, v in shape]
    uc, vc = (max(us) + min(us)) / 2, (max(vs) + min(vs)) / 2
    lo_f, hi_f = fret_line(fret_space - 1), fret_line(fret_space)
    cx = (x_on(lo_f, 0, 0) + x_on(hi_f, 0, 0)) / 2
    yl, yh = band(cx)
    cy = (yl + yh) / 2
    (ux, uy), (vx, vy) = fan_axes(fret_space) if align_to_fan else ((1.0, 0.0), (0.0, 1.0))
    def place(s):
        return [(cx + s * ((u - uc) * ux + (v - vc) * vx), cy + s * ((u - uc) * uy + (v - vc) * vy)) for u, v in shape]
    def ok(pts):
        if min(_line_dist(p, lo_f) for p in pts) - FRET_W / 2 < clear:
            return False
        if min(_line_dist(p, hi_f) for p in pts) - FRET_W / 2 < clear:
            return False
        return all(band(p[0])[0] <= p[1] <= band(p[0])[1] for p in pts)
    lo, hi = 0.05, max_scale
    if ok(place(hi)):
        return place(hi)
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if ok(place(mid)) else (lo, mid)
    return place(lo)


def full_width(clear=1.5):
    return lambda x: (edge_y(EDGE_T, x) + clear, edge_y(EDGE_B, x) - clear)


def treble_half(clear=1.5):
    return lambda x: (edge_y(EDGE_T, x) + clear, -clear)


def sparrowhawk_outline():
    """Gliding bird, wings along the fan, in the fret space above the 11th fret."""
    half = SPARROWHAWK_HALF
    loop = half + [(u, -v) for u, v in reversed(half[1:-1])]
    return fit_inlay(loop, GLIDE_FRET_SPACE, full_width(), INLAY_SCALE, align_to_fan=True)


def add_inlay(design, outline=None, name='Sparrowhawk Inlay'):
    """Rout a pocket in the fretboard and seat a flush inlay that follows the board radius."""
    fb = comp(design, 'Fretboard')
    board = [b for b in bodies_of(fb) if b.name == 'Fretboard'][0]
    sk = poly_sketch(fb, [outline or sparrowhawk_outline()], name)
    prism = extrude(fb, sk.profiles.item(0), 0, FB_T + 2).bodies.item(0)
    top = radius_cylinder(fb, FB_R, 'Inlay Top')
    floor = radius_cylinder(fb, FB_R - INLAY_DEPTH, 'Inlay Floor')
    inlay = combine(fb, prism, top, INTERSECT, False).bodies.item(0)
    inlay = combine(fb, inlay, floor, CUT, False).bodies.item(0)
    inlay.name = name
    combine(fb, board, inlay, CUT, True)
    sk.isVisible = False
    return inlay


def apply_inlay_material(design):
    app = adsk.core.Application.get()
    m = design.materials.itemByName('Mother of Pearl')
    if not m:
        m = design.materials.addByCopy(lib_item(app, 'materials', 'Acetal Resin, White'), 'Mother of Pearl')
    m.materialProperties.itemById('structural_Density').value = 2700
    for b in bodies_of(comp(design, 'Fretboard')):
        if b.name.startswith('Sparrowhawk'):
            b.material = m
            b.appearance = lib_item(app, 'appearances', 'Plastic - Glossy (White)')


# Diving sparrowhawk (side profile, in a stoop): wings swept back with the wrist raised, closed
# tail, hooked beak. s along the dive (+ = head), t across it (+ = back). mm.
SPARROWHAWK_STOOP = [(22.0, -0.6), (21.2, -1.7), (19.5, -2.3), (16.0, -3.3), (11.0, -4.1), (5.0, -4.4),
                     (-1.0, -4.0), (-6.0, -3.2), (-11.0, -2.0), (-16.0, -1.4), (-21.0, -1.1), (-22.5, -0.3),
                     (-22.0, 0.6), (-17.0, 1.2), (-12.0, 1.7), (-9.0, 2.4), (-16.0, 4.4), (-12.0, 5.6),
                     (-5.0, 6.6), (1.0, 7.0), (6.0, 5.6), (10.0, 3.8), (14.5, 2.9), (18.0, 2.6), (20.3, 1.8),
                     (21.6, 0.6)]
STOOP_FRET = 17
STOOP_ANGLE = 27.0            # dive angle to the neck axis, degrees
STOOP_TAIL_Y = 20.0           # tail starts in the bass-side third; head reaches the centre line


def stoop_outline():
    """Diving bird: tail in the bass-side third, head at the centre line, diving toward the nut."""
    th = math.radians(STOOP_ANGLE)
    dx, dy = -math.cos(th), -math.sin(th)            # dive direction: toward the nut and the centre
    tx, ty = -dy, dx
    if ty < 0:
        tx, ty = -tx, -ty                            # back of the bird faces the bass edge
    half = max(abs(s) for s, t in SPARROWHAWK_STOOP)
    cx = x_on(fret_line(STOOP_FRET), 0, 0)
    cy = STOOP_TAIL_Y - half * math.sin(th)          # head (s = +half) lands on y ~ 0
    return [(cx + s * dx + t * tx, cy + s * dy + t * ty) for s, t in SPARROWHAWK_STOOP]


# Striking sparrowhawk (side profile): wings raised and spread back to brake, tail fanned down,
# legs thrust forward with talons open toward the treble side. u along the neck (- = nut, where
# it faces), v across the board (+ = bass edge). Free units; fitted to the fret space below.
SPARROWHAWK_STRIKE = [(-14.0, 3.0), (-13.2, 1.8), (-11.5, 1.4), (-10.5, -1.5), (-8.5, -4.5), (-9.5, -7.5),
                      (-12.0, -12.0), (-13.0, -14.0), (-16.5, -15.5), (-17.2, -17.5), (-15.5, -16.2),
                      (-13.5, -15.6), (-14.5, -18.5), (-14.2, -20.0), (-13.0, -18.2), (-11.0, -17.5),
                      (-10.0, -19.2), (-10.5, -16.5), (-10.0, -14.5), (-9.0, -11.5), (-6.5, -8.0), (-3.5, -7.5),
                      (3.0, -12.0), (7.5, -14.5), (9.0, -12.0), (8.5, -9.0), (2.0, -5.0), (1.0, -2.0), (6.0, 2.0),
                      (10.0, 7.0), (12.5, 12.0), (11.0, 12.5), (12.0, 15.5), (10.0, 15.2), (10.5, 18.5),
                      (8.5, 17.5), (8.0, 20.5), (6.2, 18.8), (4.5, 21.0), (2.5, 18.0), (-0.5, 13.0), (-3.0, 8.0),
                      (-4.5, 5.0), (-7.0, 5.0), (-10.0, 5.2), (-12.0, 4.6), (-13.3, 3.8)]
STRIKE_FRET_SPACE = 4          # between frets 3 and 4
STRIKE_CLEAR = 1.5             # mm clear of fret crowns and board edges


def _line_dist(p, line):
    (x1, y1), (x2, y2) = line
    return abs((x2 - x1) * (y1 - p[1]) - (x1 - p[0]) * (y2 - y1)) / math.hypot(x2 - x1, y2 - y1)


def strike_outline():
    """Striking bird, shrunk into the treble half of its fret space."""
    return fit_inlay(SPARROWHAWK_STRIKE, STRIKE_FRET_SPACE, treble_half(STRIKE_CLEAR), 3.0, STRIKE_CLEAR)


# ======================= soundboard inlay: the hawk line, on the wind =======================
# From the Creation of Ea (A Wizard of Earthsea): the closing line, inlaid in pearl in the cedar
# under the strings, drifting on a wave from just ahead of the bridge toward the neck.
WIND_TEXT = 'bright the hawk’s flight on the empty sky'
WIND_FONT, WIND_ITALIC = 'Palatino Linotype', True
WIND_TEXT_H = 4.5             # mm letter height
WIND_DEPTH = 1.0              # mm into the 3 mm top
WIND_GAP = 8.0                # mm clear of the bridge front and of the fretboard end
WIND_AMPLITUDE, WIND_WAVES = 6.0, 1.5
WIND_CENTRE_Y = -0.6                        # path offset so the letters sit centred under the strings


def wind_path_points(n=13):
    x0 = x_on(BRIDGE_LINE, BRIDGE_FRONT, 0) - WIND_GAP          # start: just ahead of the bridge
    x1 = x_on(FB_END, 0, 0) + WIND_GAP                          # end: just short of the fretboard
    pts = []
    for k in range(n):
        f = k / (n - 1)
        x = x0 + (x1 - x0) * f
        y = WIND_CENTRE_Y + WIND_AMPLITUDE * math.sin(2 * math.pi * WIND_WAVES * f) * math.sin(math.pi * f) ** 0.5
        pts.append((x, y))
    return pts


def add_soundboard_text(design):
    """Pearl lettering along a wind-blown wave on the soundboard; pocket cut into the top."""
    c = new_comp(design, 'Soundboard Inlay')
    # Fusion keeps sketch text upright toward the sketch's +Y. Turn this component 180 deg about Z
    # so its +Y points at the bass edge: the letters then stand upright for the player.
    rot = adsk.core.Matrix3D.create()
    rot.setToRotation(math.pi, adsk.core.Vector3D.create(0, 0, 1), adsk.core.Point3D.create(0, 0, 0))
    occurrence(design, 'Soundboard Inlay').transform2 = rot
    if design.snapshots.hasPendingSnapshot:
        design.snapshots.add()
    local = lambda x, y: adsk.core.Point3D.create(-x * MM, -HAND * y * MM, 0)   # model point -> component
    sk = c.sketches.add(c.xYConstructionPlane)
    sk.name = 'Hawk Line'
    path = sk.sketchCurves.sketchFittedSplines.add(coll([local(x, y) for x, y in wind_path_points()]))
    path.isConstruction = True
    ti = sk.sketchTexts.createInput2(WIND_TEXT, WIND_TEXT_H * MM)
    ti.setAsAlongPath(path, True, adsk.core.HorizontalAlignments.CenterHorizontalAlignment, 0)
    try:
        ti.fontName = WIND_FONT
    except Exception:
        pass                                                     # keep the default font if unavailable
    if WIND_ITALIC:
        ti.textStyle = adsk.fusion.TextStyles.TextStyleItalic
    text = sk.sketchTexts.add(ti)
    fe = extrude(c, text, -WIND_DEPTH, WIND_DEPTH)
    glyphs = [fe.bodies.item(i) for i in range(fe.bodies.count)]
    for i, b in enumerate(glyphs):
        b.name = 'Hawk Line %d' % (i + 1)
    # pocket the top: root-level combine with the glyphs as tools (kept)
    top_occ = occurrence(design, 'Top')
    occ = occurrence(design, 'Soundboard Inlay')
    tools = coll([occ.bRepBodies.item(i) for i in range(occ.bRepBodies.count)])
    root = design.rootComponent
    for i in range(top_occ.bRepBodies.count):
        ci = root.features.combineFeatures.createInput(top_occ.bRepBodies.item(i), tools)
        ci.operation = CUT
        ci.isKeepToolBodies = True
        root.features.combineFeatures.add(ci)
    sk.isVisible = False
    app = adsk.core.Application.get()
    m = design.materials.itemByName('Mother of Pearl')
    if not m:
        m = design.materials.addByCopy(lib_item(app, 'materials', 'Acetal Resin, White'), 'Mother of Pearl')
        m.materialProperties.itemById('structural_Density').value = 2700
    white = lib_item(app, 'appearances', 'Plastic - Glossy (White)')
    for b in glyphs:
        b.material = m
        b.appearance = white
    return len(glyphs)


# ======================= thin variant + tail-only electronics =======================
def thin_variant(total_depth=50.0):
    """Thin sibling of The dream: body total_depth on the treble side, same proportions elsewhere.
    Call at the start of every build stage (module globals persist between Fusion script runs)."""
    global DEPTH, Z_RIM, BACK_TAPER, SIDE_PORT_Z, SIDE_PORT_AXES
    full = 2 * WALL + 100.0                 # The dream: 106 mm treble side, 10 mm wedge taper
    DEPTH = total_depth - 2 * WALL
    Z_RIM = -(WALL + DEPTH)
    BACK_TAPER = 10.0 * total_depth / full
    SIDE_PORT_Z = -(WALL + DEPTH / 2)
    SIDE_PORT_AXES = (30.0, 10.0)           # ~60 x 20 mm oval to suit the thinner wall


ENDPIN_PREAMP = (10.0, 40.0)                # radius, length of the preamp body behind the jack barrel
BATTERY_BOX = (48.0, 30.0, 20.0)            # 9 V holder: length, width, height (mm)
JACK_TARGET = (741.0, 80.0)                 # the upper (bass-side) rear point of the tail; None = butt centre
JACK_BLOCK = (40.0, 20.0)                   # length along the wall, thickness inward (mm)
BATTERY_SIDE_OFFSET = 32.0                  # (unused when BATTERY_FIXED is set)
BATTERY_FIXED = (625.0, 35.0)               # on the back, between the 595 and 655 back braces, clear of the walls


def jack_frame(design):
    """Where the jack goes: wall point, tangent, outward normal and the jack's height (between the
    top and back linings, so it clears both on a thin body)."""
    if JACK_TARGET is None:
        pts = outline_samples(design, 6000)
        m = len(pts)
        i = max((k for k in range(m) if pts[k][0] > 600 and (pts[k][1] >= 0) != (pts[(k + 1) % m][1] >= 0)),
                key=lambda k: pts[k][0])
        target = pts[i]
    else:
        target = JACK_TARGET
    jo, jt, jn = wall_frame(design, target)
    z_top_lining = -WALL - KERF_H
    z_back_lining = back_z(jo[1], WALL + KERF_H)
    return jo, jt, jn, (z_top_lining + z_back_lining) / 2


def battery_position(jo, jt, jn):
    if BATTERY_FIXED is not None:
        return BATTERY_FIXED
    r_pre, l_pre = ENDPIN_PREAMP
    along = JACK_LEN + l_pre / 2                       # level with the middle of the preamp barrel
    return (jo[0] - jn[0] * along + jt[0] * BATTERY_SIDE_OFFSET,
            jo[1] - jn[1] * along + jt[1] * BATTERY_SIDE_OFFSET)


def add_tail_electronics(design):
    """Minimal electronics: under-saddle piezo, endpin preamp/jack through a small jack block at the
    tail's upper point, and a 9 V box on the back beside it. No side panel or cutout."""
    sides = comp(design, 'Sides')
    jo, jt, jn, zc = jack_frame(design)

    add_corner_jack(design, 'Endpin Preamp + Jack', preamp=True)

    # 9 V battery box on the back, beside the preamp barrel
    bx, by = battery_position(jo, jt, jn)
    L, W, H = BATTERY_BOX
    bat = new_comp(design, 'Battery Box')
    z0 = max(back_z(by - W / 2, WALL), back_z(by + W / 2, WALL)) + 0.05
    poly_extrude(bat, [[(bx - L / 2, by - W / 2), (bx + L / 2, by - W / 2), (bx + L / 2, by + W / 2),
                        (bx - L / 2, by + W / 2)]], 'Battery Box', z0, H).bodies.item(0).name = 'Battery Box (9 V)'

    # under-saddle piezo, as on The dream
    pz = new_comp(design, 'Piezo Pickup')
    slot = strip(SADDLE_LINE, -SADDLE_W / 2, SADDLE_W / 2, SADDLE_HALF)
    poly_extrude(pz, [slot], 'Piezo Strip', 3, PIEZO_T).bodies.item(0).name = 'Piezo Strip'
    sd = comp(design, 'Saddle')
    poly_extrude(sd, [slot], 'Piezo Relief', 3, PIEZO_T, CUT, bodies_of(sd))
    hx, hy = x_on(SADDLE_LINE, 0, PIEZO_HOLE_Y), PIEZO_HOLE_Y
    for cname in ('Bridge', 'Top', 'Bridge Plate'):
        cc = comp(design, cname)
        hs = cc.sketches.add(cc.xYConstructionPlane)
        hs.name = 'Piezo Cable Hole'
        hs.sketchCurves.sketchCircles.addByCenterRadius(P(hx, hy), PIEZO_HOLE_D / 2 * MM)
        extrude(cc, hs.profiles.item(0), -WALL - 4, WALL + 7.1, CUT, bodies_of(cc))
        hs.isVisible = False

    tail_wiring(design)
    return {'jack_at': jo, 'jack_z': zc, 'battery_at': (bx, by)}


def void_body(design):
    return [b for b in bodies_of(comp(design, 'Body Master')) if b.name == 'Void'][0]


def tail_wiring(design):
    """Piezo cable runs just under the top to the preamp's inner end; the battery lead runs from the
    box beside it. Both meet the preamp end side by side."""
    jo, jt, jn, zc = jack_frame(design)
    r_pre, l_pre = ENDPIN_PREAMP
    reach = JACK_LEN + l_pre + 3.0
    ex, ey = jo[0] - jn[0] * reach, jo[1] - jn[1] * reach          # just past the preamp's inner end
    px, py = jt                                                     # sideways, along the wall
    hx, hy = x_on(SADDLE_LINE, 0, PIEZO_HOLE_Y), PIEZO_HOLE_Y
    bx, by = battery_position(jo, jt, jn)
    L, W, H = BATTERY_BOX
    z0 = max(back_z(by - W / 2, WALL), back_z(by + W / 2, WALL)) + 0.05
    z_over = zc + r_pre + 3.0                                       # above the preamp, below the top braces
    wr = new_comp(design, 'Wiring')
    a = (ex - px * 3, ey - py * 3)
    b = (ex + px * 3, ey + py * 3)
    pipe_path(wr, [(hx, hy, 2.9), (hx, hy, z_over), (a[0], a[1], z_over), (a[0], a[1], zc)], 2.0, 'Piezo Cable')
    side = (bx + L / 2 + 1.5, by)                                   # the box end facing the tail
    pipe_path(wr, [(side[0], side[1], z0 + H / 2), (b[0], b[1], z0 + H / 2), (b[0], b[1], zc)], 2.0, 'Battery Lead')


def apply_tail_electronics_materials(design):
    app = adsk.core.Application.get()
    steel = lib_item(app, 'materials', 'Stainless Steel')
    satin = lib_item(app, 'appearances', 'Stainless Steel - Satin')
    abs_mat = lib_item(app, 'materials', 'Acetal Resin, Black')
    black = lib_item(app, 'appearances', 'Plastic - Matte (Black)')
    copper = lib_item(app, 'materials', 'Copper')
    pz = design.materials.itemByName('Piezo Element')
    if not pz:
        pz = design.materials.addByCopy(lib_item(app, 'materials', 'Stainless Steel'), 'Piezo Element')
    pz.materialProperties.itemById('structural_Density').value = 7500
    for b in bodies_of(comp(design, 'Endpin Preamp + Jack')):
        b.material = abs_mat if b.name == 'Endpin Preamp' else steel
        b.appearance = black if b.name == 'Endpin Preamp' else satin
    for b in bodies_of(comp(design, 'Battery Box')):
        b.material, b.appearance = abs_mat, black
    mahogany = lib_item(app, 'materials', 'Mahogany')
    for b in bodies_of(comp(design, 'Jack Block')):
        b.material = mahogany
        b.appearance = lib_item(app, 'appearances', 'Mahogany')
    for b in bodies_of(comp(design, 'Wiring')):
        b.material, b.appearance = copper, black
    for b in bodies_of(comp(design, 'Piezo Pickup')):
        b.material, b.appearance = pz, satin


# ======================= f-hole =======================
# One violin-style f-hole in the soundboard's bass-side upper bout, running parallel to the bass edge.
F_HOLE_ENABLED = False             # removed on the thin guitar; set True to cut it again
F_HOLE_AT = (585.0, 108.0)         # centre (geometry coords, mm)
F_HOLE_ANGLE = 23.3                # degrees from the neck axis: follows the local bass edge
F_HOLE_LEN, F_HOLE_W = 84.0, 10.0  # stem length and widest point
F_HOLE_EYE_R, F_HOLE_S = 5.0, 5.0  # end eyes, and how far the stem swings either way


def f_hole_outline():
    """Stem (closed polygon) and the two eye circles, in geometry coords."""
    th = math.radians(F_HOLE_ANGLE)
    ax, ay = math.cos(th), math.sin(th)
    nx, ny = -ay, ax
    cx, cy = F_HOLE_AT
    half = F_HOLE_LEN / 2
    def pt(u, v):
        return (cx + u * ax + v * nx, cy + u * ay + v * ny)
    centre = lambda u: -F_HOLE_S * math.sin(math.pi * u / half)
    width = lambda u: 2.0 + (F_HOLE_W - 2.0) * math.sin(math.pi * (u + half) / (2 * half)) ** 1.5
    us = [-half + 2 * half * k / 30 for k in range(31)]
    left = [pt(u, centre(u) - width(u) / 2) for u in us]
    right = [pt(u, centre(u) + width(u) / 2) for u in reversed(us)]
    eyes = [(pt(-half - 1.0, 2.0), F_HOLE_EYE_R), (pt(half + 1.0, -2.0), F_HOLE_EYE_R)]
    return left + right, eyes


def add_f_hole(design):
    top = comp(design, 'Top')
    stem, eyes = f_hole_outline()
    sk = poly_sketch(top, [stem], 'F-hole')
    for (x, y), r in eyes:
        sk.sketchCurves.sketchCircles.addByCenterRadius(P(x, y), r * MM)
    extrude(top, all_profiles(sk), -WALL - 1, WALL + 2, CUT, bodies_of(top))
    sk.isVisible = False


# ======================= paint scheme: OD green with a yellow duct-tape X =======================
OD_GREEN = (124, 134, 88)            # lighter olive drab, satin
TAPE_YELLOW = (246, 204, 28)         # duct-tape yellow, matte
TAPE_W, TAPE_T = 48.0, 0.2           # 2" duct tape; thin decal layer
TAPE_CROSS = (600.0, 38.0)           # off-centre: toward the bass side, just ahead of the bridge
TAPE_ANGLES = (31.0, -57.0)          # uneven, as if slapped on by hand


def custom_appearance(design, base, name, rgb):
    app = adsk.core.Application.get()
    a = design.appearances.itemByName(name)
    if not a:
        a = design.appearances.addByCopy(lib_item(app, 'appearances', base), name)
    a.appearanceProperties.itemById('opaque_albedo').value = adsk.core.Color.create(rgb[0], rgb[1], rgb[2], 255)
    return a


def paint_body(design):
    """Top, sides and back painted OD green (the wood materials stay for mass and properties)."""
    green = custom_appearance(design, 'Paint - Enamel Glossy (Green)', 'OD Green (satin)', OD_GREEN)
    for cname in ('Top', 'Sides', 'Back'):
        for b in bodies_of(comp(design, cname)):
            b.appearance = green


def add_tape_x(design):
    """Yellow duct-tape X on the soundboard: kept on the flat of the top, stopped at the bridge,
    the fretboard and the f-hole."""
    c = new_comp(design, 'Tape X (paint)')
    cx, cy = TAPE_CROSS
    tape = poly_extrude(c, [bar(cx, cy, a, 900, TAPE_W) for a in TAPE_ANGLES], 'Tape Strips', 0, TAPE_T)
    bodies = [tape.bodies.item(i) for i in range(tape.bodies.count)]
    # keep it on the flat of the top, inside the edge roundover
    sk, sp = outline_sketch(c, [EDGE_R + 0.5], 'Tape Clip')
    clip = extrude(c, inner_profile(sk), -1, TAPE_T + 2).bodies.item(0)
    for b in bodies:
        combine(c, b, clip, INTERSECT, True)
    c.features.removeFeatures.add(clip)
    sk.isVisible = False
    # stop at the bridge, the fretboard and the f-hole
    stem, eyes = f_hole_outline() if F_HOLE_ENABLED else ([], [])
    polys = [strip(BRIDGE_LINE, BRIDGE_FRONT, BRIDGE_BACK, BRIDGE_HALF), band(NUT_LINE, FB_END)] + ([stem] if stem else [])
    hs = poly_sketch(c, polys, 'Tape Reliefs')
    for (x, y), r in eyes:
        hs.sketchCurves.sketchCircles.addByCenterRadius(P(x, y), r * MM)
    extrude(c, all_profiles(hs), -1, TAPE_T + 2, CUT, bodies_of(c))
    hs.isVisible = False
    yellow = custom_appearance(design, 'Plastic - Matte (Black)', 'Duct Tape Yellow (matte)', TAPE_YELLOW)
    for b in bodies_of(c):
        b.appearance = yellow
        b.name = 'Tape X'
    return len(bodies_of(c))


# ======================= side markers as the |-/ symbols =======================
# Read along the bass edge from the headless end toward the body, as the player sees it:
# the logo spelled out one symbol at a time, then complete at 12 and 24; plain dots at 9 and 21.
SIDE_GLYPHS = {3: '|', 5: '-', 7: '/', 9: '.', 12: '|-/', 15: '|', 17: '-', 19: '/', 21: '.', 24: '|-/'}
GLYPH_H, GLYPH_T, GLYPH_GAP = 3.2, 0.9, 3.0     # symbol height, stroke thickness, spacing inside |-/
GLYPH_DEPTH = 2.0


def _glyph_shapes(sym, u0):
    """Polygons [(u, v)] and circles [((u, v), r)] for one symbol centred at u0 on the edge;
    u runs nut -> bridge, v is height above the dot centre line."""
    h, t = GLYPH_H, GLYPH_T
    def rect(cu, cv, w, hh, ang=0.0):
        a = math.radians(ang)
        ux, uy, vx, vy = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
        return [(cu + ux * su * w / 2 + vx * sv * hh / 2, cv + uy * su * w / 2 + vy * sv * hh / 2)
                for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    if sym == '.':
        return [], [((u0, 0.0), 1.0)]
    if sym == '|':
        return [rect(u0, 0, t, h)], []
    if sym == '-':
        return [rect(u0, 0, 0.75 * h, t)], []
    if sym == '/':
        return [rect(u0, 0, h * 1.12, t, 62.0)], []
    if sym == '|-/':
        polys = []
        for k, s in enumerate('|-/'):
            p, _ = _glyph_shapes(s, u0 + (k - 1) * GLYPH_GAP)
            polys += p
        return polys, []
    raise ValueError(sym)


def fill_side_dots(design):
    """Fill the round side-dot holes back in (merge each dot into the board)."""
    fb = comp(design, 'Fretboard')
    board = [b for b in bodies_of(fb) if b.name == 'Fretboard'][0]
    for d in [b for b in bodies_of(fb) if b.name.startswith('Side Dot')]:
        combine(fb, board, d, JOIN, False)


def add_side_glyphs(design):
    """Inlay the SIDE_GLYPHS symbols into the bass edge of the fretboard (glow resin)."""
    fb = comp(design, 'Fretboard')
    board = [b for b in bodies_of(fb) if b.name == 'Fretboard'][0]
    (x1, y1), (x2, y2) = EDGE_B
    l = math.hypot(x2 - x1, y2 - y1)
    ex, ey = (x2 - x1) / l, (y2 - y1) / l
    ref = fb.sketches.add(fb.xYConstructionPlane)
    ref.name = 'Side Glyph Plane'
    ref.isVisible = False
    rp = [ref.sketchPoints.add(ref.modelToSketchSpace(P(*p))) for p in
          ((x1, y1, SIDE_DOT_Z), (x2, y2, SIDE_DOT_Z), (x1, y1, SIDE_DOT_Z + 1))]
    pi = fb.constructionPlanes.createInput()
    pi.setByThreePoints(*rp)
    pl = fb.constructionPlanes.add(pi)
    pl.isLightBulbOn = False
    sk = fb.sketches.add(pl)
    sk.name = 'Side Glyphs'
    m = lambda bx, by, u, v: sk.modelToSketchSpace(P(bx + ex * u, by + ey * u, SIDE_DOT_Z + v))
    lines = sk.sketchCurves.sketchLines
    for n, sym in sorted(SIDE_GLYPHS.items()):
        a = across(fret_line(n - 1))[0]
        b = across(fret_line(n))[0]
        bx, by = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        polys, circles = _glyph_shapes(sym, 0.0)
        for poly in polys:
            q = [m(bx, by, u, v) for u, v in poly]
            first = prev = lines.addByTwoPoints(q[0], q[1])
            for p in q[2:]:
                prev = lines.addByTwoPoints(prev.endSketchPoint, p)
            lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)
        for (u, v), r in circles:
            sk.sketchCurves.sketchCircles.addByCenterRadius(m(bx, by, u, v), r * MM)
    ext = fb.features.extrudeFeatures
    inp = ext.createInput(all_profiles(sk), NEW)
    inp.setSymmetricExtent(VI(2 * GLYPH_DEPTH * MM), True)
    fe = ext.add(inp)
    marks = [fe.bodies.item(i) for i in range(fe.bodies.count)]
    tool = paste(fb, board)
    kept = []
    for d in marks:
        kept.append(combine(fb, d, tool, INTERSECT, True).bodies.item(0))
    fb.features.removeFeatures.add(tool)
    for i, d in enumerate(kept):
        combine(fb, board, d, CUT, True)
        d.name = 'Side Dot %d' % (i + 1)               # reuse the glow-marker material rules
    return len(kept)

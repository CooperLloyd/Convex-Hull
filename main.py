# Convex hull
#
# Usage: python main.py [-d] file_of_points
#
# You can press ESC in the window to exit.
#
# You'll need Python 3 and must install these packages:
#
#   PyOpenGL, GLFW


import math
import sys

try:  # PyOpenGL
    from OpenGL.GL import *
except:
    print('Error: PyOpenGL has not been installed.')
    sys.exit(0)

try:  # GLFW
    import glfw
except:
    print('Error: GLFW has not been installed.')
    sys.exit(0)

# Globals

window = None

windowWidth = 800  # window dimensions
windowHeight = 800

minX = None  # range of points
maxX = None
minY = None
maxY = None

r = 0.01  # point radius as fraction of window size

numAngles = 32
thetas = [i / float(numAngles) * 2 * 3.14159 for i in range(numAngles)]  # used for circle drawing

allPoints = []  # list of points

lastKey = None  # last key pressed

discardPoints = False


# Point
#
# A Point stores its coordinates and pointers to the two points beside
# it (CW and CCW) on its hull.  The CW and CCW pointers are None if
# the point is not on any hull.
#
# For debugging, you can set the 'highlight' flag of a point.  This
# will cause the point to be highlighted when it's drawn.

class Point(object):

    def __init__(self, coords):

        self.x = float(coords[0])  # coordinates
        self.y = float(coords[1])

        self.ccwPoint = None  # point CCW of this on hull
        self.cwPoint = None  # point CW of this on hull

        self.highlight = False  # to cause drawing to highlight this point

    def __repr__(self):
        return 'pt(%g,%g)' % (self.x, self.y)

    def drawPoint(self):

        # Highlight with yellow fill

        if self.highlight:
            glColor3f(0.9, 0.9, 0.4)
            glBegin(GL_POLYGON)
            for theta in thetas:
                glVertex2f(self.x + r * math.cos(theta), self.y + r * math.sin(theta))
            glEnd()

        # Outline the point

        glColor3f(0, 0, 0)
        glBegin(GL_LINE_LOOP)
        for theta in thetas:
            glVertex2f(self.x + r * math.cos(theta), self.y + r * math.sin(theta))
        glEnd()

        # Draw edges to next CCW and CW points.

        if self.ccwPoint:
            glColor3f(0, 0, 1)  # blue
            drawArrow(self.x, self.y, self.ccwPoint.x, self.ccwPoint.y)

        if self.cwPoint:
            glColor3f(1, 0, 0)  # red
            drawArrow(self.x, self.y, self.cwPoint.x, self.cwPoint.y)


# Draw an arrow between two points, offset a bit to the right
def drawArrow(x0, y0, x1, y1):
    d = math.sqrt((x1 - x0) * (x1 - x0) + (y1 - y0) * (y1 - y0))

    vx = (x1 - x0) / d  # unit direction (x0,y0) -> (x1,y1)
    vy = (y1 - y0) / d

    vpx = -vy  # unit direction perpendicular to (vx,vy)
    vpy = vx

    xa = x0 + 1.5 * r * vx - 0.4 * r * vpx  # arrow tail
    ya = y0 + 1.5 * r * vy - 0.4 * r * vpy

    xb = x1 - 1.5 * r * vx - 0.4 * r * vpx  # arrow head
    yb = y1 - 1.5 * r * vy - 0.4 * r * vpy

    xc = xb - 2 * r * vx + 0.5 * r * vpx  # arrow outside left
    yc = yb - 2 * r * vy + 0.5 * r * vpy

    xd = xb - 2 * r * vx - 0.5 * r * vpx  # arrow outside right
    yd = yb - 2 * r * vy - 0.5 * r * vpy

    glBegin(GL_LINES)
    glVertex2f(xa, ya)
    glVertex2f(xb, yb)
    glEnd()

    glBegin(GL_POLYGON)
    glVertex2f(xb, yb)
    glVertex2f(xc, yc)
    glVertex2f(xd, yd)
    glEnd()


# Determine whether three points make a left or right turn
LEFT_TURN = 1
RIGHT_TURN = 2
COLLINEAR = 3


def turn(a, b, c):
    det = (a.x - c.x) * (b.y - c.y) - (b.x - c.x) * (a.y - c.y)

    if det > 0:
        return LEFT_TURN
    elif det < 0:
        return RIGHT_TURN
    else:
        return COLLINEAR


# Build a convex hull from a set of point
#
# Use the method described in class


def buildHull(points):
    # Handle base cases of two or three points

    size = len(points)  # Get size of points

    # For cases of two points, set p1's cw and ccw to p2, and vice versa
    if size == 2:
        p1 = points[0]
        p2 = points[1]

        p1.ccwPoint = p2
        p2.ccwPoint = p1
        p1.cwPoint = p2
        p2.cwPoint = p1

    # For cases of three points, use turn() to find the direction of the three points
    # Create a triangle by setting each point's cw and ccw to the other two points
    if size == 3:
        p1 = points[0]
        p2 = points[1]
        p3 = points[2]

        if turn(p2, p1, p3) == RIGHT_TURN:
            p1.cwPoint = p3
            p3.cwPoint = p2
            p2.cwPoint = p1

            p1.ccwPoint = p2
            p2.ccwPoint = p3
            p3.ccwPoint = p1

        if turn(p2, p1, p3) == LEFT_TURN:
            p1.cwPoint = p2
            p3.cwPoint = p1
            p2.cwPoint = p3

            p1.ccwPoint = p3
            p2.ccwPoint = p1
            p3.ccwPoint = p2

    # Handle recursive case
    if size > 3:
        # Recursion by dividing into small groups, either of size two or three
        buildHull(points[0:size // 2])
        buildHull(points[size // 2:])

        # Start merge
        # Set left to be the rightmost point in the left hull and vice versa
        left = points[size // 2 - 1]
        right = points[size // 2]

        # Copies of left and right for walk-down
        leftCopy = left
        rightCopy = right

        # Walk-up
        while turn(left.ccwPoint, left, right) == LEFT_TURN or turn(left, right, right.cwPoint) == LEFT_TURN:
            if turn(left.ccwPoint, left, right) == LEFT_TURN:
                left = left.ccwPoint
            else:
                right = right.cwPoint

        # Walk-down
        while turn(rightCopy.ccwPoint, rightCopy, leftCopy) == LEFT_TURN or turn(rightCopy, leftCopy,
                                                                                 leftCopy.cwPoint) == LEFT_TURN:
            if turn(rightCopy.ccwPoint, rightCopy, leftCopy) == LEFT_TURN:
                rightCopy = rightCopy.ccwPoint
            else:
                leftCopy = leftCopy.cwPoint

        # Finish by setting left and right points to point to each other, same for the copies
        left.cwPoint = right
        right.ccwPoint = left
        leftCopy.ccwPoint = rightCopy
        rightCopy.cwPoint = leftCopy

        completeHull = []  # Blank array to hold the completed hull
        start = points[0]
        while True:
            completeHull.append(start)  # Add current point to hull
            start = start.ccwPoint  # Next point
            if start == points[0]:  # Break once reached start
                break

        for point in points:  # Go through every point
            if point not in completeHull:  # If they aren't in the completedHull[]
                point.cwPoint = None  # Remove their pointers to remove arrows
                point.ccwPoint = None

    # Highlight
    for p in points:
        p.highlight = True
    display(wait=True)

    # Display
    display()


windowLeft = None
windowRight = None
windowTop = None
windowBottom = None


# Set up the display and draw the current image
def display(wait=False):
    global lastKey, windowLeft, windowRight, windowBottom, windowTop

    # Handle any events that have occurred

    glfw.poll_events()

    # Set up window

    glClearColor(1, 1, 1, 0)
    glClear(GL_COLOR_BUFFER_BIT)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    windowLeft = -0.1 * (maxX - minX) + minX
    windowRight = 1.1 * (maxX - minX) + minX
    windowTop = -0.1 * (maxY - minY) + minY
    windowBottom = 1.1 * (maxY - minY) + minY

    glOrtho(windowLeft, windowRight, windowBottom, windowTop, 0, 1)

    # Draw points and hull

    for p in allPoints:
        p.drawPoint()

    # Show window

    glfw.swap_buffers(window)

    # Maybe wait until the user presses 'p' to proceed

    if wait:

        sys.stderr.write('Press "p" to proceed ')
        sys.stderr.flush()

        lastKey = None
        while lastKey != 80:  # wait for 'p'
            glfw.wait_events()
            display()

        sys.stderr.write('\r                     \r')
        sys.stderr.flush()


# Handle keyboard input
def keyCallback(window, key, scancode, action, mods):
    global lastKey

    if action == glfw.PRESS:

        if key == glfw.KEY_ESCAPE:  # quit upon ESC
            sys.exit(0)
        else:
            lastKey = key


# Handle window reshape
def windowReshapeCallback(window, newWidth, newHeight):
    global windowWidth, windowHeight

    windowWidth = newWidth
    windowHeight = newHeight


# Handle mouse click/release
def mouseButtonCallback(window, btn, action, keyModifiers):
    if action == glfw.PRESS:

        # Find point under mouse

        x, y = glfw.get_cursor_pos(window)  # mouse position

        wx = (x - 0) / float(windowWidth) * (windowRight - windowLeft) + windowLeft
        wy = (windowHeight - y) / float(windowHeight) * (windowTop - windowBottom) + windowBottom

        minDist = windowRight - windowLeft
        minPoint = None
        for p in allPoints:
            dist = math.sqrt((p.x - wx) * (p.x - wx) + (p.y - wy) * (p.y - wy))
            if dist < r and dist < minDist:
                minDist = dist
                minPoint = p

        # print point and toggle its highlight

        if minPoint:
            minPoint.highlight = not minPoint.highlight
            print(minPoint)


# Initialize GLFW and run the main event loop

def main():
    global window, allPoints, minX, maxX, minY, maxY, r, discardPoints

    # Check command-line args

    if len(sys.argv) < 2:
        print('Usage: %s filename' % sys.argv[0])
        sys.exit(1)

    args = sys.argv[1:]
    while len(args) > 1:
        print(args)
        if args[0] == '-d':
            discardPoints = not discardPoints
        args = args[1:]

    # Set up window

    if not glfw.init():
        print('Error: GLFW failed to initialize')
        sys.exit(1)

    window = glfw.create_window(windowWidth, windowHeight, "Assignment 1", None, None)

    if not window:
        glfw.terminate()
        print('Error: GLFW failed to create a window')
        sys.exit(1)

    glfw.make_context_current(window)
    glfw.swap_interval(1)
    glfw.set_key_callback(window, keyCallback)
    glfw.set_window_size_callback(window, windowReshapeCallback)
    glfw.set_mouse_button_callback(window, mouseButtonCallback)

    # Read the points

    with open(args[0], 'rb') as f:
        allPoints = [Point(line.split(b' ')) for line in f.readlines()]

    # Get bounding box of points

    minX = min(p.x for p in allPoints)
    maxX = max(p.x for p in allPoints)
    minY = min(p.y for p in allPoints)
    maxY = max(p.y for p in allPoints)

    # Adjust point radius in proportion to bounding box

    if maxX - minX > maxY - minY:
        r *= maxX - minX
    else:
        r *= maxY - minY

    # Sort by increasing x.  For equal x, sort by increasing y.

    allPoints.sort(key=lambda p: (p.x, p.y))

    # Run the code

    buildHull(allPoints)

    # Wait to exit

    while not glfw.window_should_close(window):
        glfw.wait_events()

    glfw.destroy_window(window)
    glfw.terminate()


if __name__ == '__main__':
    main()

from tkinter import *
import numpy as np
from numpy import matrix as M
from math import sin, cos, pi

newline = 0
lineID = 1
line_points = []
controlpoints = []
endpoints = []
lines = []


class Scene:

    @staticmethod
    def transform(shape, matrix):
        ret = []
        for point in shape:
            if len(point) == 2:
                point = list(point)
                point.append(1)
            elif len(point) != 3:
                raise ValueError("Points need to have a length of 2 or 3.")
            p = matrix @ point
            x = p.tolist()[0][0]
            y = p.tolist()[0][1]
            ret.append((x, y))
        return ret

    def __init__(self):
        self.root = None
        self.canvas = canvas
        self.camera = None
        self.selected = None

    def draw_shape(self, shape, curve, control=None, color=(255, 255, 255)):
        if curve:
            for p1, p2 in pairwise_wrap(shape):
                con = (((control.p1 + control.p2) / 2), ((control.p3 + control.p4) / 2))
                return bezier(map(int, p1), con, map(int, p2))
        else:
            for p1, p2 in pairwise_wrap(shape):
                return naive_line(self.canvas, map(int, p1), map(int, p2), color)

    def render(self, single=None, curve=False):
        m = np.linalg.inv(self.camera.transform)
        self.root.apply(m, single, curve)
        return self.canvas

    def is_selected(self, selected_point):
        self.selected = selected_point


class Node:

    def __init__(self, scene):
        self.parent = None
        self.scene = scene
        self.children = []
        self.transform = M([[1, 0, 0],
                            [0, 1, 0],
                            [0, 0, 1]])

    def add_child(self, child):
        self.children.append(child)

    def remove_child(self, child):
        self.children.remove(child)

    def get_Nodes(self):
        return self.children

    def translate(self, x, y):
        tm = translate(x, y)
        self.transform = tm @ self.transform

    def apply(self, transform_matrix, single=None, curve=False):
        new_transform = transform_matrix @ self.transform
        if single:
            new_transform = transform_matrix @ single.node.transform
            return single.apply(new_transform, single, curve)
        else:
            for child in self.children:
                child.apply(new_transform)


class Shape:

    def __init__(self, scene, path, color=(255, 255, 255)):
        self.scene = scene
        self.path = path
        self.color = color

    def apply(self, transform_matrix, curve=False):
        self.scene.draw_shape(transform(self.path, transform_matrix), curve)


class Point:
    def __init__(self, rect, p1, p2, p3, p4, point_type):
        self.rect = rect
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.p4 = p4
        self.point_type = point_type
        self.parent = None

    def setParent(self, parent):
        self.parent = parent

    def setp1(self, value):
        self.p1 = value

    def setp2(self, value):
        self.p2 = value

    def setp3(self, value):
        self.p3 = value

    def setp4(self, value):
        self.p4 = value

    def move(self, x, y):
        canvas.move(self.rect, x, y)


class Line:
    def __init__(self, scene, path, node, color=(255, 255, 255)):
        self.scene = scene
        self.path = path
        self.node = node
        self.color = color
        self.controlpoint = None
        self.startpoint = None
        self.endpoint = None
        self.currentpixels = None
        self.line_type = None

    def apply(self, transform_matrix, single=None, curve=False):
        if curve:
            attlist = self.scene.draw_shape(transform(self.path, transform_matrix), curve, self.controlpoint,
                                            self.color)
            self.currentpixels = attlist
        else:
            attlist = self.scene.draw_shape(transform(self.path, transform_matrix), False, self.color)
            self.controlpoint = attlist[0]
            self.startpoint = attlist[1]
            self.endpoint = attlist[2]
            self.currentpixels = attlist[3]
            self.line_type = attlist[4]

    def setcontrol(self, value):
        self.controlpoint = value

    def setpixels(self, value):
        self.currentpixels = value

    def set_type(self, value):
        self.line_type = value

    def set_path(self, value):
        self.path = value


def callback(event):
    global newline
    global line_points

    if line_btn["bg"] == "green":
        if newline == 0:
            line_points.append((event.x, event.y))
            newline = newline + 1
        else:
            t = Node(scene)
            scene.root.add_child(t)
            new_line = Line(scene, ((line_points[0]), (event.x, event.y)), t)
            t.add_child(new_line)
            line_points = []
            scene.render(new_line)
            new_line.controlpoint.setParent(new_line)
            new_line.startpoint.setParent(new_line)
            new_line.endpoint.setParent(new_line)
            newline = 0
            line_btn["bg"] = "white"

    else:
        if isControlPoint(event.x, event.y) != 0:
            selected = isControlPoint(event.x, event.y)
            scene.selected = selected
            canvas.selecttype = "control"
            canvas.startxy = (event.x, event.y)
        elif isEndPoint(event.x, event.y) != 0:
            selected = isEndPoint(event.x, event.y)
            scene.selected = selected
            canvas.selecttype = "end"
            canvas.startxy = (event.x, event.y)
        else:
            scene.selected = None


def on_drag(event):
    if scene.selected:
        if type(scene.selected) is Point:
            if scene.selected.point_type == "controlpoint":
                dx, dy = event.x - canvas.startxy[0], event.y - canvas.startxy[1]
                line = scene.selected.parent
                canvas.move(scene.selected.rect, dx, dy)
                newcords = canvas.coords(scene.selected.rect)
                scene.selected.setp1(newcords[0])
                scene.selected.setp2(newcords[2])
                scene.selected.setp3(newcords[1])
                scene.selected.setp4(newcords[3])
                canvas.startxy = (event.x, event.y)
                rects = line.currentpixels
                for rect in rects:
                    canvas.delete(rect)
                scene.render(line, True)
            if scene.selected.point_type == "endpoint":
                index = 0
                dx, dy = event.x - canvas.startxy[0], event.y - canvas.startxy[1]
                line = scene.selected.parent
                rects = line.currentpixels
                for rect in rects:
                    canvas.delete(rect)
                canvas.delete(line.startpoint.rect)
                canvas.delete(line.endpoint.rect)
                canvas.delete(line.controlpoint.rect)
                print(line.node)
                line.node.translate(dx, dy)
                canvas.startxy = (event.x, event.y)
                # canvas.move(scene.selected.rect, dx, dy)
                # newcords = canvas.coords(scene.selected.rect)
                # df = (((scene.selected.p1 + scene.selected.p2) / 2), ((scene.selected.p3 + scene.selected.p4) / 2))
                # for i in range(2):
                #    if line.path[i] == df:
                #        index = i
                # scene.selected.setp1(newcords[0])
                # scene.selected.setp2(newcords[2])
                # scene.selected.setp3(newcords[1])
                # scene.selected.setp4(newcords[3])
                # df = (((scene.selected.p1 + scene.selected.p2) / 2), ((scene.selected.p3 + scene.selected.p4) / 2))
                # line.path = list(line.path)
                # line.path[index] = df
                # line.path = tuple(line.path)
                # canvas.startxy = (event.x, event.y)
                # rects = line.currentpixels
                # for rect in rects:
                #    canvas.delete(rect)
                scene.render(line, False)


def isControlPoint(x, y):
    for node in scene.root.children:
        for shape in node.children:
            control = shape.controlpoint
            if control.p2 >= x >= control.p1:
                if control.p4 >= y >= control.p3:
                    return control
    return 0


def isEndPoint(x, y):
    for node in scene.root.children:
        for shape in node.children:
            startPoint = shape.startpoint
            endPoint = shape.endpoint
            if startPoint.p3 >= x >= startPoint.p1:
                if startPoint.p4 >= y >= startPoint.p2:
                    return startPoint
            if endPoint.p3 >= x >= endPoint.p1:
                if endPoint.p4 >= y >= endPoint.p2:
                    return endPoint
    return 0


def naive_line(canvas2, p1, p2, color=255):
    rects = []
    vertical = False
    x1, y1 = p1
    x2, y2 = p2
    _x1 = x1
    _y1 = y1
    _x2 = x2
    _y2 = y2
    controlx = (x1 + x2) / 2
    controly = (y1 + y2) / 2
    if abs(y2 - y1) > abs(x2 - x1):
        vertical = True
        x1, y1 = y1, x1
        x2, y2 = y2, x2
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
    m = (y2 - y1) / (x2 - x1)
    t = y1 - m * x1
    for x in range(x1, x2 + 1):
        y = int(m * x + t)
        if vertical:
            x, y = y, x
        pixel = canvas2.create_rectangle(x, y, x, y)
        rects.append(pixel)
    start = canvas.create_rectangle(_x1 - 3, _y1 - 3, _x1 + 3, _y1 + 3, fill="blue")
    end = canvas.create_rectangle(_x2 - 3, _y2 - 3, _x2 + 3, _y2 + 3, fill="blue")
    startp = Point(start, _x1 - 3, _y1 - 3, _x1 + 3, _y1 + 3, "endpoint")
    endp = Point(end, _x2 - 3, _y2 - 3, _x2 + 3, _y2 + 3, "endpoint")
    control = canvas.create_rectangle(controlx - 5, controly - 5, controlx + 5, controly + 5, fill="red")
    controlpoint = Point(control, controlx - 5, controlx + 5, controly - 5, controly + 5, "controlpoint")
    attlist = [controlpoint, startp, endp, rects, "line"]
    return attlist


def bezier(p0, p1, p2):
    rects = []
    x0, y0 = p0
    x1, y1 = p1
    x2, y2 = p2
    t = 0
    while t < 1:
        p0_x = pow((1 - t), 2) * x0
        p0_y = pow((1 - t), 2) * y0
        p1_x = 2 * (1 - t) * t * x1
        p1_y = 2 * (1 - t) * t * y1
        p2_x = t ** 2 * x2
        p2_y = t ** 2 * y2
        rect = canvas.create_rectangle(p0_x + p1_x + p2_x, p0_y + p1_y + p2_y, p0_x + p1_x + p2_x, p0_y + p1_y + p2_y)
        rects.append(rect)
        t = t + 0.001
    return rects


def pairwise_wrap(l):
    l = iter(l)
    first = next(l, None)
    prev = first
    while o := next(l, False):
        yield (prev, o)
        prev = o
    yield prev, first


def changeToLine():
    line_btn["bg"] = "green"


def translate(tx, ty, p=None):
    T = M([[1, 0, tx],
           [0, 1, ty],
           [0, 0, 1]])
    if p is None:
        return T
    else:
        p = list(p)
        p.append(1)
        p = T @ p
        x = p.tolist()[0][0]
        y = p.tolist()[0][1]
        return ((x, y))


def rotate(angle, p=None):
    # degree to radian
    angle = angle / (180 / pi)
    R = M([[cos(angle), -sin(angle), 0],
           [sin(angle), cos(angle), 0],
           [0, 0, 1]])
    if p is None:
        return R
    else:
        p = list(p)
        p.append(1)
        p = R @ p
        x = p.tolist()[0][0]
        y = p.tolist()[0][1]
        return ((x, y))


def scale(sx, sy, p=None):
    S = M([[sx, 0, 0],
           [0, sy, 0],
           [0, 0, 1]])
    if p is None:
        return S
    else:
        p = list(p)
        p.append(1)
        p = S @ p
        x = p.tolist()[0][0]
        y = p.tolist()[0][1]
        return ((x, y))


def transform(shape, matrix):
    ret = []
    for point in shape:
        if len(point) == 2:
            point = list(point)
            point.append(1)
        elif len(point) != 3:
            raise ValueError("Points need to have a length of 2 or 3.")
        p = matrix @ point
        x = p.tolist()[0][0]
        y = p.tolist()[0][1]
        ret.append((x, y))
    return ret


root = Tk()
root.title("miniscape")
root.geometry("700x700")
canvas = Canvas(root, width=600, height=600, bg="white")
canvas.pack(pady=50)
line_btn = Button(root, text="Linie", width=10, height=2, command=changeToLine)
line_btn.place(x=550, y=70)
canvas.bind("<B1-Motion>", on_drag)
canvas.bind("<Button-1>", callback)

scene = Scene()
scene.root = Node(scene)

cam = Node(scene)
scene.camera = cam

root.mainloop()

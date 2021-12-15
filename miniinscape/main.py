import math
import sys
import tkinter.filedialog
from tkinter import *
from tkinter.colorchooser import askcolor
import numpy as np
from numpy import matrix as M
from math import sin, cos, pi
import json

newline = 0
newcircle = 0
lineID = 1
line_points = []
circle_points = []
controlpoints = []
endpoints = []
lines = []
polygonhelper = []
newpol = 0
finalpoint = None
finalspecialpoint = None
hidden = False
camerastartx = []
chosen_color = "black"


class Scene:

    @staticmethod
    def transform(shape, matrix):
        ret = []
        for point in shape:
            if len(point) == 2 or len(point) == 1:
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

    def hide_points(self):
        self.root.hide()

    def show_point(self):
        self.root.show()

    def clear(self):
        self.root.clear()

    def draw_shape(self, shape, curve, control=None, color=(255, 255, 255)):
        if curve:
            for p1, p2 in pairwise_wrap(shape):
                con = (((control.p1 + control.p2) / 2), ((control.p3 + control.p4) / 2))
                return bezier(map(int, p1), con, map(int, p2), color)
        else:
            for p1, p2 in pairwise_wrap(shape):
                return naive_line(self.canvas, map(int, p1), map(int, p2), color)

    def draw_circle(self, center, radius, color="black"):
        return bezier_circle(center, radius)

    def render(self, single=None, curve=False):
        if single is not None:
            curve = single.curve
        m = np.linalg.inv(self.camera.transform)
        self.root.apply(m, single, curve)
        return self.canvas

    def is_selected(self, selected_point):
        self.selected = selected_point

    def get_all(self):
        objects = []
        for node in self.root.children:
            for child in node.children:
                objects.append(child)
        return objects


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
            return single.apply(new_transform, curve)
        else:
            for child in self.children:
                child.apply(new_transform)

    def hide(self):
        for child in self.children:
            child.hide()

    def show(self):
        for child in self.children:
            child.show()

    def clear(self):
        self.children = []
        for child in self.children:
            child.clear()

    def delete_on_canvas(self):
        for child in self.children:
            child.delete()

    def detranslate(self):
        self.transform = M([[1, 0, 0],
                            [0, 1, 0],
                            [0, 0, 1]])


class Shape:

    def __init__(self, scene, path, node, color=(255, 255, 255)):
        self.scene = scene
        self.path = path
        self.color = color
        self.node = node
        self.fill = None
        self.curve = False

    def apply(self, transform_matrix, curve=False):
        global finalpoint
        global finalspecialpoint
        if new_polygon(self.path):
            for i in range(len(self.path)):
                self.path[i].apply(transform_matrix, self.path[i].curve)
                self.path[i].rendered = True
                canvas.delete(self.path[i].controlpoint.rect)
                self.path[i].controlpoint = None
                canvas.delete(self.path[i].endpoint.rect)
            # self.fill = scanline_fill(self, 300, 300, "red")
            # fill(self.fill)
            for i in range(len(self.path)):
                if i < len(self.path) - 1:
                    self.path[i].endpoint = self.path[i + 1].startpoint
                    self.path[i].endpoint.setParent([self.path[i], self.path[i + 1]])
                else:
                    self.path[i].endpoint = self.path[0].startpoint
                    self.path[i].endpoint.setParent([self.path[i], self.path[0]])

        else:
            index = -1
            special = False
            for i in range(len(self.path)):
                if self.path[i].rendered is False:
                    self.path[i].apply(transform_matrix, self.path[i].curve)
                    self.path[i].rendered = True
                    finalpoint = self.path[i].endpoint.rect
                    canvas.delete(self.path[i].controlpoint.rect)
                    self.path[i].controlpoint = None

                    if i == 0:
                        if self.path[1].rendered is False:
                            canvas.delete(self.path[0].endpoint.rect)
                        if self.path[len(self.path) - 1].rendered is False:
                            special = True
                            finalspecialpoint = self.path[0].endpoint.rect
                    else:
                        if i < len(self.path) - 1:
                            if self.path[i + 1].rendered is False:
                                canvas.delete(self.path[i].endpoint.rect)
                                index = i + 1
            # newfill = scanline_fill(self, 300, 300, "red")
            # changeFill(self.fill, newfill)
            # self.fill = newfill
            if special:
                canvas.delete(self.path[len(self.path) - 1].endpoint.rect)
            for i in range(len(self.path)):
                if i < len(self.path) - 1:
                    self.path[i].endpoint = self.path[i + 1].startpoint
                    self.path[i].endpoint.setParent([self.path[i], self.path[i + 1]])
                else:
                    self.path[i].endpoint = self.path[0].startpoint
                    self.path[i].endpoint.setParent([self.path[i], self.path[0]])

    def hide(self):
        for line in self.path:
            canvas.delete(line.endpoint.rect)
            line.endpoint.dragable = False

    def show(self):
        for line in self.path:
            rect = canvas.create_rectangle(line.endpoint.p1, line.endpoint.p2, line.endpoint.p3, line.endpoint.p4,
                                           fill="blue")
            line.endpoint.rect = rect
            line.endpoint.dragable = True

    def clear(self):
        for line in self.path:
            line.clear()

    def delete(self):
        for line in self.path:
            canvas.delete(line.endpoint.rect)
            for rect in line.currentpixels:
                canvas.delete(rect)


class Point:
    def __init__(self, rect, p1, p2, p3, p4, point_type):
        self.rect = rect
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.p4 = p4
        self.point_type = point_type
        self.dragable = True
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
    def __init__(self, scene, path, node, curve, color=(255, 255, 255)):
        self.scene = scene
        self.path = path
        self.node = node
        self.curve = curve
        self.color = color
        self.rendered = False
        self.parent = None
        self.controlpoint = None
        self.startpoint = None
        self.endpoint = None
        self.currentpixels = None
        self.line_type = None

    def apply(self, transform_matrix, curve=False):
        if curve:
            x = int(transform_matrix[0, 2])
            y = int(transform_matrix[1, 2])
            self.controlpoint.p1 = self.controlpoint.p1 + x
            self.controlpoint.p2 = self.controlpoint.p2 + x
            self.controlpoint.p3 = self.controlpoint.p3 + y
            self.controlpoint.p4 = self.controlpoint.p4 + y
            self.path = transform(self.path, transform_matrix)
            attlist = self.scene.draw_shape(self.path, curve, self.controlpoint,
                                            self.color)

        else:
            self.path = transform(self.path, transform_matrix)
            attlist = self.scene.draw_shape(self.path, False, None, self.color)

        self.controlpoint = attlist[0]
        self.controlpoint.setParent([self])
        self.startpoint = attlist[1]
        self.startpoint.setParent([self])
        self.endpoint = attlist[2]
        self.endpoint.setParent([self])
        self.currentpixels = attlist[3]
        self.line_type = attlist[4]

    def setParent(self, value):
        self.parent = value

    def setStart(self, value):
        self.startpoint = value

    def setcontrol(self, value):
        self.controlpoint = value

    def setpixels(self, value):
        self.currentpixels = value

    def set_type(self, value):
        self.line_type = value

    def set_path(self, value):
        self.path = value

    def set_curve(self, value):
        self.curve = value

    def hide(self):
        canvas.delete(self.endpoint.rect)
        self.endpoint.dragable = False
        canvas.delete(self.startpoint.rect)
        self.startpoint.dragable = False
        canvas.delete(self.controlpoint.rect)
        self.controlpoint.dragable = False

    def show(self):
        endpoint = self.endpoint
        end = canvas.create_rectangle(endpoint.p1, endpoint.p2, endpoint.p3, endpoint.p4, fill="blue")
        self.endpoint.rect = end
        self.endpoint.dragable = True
        startpoint = self.startpoint
        start = canvas.create_rectangle(startpoint.p1, startpoint.p2, startpoint.p3, startpoint.p4, fill="blue")
        self.startpoint.rect = start
        self.startpoint.dragable = True
        controlpoint = self.controlpoint
        control = canvas.create_rectangle(controlpoint.p1, controlpoint.p3, controlpoint.p2, controlpoint.p4,
                                          fill="red")
        self.controlpoint.rect = control
        self.controlpoint.dragable = True

    def clear(self):
        self.scene = None
        self.path = None
        self.node = None
        self.curve = None
        self.color = None
        self.rendered = False
        self.parent = None
        self.controlpoint = None
        self.startpoint = None
        self.endpoint = None
        self.currentpixels = None
        self.line_type = None

    def delete(self):
        canvas.delete(self.endpoint.rect)
        canvas.delete(self.startpoint.rect)
        canvas.delete(self.controlpoint.rect)
        for rect in self.currentpixels:
            canvas.delete(rect)


class Circle:
    def __init__(self, scene, node, center, radius, color="black"):
        self.scene = scene
        self.node = node
        self.center = center
        self.radius = radius
        self.color = color
        self.curve = False
        self.controlpoint = None
        self.middlepoint = None
        self.currentpixels = None

    def apply(self, transform_matrix, curve):
        attlist = self.scene.draw_circle(self.center, self.radius, self.color)
        self.controlpoint = attlist[0]
        self.controlpoint.setParent(self)
        self.middlepoint = attlist[1]
        self.middlepoint.setParent(self)
        self.currentpixels = attlist[2]

    def hide(self):
        canvas.delete(self.middlepoint.rect)
        self.middlepoint.dragable = False
        canvas.delete(self.controlpoint.rect)
        self.controlpoint.dragable = False

    def show(self):
        middlepoint = self.middlepoint
        center = canvas.create_rectangle(middlepoint.p1, middlepoint.p2, middlepoint.p3, middlepoint.p4, fill="blue")
        self.middlepoint.rect = center
        self.middlepoint.dragable = True
        controlpoint = self.controlpoint
        control = canvas.create_rectangle(controlpoint.p1, controlpoint.p3, controlpoint.p2, controlpoint.p4,
                                          fill="red")
        self.controlpoint.rect = control
        self.controlpoint.dragable = True


def callback(event):
    global newline
    global newpol
    global line_points
    global lines
    global polygonhelper
    if line_btn["bg"] == "green":
        if newline == 0:
            line_points.append((event.x, event.y))
            newline = newline + 1
        else:
            t = Node(scene)
            scene.root.add_child(t)
            new_line = Line(scene, ((line_points[0]), (event.x, event.y)), t, False, chosen_color)
            t.add_child(new_line)
            line_points = []
            scene.render(new_line)
            new_line.controlpoint.setParent(new_line)
            new_line.startpoint.setParent(new_line)
            new_line.endpoint.setParent(new_line)
            newline = 0
            line_btn["bg"] = "white"
            scene.selected = None
    if pol_btn["bg"] == "green":
        if newpol == 0:
            newline = 0
            line_points = []
            scene.selected = None
            line_points.append((event.x, event.y))
            rect = canvas.create_rectangle(event.x - 5, event.y - 5, event.x + 5, event.y + 5, outline="green")
            polygonhelper.append(rect)
            newpol = newpol + 1
        else:
            # t = Node(scene)
            scene.selected = None
            new_polline = Line(scene, ((line_points[len(line_points) - 1]), (event.x, event.y)), None, False,
                               chosen_color)
            rect = canvas.create_rectangle(event.x - 3, event.y - 3, event.x + 3, event.y + 3, outline="orange")
            polygonhelper.append(rect)
            lines.append(new_polline)
            # t.add_child(new_polline)
            line_points.append((event.x, event.y))
            # scene.root.add_child(t)
        if len(line_points) > 1:
            if line_points[0][0] - 5 < event.x < line_points[0][0] + 5 and line_points[0][1] - 5 < event.y < \
                    line_points[0][1] + 5:
                t = Node(scene)
                shape = Shape(scene, lines, t)
                for rect in polygonhelper:
                    canvas.delete(rect)
                for line in lines:
                    line.node = t
                    line.parent = shape
                lines[len(lines) - 1].path = list(lines[len(lines) - 1].path)
                lines[len(lines) - 1].path[1] = lines[0].path[0]
                lines[len(lines) - 1].path = tuple(lines[len(lines) - 1].path)
                t.add_child(shape)
                scene.root.add_child(t)
                scene.render(shape)
                pol_btn["bg"] = "white"
                polygonhelper = []
                line_points = []
                lines = []
                newpol = 0
            # for line in lines:
            #   scene.render(line)
            # for i in range(len(lines)-1):
            #   lines[i+1].setStart(lines[i].endpoint)
            #  scene.render(lines[i])

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
                canvas.delete(finalpoint)
                canvas.delete(finalspecialpoint)
                dx, dy = event.x - canvas.startxy[0], event.y - canvas.startxy[1]
                if type(scene.selected.parent) is list:
                    line = scene.selected.parent[0]
                else:
                    line = scene.selected.parent
                line.set_curve(True)
                line.rendered = False
                scene.selected.setp1(scene.selected.p1 + dx)
                scene.selected.setp2(scene.selected.p2 + dx)
                scene.selected.setp3(scene.selected.p3 + dy)
                scene.selected.setp4(scene.selected.p4 + dy)
                line.controlpoint.setp1(scene.selected.p1)
                line.controlpoint.setp2(scene.selected.p2)
                line.controlpoint.setp3(scene.selected.p3)
                line.controlpoint.setp4(scene.selected.p4)
                rects = line.currentpixels
                for rect in rects:
                    canvas.delete(rect)
                canvas.delete(line.startpoint.rect)
                canvas.delete(line.endpoint.rect)
                canvas.delete(line.controlpoint.rect)
                canvas.startxy = (event.x, event.y)
                if line.parent is not None:
                    scene.render(line.parent)
                else:
                    scene.render(line)
            if scene.selected.point_type == "endpoint":
                canvas.delete(finalpoint)
                canvas.delete(finalspecialpoint)
                dx, dy = event.x - canvas.startxy[0], event.y - canvas.startxy[1]
                if type(scene.selected.parent) is not list:
                    linelist = [scene.selected.parent]
                else:
                    linelist = scene.selected.parent
                for parent in linelist:
                    parent.rendered = False
                    rects = parent.currentpixels
                    for i in range(2):
                        if parent.path[i] == (scene.selected.p3 - 3, scene.selected.p4 - 3):
                            parent.path = list(parent.path)
                            parent.path[i] = (scene.selected.p3 - 3 + dx, scene.selected.p4 - 3 + dy)
                            parent.path = tuple(parent.path)
                    for rect in rects:
                        canvas.delete(rect)
                    canvas.delete(parent.startpoint.rect)
                    canvas.delete(parent.endpoint.rect)
                    if parent.controlpoint is not None:
                        canvas.delete(parent.controlpoint.rect)

                scene.selected.setp1(scene.selected.p1 + dx)
                scene.selected.setp2(scene.selected.p2 + dy)
                scene.selected.setp3(scene.selected.p3 + dx)
                scene.selected.setp4(scene.selected.p4 + dy)

                canvas.startxy = (event.x, event.y)

                if len(linelist) > 1:
                    scene.render(scene.selected.parent[0].parent)
                else:
                    scene.render(linelist[0])

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


def circle_callback(event):
    global newcircle
    global circle_points
    if isControlPoint(event.x, event.y) != 0:
        scene.selected = isControlPoint(event.x, event.y)
        canvas.startxy = (event.x, event.y)
    elif isCenterPoint(event.x, event.y) != 0:
        scene.selected = isCenterPoint(event.x, event.y)
        canvas.startxy = (event.x, event.y)
    else:
        if newcircle == 0:
            circle_points.append((event.x, event.y))
            newcircle = newcircle + 1
        else:
            circle_points.append((event.x, event.y))
            radius = ((((circle_points[1][0] - circle_points[0][0]) ** 2) + (
                    (circle_points[1][1] - circle_points[0][1]) ** 2)) ** 0.5)
            t = Node(scene)
            scene.root.add_child(t)
            new_circle = Circle(scene, t, circle_points[0], radius)
            t.add_child(new_circle)
            newcircle = 0
            circle_points = []
            scene.render(new_circle)


def circle_drag(event):
    if scene.selected:
        if type(scene.selected) is Point:
            if scene.selected.point_type == "controlpoint":
                dx, dy = event.x - canvas.startxy[0], event.y - canvas.startxy[1]
                circle = scene.selected.parent
                scene.selected.setp1(scene.selected.p1 + dx)
                scene.selected.setp2(scene.selected.p2 + dx)
                scene.selected.setp3(scene.selected.p3 + dy)
                scene.selected.setp4(scene.selected.p4 + dy)
                circle.radius = ((((circle.middlepoint.p1 + 5 - scene.selected.p1 + 5) ** 2) + (
                        (circle.middlepoint.p2 + 5 - scene.selected.p3 + 5) ** 2)) ** 0.5)
                rects = circle.currentpixels
                for rect in rects:
                    canvas.delete(rect)
                canvas.delete(circle.middlepoint.rect)
                canvas.delete(circle.controlpoint.rect)
                canvas.startxy = (event.x, event.y)
                scene.render(circle)
            if scene.selected.point_type == "centerpoint":
                dx, dy = event.x - canvas.startxy[0], event.y - canvas.startxy[1]
                circle = scene.selected.parent
                scene.selected.setp1(scene.selected.p1 + dx)
                scene.selected.setp2(scene.selected.p2 + dx)
                scene.selected.setp3(scene.selected.p3 + dy)
                scene.selected.setp4(scene.selected.p4 + dy)
                circle.controlpoint.setp1(circle.controlpoint.p1 + dx)
                circle.controlpoint.setp2(circle.controlpoint.p2 + dy)
                circle.controlpoint.setp3(circle.controlpoint.p3 + dx)
                circle.controlpoint.setp4(circle.controlpoint.p4 + dy)
                circle.center = (circle.center[0] + dx, circle.center[1] + dy)
                rects = circle.currentpixels
                for rect in rects:
                    canvas.delete(rect)
                canvas.delete(circle.middlepoint.rect)
                canvas.delete(circle.controlpoint.rect)
                canvas.startxy = (event.x, event.y)
                scene.render(circle)


def isCenterPoint(x, y):
    for node in scene.root.children:
        for shape in node.children:
            if type(shape) is Circle:
                center = shape.middlepoint
                if center.p3 >= x >= center.p1:
                    if center.p4 >= y >= center.p2:
                        if center.dragable:
                            return center
    return 0


def isControlPoint(x, y):
    for node in scene.root.children:
        for shape in node.children:
            if type(shape) is Shape:
                for line in shape.path:
                    if line.controlpoint is not None:
                        control = line.controlpoint
                        if control.p2 >= x >= control.p1:
                            if control.p4 >= y >= control.p3:
                                if control.dragable:
                                    return control
            else:
                control = shape.controlpoint
                if control.p2 >= x >= control.p1:
                    if control.p4 >= y >= control.p3:
                        if control.dragable:
                            return control
    return 0


def isEndPoint(x, y):
    for node in scene.root.children:
        for shape in node.children:
            if type(shape) is Shape:
                for line in shape.path:
                    startPoint = line.startpoint
                    endPoint = line.endpoint
                    if startPoint.p3 >= x >= startPoint.p1:
                        if startPoint.p4 >= y >= startPoint.p2:
                            if startPoint.dragable:
                                return startPoint

                    if endPoint.p3 >= x >= endPoint.p1:
                        if endPoint.p4 >= y >= endPoint.p2:
                            if endPoint.dragable:
                                return endPoint
            elif type(shape) is Line:
                startPoint = shape.startpoint
                endPoint = shape.endpoint
                if startPoint.p3 >= x >= startPoint.p1:
                    if startPoint.p4 >= y >= startPoint.p2:
                        if startPoint.dragable:
                            return startPoint
                if endPoint.p3 >= x >= endPoint.p1:
                    if endPoint.p4 >= y >= endPoint.p2:
                        if endPoint.dragable:
                            return endPoint
    return 0


def naive_line(canvas2, p1, p2, color):
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
        pixel = canvas2.create_rectangle(x, y, x, y, outline=color)
        rects.append(pixel)
    start = canvas.create_rectangle(_x1 - 3, _y1 - 3, _x1 + 3, _y1 + 3, fill="blue")
    end = canvas.create_rectangle(_x2 - 3, _y2 - 3, _x2 + 3, _y2 + 3, fill="blue")

    startp = Point(start, _x1 - 3, _y1 - 3, _x1 + 3, _y1 + 3, "endpoint")
    endp = Point(end, _x2 - 3, _y2 - 3, _x2 + 3, _y2 + 3, "endpoint")
    control = canvas.create_rectangle(controlx - 5, controly - 5, controlx + 5, controly + 5, fill="red")
    controlpoint = Point(control, controlx - 5, controlx + 5, controly - 5, controly + 5, "controlpoint")
    attlist = [controlpoint, startp, endp, rects, "line"]
    return attlist


def bezier(p0, p1, p2, color):
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
        rect = canvas.create_rectangle(p0_x + p1_x + p2_x, p0_y + p1_y + p2_y, p0_x + p1_x + p2_x, p0_y + p1_y + p2_y,
                                       outline=color)
        rects.append(rect)
        t = t + 0.002

    start = canvas.create_rectangle(x0 - 3, y0 - 3, x0 + 3, y0 + 3, fill="blue")
    end = canvas.create_rectangle(x2 - 3, y2 - 3, x2 + 3, y2 + 3, fill="blue")
    startp = Point(start, x0 - 3, y0 - 3, x0 + 3, y0 + 3, "endpoint")
    endp = Point(end, x2 - 3, y2 - 3, x2 + 3, y2 + 3, "endpoint")
    control = canvas.create_rectangle(x1 - 5, y1 - 5, x1 + 5, y1 + 5, fill="red")
    controlpoint = Point(control, x1 - 5, x1 + 5, y1 - 5, y1 + 5, "controlpoint")
    attlist = [controlpoint, startp, endp, rects, "curve"]
    return attlist


def bezier_circle(p0, r):
    rects = []
    x0, y0 = p0
    d = 3 - (2 * r)
    x = 0
    y = r
    points = draw_circle(x0, y0, x, y)
    for point in points:
        rects.append(point)
    while y >= x:
        x = x + 1
        if d > 0:
            y = y - 1
            d = d + 4 * (x - y) + 10
        else:
            d = d + 4 * x + 6
        points = draw_circle(x0, y0, x, y)
        for point in points:
            rects.append(point)
    controlp = canvas.create_rectangle(x0 - 5, (y0 - r) - 5, x0 + 5, (y0 - r) + 5, fill="red")
    centerp = canvas.create_rectangle(x0 - 5, y0 - 5, x0 + 5, y0 + 5, fill="blue")
    controlpoint = Point(controlp, x0 - 5, x0 + 5, (y0 - r) - 5, (y0 - r) + 5, "controlpoint")
    centerpoint = Point(centerp, x0 - 5, y0 - 5, x0 + 5, y0 + 5, "centerpoint")
    attlist = [controlpoint, centerpoint, rects]
    return attlist


def draw_circle(xc, yc, x, y):
    rect1 = canvas.create_rectangle(xc + x, yc + y, xc + x, yc + y)
    rect2 = canvas.create_rectangle(xc - x, yc + y, xc - x, yc + y)
    rect3 = canvas.create_rectangle(xc + x, yc - y, xc + x, yc - y)
    rect4 = canvas.create_rectangle(xc - x, yc - y, xc - x, yc - y)
    rect5 = canvas.create_rectangle(xc + y, yc + x, xc + y, yc + x)
    rect6 = canvas.create_rectangle(xc - y, yc + x, xc - y, yc + x)
    rect7 = canvas.create_rectangle(xc + y, yc - x, xc + y, yc - x)
    rect8 = canvas.create_rectangle(xc - y, yc - x, xc - y, yc - x)
    return rect1, rect2, rect3, rect4, rect5, rect6, rect7, rect8


def scanline_fill(polygon, px, py, color):
    allcoords = []
    newcoords = set()
    ymin = 700
    ymax = 0
    xmin = 700
    xmax = 0
    for line in polygon.path:
        for pixel in line.currentpixels:
            allcoords.append((int(canvas.coords(pixel)[0]), int(canvas.coords(pixel)[1])))
            if int(canvas.coords(pixel)[0]) < xmin:
                xmin = int(canvas.coords(pixel)[0])
            if int(canvas.coords(pixel)[0]) > xmax:
                xmax = int(canvas.coords(pixel)[0])
            if int(canvas.coords(pixel)[1]) < ymin:
                ymin = int(canvas.coords(pixel)[1])
            if int(canvas.coords(pixel)[1]) > ymax:
                ymax = int(canvas.coords(pixel)[1])

        for i in range(7):
            for z in range(7):
                allcoords.append((line.endpoint.p1 + i, line.endpoint.p2 + z))

    toFill = set()
    toFill.add((300, 300))
    while not len(toFill) == 0:
        (x, y) = toFill.pop()
        if (x, y) in allcoords or (x, y) in newcoords:
            continue
        if x < xmin or x > xmax or y < ymin or y > ymax:
            continue
        newcoords.add((x, y))
        toFill.add((x - 1, y))
        toFill.add((x + 1, y))
        toFill.add((x, y - 1))
        toFill.add((x, y + 1))
    return newcoords


def fill(coords):
    for coord in coords:
        canvas.create_rectangle(coord[0], coord[1], coord[0], coord[1], outline="red")


def changeFill(oldfill, newfill):
    erasepoints = oldfill - newfill
    addpoints = newfill - oldfill
    for point in erasepoints:
        pixel = canvas.find_closest(point[0], point[1])
        canvas.delete(pixel)
    for point in addpoints:
        canvas.create_rectangle(point[0], point[1], point[0], point[1], outline="red")


def pairwise_wrap(l):
    l = iter(l)
    first = next(l, None)
    prev = first
    while o := next(l, False):
        yield (prev, o)
        prev = o
    yield prev, first


def changeToLine():
    if line_btn["bg"] == "white":
        line_btn["bg"] = "green"
        pol_btn["bg"] = "white"
    else:
        line_btn["bg"] = "white"


def point_state(event):
    global hidden
    if not hidden:
        scene.hide_points()
        hidden = True
    else:
        scene.show_point()
        hidden = False


def clear_canvas(event):
    canvas.delete("all")
    scene.clear()


def set_startxy(event):
    global camerastartx
    camerastartx = (event.x, event.y)


def move_canvas(event):
    global camerastartx
    dx, dy = event.x - camerastartx[0], event.y - camerastartx[1]
    for node in scene.root.children:
        node.translate(dx, dy)
        node.delete_on_canvas()
        for child in node.children:
            if type(child) is Shape:
                for line in child.path:
                    line.rendered = False
            scene.render(child)
        node.detranslate()

    camerastartx = (event.x, event.y)


def new_polygon(pol_lines):
    for line in pol_lines:
        if line.rendered:
            return False
    return True


def changeToPolygon():
    if pol_btn["bg"] == "white":
        pol_btn["bg"] = "green"
        line_btn["bg"] = "white"
    else:
        pol_btn["bg"] = "white"


def change_color():
    global chosen_color
    colors = askcolor(title="Tkinter Color Chooser")
    chosen_color = colors[1]


def save_scene():
    filesaver = tkinter.filedialog.asksaveasfile(filetypes=[('Text Documents', '*txt')], defaultextension=".txt")
    save_json(filesaver)


def save_json(file):
    with open(file.name, 'w') as f:
        for item in scene.get_all():
            if type(item) is Line:
                print(json.dumps({
                    'type': "line",
                    'path': item.path,
                    'curve': item.curve,
                    'color': item.color,
                }), file=file)


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
line_btn = Button(root, text="Linie", width=10, height=2, bg="white", command=changeToLine)
line_btn.place(x=450, y=70)
pol_btn = Button(root, text="Polygon", width=10, height=2, bg="white", command=changeToPolygon)
pol_btn.place(x=550, y=70)
color_btn = Button(root, text="color", width=10, height=2, command=change_color)
color_btn.place(x=500, y=150)
save_btn = Button(root, text="save", width=10, height=2, command=lambda: save_scene())
save_btn.place(x=450, y=230)
# load_btn = Button(root, text="load", width=10, height=2, command=load_scene)
# load_btn.place(x=550, y=230)
canvas.bind("<B1-Motion>", on_drag)
canvas.bind("<Button-1>", callback)
canvas.master.bind("x", point_state)
canvas.master.bind("c", clear_canvas)
canvas.bind("<B2-Motion>", move_canvas)
canvas.bind("<Button-2>", set_startxy)
canvas.bind("<Button-3>", circle_callback)
canvas.bind("<B3-Motion>", circle_drag)

scene = Scene()
scene.root = Node(scene)

rect = ((0, 0), (0, 100), (100, 100), (100, 0))

cam = Node(scene)

scene.camera = cam

root.mainloop()

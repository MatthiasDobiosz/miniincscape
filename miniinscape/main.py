from tkinter import *
import numpy as np

root = Tk()
root.title("miniscape")
root.geometry("500x500")
canvas = Canvas(root, width=400, height=400, bg="white")
canvas.pack(pady=50)
newline = 0
lineID = 1
line_points = []
controlpoints = []


def clicked(event):
    print("lol")


def drag(event):
    component = event.widget
    locx, locy = component.winfo_x(), component.winfo_y()
    w, h = canvas.winfo_width(), canvas.winfo_height()
    mx, my = component.winfo_width(), component.winfo_height()
    xpos = (locx + event.x) - 15
    ypos = (locy + event.y) - int(my / 2)

    for point in controlpoints:
        if isControlPoint(event.x, event.y) != 0:
            canvas.move(isControlPoint(event.x, event.y)[1], 1, 1)
            # update controlpoints


def callback(event):
    global newline
    global line_points
    if isControlPoint(event.x, event.y):
        print("ja")
    elif newline == 0:
        print("nein")
        line_points.append((event.x, event.y))
        newline = newline + 1
    else:
        bresenham(line_points[0], (event.x, event.y))
        line_points = []
        newline = 0
    print("clicked at", event.x, event.y)


def isControlPoint(x, y):
    for point in controlpoints:
        if point[2][1] >= x >= point[2][0]:
            if point[2][3] >= y >= point[2][2]:
                return point
    return 0


canvas.bind("<Key>", clicked)
canvas.bind("<B1-Motion>", drag)
canvas.bind("<Button-1>", callback)


def bresenham(p1, p2):
    global lineID, controlpoints
    x1, y1 = p1
    x2, y2 = p2
    controlx = (x1 + x2) / 2
    controly = (y1 + y2) / 2
    dx = x2 - x1
    dy = y2 - y1
    vertical = False
    if abs(dy) > abs(dx):
        vertical = True
        x1, y1 = y1, x1
        x2, y2 = y2, x2
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1

    control = canvas.create_rectangle(controlx - 5, controly - 5, controlx + 5, controly + 5, fill="red")

    dx = x2 - x1
    dy = y2 - y1
    error = (2 * dy) - dx
    yi = 1
    if dy < 0:
        yi = -1
        dy = -dy
    y = y1
    for x in range(x1, x2 + 1):
        if vertical:
            canvas.create_rectangle(y, x, y, x)
        else:
            canvas.create_rectangle(x, y, x, y)

        if error > 0:
            y = y + yi
            error = error + (2 * (dy - dx))
        else:
            error = error + 2 * dy
    lineID = lineID + 1
    controlpoints.append(((p1, p2), control, (controlx - 5, controlx + 5, controly - 5, controly + 5)))
    print(controlpoints)


root.mainloop()

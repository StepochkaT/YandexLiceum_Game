import math
import heapq
import os
import sys

import pygame


def euclidean_distance(p1, p2):
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def obstacle_intersect_by_line(x1, y1, x2, y2, points, graph_points):
    intersect_points = []
    ret_points = []
    for i in range(-1, len(points) - 1, 1):
        point3, point4 = points[i], points[i + 1]
        intersect = find_intersection(int(x1), int(y1), int(x2), int(y2), int(point3[0]), int(point3[1]),
                                      int(point4[0]), int(point4[1]))
        if intersect:
            ret_points.append(intersect)
            intersect_points.append(intersect[0])
    intersect_points = [item for item in intersect_points if isinstance(item, tuple)]
    if len(intersect_points) <= 2 and all([j in graph_points for j in intersect_points]):
        return True
    return ret_points


def find_intersection(x1, y1, x2, y2, x3, y3, x4, y4):
    def determinant(a, b, c, d):
        return a * d - b * c

    def is_between(a, b, c):
        return min(a, b) <= c <= max(a, b)

    a1 = y2 - y1
    b1 = x1 - x2
    c1 = a1 * x1 + b1 * y1

    a2 = y4 - y3
    b2 = x3 - x4
    c2 = a2 * x3 + b2 * y3

    det = determinant(a1, b1, a2, b2)

    if det == 0:
        return False

    x = determinant(c1, b1, c2, b2) / det
    y = determinant(a1, c1, a2, c2) / det

    if (is_between(x1, x2, x) and is_between(y1, y2, y) and
            is_between(x3, x4, x) and is_between(y3, y4, y)):
        return (x, y), (x3, y3), (x4, y4)
    return False


def find_path_in_graph(graph, start, goal):
    queue = [(0, start, [])]
    visited = set()

    while queue:
        cost, node, path = heapq.heappop(queue)

        if node in visited:
            continue
        visited.add(node)

        path = path + [node]

        if node == goal:
            return cost, path

        for neighbor, edge_cost in graph.get(node, []):
            if neighbor not in visited:
                heapq.heappush(queue, (cost + edge_cost, neighbor, path))

    return float("inf"), []


def load_image(name):
    fullname = os.path.join("Data", "Images", name)
    if not os.path.isfile(fullname):
        sys.exit(f"Файл {fullname} не найден")
    image = pygame.image.load(fullname)
    image = image.convert_alpha()
    return image


def load_sound(name):
    fullname = os.path.join("Data", "Sounds", name)
    if not os.path.isfile(fullname):
        sys.exit(f"Файл {fullname} не найден")
    return fullname

#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Author: Andreas Rößler
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: February 2021
# License: MIT License
# =============================================================================
# This Script provides the Edge- Class to store and handle Edge- Information
# =============================================================================

import math
from enum import Enum
from random import randrange, choice


class EdgeType(Enum):
    std = 0
    roundabout = 1
    busstop = 2
    parking = 3


class Edge:
    counter = 0

    def __init__(self, from_node: Node, to_node: Node, edge_type=EdgeType.std):
        Edge.counter += 1
        self.__type = edge_type
        self.__nid = Edge.counter  # nid; numerical ID
        self.__from_node = from_node
        self.___to_node = to_node

    def __str__(self):
        fstr = str(self.__from_node)
        tstr = str(self.___to_node)
        return "{}_{}".format(fstr, tstr)

    def get_id(self):
        return self.__nid

    def get_type(self):
        return self.__type

    def set_type(self, edge_type=EdgeType.std):
        self.__type = edge_type


class Edges:
    def __init__(self, grid):
        self.__grid = grid
        self.__edge_list = []
        for node in grid:
            for neighbor in node:
                edge_type = EdgeType.std
                if (
                    node.get_type() == NodeType.roundabout
                    and neighbor.get_type() == NodeType.roundabout
                ):
                    edge_type = EdgeType.roundabout
                self.__edge_list.append(Edge(node, neighbor, edge_type))

    def __iter__(self):
        return iter(self.__edge_list)

    def list_by_type(self, edge_type: EdgeType.std):
        return [str(edge) for edge in self.__edge_list if edge.get_type() == edge_type]

    def number_of_edges(self):
        return len(self.__edge_list)

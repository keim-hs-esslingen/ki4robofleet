class BaseAlgorithm:
    def __init__(self):
        self._vid_edge_map = {}

    def get_edge(self, vid):
        pass

    def push_edge(self, vid, edge_id: str, time: int):
        self._vid_edge_map[vid] = edge_id
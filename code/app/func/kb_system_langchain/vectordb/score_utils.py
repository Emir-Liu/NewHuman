"""向量检索分数转换工具"""


def distance_to_similarity(distance: float) -> float:
    """
    将向量库返回的距离转为 0~1 相似度（越大越相似）。

    Chroma 余弦距离通常在 [0, 1]；L2 距离用反比例映射。
    """
    distance = float(distance)
    if distance <= 1.0:
        return max(0.0, 1.0 - distance)
    return 1.0 / (1.0 + distance)

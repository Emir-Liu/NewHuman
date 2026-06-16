"""
工具，显示工作流结构
"""
from IPython.display import Image, display



def save_graph_img(agent):
    # 保存图片到本地文件
    graph_image = agent.get_graph(xray=True).draw_mermaid_png()
    with open("agent_graph.png", "wb") as f:
        f.write(graph_image)
    print("工作流图已保存到 agent_graph.png")

if __name__ == "__main__":
    from func.graph.build import build_graph
    agent = build_graph()
    # from func.graph.build import build_graph_with_history
    # agent = build_graph_with_history()
    save_graph_img(agent)
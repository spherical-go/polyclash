import numpy as np
import pyvista as pv

# Load the snub dodecahedron model from a VTK file
# 从 VTK 文件加载扭棱十二面体模型
model_path = "model3d/snub_dodecahedron_new.vtk"
mesh = pv.read(model_path)
vertices = mesh.points

# Load additional data from a NPZ file
# 从 NPZ 文件加载额外数据
data_path = "model3d/snub_dodecahedron_new.npz"
npz_data = np.load(data_path)
edges = npz_data["edges"]
pentagons = npz_data["pentagons"]
triangles = npz_data["triangles"]

# Load cities data from a NPZ file
# 从 NPZ 文件加载城市数据
cities_path = "model3d/cities.npz"
cities_data = np.load(cities_path)
cities = cities_data["cities"]


# Define colors for different purposes
# 定义不同用途的颜色
group_colors = {
    0: (0.85, 0.75, 0.60, 1.0),  # Warm earth tone
    1: (0.65, 0.85, 0.65, 1.0),  # Fresh green
    2: (0.75, 0.70, 0.50, 1.0),  # Sandy brown
    3: (0.65, 0.65, 0.60, 1.0),  # Rocky gray
}
sea_color = (0.3, 0.5, 0.7, 1.0)  # Ocean blue
city_color = (0.8, 0.8, 0.8, 1.0)  # City marker color
font_color = (0.2, 0.2, 0.2, 1.0)  # Text color

# Initialize the color array for all faces
# 初始化所有面的颜色数组
face_colors = np.zeros((mesh.n_cells, 4))

# Apply colors to each face based on its vertices
# 根据每个面的顶点应用颜色
for i in range(mesh.n_cells):
    if i < len(triangles):
        face = triangles[i]
    else:
        face = pentagons[i - len(triangles)]

    groups = [vertex // 15 for vertex in face]
    # If all vertices are from the same group, color the face accordingly
    # 如果所有顶点来自同一组，则相应地着色面
    if len(set(groups)) == 1:
        face_colors[i] = group_colors[groups[0]]
    else:
        # Default to sea color for mixed groups
        # 对于混合组，默认为海洋颜色
        face_colors[i] = sea_color

# Set the color data to the mesh object
# 将颜色数据设置到网格对象
mesh.cell_data["colors"] = face_colors


# Create a PyVista plotter object and display the mesh with applied colors
# 创建一个 PyVista 绘图器对象，并显示应用颜色的网格
plotter = pv.Plotter()
plotter.add_mesh(mesh, scalars=face_colors, rgba=True)

# Add city labels
# 添加城市标签
plotter.add_point_labels(
    cities[:60],
    range(60),
    point_color=city_color,
    point_size=10,
    render_points_as_spheres=True,
    text_color=font_color,
    font_size=100,
    shape_opacity=0.0,
)
plotter.show()

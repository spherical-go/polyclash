import pyvista as pv

# Load the GLB format 3D model
model_path = 'model3d/snub_dodecahedron.vtk'  # Replace with the path to your model file
mesh = pv.read(model_path)

# Create a plotting window with a white background
plotter = pv.Plotter(window_size=(1600, 1200))
plotter.set_background('white')

# Add the model to the plotting window
plotter.add_mesh(mesh, show_edges=True, color='lightblue')

plotter.show_axes = True
# Show the coordinate axes in the corner
plotter.add_axes(interactive=True)

# Display the model
plotter.show()

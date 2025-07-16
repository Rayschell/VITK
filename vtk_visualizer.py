"""
Module de visualisation VTK pour le projet ITK/VTK
"""

import vtk
import os

def setup_vtk_renderer():
    """Configure le renderer VTK de base"""
    renderer = vtk.vtkRenderer()
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)
    render_window.SetSize(800, 600)
    
    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(render_window)
    
    renderer.SetBackground(0.1, 0.1, 0.2)
    
    return renderer, render_window, interactor

def load_nrrd_with_vtk(filepath):
    """Charge un fichier NRRD avec VTK"""
    try:
        reader = vtk.vtkNrrdReader()
        reader.SetFileName(filepath)
        reader.Update()
        
        print(f"Image VTK chargee: {filepath}")
        image_data = reader.GetOutput()
        
        dims = image_data.GetDimensions()
        spacing = image_data.GetSpacing()
        scalar_range = image_data.GetScalarRange()
        
        print(f"Dimensions VTK: {dims}")
        print(f"Espacement VTK: {spacing}")
        print(f"Plage de valeurs: {scalar_range}")
        
        return image_data
    except Exception as e:
        print(f"Erreur chargement VTK: {e}")
        return None

def create_volume_rendering(image_data):
    """Cree un rendu volumique"""
    try:
        volume_mapper = vtk.vtkGPUVolumeRayCastMapper()
        volume_mapper.SetInputData(image_data)
        
        volume_property = vtk.vtkVolumeProperty()
        volume_property.ShadeOff()
        volume_property.SetInterpolationTypeToLinear()
        
        scalar_range = image_data.GetScalarRange()
        
        color_func = vtk.vtkColorTransferFunction()
        color_func.AddRGBPoint(scalar_range[0], 0.0, 0.0, 0.0)
        color_func.AddRGBPoint(scalar_range[1] * 0.5, 1.0, 0.5, 0.3)
        color_func.AddRGBPoint(scalar_range[1], 1.0, 1.0, 1.0)
        
        opacity_func = vtk.vtkPiecewiseFunction()
        opacity_func.AddPoint(scalar_range[0], 0.0)
        opacity_func.AddPoint(scalar_range[1] * 0.3, 0.0)
        opacity_func.AddPoint(scalar_range[1] * 0.6, 0.5)
        opacity_func.AddPoint(scalar_range[1], 1.0)
        
        volume_property.SetColor(color_func)
        volume_property.SetScalarOpacity(opacity_func)
        
        volume = vtk.vtkVolume()
        volume.SetMapper(volume_mapper)
        volume.SetProperty(volume_property)
        
        return volume
    except Exception as e:
        print(f"Erreur rendu volumique: {e}")
        return None

def create_slice_viewer(image_data):
    """Cree un visualiseur de coupes"""
    try:
        dims = image_data.GetDimensions()
        
        slice_mapper = vtk.vtkImageSliceMapper()
        slice_mapper.SetInputData(image_data)
        slice_mapper.SetSliceNumber(dims[2] // 2)
        slice_mapper.SetOrientationToZ()
        
        slice_actor = vtk.vtkImageSlice()
        slice_actor.SetMapper(slice_mapper)
        
        return slice_actor
    except Exception as e:
        print(f"Erreur visualiseur coupes: {e}")
        return None

def create_isosurface(image_data, iso_value=None):
    """Cree une isosurface"""
    try:
        if iso_value is None:
            scalar_range = image_data.GetScalarRange()
            iso_value = (scalar_range[0] + scalar_range[1]) / 2.0
        
        marching_cubes = vtk.vtkMarchingCubes()
        marching_cubes.SetInputData(image_data)
        marching_cubes.SetValue(0, iso_value)
        marching_cubes.Update()
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(marching_cubes.GetOutputPort())
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.8, 0.6, 0.4)
        actor.GetProperty().SetOpacity(0.8)
        
        print(f"Isosurface creee avec valeur: {iso_value}")
        return actor
    except Exception as e:
        print(f"Erreur isosurface: {e}")
        return None

def visualize_volume(filepath, mode="volume"):
    """Visualise un volume 3D"""
    print(f"Visualisation VTK: {filepath}")
    
    image_data = load_nrrd_with_vtk(filepath)
    if image_data is None:
        return False
    
    renderer, render_window, interactor = setup_vtk_renderer()
    
    if mode == "volume":
        volume = create_volume_rendering(image_data)
        if volume:
            renderer.AddVolume(volume)
            print("Rendu volumique ajoute")
    
    elif mode == "slice":
        slice_actor = create_slice_viewer(image_data)
        if slice_actor:
            renderer.AddActor(slice_actor)
            print("Visualiseur de coupes ajoute")
    
    elif mode == "isosurface":
        iso_actor = create_isosurface(image_data)
        if iso_actor:
            renderer.AddActor(iso_actor)
            print("Isosurface ajoutee")
    
    elif mode == "combined":
        iso_actor = create_isosurface(image_data)
        if iso_actor:
            renderer.AddActor(iso_actor)
        
        slice_actor = create_slice_viewer(image_data)
        if slice_actor:
            renderer.AddActor(slice_actor)
        
        print("Mode combine active")
    
    axes = vtk.vtkAxesActor()
    axes.SetTotalLength(50, 50, 50)
    renderer.AddActor(axes)
    
    renderer.ResetCamera()
    
    base_name = os.path.splitext(os.path.basename(filepath))[0]
    render_window.SetWindowName(f"VTK - {base_name} - Mode: {mode}")
    
    print("Controles VTK:")
    print("- Clic gauche + glisser: Rotation")
    print("- Clic droit + glisser: Zoom")
    print("- Clic milieu + glisser: Pan")
    print("- 'q' pour quitter")
    
    render_window.Render()
    interactor.Start()
    
    return True

def save_vtk_screenshot(filepath, output_file, mode="isosurface"):
    """Sauvegarde une capture d'ecran VTK"""
    print(f"Capture VTK: {filepath} -> {output_file}")
    
    image_data = load_nrrd_with_vtk(filepath)
    if image_data is None:
        return False
    
    renderer, render_window, interactor = setup_vtk_renderer()
    
    if mode == "isosurface":
        iso_actor = create_isosurface(image_data)
        if iso_actor:
            renderer.AddActor(iso_actor)
    
    renderer.ResetCamera()
    render_window.SetOffScreenRendering(1)
    render_window.Render()
    
    w2if = vtk.vtkWindowToImageFilter()
    w2if.SetInput(render_window)
    w2if.Update()
    
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(output_file)
    writer.SetInputConnection(w2if.GetOutputPort())
    writer.Write()
    
    print(f"Capture sauvegardee: {output_file}")
    return True

def demo_vtk_visualization():
    """Demonstration des capacites VTK"""
    print("Demo visualisation VTK")
    
    nrrd_files = [
        "Data/case6_gre1.nrrd",
        "Data/case6_gre2.nrrd"
    ]
    
    for filepath in nrrd_files:
        if os.path.exists(filepath):
            base_name = os.path.splitext(os.path.basename(filepath))[0]
            
            print(f"\nTraitement VTK: {base_name}")
            
            screenshot_file = f"Output/{base_name}_vtk_screenshot.png"
            if save_vtk_screenshot(filepath, screenshot_file):
                print(f"Capture VTK sauvegardee")
            
            response = input(f"Visualiser {base_name} interactivement? (o/n): ").lower()
            if response in ['o', 'oui', 'y', 'yes']:
                visualize_volume(filepath, mode="isosurface")
        else:
            print(f"Fichier non trouve: {filepath}")

if __name__ == "__main__":
    demo_vtk_visualization()

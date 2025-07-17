import vtk
import itk
import numpy as np
from pathlib import Path


class TumorVisualization:
    def __init__(self):
        self.renderer = vtk.vtkRenderer()
        self.render_window = vtk.vtkRenderWindow()
        self.render_window_interactor = vtk.vtkRenderWindowInteractor()
        
        self.render_window.AddRenderer(self.renderer)
        self.render_window_interactor.SetRenderWindow(self.render_window)
        
        # Set up camera and lighting with enhanced settings
        self.renderer.SetBackground(0.05, 0.05, 0.1)  # Dark blue background
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(200, 200, 200)
        camera.SetFocalPoint(0, 0, 0)
        camera.SetViewUp(0, 0, 1)  # Z-axis up
        
        # Store references for dynamic adjustment
        self.brain_volume = None
        self.tumor_actors = []
        
    def load_image_as_vtk(self, image_path):
        reader = vtk.vtkNrrdReader()
        reader.SetFileName(str(image_path))
        reader.Update()
        return reader.GetOutput()
    
    def create_brain_volume_rendering(self, image_path, opacity=0.02):
        volume_data = self.load_image_as_vtk(image_path)
        
        # Volume mapper
        volume_mapper = vtk.vtkGPUVolumeRayCastMapper()
        volume_mapper.SetInputData(volume_data)
        
        # Enhanced transfer functions for better tumor visibility
        color_func = vtk.vtkColorTransferFunction()
        color_func.AddRGBPoint(0, 0.0, 0.0, 0.0)      # Background: black
        color_func.AddRGBPoint(200, 0.1, 0.1, 0.1)    # Low intensity: very dark gray
        color_func.AddRGBPoint(400, 0.2, 0.2, 0.25)   # Brain tissue: subtle blue-gray
        color_func.AddRGBPoint(600, 0.3, 0.3, 0.35)   # Higher brain: slightly brighter
        color_func.AddRGBPoint(800, 0.4, 0.4, 0.45)   # White matter: light gray
        color_func.AddRGBPoint(1200, 0.6, 0.6, 0.7)   # High intensity: brighter
        
        # Very transparent opacity function to let tumors show through
        opacity_func = vtk.vtkPiecewiseFunction()
        opacity_func.AddPoint(0, 0.0)        # Background: completely transparent
        opacity_func.AddPoint(100, 0.0)      # Low values: transparent
        opacity_func.AddPoint(200, opacity * 0.3)  # Brain edges: very faint
        opacity_func.AddPoint(400, opacity * 0.5)  # Brain tissue: subtle
        opacity_func.AddPoint(600, opacity * 0.8)  # Denser tissue: slightly more visible
        opacity_func.AddPoint(800, opacity * 1.2)  # White matter: more visible
        opacity_func.AddPoint(1000, opacity * 1.5) # High intensity: most visible but still faint
        
        # Volume property with enhanced settings
        volume_property = vtk.vtkVolumeProperty()
        volume_property.SetColor(color_func)
        volume_property.SetScalarOpacity(opacity_func)
        volume_property.ShadeOn()
        volume_property.SetInterpolationTypeToLinear()
        volume_property.SetAmbient(0.4)    # Increased ambient lighting
        volume_property.SetDiffuse(0.6)    # Good diffuse lighting
        volume_property.SetSpecular(0.2)   # Minimal specular highlights
        
        # Volume
        volume = vtk.vtkVolume()
        volume.SetMapper(volume_mapper)
        volume.SetProperty(volume_property)
        
        return volume
    
    def create_tumor_surface(self, mask_path, color=(1.0, 0.0, 0.0), smoothing=True):
        # Load mask as VTK
        reader = vtk.vtkNrrdReader()
        reader.SetFileName(str(mask_path))
        reader.Update()
        mask_data = reader.GetOutput()
        
        # Marching cubes to create surface
        marching_cubes = vtk.vtkMarchingCubes()
        marching_cubes.SetInputData(mask_data)
        marching_cubes.SetValue(0, 0.5)
        marching_cubes.Update()
        
        surface = marching_cubes.GetOutput()
        
        if smoothing and surface.GetNumberOfPoints() > 0:
            # Smooth the surface for better appearance
            smoother = vtk.vtkSmoothPolyDataFilter()
            smoother.SetInputData(surface)
            smoother.SetNumberOfIterations(30)  # Reduced for less aggressive smoothing
            smoother.SetRelaxationFactor(0.15)  # Slightly more relaxation
            smoother.Update()
            surface = smoother.GetOutput()
        
        # Create mapper and actor
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(surface)
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        
        # Enhanced tumor appearance for better visibility
        property = actor.GetProperty()
        property.SetColor(color)
        property.SetOpacity(0.95)         # Very opaque tumors
        property.SetAmbient(0.3)          # Good ambient lighting
        property.SetDiffuse(0.7)          # Strong diffuse component
        property.SetSpecular(0.4)         # Some specular highlights
        property.SetSpecularPower(20)     # Moderate shininess
        property.SetInterpolationToPhong() # Best quality shading
        
        # Add slight edge highlighting for better definition
        property.EdgeVisibilityOn()
        property.SetEdgeColor(0.8, 0.8, 0.8)  # Light gray edges
        property.SetLineWidth(1.0)
        
        return actor
    
    def create_slice_view(self, image_path, slice_number=None):
        volume_data = self.load_image_as_vtk(image_path)
        
        # Auto-select middle slice if not specified
        if slice_number is None:
            dims = volume_data.GetDimensions()
            slice_number = dims[2] // 2
        
        # Extract slice
        extract = vtk.vtkImageSlice()
        extract.SetInputData(volume_data)
        
        # Create slice mapper
        slice_mapper = vtk.vtkImageSliceMapper()
        slice_mapper.SetInputData(volume_data)
        slice_mapper.SetOrientationToZ()
        slice_mapper.SetSliceNumber(slice_number)
        
        # Create slice actor
        slice_actor = vtk.vtkImageSlice()
        slice_actor.SetMapper(slice_mapper)
        
        # Adjust window/level for better contrast
        slice_actor.GetProperty().SetColorWindow(1000)
        slice_actor.GetProperty().SetColorLevel(500)
        
        return slice_actor
    
    def add_text_annotation(self, text, position=(10, 10), color=(1, 1, 1)):
        text_actor = vtk.vtkTextActor()
        text_actor.SetInput(text)
        text_actor.SetPosition(position)
        text_actor.GetTextProperty().SetFontSize(14)
        text_actor.GetTextProperty().SetColor(color)
        text_actor.GetTextProperty().SetFontFamilyToArial()
        
        self.renderer.AddActor2D(text_actor)
        return text_actor
    
    def visualize_tumor_evolution(self, brain_image_path, tumor1_mask_path, 
                                 tumor2_mask_path, analysis_results):
        # Clear previous actors
        self.renderer.RemoveAllViewProps()
        
        # Enhanced background for better contrast
        self.renderer.SetBackground(0.05, 0.05, 0.1)  # Very dark blue background
        
        # Add brain volume with very low opacity to let tumors stand out
        self.brain_volume = self.create_brain_volume_rendering(brain_image_path, opacity=0.01)
        self.renderer.AddVolume(self.brain_volume)
        
        # Add tumor surfaces with enhanced visibility and brighter colors
        tumor1_actor = self.create_tumor_surface(tumor1_mask_path, color=(1.0, 0.2, 0.2))  # Bright red
        tumor2_actor = self.create_tumor_surface(tumor2_mask_path, color=(0.2, 1.0, 0.2))  # Bright green
        
        # Store tumor actors for potential future use
        self.tumor_actors = [tumor1_actor, tumor2_actor]
        
        self.renderer.AddActor(tumor1_actor)
        self.renderer.AddActor(tumor2_actor)
        
        # Enhanced lighting for better tumor visibility
        light1 = vtk.vtkLight()
        light1.SetPosition(200, 200, 200)
        light1.SetIntensity(0.8)
        light1.SetColor(1.0, 1.0, 1.0)
        self.renderer.AddLight(light1)
        
        light2 = vtk.vtkLight()
        light2.SetPosition(-200, -200, 200)
        light2.SetIntensity(0.6)
        light2.SetColor(1.0, 1.0, 1.0)
        self.renderer.AddLight(light2)
        
        # Fill light for even illumination
        light3 = vtk.vtkLight()
        light3.SetPosition(0, 0, 300)
        light3.SetIntensity(0.4)
        light3.SetColor(1.0, 1.0, 1.0)
        self.renderer.AddLight(light3)
        
        # Add annotations with better visibility
        volume_change = analysis_results['comparison']['volume_change_percent']
        dice_score = analysis_results['comparison']['dice_coefficient']
        
        self.add_text_annotation(f"Tumor Evolution Analysis", (10, 580), color=(1, 1, 0.8))
        self.add_text_annotation(f"Rouge: Scan initial", (10, 550), color=(1.0, 0.6, 0.6))
        self.add_text_annotation(f"Vert: Scan de suivi", (10, 520), color=(0.6, 1.0, 0.6))
        self.add_text_annotation(f"Changement de volume: {volume_change:.1f}%", (10, 490), color=(1, 1, 1))
        self.add_text_annotation(f"Coefficient Dice: {dice_score:.3f}", (10, 460), color=(1, 1, 1))
        self.add_text_annotation(f"Controles: Clic gauche=rotation, Molette=zoom", (10, 430), color=(0.8, 0.8, 0.8))
        
        # Add coordinate axes with better visibility
        axes = vtk.vtkAxesActor()
        axes.SetTotalLength(50, 50, 50)
        axes.SetShaftType(0)  # Cylinder shafts
        axes.SetAxisLabels(1) # Show labels
        self.renderer.AddActor(axes)
        
        # Reset camera with better positioning for tumor viewing
        self.renderer.ResetCamera()
        camera = self.renderer.GetActiveCamera()
        camera.Azimuth(30)    # Rotate around vertical axis
        camera.Elevation(15)  # Slight elevation for better view
        camera.Zoom(1.2)      # Zoom in a bit for closer view
        
        # Set window properties
        self.render_window.SetSize(1000, 800)  # Larger window for better visibility
        self.render_window.SetWindowName("Analyse Evolution Tumorale - Visualisation 3D Interactive")
        
    def create_comparative_slices(self, image1_path, mask1_path, image2_path, mask2_path, 
                                 slice_number=None):
        # Create a new renderer for slice comparison
        slice_renderer = vtk.vtkRenderer()
        slice_renderer.SetViewport(0.0, 0.0, 1.0, 1.0)
        slice_renderer.SetBackground(0.0, 0.0, 0.0)
        
        # Load images
        volume1 = self.load_image_as_vtk(image1_path)
        volume2 = self.load_image_as_vtk(image2_path)
        
        # Auto-select middle slice
        if slice_number is None:
            dims = volume1.GetDimensions()
            slice_number = dims[2] // 2
        
        # Create side-by-side slice view
        # Left side: Initial scan
        slice1_mapper = vtk.vtkImageSliceMapper()
        slice1_mapper.SetInputData(volume1)
        slice1_mapper.SetOrientationToZ()
        slice1_mapper.SetSliceNumber(slice_number)
        
        slice1_actor = vtk.vtkImageSlice()
        slice1_actor.SetMapper(slice1_mapper)
        slice1_actor.SetPosition(-100, 0, 0)
        
        # Right side: Follow-up scan
        slice2_mapper = vtk.vtkImageSliceMapper()
        slice2_mapper.SetInputData(volume2)
        slice2_mapper.SetOrientationToZ()
        slice2_mapper.SetSliceNumber(slice_number)
        
        slice2_actor = vtk.vtkImageSlice()
        slice2_actor.SetMapper(slice2_mapper)
        slice2_actor.SetPosition(100, 0, 0)
        
        slice_renderer.AddActor(slice1_actor)
        slice_renderer.AddActor(slice2_actor)
        
        return slice_renderer
    
    def start_interaction(self):
        # Add interactor style for better navigation
        style = vtk.vtkInteractorStyleTrackballCamera()
        self.render_window_interactor.SetInteractorStyle(style)
        
        # Add keyboard controls for transparency adjustment
        self.create_interactive_controls()
        
        # Print help message
        print("\nControles disponibles:")
        print("  Souris - Clic gauche + glisser: Rotation")
        print("  Souris - Molette: Zoom")
        print("  Souris - Clic droit + glisser: Translation")
        print("  Clavier - +: Augmenter transparence cerveau")
        print("  Clavier - -: Diminuer transparence cerveau")
        print("  Clavier - r: Reinitialiser la vue")
        print("  Clavier - h: Afficher l'aide")
        
        # Start the interaction
        self.render_window.Render()
        self.render_window_interactor.Start()
    
    def save_screenshot(self, output_path):
        window_to_image = vtk.vtkWindowToImageFilter()
        window_to_image.SetInput(self.render_window)
        window_to_image.Update()
        
        writer = vtk.vtkPNGWriter()
        writer.SetFileName(str(output_path))
        writer.SetInputConnection(window_to_image.GetOutputPort())
        writer.Write()
    
    def adjust_brain_transparency(self, opacity_factor):
        """Adjust brain volume transparency dynamically"""
        if self.brain_volume:
            volume_property = self.brain_volume.GetProperty()
            opacity_func = volume_property.GetScalarOpacity()
            
            # Scale all opacity values by the factor
            for i in range(opacity_func.GetSize()):
                point = [0, 0, 0, 0]  # x, y, midpoint, sharpness
                opacity_func.GetNodeValue(i, point)
                opacity_func.SetNodeValue(i, [point[0], point[1] * opacity_factor, point[2], point[3]])
            
            self.render_window.Render()
    
    def create_interactive_controls(self):
        """Add keyboard controls for transparency adjustment"""
        def on_key_press(obj, event):
            key = self.render_window_interactor.GetKeySym()
            if key == 'plus' or key == 'equal':
                # Increase brain transparency (make more visible)
                self.adjust_brain_transparency(1.5)
                print("Transparence cerveau augmentee")
            elif key == 'minus':
                # Decrease brain transparency (make less visible)
                self.adjust_brain_transparency(0.7)
                print("Transparence cerveau diminuee")
            elif key == 'r' or key == 'R':
                # Reset view
                self.renderer.ResetCamera()
                self.render_window.Render()
                print("Vue reinitalisee")
            elif key == 'h' or key == 'H':
                # Show help
                print("\nControles clavier:")
                print("  + : Augmenter transparence cerveau")
                print("  - : Diminuer transparence cerveau")
                print("  r : Reinitialiser la vue")
                print("  h : Afficher cette aide")
        
        self.render_window_interactor.AddObserver("KeyPressEvent", on_key_press)

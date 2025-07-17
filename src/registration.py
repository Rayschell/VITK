import itk
import numpy as np
from pathlib import Path


class ImageRegistration:
    def __init__(self):
        self.PixelType = itk.F
        self.Dimension = 3
        self.ImageType = itk.Image[self.PixelType, self.Dimension]
        
    def load_image(self, image_path):
        reader = itk.ImageFileReader[self.ImageType].New()
        reader.SetFileName(str(image_path))
        reader.Update()
        return reader.GetOutput()
    
    def register_images(self, fixed_image_path, moving_image_path, output_path=None):
        fixed_image = self.load_image(fixed_image_path)
        moving_image = self.load_image(moving_image_path)
        
        # Multi-resolution registration with rigid + affine transformations
        registration = itk.ImageRegistrationMethodv4[self.ImageType, self.ImageType].New()
        
        # Metric: Mutual Information
        metric = itk.MattesMutualInformationImageToImageMetricv4[self.ImageType, self.ImageType].New()
        metric.SetNumberOfHistogramBins(50)
        registration.SetMetric(metric)
        
        # Optimizer: Regular Step Gradient Descent
        optimizer = itk.RegularStepGradientDescentOptimizerv4.New()
        optimizer.SetLearningRate(4.0)
        optimizer.SetMinimumStepLength(0.001)
        optimizer.SetRelaxationFactor(0.5)
        optimizer.SetNumberOfIterations(200)
        registration.SetOptimizer(optimizer)
        
        # Transform: Use VersorRigid3DTransform for better compatibility
        transform = itk.VersorRigid3DTransform[itk.D].New()
        registration.SetInitialTransform(transform)
        
        # Multi-resolution pyramid
        registration.SetFixedImage(fixed_image)
        registration.SetMovingImage(moving_image)
        
        # Shrink factors and smoothing sigmas for multi-resolution
        registration.SetNumberOfLevels(3)
        registration.SetShrinkFactorsPerLevel([4, 2, 1])
        registration.SetSmoothingSigmasPerLevel([2.0, 1.0, 0.0])
        
        # Initialize with geometric center
        initializer = itk.CenteredTransformInitializer[
            itk.VersorRigid3DTransform[itk.D], self.ImageType, self.ImageType
        ].New()
        initializer.SetTransform(transform)
        initializer.SetFixedImage(fixed_image)
        initializer.SetMovingImage(moving_image)
        initializer.MomentsOn()
        initializer.InitializeTransform()
        
        try:
            registration.Update()
            final_transform = registration.GetTransform()
            
            # Apply transform to moving image
            resampler = itk.ResampleImageFilter[self.ImageType, self.ImageType].New()
            resampler.SetInput(moving_image)
            resampler.SetTransform(final_transform)
            resampler.SetUseReferenceImage(True)
            resampler.SetReferenceImage(fixed_image)
            resampler.SetDefaultPixelValue(0)
            resampler.Update()
            
            registered_image = resampler.GetOutput()
            
            if output_path:
                writer = itk.ImageFileWriter[self.ImageType].New()
                writer.SetFileName(str(output_path))
                writer.SetInput(registered_image)
                writer.Update()
            
            return registered_image, final_transform
            
        except Exception as e:
            print(f"Registration failed: {e}")
            return moving_image, None
    
    def save_transform(self, transform, output_path):
        writer = itk.TransformFileWriterTemplate[itk.D].New()
        writer.SetFileName(str(output_path))
        writer.SetInput(transform)
        writer.Update()

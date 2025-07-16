"""
Module de recalage d'images pour le suivi longitudinal des tumeurs
"""

import itk
import numpy as np

def register_images(fixed_image, moving_image, registration_type="rigid"):
    """
    Recale deux images médicales
    
    Args:
        fixed_image: Image de référence
        moving_image: Image à recaler
        registration_type: Type de recalage ("rigid", "affine", "bspline")
    
    Returns:
        registered_image: Image recalée
        transform: Transformation appliquée
        metric_value: Valeur de la métrique finale
    """
    print(f"Debut recalage {registration_type}...")
    
    try:
        # Types d'images
        FixedImageType = type(fixed_image)
        MovingImageType = type(moving_image)
        
        # Conversion en float pour le recalage
        FloatImageType = itk.Image[itk.F, 3]
        
        fixed_caster = itk.CastImageFilter[FixedImageType, FloatImageType].New()
        fixed_caster.SetInput(fixed_image)
        fixed_caster.Update()
        fixed_float = fixed_caster.GetOutput()
        
        moving_caster = itk.CastImageFilter[MovingImageType, FloatImageType].New()
        moving_caster.SetInput(moving_image)
        moving_caster.Update()
        moving_float = moving_caster.GetOutput()
        
        # Configuration du recalage
        registration = itk.ImageRegistrationMethodv4[FloatImageType, FloatImageType].New()
        registration.SetFixedImage(fixed_float)
        registration.SetMovingImage(moving_float)
        
        # Métrique (Information Mutuelle)
        metric = itk.MattesMutualInformationImageToImageMetricv4[FloatImageType, FloatImageType].New()
        metric.SetNumberOfHistogramBins(50)  # Bon compromis pour la précision
        registration.SetMetric(metric)
        
        # Optimiseur
        optimizer = itk.RegularStepGradientDescentOptimizerv4.New()
        optimizer.SetLearningRate(1.0)  # Valeur standard pour convergence stable
        optimizer.SetMinimumStepLength(0.001)  # Précision fine
        optimizer.SetNumberOfIterations(100)  # Compromis qualité/temps
        optimizer.SetRelaxationFactor(0.5)  # Valeur classique
        registration.SetOptimizer(optimizer)
        
        # Transformation selon le type
        if registration_type == "rigid":
            transform = itk.Euler3DTransform[itk.D].New()
            scales = itk.OptimizerParameters[itk.D](6)
            scales[0] = 1.0  # rotation X
            scales[1] = 1.0  # rotation Y  
            scales[2] = 1.0  # rotation Z
            scales[3] = 1.0/1000.0  # translation X
            scales[4] = 1.0/1000.0  # translation Y
            scales[5] = 1.0/1000.0  # translation Z
            optimizer.SetScales(scales)
            
        elif registration_type == "affine":
            transform = itk.AffineTransform[itk.D, 3].New()
            scales = itk.OptimizerParameters[itk.D](12)
            for i in range(9):  # matrice 3x3
                scales[i] = 1.0
            for i in range(9, 12):  # translation
                scales[i] = 1.0/1000.0
            optimizer.SetScales(scales)
            
        else:  # rigid par défaut
            transform = itk.Euler3DTransform[itk.D].New()
            
        # Centrer la transformation
        spacing = fixed_float.GetSpacing()
        origin = fixed_float.GetOrigin()
        size = fixed_float.GetLargestPossibleRegion().GetSize()
        center = [
            origin[0] + spacing[0] * size[0] / 2.0,
            origin[1] + spacing[1] * size[1] / 2.0,
            origin[2] + spacing[2] * size[2] / 2.0
        ]
        transform.SetCenter(center)
        
        registration.SetInitialTransform(transform)
        
        # Pyramide multi-résolution pour meilleure convergence
        registration.SetNumberOfLevels(3)  # 3 niveaux de résolution
        registration.SetSmoothingSigmasPerLevel([2, 1, 0])  # Lissage décroissant
        registration.SetShrinkFactorsPerLevel([4, 2, 1])   # Facteurs de réduction
        
        # Configuration du sampling - équilibre qualité/performance
        registration.SetMetricSamplingPercentage(0.15)  # 15% pour bon compromis
        
        print(f"Execution du recalage {registration_type} (multi-résolution: 3 niveaux, 100 iterations)...")
        registration.Update()
        
        # Récupération de la transformation finale
        final_transform = registration.GetOutput().Get()
        final_metric = registration.GetMetricValue()
        
        print(f"Recalage termine - Metric finale: {final_metric:.6f}")
        
        # Application de la transformation
        resampler = itk.ResampleImageFilter[FloatImageType, FloatImageType].New()
        resampler.SetInput(moving_float)
        resampler.SetTransform(final_transform)
        resampler.SetReferenceImage(fixed_float)
        resampler.UseReferenceImageOn()
        resampler.SetDefaultPixelValue(0)
        
        # Ajouter l'interpolateur ici
        interpolator = itk.LinearInterpolateImageFunction[FloatImageType, itk.D].New()
        resampler.SetInterpolator(interpolator)
        
        resampler.Update()
        
        registered_image = resampler.GetOutput()
        
        return registered_image, final_transform, final_metric
        
    except Exception as e:
        print(f"Erreur lors du recalage: {e}")
        return None, None, None

def apply_transform_to_image(image, transform, reference_image):
    """Applique une transformation à une image"""
    try:
        FloatImageType = itk.Image[itk.F, 3]
        
        # Conversion en float
        ImageType = type(image)
        caster = itk.CastImageFilter[ImageType, FloatImageType].New()
        caster.SetInput(image)
        caster.Update()
        float_image = caster.GetOutput()
        
        # Application de la transformation
        resampler = itk.ResampleImageFilter[FloatImageType, FloatImageType].New()
        resampler.SetInput(float_image)
        resampler.SetTransform(transform)
        resampler.SetReferenceImage(reference_image)
        resampler.UseReferenceImageOn()
        resampler.SetDefaultPixelValue(0)
        resampler.Update()
        
        return resampler.GetOutput()
        
    except Exception as e:
        print(f"Erreur application transformation: {e}")
        return None

def evaluate_registration_quality(fixed_image, registered_image):
    """Évalue la qualité du recalage"""
    try:
        # Information mutuelle
        mi_metric = itk.MattesMutualInformationImageToImageMetricv4[
            itk.Image[itk.F, 3], itk.Image[itk.F, 3]
        ].New()
        mi_metric.SetFixedImage(fixed_image)
        mi_metric.SetMovingImage(registered_image)
        mi_metric.SetNumberOfHistogramBins(50)
        
        # Transformation identité pour l'évaluation
        identity_transform = itk.IdentityTransform[itk.D, 3].New()
        mi_metric.SetTransform(identity_transform)
        mi_metric.Initialize()
        
        mi_value = mi_metric.GetValue()
        
        # Corrélation croisée normalisée
        correlation_metric = itk.CorrelationImageToImageMetricv4[
            itk.Image[itk.F, 3], itk.Image[itk.F, 3]
        ].New()
        correlation_metric.SetFixedImage(fixed_image)
        correlation_metric.SetMovingImage(registered_image)
        correlation_metric.SetTransform(identity_transform)
        correlation_metric.Initialize()
        
        correlation_value = correlation_metric.GetValue()
        
        return {
            'mutual_information': mi_value,
            'correlation': correlation_value
        }
        
    except Exception as e:
        print(f"Erreur évaluation recalage: {e}")
        return None

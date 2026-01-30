"""
Synthetic Data Package
Generates synthetic data for training when real data is scarce
"""

from .generators import (
    SyntheticJobGenerator,
    SyntheticUserGenerator,
    SyntheticInteractionGenerator,
    generate_training_dataset,
)

__all__ = [
    "SyntheticJobGenerator",
    "SyntheticUserGenerator", 
    "SyntheticInteractionGenerator",
    "generate_training_dataset",
]

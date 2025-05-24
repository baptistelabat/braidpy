import matplotlib.pyplot as plt
import numpy as np
from typing import Optional
import matplotlib
from matplotlib.axes import Axes
matplotlib.use('WebAgg')

from src.braidpy import Braid
import braidvisualiser as bv


def plot_braid(braid: Braid, ax: Optional[Axes] = None) -> Axes:
    """
    Plot a braid diagram.
    
    Args:
        braid: The Braid object to plot
        ax: Optional matplotlib Axes object to plot on
        
    Returns:
        The matplotlib Axes object
    """


    b = bv.Braid(braid.n_strands, *braid.generators)

    b.draw()

def save_braid_plot(braid: Braid, filename: str, format: str = 'png'):
    """
    Save a braid plot to a file.
    
    Args:
        braid: The Braid object to plot
        filename: Output filename
        format: Image format (png, pdf, svg, etc.)
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    plot_braid(braid, ax)
    plt.savefig(filename, format=format, bbox_inches='tight')
    plt.close(fig)

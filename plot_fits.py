import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits

def process_and_plot_fits(fits_file_path, background_file=None):
    """
    Processes a single .fits file and plots Counts vs. Channel Number.
    Applies background subtraction if a background file is provided.

    Parameters:
    - fits_file_path (str): Path to the .fits file to be processed.
    - background_file (str, optional): Path to a background .fits file for background subtraction.
    """

    # Load the background data if specified
    background_counts = None
    if background_file:
        with fits.open(background_file) as bg_hdul:
            bg_data = bg_hdul[1].data
            background_counts = bg_data['COUNTS']

    # Process the specified .fits file
    with fits.open(fits_file_path) as hdul:
        spectrum_data = hdul[1].data
        channels = spectrum_data['CHANNEL']
        counts = spectrum_data['COUNTS']

        # Filter channels between 37 and 800
        valid_indices = (channels >= 37) & (channels <= 800)
        channels = channels[valid_indices]
        counts = counts[valid_indices]

        # Perform background subtraction if background counts are available
        if background_counts is not None:
            counts = counts - background_counts[valid_indices]

        # Plot Counts vs. Channel for the .fits file
        plt.plot(channels ,counts, label=f'Spectrum: {fits_file_path}', alpha=0.7, color='#4657ca')

    # Configure plot labels and title
    plt.xlabel('Channel Number')
    plt.ylabel('Counts')
    plt.title('X-ray Spectrum (Counts vs. Channel Number)')
    plt.grid()
    plt.tight_layout()
    plt.show()

# Example usage:
fits_file_path = '/home/vdnt/Documents/INTER--IIT/CLASS_data/added_2020-02-01T00-00-00.114_2020-02-01T00-45-12.114______________________.fits'
background_file = '/home/vdnt/Documents/INTER--IIT/ch2_class_pds_release_38_20240927/cla/calibration/background_allevents.fits'
process_and_plot_fits(fits_file_path, background_file)

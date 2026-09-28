import numpy as np
import batman
import matplotlib.pyplot as plt


class TransitModel:
    """
    Transit model class for exoplanet detection using batman.
    
    This class generates synthetic light curves for exoplanet transits
    and provides visualization capabilities.
    """
    
    def __init__(self, params_dict):
        """
        Initialize the transit model with parameters from configuration file.
        
        Parameters
        ----------
        params_dict : dict
            Dictionary containing transit parameters loaded from YAML file
        """
        self.params = batman.TransitParams()
        self.params.t0 = params_dict.get('t0', 0.0)
        self.params.per = params_dict.get('per')
        self.params.rp = params_dict.get('rp')
        self.params.a = params_dict.get('a')
        self.params.inc = params_dict.get('inc')
        self.params.ecc = params_dict.get('ecc', 0.0)
        self.params.w = params_dict.get('w', 90.0)
        self.params.u = params_dict.get('u', [0.1, 0.3])
        self.params.limb_dark = params_dict.get('limb_dark', 'quadratic')
        
        # Time array for model evaluation
        self.t = np.linspace(-0.075, 0.075, 1000)
        
        # Initialize batman model
        self.model = batman.TransitModel(self.params, self.t)
        
    def compute_light_curve(self):
        """
        Compute the light curve using the batman transit model.
        
        Returns
        -------
        flux : ndarray
            Array of relative flux values
        """
        self.flux = self.model.light_curve(self.params)
        return self.flux
    
    def plot_light_curve(self, output_file='lc.png', show=False):
        """
        Plot and save the transit light curve.
        
        Parameters
        ----------
        output_file : str, optional
            Output filename for the plot (default: 'lc.png')
        """
        if not hasattr(self, 'flux'):
            self.compute_light_curve()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(self.t, self.flux)
        ax.set(xlabel="Time from central transit (days)", ylabel="Relative flux")
        fig.tight_layout()
        fig.savefig(output_file, dpi=150)
        if show:
            plt.show()
        plt.close(fig)
        print(f"Light curve saved to {output_file}")
    
    def run(self, output_file='lc.png'):
        """
        Run the complete transit model workflow: compute and plot light curve.
        
        Parameters
        ----------
        output_file : str, optional
            Output filename for the plot (default: 'lc.png')
        """
        self.compute_light_curve()
        self.plot_light_curve(output_file)

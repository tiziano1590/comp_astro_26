"""Data preprocessing utilities for exoplanet detection.

This module provides functions for balancing datasets through data augmentation,
which is crucial for training machine learning models on imbalanced exoplanet
detection datasets where positive samples (planets) are typically much rarer
than negative samples (non-planets).
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Random state for reproducibility
RANDOM_STATE = 42


def create_balanced_dataset(X, y, samples_per_class=400, random_state=RANDOM_STATE):
    """Create a balanced dataset through data augmentation.
    
    This function balances an imbalanced dataset by either downsampling the majority
    class or augmenting the minority class. Data augmentation techniques include:
    - Adding Gaussian noise
    - Scaling the signal
    - Shifting the signal in time
    - Combining scaling with noise
    
    Parameters
    ----------
    X : numpy.ndarray
        Feature matrix of shape (n_samples, n_features) containing the input data.
        Typically light curve flux values for exoplanet detection.
    y : numpy.ndarray
        Target labels of shape (n_samples,) with binary values (0 or 1).
        0 represents non-planet samples, 1 represents planet samples.
    samples_per_class : int, optional
        Number of samples to generate for each class in the balanced dataset.
        Default is 400.
    
    Returns
    -------
    X_balanced : numpy.ndarray
        Balanced feature matrix of shape (2 * samples_per_class, n_features).
    y_balanced : numpy.ndarray
        Balanced target labels of shape (2 * samples_per_class,).
    
    Notes
    -----
    The augmentation process randomly applies one of four techniques:
    - 25% probability: Add Gaussian noise (mean=0, std=0.01)
    - 25% probability: Scale by factor in range [0.97, 1.03]
    - 25% probability: Shift signal by -20 to +20 positions
    - 25% probability: Combined scaling and noise addition
    
    Examples
    --------
    >>> X_train = np.random.randn(100, 3000)  # 100 samples, 3000 time points
    >>> y_train = np.array([0]*90 + [1]*10)   # Imbalanced: 90 non-planets, 10 planets
    >>> X_bal, y_bal = create_balanced_dataset(X_train, y_train, samples_per_class=200)
    >>> X_bal.shape
    (400, 3000)
    >>> np.sum(y_bal == 0), np.sum(y_bal == 1)
    (200, 200)
    """
    if samples_per_class < 1:
        raise ValueError("samples_per_class must be positive")

    X = np.asarray(X)
    y = np.asarray(y)
    if X.ndim != 2 or y.ndim != 1 or len(X) != len(y):
        raise ValueError("X must be 2-D and y must be a matching 1-D array")
    if not np.isin(y, [0, 1]).all():
        raise ValueError("y must contain only binary labels 0 and 1")

    rng = np.random.default_rng(random_state)
    print("\n" + "="*70)
    print("CREATING BALANCED DATASET")
    print("="*70)
    
    # Separate samples by class
    X0 = X[y == 0]
    X1 = X[y == 1]
    if len(X0) == 0 or len(X1) == 0:
        raise ValueError("Both classes must be present to create a balanced dataset")
    print(f"Original - Class 0: {len(X0)}, Class 1: {len(X1)}")
    
    def augment_to_target(X_orig, n_target):
        """Augment dataset to reach target number of samples.
        
        If the original dataset has enough samples, randomly subsample.
        Otherwise, augment using various techniques until target is reached.
        
        Parameters
        ----------
        X_orig : numpy.ndarray
            Original samples to augment.
        n_target : int
            Target number of samples to generate.
        
        Returns
        -------
        numpy.ndarray
            Augmented dataset with exactly n_target samples.
        """
        # If we have enough samples, just subsample
        if len(X_orig) >= n_target:
            idx = rng.choice(len(X_orig), n_target, replace=False)
            return X_orig[idx]
        
        # Start with original samples and augment until we reach target
        X_result = [X_orig]
        while len(np.vstack(X_result)) < n_target:
            n_needed = n_target - len(np.vstack(X_result))
            idx = rng.choice(len(X_orig), min(len(X_orig), n_needed))
            aug_type = rng.random()
            
            # Randomly select augmentation technique
            if aug_type < 0.25:
                # Add Gaussian noise
                X_aug = X_orig[idx] + rng.normal(0, 0.01, (len(idx), X_orig.shape[1]))
            elif aug_type < 0.5:
                # Scale the signal
                scale = 1.0 + rng.uniform(-0.03, 0.03, (len(idx), 1))
                X_aug = X_orig[idx] * scale
            elif aug_type < 0.75:
                # Shift the signal in time
                shifts = rng.integers(-20, 20, len(idx))
                X_aug = np.array([np.roll(X_orig[i], s) for i, s in zip(idx, shifts)])
            else:
                # Combine scaling and noise
                X_aug = X_orig[idx] * (1.0 + rng.uniform(-0.02, 0.02, (len(idx), 1)))
                X_aug += rng.normal(0, 0.008, X_aug.shape)
            
            X_result.append(X_aug)
        
        X_final = np.vstack(X_result)
        return X_final[:n_target]
    
    # Balance both classes
    X0_bal = augment_to_target(X0, samples_per_class)
    X1_bal = augment_to_target(X1, samples_per_class)
    print(f"Balanced - Class 0: {len(X0_bal)}, Class 1: {len(X1_bal)}")
    
    # Combine and shuffle
    X_bal = np.vstack([X0_bal, X1_bal])
    y_bal = np.concatenate([np.zeros(samples_per_class), np.ones(samples_per_class)])
    
    idx = np.arange(len(X_bal))
    rng.shuffle(idx)
    return X_bal[idx], y_bal[idx]


def load_data(csv_path='tess_data.csv', n_bins=1000, use_scaler=False, samples_per_class=350):
    """Load and preprocess exoplanet detection data from CSV.
    
    This function handles the complete data loading pipeline for exoplanet detection:
    - Loads light curve data from CSV
    - Extracts flux values, flux errors, labels, and metadata
    - Splits data into train and test sets with stratification
    - Balances the training set using data augmentation
    - Optionally applies standardization scaling
    
    Parameters
    ----------
    csv_path : str, optional
        Path to the CSV file containing TESS light curve data.
        Default is 'tess_data.csv'.
    n_bins : int, optional
        Number of time bins in the light curve. The CSV should contain
        columns named 'flux_0000' through 'flux_{n_bins-1:04d}'.
        Default is 1000.
    use_scaler : bool, optional
        Whether to apply StandardScaler normalization to the flux values.
        If True, data is standardized to zero mean and unit variance.
        Default is False.
    samples_per_class : int, optional
        Number of samples to generate for each class (0 and 1) in the
        balanced training set. Default is 350.
    
    Returns
    -------
    X_train : numpy.ndarray
        Training feature matrix of shape (2 * samples_per_class, n_bins).
        Contains balanced flux values, possibly scaled.
    X_test : numpy.ndarray
        Test feature matrix of shape (n_test_samples, n_bins).
        Contains unbalanced test flux values, possibly scaled.
    y_train : numpy.ndarray
        Training labels of shape (2 * samples_per_class,).
        Binary labels (0=non-planet, 1=planet), balanced.
    y_test : numpy.ndarray
        Test labels of shape (n_test_samples,).
        Binary labels preserving original class distribution.
    metadata_test : pandas.DataFrame
        Metadata for test samples containing columns:
        ['toi_name', 'tic', 'label', 'disp', 'period_d', 't0_bjd', 'dur_hr', 'sector']
    X_test_copy : numpy.ndarray
        Unscaled copy of X_test, useful for visualization if scaling was applied.
    X_err_test : numpy.ndarray
        Flux uncertainties for test samples of shape (n_test_samples, n_bins).
    scaler : StandardScaler or None
        The fitted StandardScaler object if use_scaler=True, otherwise None.
        Can be used for inverse transformation or scaling new data.
    
    Notes
    -----
    The function performs a stratified train-test split with 80/20 ratio and
    random_state=42 for reproducibility. Only the training set is balanced;
    the test set maintains the original class distribution to evaluate model
    performance on realistic data.
    
    The CSV file is expected to have the following structure:
    - Flux columns: 'flux_0000', 'flux_0001', ..., 'flux_{n_bins-1:04d}'
    - Error columns: 'flux_err_0000', 'flux_err_0001', ..., 'flux_err_{n_bins-1:04d}'
    - Label column: 'label' (0 or 1)
    - Metadata columns: 'toi_name', 'tic', 'disp', 'period_d', 't0_bjd', 'dur_hr', 'sector'
    
    Examples
    --------
    >>> # Load data with default settings
    >>> X_train, X_test, y_train, y_test, meta, X_test_raw, X_err, scaler = load_data()
    >>> X_train.shape
    (700, 1000)  # 350 samples per class, 1000 time bins
    
    >>> # Load with standardization
    >>> X_train, X_test, y_train, y_test, meta, X_test_raw, X_err, scaler = load_data(
    ...     csv_path='my_data.csv',
    ...     use_scaler=True,
    ...     samples_per_class=500
    ... )
    >>> X_train.mean(), X_train.std()
    (0.0, 1.0)  # Standardized
    """
    if n_bins < 1:
        raise ValueError("n_bins must be positive")

    print("\n" + "="*70)
    print("LOADING DATA")
    print("="*70)
    
    # Load CSV data
    df = pd.read_csv(csv_path)
    print(f"Dataset: {df.shape[0]} samples")
    
    # Extract flux values and errors
    flux_cols = [f'flux_{i:04d}' for i in range(n_bins)]
    flux_err_cols = [f'flux_err_{i:04d}' for i in range(n_bins)]
    X = df[flux_cols].values
    X_err = df[flux_err_cols].values
    y = df['label'].values
    
    # Extract metadata for later use
    metadata_cols = ['toi_name', 'tic', 'label', 'disp', 'period_d', 't0_bjd', 'dur_hr', 'sector']
    metadata = df[metadata_cols]
    
    # Display original class distribution
    print("Original distribution:")
    print(f"  Class 0: {(y==0).sum()}, Class 1: {(y==1).sum()}")
    if (y==0).sum() > 0:
        print(f"  Ratio: {(y==1).sum() / (y==0).sum():.2f}:1")
    
    # Stratified train-test split (80/20)
    X_train, X_test, y_train, y_test, _X_err_train, X_err_test, _idx_train, idx_test = train_test_split(
        X, y, X_err, np.arange(len(y)),
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=y  # Maintain class distribution in both sets
    )
    print(f"Initial split - Train: {len(X_train)}, Test: {len(X_test)}")
    
    # Balance training set using data augmentation
    X_train, y_train = create_balanced_dataset(
        X_train, y_train, samples_per_class=samples_per_class
    )

    # Preserve an unscaled copy for plotting and inspection.
    X_test_raw = X_test.copy()
    
    # Optional standardization (z-score normalization)
    scaler = None
    if use_scaler:
        print("\n" + "="*70)
        print("STANDARDIZATION")
        print("="*70)
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)  # Fit on training data
        X_test = scaler.transform(X_test)  # Apply same transformation to test
        print(f"Train: mean={X_train.mean():.6f}, std={X_train.std():.6f}")
        print(f"Test:  mean={X_test.mean():.6f}, std={X_test.std():.6f}")
    
    # Extract metadata for test samples only
    metadata_test = metadata.iloc[idx_test].reset_index(drop=True)
    print(f"Final - X_train: {X_train.shape}, X_test: {X_test.shape}")
    print(f"Train dist: 0={(y_train==0).sum()}, 1={(y_train==1).sum()}")
    
    # Return X_test copy for visualization (unscaled version if scaler was used)
    return X_train, X_test, y_train, y_test, metadata_test, X_test_raw, X_err_test, scaler

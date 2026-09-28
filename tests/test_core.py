import numpy as np
import pytest

from daneel.detection.data_process import create_balanced_dataset
from daneel.detection.transit_model import TransitModel
from daneel.parameters import Parameters


def test_parameters_load_nested_none(tmp_path):
    path = tmp_path / "params.yaml"
    path.write_text("a: None\nnested:\n  b: None\n", encoding="utf-8")

    params = Parameters(path)

    assert params.get("a") is None
    assert params.get("nested")["b"] is None


def test_parameters_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        Parameters(tmp_path / "missing.yaml")


def test_balanced_dataset_is_reproducible():
    X = np.arange(30, dtype=float).reshape(6, 5)
    y = np.array([0, 0, 0, 1, 1, 1])

    first = create_balanced_dataset(X, y, samples_per_class=5, random_state=7)
    second = create_balanced_dataset(X, y, samples_per_class=5, random_state=7)

    assert np.array_equal(first[0], second[0])
    assert np.array_equal(first[1], second[1])
    assert np.bincount(first[1].astype(int)).tolist() == [5, 5]


def test_transit_model_produces_flux():
    model = TransitModel(
        {"per": 2.2, "rp": 0.15, "a": 9.0, "inc": 85.7, "ecc": 0.0}
    )

    flux = model.compute_light_curve()

    assert flux.shape == (1000,)
    assert np.isfinite(flux).all()

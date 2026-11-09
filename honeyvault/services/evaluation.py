"""Evaluasi kuantitatif: membandingkan Random Decoy dan Adaptive Decoy.

Metrik yang dihitung:

1. Selisih mean dan standar deviasi saldo.
2. Overlap histogram (koefisien tumpang tindih 0..1).
3. Wasserstein distance dan statistik Kolmogorov-Smirnov.
4. Waktu pembentukan decoy.
5. Akurasi classifier sederhana yang mencoba membedakan data asli dan decoy.

Catatan penting: jarak distribusi yang lebih kecil berarti distribusi lebih
dekat, tetapi **tidak** membuktikan keamanan kriptografi. Classification test
mem memakai pemisahan data latih dan uji yang benar.
"""

import time

import numpy as np
from scipy import stats as scipy_stats

BALANCE_FIELDS = ("balance",)


def _balances(rows, field="balance"):
    return np.array([float(r[field]) for r in rows], dtype=float)


def mean_difference(real, decoy):
    """Selisih mean antara data asli dan decoy."""
    return float(abs(np.mean(real) - np.mean(decoy)))


def sd_difference(real, decoy):
    """Selisih standar deviasi antara data asli dan decoy."""
    return float(abs(np.std(real, ddof=1) - np.std(decoy, ddof=1)))


def histogram_overlap(real, decoy, bins=20):
    """Koefisien tumpang tindih dua histogram.

    Nilai 1 berarti histogram identik, 0 berarti tidak ada tumpang tindih.
    """
    real = np.asarray(real, dtype=float)
    decoy = np.asarray(decoy, dtype=float)
    if len(real) == 0 or len(decoy) == 0:
        return 0.0
    lo = min(real.min(), decoy.min())
    hi = max(real.max(), decoy.max())
    if hi <= lo:
        return 1.0
    edges = np.linspace(lo, hi, bins + 1)
    hist_real, _ = np.histogram(real, bins=edges, density=True)
    hist_decoy, _ = np.histogram(decoy, bins=edges, density=True)
    width = edges[1] - edges[0]
    overlap = np.minimum(hist_real, hist_decoy).sum() * width
    return float(overlap)


def wasserstein_distance(real, decoy):
    """Jarak Wasserstein (Earth Mover's Distance) antar distribusi."""
    if len(real) == 0 or len(decoy) == 0:
        return float("nan")
    return float(scipy_stats.wasserstein_distance(real, decoy))


def ks_statistic(real, decoy):
    """Statistik Kolmogorov-Smirnov dua sampel."""
    if len(real) == 0 or len(decoy) == 0:
        return float("nan"), float("nan")
    result = scipy_stats.ks_2samp(real, decoy)
    return float(result.statistic), float(result.pvalue)


def time_generation(fn, *args, **kwargs):
    """Mengukur waktu pembentukan decoy dalam detik."""
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    return result, time.perf_counter() - start


def classifier_accuracy(real, decoy, seed=42, test_ratio=0.3):
    """Menguji seberapa mudah data asli dipisahkan dari data decoy.

    Classifier yang dipakai adalah Gaussian Naive Bayes sederhana pada satu
    fitur (saldo). Data diacak dengan seed, lalu dipisah menjadi data latih
    dan data uji.

    Returns:
        Dict berisi akurasi latih, akurasi uji, dan ukuran sampel.
    """
    if len(real) < 2 or len(decoy) < 2:
        return {
            "train_accuracy": float("nan"),
            "test_accuracy": float("nan"),
            "train_size": 0,
            "test_size": 0,
            "balanced_accuracy": float("nan"),
        }

    rng = np.random.default_rng(seed)
    real_shuffled = rng.permutation(real)
    decoy_shuffled = rng.permutation(decoy)

    # Jumlah data latih mengikuti rasio yang sama untuk kedua kelas.
    n_real_train = int(len(real_shuffled) * (1 - test_ratio))
    n_decoy_train = int(len(decoy_shuffled) * (1 - test_ratio))

    x_train = np.concatenate([real_shuffled[:n_real_train], decoy_shuffled[:n_decoy_train]])
    y_train = np.concatenate([
        np.ones(n_real_train),
        np.zeros(n_decoy_train),
    ])
    x_test = np.concatenate([real_shuffled[n_real_train:], decoy_shuffled[n_decoy_train:]])
    y_test = np.concatenate([
        np.ones(len(real_shuffled) - n_real_train),
        np.zeros(len(decoy_shuffled) - n_decoy_train),
    ])

    model = _GaussianNaiveBayes()
    model.fit(x_train, y_train)
    train_acc = float((model.predict(x_train) == y_train).mean())
    test_acc = float((model.predict(x_test) == y_test).mean())

    # Balanced accuracy lebih adil bila ukuran kedua kelas tidak sama.
    balanced = _balanced_accuracy(model.predict(x_test), y_test)

    return {
        "train_accuracy": train_acc,
        "test_accuracy": test_acc,
        "balanced_accuracy": balanced,
        "train_size": int(len(x_train)),
        "test_size": int(len(x_test)),
    }


def _balanced_accuracy(predictions, truth):
    """Rata-rata recall kelas 0 dan kelas 1."""
    recalls = []
    for label in (0.0, 1.0):
        mask = truth == label
        if mask.sum() == 0:
            continue
        recalls.append(float((predictions[mask] == label).mean()))
    return float(np.mean(recalls)) if recalls else float("nan")


class _GaussianNaiveBayes:
    """Gaussian Naive Bayes satu fitur, ditulis manual tanpa scikit-learn."""

    def __init__(self):
        self.mean_ = {}
        self.var_ = {}
        self.prior_ = {}

    def fit(self, x, y):
        for label in np.unique(y):
            samples = x[y == label]
            self.mean_[label] = samples.mean()
            # Varian minimum mencegah pembagian dengan nol.
            self.var_[label] = max(samples.var(ddof=1) if len(samples) > 1 else 0.0, 1e-9)
            self.prior_[label] = len(samples) / len(x)
        return self

    def _log_posterior(self, x, label):
        mean = self.mean_[label]
        var = self.var_[label]
        prior = self.prior_[label]
        coefficient = -0.5 * np.log(2 * np.pi * var)
        exponent = -((x - mean) ** 2) / (2 * var)
        return coefficient + exponent + np.log(prior)

    def predict(self, x):
        labels = list(self.mean_.keys())
        scores = np.column_stack([self._log_posterior(x, label) for label in labels])
        return np.array(labels)[scores.argmax(axis=1)].astype(float)


def evaluate_method(real_rows, decoy_rows, field="balance"):
    """Menghitung seluruh metrik untuk satu metode generator."""
    real = _balances(real_rows, field)
    decoy = _balances(decoy_rows, field)

    ks_stat, ks_pvalue = ks_statistic(real, decoy)

    return {
        "mean_difference": mean_difference(real, decoy),
        "sd_difference": sd_difference(real, decoy),
        "histogram_overlap": histogram_overlap(real, decoy),
        "wasserstein_distance": wasserstein_distance(real, decoy),
        "ks_statistic": ks_stat,
        "ks_pvalue": ks_pvalue,
        "classifier": classifier_accuracy(real, decoy),
        "real_mean": float(real.mean()) if len(real) else float("nan"),
        "decoy_mean": float(decoy.mean()) if len(decoy) else float("nan"),
        "real_sd": float(real.std(ddof=1)) if len(real) > 1 else float("nan"),
        "decoy_sd": float(decoy.std(ddof=1)) if len(decoy) > 1 else float("nan"),
        "real_count": int(len(real)),
        "decoy_count": int(len(decoy)),
    }


def compare_methods(real_rows, random_rows, adaptive_rows, field="balance"):
    """Membandingkan kedua metode dan menyusun tabel ringkas.

    ``winner`` ditentukan dari jarak Wasserstein terendah, dengan
    kesetaraan pada selisih mean.
    """
    random_metrics = evaluate_method(real_rows, random_rows, field)
    adaptive_metrics = evaluate_method(real_rows, adaptive_rows, field)

    random_distance = random_metrics["wasserstein_distance"]
    adaptive_distance = adaptive_metrics["wasserstein_distance"]

    if np.isnan(random_distance) or np.isnan(adaptive_distance):
        winner = "tidak dapat ditentukan"
    elif abs(random_distance - adaptive_distance) < 1e-9:
        winner = "seri"
    else:
        winner = "adaptive" if adaptive_distance < random_distance else "random"

    return {
        "random": random_metrics,
        "adaptive": adaptive_metrics,
        "winner": winner,
    }

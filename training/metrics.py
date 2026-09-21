import numpy as np
from typing import Dict

class MetricsCalculator:
    def __init__(self, threshold=0.5):
        self.threshold = threshold

    def binary(self, pred, target):
        p = (pred > self.threshold).astype(np.int32)
        t = (target > self.threshold).astype(np.int32)
        return p, t

    def iou(self, pred, target):
        p, t = self.binary(pred, target)
        inter = np.logical_and(p, t).sum()
        union = np.logical_or(p, t).sum()
        return float(inter) / float(union) if union > 0 else 0.0

    def dice(self, pred, target):
        p, t = self.binary(pred, target)
        inter = np.logical_and(p, t).sum()
        total = p.sum() + t.sum()
        return 2.0 * float(inter) / float(total) if total > 0 else 0.0

    def precision(self, pred, target):
        p, t = self.binary(pred, target)
        tp = np.logical_and(p, t).sum()
        fp = np.logical_and(p, np.logical_not(t)).sum()
        return float(tp) / float(tp + fp) if (tp + fp) > 0 else 0.0

    def recall(self, pred, target):
        p, t = self.binary(pred, target)
        tp = np.logical_and(p, t).sum()
        fn = np.logical_and(np.logical_not(p), t).sum()
        return float(tp) / float(tp + fn) if (tp + fn) > 0 else 0.0

    def f1(self, pred, target):
        p = self.precision(pred, target)
        r = self.recall(pred, target)
        return 2.0 * p * r / (p + r) if (p + r) > 0 else 0.0

    def calculate_all(self, preds, targets):
        return {
            "iou": self.iou(preds, targets),
            "dice": self.dice(preds, targets),
            "precision": self.precision(preds, targets),
            "recall": self.recall(preds, targets),
            "f1": self.f1(preds, targets),
        }
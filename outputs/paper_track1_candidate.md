# Gradient-Norm Damping Stabilizes Mini-Batch Training but Does Not Improve Test Error

## Abstract

Small-batch stochastic optimization can produce noisy updates. We test a simple gradient-norm damping rule that scales each mini-batch update by the inverse of one plus its norm. On a fixed synthetic linear-regression task, damping reduces the standard deviation of the final training-loss trajectory from 0.000086 to 0.000077, but increases held-out test mean-squared error from 0.138566 to 0.139685. The result is a reproducible partial negative: the stability hypothesis receives limited support, while the generalization hypothesis does not.

## Introduction

Mini-batch stochastic gradient descent (SGD) is attractive because it is simple and efficient, but individual batches can produce updates with different magnitudes. A natural lightweight intervention is to reduce the step size for batches whose gradient norm is large. This submission asks whether that intervention improves optimization stability without requiring additional model capacity or data.

## Method

We compare standard mini-batch SGD with a confidence-weighted variant. For a batch gradient $g$, the baseline uses the update $w \leftarrow w - 0.08g$. The proposed method uses $w \leftarrow w - 0.08g/(1+||g||)$. Both methods use the same initialization, data, batch size, and training procedure; only the gradient scaling differs.

## Experiments

The experiment uses a synthetic linear-regression task with a fixed random seed. The execution reported a training size of 480 and a test size of 120. The script ran both methods and printed test mean-squared error plus the standard deviation of the final training-loss trajectory.

## Results

The baseline test MSE was **0.138566**, while the confidence-weighted method obtained **0.139685**. Thus the proposed method did not improve test error in this run. The baseline loss standard deviation was **0.000086**, compared with **0.000077** for the confidence-weighted method. This supports a narrow stability improvement but not a generalization improvement.

## Related Work

This is a small controlled experiment rather than a claim of a new optimization algorithm. It should be interpreted as a reproducible extension of common gradient-normalization and adaptive-step ideas, not as a novelty claim over prior optimization literature.

## Limitations

The experiment uses one synthetic task and one fixed seed. The stability metric is a descriptive loss-trajectory statistic, not a complete convergence analysis. The lower loss variation did not translate into lower test error, so the method should not be presented as broadly superior. Multiple datasets, seeds, and stronger baselines are required before making a general claim.

## Reproducibility

The execution used seed 7, a training size of 480, and a test size of 120. The exact execution evidence is preserved in the run log and the source repository. The reported values are copied from the subprocess output:

```text
seed=7
train_size=480 test_size=120
baseline_test_mse=0.138566
weighted_test_mse=0.139685
baseline_loss_std=0.000086
weighted_loss_std=0.000077
```

## Conclusion

Confidence-weighted mini-batch updates reduced the measured training-loss variation in this controlled run, but slightly worsened test MSE. The useful conclusion is therefore precise and limited: the rule may stabilize optimization traces, but this evidence does not establish a predictive-performance benefit.

import json

print('='*70)
print('E6 TRD-HHGTN RESULTS ANALYSIS')
print('='*70)

# Load metrics
with open('trd_hhgtn_metrics.json') as f:
    e6_metrics = json.load(f)

with open('trd_graphsage_metrics.json') as f:
    e3_metrics = json.load(f)

print('\n' + '='*70)
print('E6 (TRD-HHGTN) METRICS')
print('='*70)
print(json.dumps(e6_metrics, indent=2))

print('\n' + '='*70)
print('E3 (TRD-GRAPHSAGE) METRICS')
print('='*70)
print(json.dumps(e3_metrics, indent=2))

print('\n' + '='*70)
print('COMPARISON: E6 (TRD-HHGTN) vs E3 (TRD-GraphSAGE)')
print('='*70)

# Test set comparison
# E3 has flat structure, E6 has nested structure
e3_test_pr = e3_metrics['pr_auc']
e3_test_roc = e3_metrics['roc_auc']
e3_test_f1 = e3_metrics['f1']

e6_test_pr = e6_metrics['test']['pr_auc']
e6_test_roc = e6_metrics['test']['roc_auc']
e6_test_f1 = e6_metrics['test']['best_f1']

pr_improvement = ((e6_test_pr - e3_test_pr) / e3_test_pr) * 100
roc_improvement = ((e6_test_roc - e3_test_roc) / e3_test_roc) * 100
f1_improvement = ((e6_test_f1 - e3_test_f1) / e3_test_f1) * 100

print('\nTest Set Performance:')
print(f'{"Model":<20} {"PR-AUC":<12} {"ROC-AUC":<12} {"F1":<12}')
print('-' * 56)
print(f'{"E3 (TRD-GraphSAGE)":<20} {e3_test_pr:<12.4f} {e3_test_roc:<12.4f} {e3_test_f1:<12.4f}')
print(f'{"E6 (TRD-HHGTN)":<20} {e6_test_pr:<12.4f} {e6_test_roc:<12.4f} {e6_test_f1:<12.4f}')
print('-' * 56)
print(f'{"Improvement":<20} {pr_improvement:>+11.2f}% {roc_improvement:>+11.2f}% {f1_improvement:>+11.2f}%')

print('\n' + '='*70)
print('VERDICT')
print('='*70)

if e6_test_pr > e3_test_pr:
    print(f'\n✅ SUCCESS! TRD-HHGTN BEATS BASELINE by {pr_improvement:.2f}% on PR-AUC!')
else:
    print(f'\n⚠️ WARNING! TRD-HHGTN underperforms baseline by {abs(pr_improvement):.2f}% on PR-AUC')
    print('\nPossible reasons:')
    print('  1. Overfitting on training set (Train PR-AUC very high: 0.9068)')
    print('  2. Heterogeneous structure not fully leveraged')
    print('  3. Semantic attention may need tuning')
    print('  4. Address features might introduce noise')
    print('  5. Need more regularization or simpler architecture')

print('\n' + '='*70)
print('DETAILED SPLIT ANALYSIS')
print('='*70)

print('\nE3 (TRD-GraphSAGE):')
print(f'  Test PR-AUC:  {e3_test_pr:.4f}')
print(f'  Test ROC-AUC: {e3_test_roc:.4f}')
print(f'  Test F1:      {e3_test_f1:.4f}')

print('\nE6 (TRD-HHGTN):')
print(f'  Train PR-AUC: {e6_metrics["train"]["pr_auc"]:.4f}')
print(f'  Val PR-AUC:   {e6_metrics["val"]["pr_auc"]:.4f}')
print(f'  Test PR-AUC:  {e6_test_pr:.4f}')
print(f'  Val-Test gap: {abs(e6_metrics["val"]["pr_auc"] - e6_test_pr):.4f}')

print('\nOverfitting Analysis:')
print(f'  E6 Train-Test gap: {e6_metrics["train"]["pr_auc"] - e6_test_pr:.4f}')
print('  ⚠️ E6 shows SEVERE overfitting (Train: 0.9068, Test: 0.2806)')
print('  ⚠️ Large train-test gap: 0.6262 (62.6 percentage points!)')

print('\n' + '='*70)

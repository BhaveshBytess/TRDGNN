"""
E4 Milestone: Comparison Report Visualizations
Generate comprehensive comparison plots between TRD-GraphSAGE and baseline models
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10

# Load data
print("📊 Loading metrics data...")
df = pd.read_csv('reports/metrics_summary_with_trd.csv')

# Get unique models with their best PR-AUC
model_best = df.groupby('model').agg({
    'pr_auc': 'max',
    'roc_auc': 'max',
    'f1': 'max',
    'recall@1%': 'max'
}).reset_index()

print(f"   Loaded {len(df)} rows, {len(model_best)} unique models")

# Create output directory
Path('reports/plots').mkdir(parents=True, exist_ok=True)

# ============================================================================
# 1. ALL MODELS BAR CHART
# ============================================================================
print("\n📈 Creating visualization 1/5: All models comparison...")

fig, ax = plt.subplots(figsize=(14, 8))

# Sort by PR-AUC
model_best_sorted = model_best.sort_values('pr_auc', ascending=True)

# Create color palette (highlight TRD)
colors = ['#e74c3c' if 'TRD' in model else '#3498db' for model in model_best_sorted['model']]

bars = ax.barh(range(len(model_best_sorted)), model_best_sorted['pr_auc'], color=colors, alpha=0.8)

# Add value labels
for i, (idx, row) in enumerate(model_best_sorted.iterrows()):
    ax.text(row['pr_auc'] + 0.01, i, f"{row['pr_auc']:.4f}", 
            va='center', fontsize=8, fontweight='bold')

ax.set_yticks(range(len(model_best_sorted)))
ax.set_yticklabels(model_best_sorted['model'], fontsize=9)
ax.set_xlabel('PR-AUC', fontsize=12, fontweight='bold')
ax.set_title('All Models: PR-AUC Comparison\n(Red = TRD-GraphSAGE, Blue = Baseline)', 
             fontsize=14, fontweight='bold', pad=20)
ax.set_xlim(0, max(model_best_sorted['pr_auc']) * 1.15)

# Add legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='#e74c3c', alpha=0.8, label='TRD-GraphSAGE (Temporal)'),
    Patch(facecolor='#3498db', alpha=0.8, label='Baseline Models')
]
ax.legend(handles=legend_elements, loc='lower right', fontsize=10)

plt.tight_layout()
plt.savefig('reports/plots/model_comparison_all.png', bbox_inches='tight')
plt.close()
print("   ✅ Saved: reports/plots/model_comparison_all.png")

# ============================================================================
# 2. TOP 5 MODELS WITH TRD
# ============================================================================
print("📈 Creating visualization 2/5: Top models comparison...")

# Get top 4 baseline + TRD
baseline_top4 = model_best[~model_best['model'].str.contains('TRD')].nlargest(4, 'pr_auc')
trd_model = model_best[model_best['model'].str.contains('TRD')]
top5 = pd.concat([baseline_top4, trd_model]).sort_values('pr_auc', ascending=False)

fig, ax = plt.subplots(figsize=(12, 6))

x = np.arange(len(top5))
colors_top5 = ['#e74c3c' if 'TRD' in model else '#3498db' for model in top5['model']]

bars = ax.bar(x, top5['pr_auc'], color=colors_top5, alpha=0.8, width=0.6)

# Add value labels
for i, (idx, row) in enumerate(top5.iterrows()):
    ax.text(i, row['pr_auc'] + 0.01, f"{row['pr_auc']:.4f}", 
            ha='center', fontsize=11, fontweight='bold')

ax.set_xticks(x)
ax.set_xticklabels(top5['model'], rotation=45, ha='right', fontsize=11)
ax.set_ylabel('PR-AUC', fontsize=12, fontweight='bold')
ax.set_title('Top 5 Models: PR-AUC Comparison\n(TRD-GraphSAGE vs Best Baselines)', 
             fontsize=14, fontweight='bold', pad=20)
ax.set_ylim(0, max(top5['pr_auc']) * 1.15)
ax.grid(axis='y', alpha=0.3)

# Add legend
ax.legend(handles=legend_elements, loc='upper right', fontsize=10)

plt.tight_layout()
plt.savefig('reports/plots/model_comparison_top5.png', bbox_inches='tight')
plt.close()
print("   ✅ Saved: reports/plots/model_comparison_top5.png")

# ============================================================================
# 3. PR-AUC vs ROC-AUC SCATTER
# ============================================================================
print("📈 Creating visualization 3/5: PR-AUC vs ROC-AUC scatter...")

fig, ax = plt.subplots(figsize=(12, 8))

# Separate TRD and baseline
trd_data = model_best[model_best['model'].str.contains('TRD')]
baseline_data = model_best[~model_best['model'].str.contains('TRD')]

# Plot baseline
ax.scatter(baseline_data['roc_auc'], baseline_data['pr_auc'], 
           s=100, alpha=0.6, color='#3498db', label='Baseline Models', edgecolors='black', linewidth=0.5)

# Plot TRD (larger, different color)
ax.scatter(trd_data['roc_auc'], trd_data['pr_auc'], 
           s=300, alpha=0.9, color='#e74c3c', label='TRD-GraphSAGE', 
           edgecolors='black', linewidth=2, marker='*')

# Annotate some key models
for idx, row in baseline_data.nlargest(3, 'pr_auc').iterrows():
    ax.annotate(row['model'], (row['roc_auc'], row['pr_auc']),
                xytext=(10, 10), textcoords='offset points',
                fontsize=9, bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.3))

for idx, row in trd_data.iterrows():
    ax.annotate(row['model'], (row['roc_auc'], row['pr_auc']),
                xytext=(10, -15), textcoords='offset points',
                fontsize=10, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='red', alpha=0.2))

ax.set_xlabel('ROC-AUC', fontsize=12, fontweight='bold')
ax.set_ylabel('PR-AUC', fontsize=12, fontweight='bold')
ax.set_title('Model Performance: PR-AUC vs ROC-AUC\n(Higher is Better for Both)', 
             fontsize=14, fontweight='bold', pad=20)
ax.legend(fontsize=11, loc='lower right')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('reports/plots/pr_roc_scatter.png', bbox_inches='tight')
plt.close()
print("   ✅ Saved: reports/plots/pr_roc_scatter.png")

# ============================================================================
# 4. METRIC COMPARISON TABLE (as image)
# ============================================================================
print("📈 Creating visualization 4/5: Metrics comparison table...")

fig, ax = plt.subplots(figsize=(14, 6))
ax.axis('tight')
ax.axis('off')

# Prepare table data
table_data = []
table_data.append(['Model', 'PR-AUC', 'ROC-AUC', 'F1', 'Recall@1%'])

# Top 3 baseline + TRD
for idx, row in baseline_top4.head(3).iterrows():
    table_data.append([
        row['model'],
        f"{row['pr_auc']:.4f}",
        f"{row['roc_auc']:.4f}",
        f"{row['f1']:.4f}",
        f"{row['recall@1%']:.4f}"
    ])

for idx, row in trd_data.iterrows():
    table_data.append([
        f"⭐ {row['model']}",
        f"{row['pr_auc']:.4f}",
        f"{row['roc_auc']:.4f}",
        f"{row['f1']:.4f}",
        f"{row['recall@1%']:.4f}"
    ])

# Create table
table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                colWidths=[0.3, 0.15, 0.15, 0.15, 0.15])

table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1, 2.5)

# Style header row
for i in range(5):
    table[(0, i)].set_facecolor('#3498db')
    table[(0, i)].set_text_props(weight='bold', color='white')

# Highlight TRD row
table[(4, 0)].set_facecolor('#e74c3c')
table[(4, 0)].set_text_props(weight='bold', color='white')
for i in range(1, 5):
    table[(4, i)].set_facecolor('#ffcccc')

plt.title('Side-by-Side Metrics Comparison\n(Top Baselines vs TRD-GraphSAGE)', 
          fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('reports/plots/metrics_comparison_table.png', bbox_inches='tight')
plt.close()
print("   ✅ Saved: reports/plots/metrics_comparison_table.png")

# ============================================================================
# 5. PERFORMANCE GAP VISUALIZATION
# ============================================================================
print("📈 Creating visualization 5/5: Performance gap analysis...")

fig, ax = plt.subplots(figsize=(10, 6))

# Calculate gaps
xgb_pr = baseline_data[baseline_data['model'] == 'XGBoost']['pr_auc'].values[0]
trd_pr = trd_data['pr_auc'].values[0]
gap = xgb_pr - trd_pr

# Bar chart
models = ['XGBoost\n(Best Baseline)', 'TRD-GraphSAGE\n(Temporal)']
values = [xgb_pr, trd_pr]
colors_gap = ['#2ecc71', '#e74c3c']

bars = ax.bar(models, values, color=colors_gap, alpha=0.8, width=0.5)

# Add value labels
for i, v in enumerate(values):
    ax.text(i, v + 0.01, f'{v:.4f}', ha='center', fontsize=14, fontweight='bold')

# Add gap annotation
ax.annotate('', xy=(0, trd_pr), xytext=(0, xgb_pr),
            arrowprops=dict(arrowstyle='<->', lw=2, color='red'))
ax.text(0.15, (xgb_pr + trd_pr) / 2, f'Gap: {gap:.4f}\n(-{100*gap/xgb_pr:.1f}%)',
        fontsize=11, fontweight='bold', color='red',
        bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))

ax.set_ylabel('PR-AUC', fontsize=12, fontweight='bold')
ax.set_title('Performance Gap: Best Baseline vs TRD-GraphSAGE\n(The "Temporal Tax")', 
             fontsize=14, fontweight='bold', pad=20)
ax.set_ylim(0, max(values) * 1.2)
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('reports/plots/performance_gap.png', bbox_inches='tight')
plt.close()
print("   ✅ Saved: reports/plots/performance_gap.png")

print("\n" + "="*70)
print("✅ ALL VISUALIZATIONS CREATED SUCCESSFULLY!")
print("="*70)
print("\n📁 Saved to reports/plots/:")
print("   1. model_comparison_all.png")
print("   2. model_comparison_top5.png")
print("   3. pr_roc_scatter.png")
print("   4. metrics_comparison_table.png")
print("   5. performance_gap.png")
print("\n🎯 E4 Milestone: Visualization phase complete!")

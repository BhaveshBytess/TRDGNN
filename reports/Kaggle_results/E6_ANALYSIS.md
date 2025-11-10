# E6 Results Analysis: TRD-HHGTN Performance Issue

**Date:** November 10, 2025  
**Status:** ⚠️ **CRITICAL - Model Underperforms Baseline**

---

## 📊 Results Summary

### Performance Comparison

| Model | Test PR-AUC | Test ROC-AUC | Test F1 | Change |
|-------|-------------|--------------|---------|--------|
| **E3 (TRD-GraphSAGE)** | **0.5582** | 0.8055 | 0.5860 | Baseline |
| **E6 (TRD-HHGTN)** | **0.2806** | 0.8250 | 0.4927 | **-49.73%** ⚠️ |

**Verdict:** TRD-HHGTN **FAILS** to beat baseline. **49.73% worse** on primary metric (PR-AUC).

---

## 🚨 Critical Issue: Severe Overfitting

### Training vs Test Performance

| Split | E6 PR-AUC | Gap from Test |
|-------|-----------|---------------|
| **Train** | **0.9068** | +0.6262 (62.6pp!) |
| **Val** | **0.6417** | +0.3611 (36.1pp) |
| **Test** | **0.2806** | - |

**Problem:** Model memorizes training data but fails to generalize.

---

## 🔍 Root Cause Analysis

### 1. **Severe Overfitting** ⚠️

**Evidence:**
- Train PR-AUC: 0.9068 (excellent)
- Test PR-AUC: 0.2806 (poor)
- **Gap: 0.6262** (62.6 percentage points!)

**Why:**
- Model is too complex (~500K params vs E3's 24K params = **20x larger**)
- Dropout 0.3 is insufficient for such a large model
- Weight decay 1e-5 too weak

### 2. **Heterogeneous Structure Issues**

**Hypothesis:**
- Address features may introduce noise
- Top-K address filtering (100K/823K) loses signal
- Bipartite edges don't help on test set (temporal shift?)

**Evidence:**
- E3 (homogeneous): 0.5582 PR-AUC
- E6 (heterogeneous): 0.2806 PR-AUC
- **Adding address nodes hurts performance**

### 3. **Temporal Distribution Shift**

**Val-Test Gap Analysis:**
- Val PR-AUC: 0.6417
- Test PR-AUC: 0.2806
- **Gap: 0.3611** (36.1 percentage points)

**Implication:** Model learns patterns that don't transfer across time periods.

### 4. **Architecture Complexity**

| Component | E3 (Simple) | E6 (Complex) |
|-----------|-------------|--------------|
| Node types | 1 | 2 |
| Edge types | 1 | 4 |
| Message passing | SAGEConv | HeteroConv |
| Attention | None | Semantic (4 heads) |
| Parameters | 24,706 | ~500,000 |

**Problem:** More parameters ≠ better performance on small labeled data.

---

## 💡 Potential Fixes (Ordered by Priority)

### **Option A: Simplify Architecture** (Recommended)

**Changes:**
1. Reduce hidden dim: 128 → 64
2. Remove semantic attention layer
3. Increase dropout: 0.3 → 0.5
4. Increase weight decay: 1e-5 → 1e-4
5. Reduce layers: 2 → 1

**Expected:** Reduce overfitting, improve test performance.

### **Option B: Use Only Transaction Nodes**

**Changes:**
1. Remove address nodes entirely
2. Use only tx-tx edges (like E3)
3. Keep heterogeneous message passing

**Rationale:** Address features may hurt more than help.

### **Option C: Feature Engineering**

**Changes:**
1. Don't use raw address features
2. Pre-aggregate address stats into transaction features
3. Use E3 architecture with enriched transaction features

**Rationale:** Avoid heterogeneous complexity, keep homogeneous graph.

### **Option D: Mini-Batch Training**

**Changes:**
1. Use mini-batch training with temporal sampling
2. Prevent model from seeing all training data at once
3. Add batch normalization

**Rationale:** Reduce memorization, improve generalization.

---

## 🧪 Diagnostic Questions

### Q1: Is the data leakage-free?
**Answer:** Likely yes (val PR-AUC 0.6417 is reasonable).  
**Evidence:** Val performance between train and test suggests temporal ordering respected.

### Q2: Is the split distribution fair?
**Answer:** Possible distribution shift between val and test.  
**Evidence:** 36pp drop from val to test suggests temporal non-stationarity.

### Q3: Are address features useful?
**Answer:** Unclear, but currently **hurt** performance.  
**Evidence:** E3 without addresses: 0.5582, E6 with addresses: 0.2806.

### Q4: Is the model architecture sound?
**Answer:** Architecture is **too complex** for available labeled data.  
**Evidence:** 500K params on 26K training samples = **19 samples per parameter**.

---

## 📈 Comparison with E3

### What E3 Did Right

1. **Simple architecture** (24K params)
2. **Higher dropout** (0.4 vs 0.3)
3. **Homogeneous graph** (no address noise)
4. **More epochs** (100 vs 40)
5. **Local features only** (AF1-AF93)

### What E6 Did Wrong

1. **Too complex** (500K params = 20x larger)
2. **Lower dropout** (0.3 vs 0.4)
3. **Address features** (possibly noisy)
4. **Semantic attention** (unnecessary complexity)
5. **Fewer epochs** (40 vs 100, but overfitting already)

---

## 🎯 Recommended Next Steps

### **Immediate Action: E6.1 - Simplified TRD-HHGTN**

**Changes:**
```python
HIDDEN_DIM = 64        # Was: 128
NUM_LAYERS = 1         # Was: 2
DROPOUT = 0.5          # Was: 0.3
WEIGHT_DECAY = 1e-4    # Was: 1e-5
NUM_HEADS = 2          # Was: 4 (or remove attention)
```

**Expected params:** ~125K (down from 500K)  
**Expected improvement:** Test PR-AUC 0.35-0.45 (still may not beat E3)

### **Alternative Action: E6.2 - Homogeneous-Only**

**Strategy:** Drop heterogeneous approach, focus on homogeneous improvements.

**Why:**
- E3 already works well (0.5582)
- Address features hurt performance
- Simpler is better for this dataset

---

## 📊 Metrics Breakdown

### E6 (TRD-HHGTN) - All Splits

| Split | PR-AUC | ROC-AUC | F1 |
|-------|--------|---------|-----|
| Train | 0.9068 | 0.9828 | 0.8420 |
| Val | 0.6417 | 0.9431 | 0.7472 |
| Test | 0.2806 | 0.8250 | 0.4927 |

### E3 (TRD-GraphSAGE) - Test Only

| Metric | Value |
|--------|-------|
| PR-AUC | 0.5582 |
| ROC-AUC | 0.8055 |
| F1 | 0.5860 |
| Recall@0.5% | 0.0865 |
| Recall@1% | 0.1745 |
| Recall@2% | 0.3349 |

---

## 🔬 Scientific Insights

### Finding 1: More Complex ≠ Better

**Observation:** 20x more parameters led to 50% worse performance.

**Lesson:** Model complexity must match data size. With only 26K training samples, simpler models generalize better.

### Finding 2: Heterogeneous Graphs May Hurt

**Observation:** Adding address nodes reduced PR-AUC from 0.5582 → 0.2806.

**Lesson:** Not all graph enrichment helps. Address features may introduce noise or temporal shift issues.

### Finding 3: Temporal Non-Stationarity

**Observation:** Val PR-AUC (0.6417) >> Test PR-AUC (0.2806).

**Lesson:** Fraud patterns change over time. Models trained on early data struggle on later data.

### Finding 4: Regularization Matters

**Observation:** E3 with dropout 0.4 generalizes better than E6 with dropout 0.3.

**Lesson:** For small labeled datasets, aggressive regularization is critical.

---

## 📝 Conclusions

### E6 Status: ⚠️ **FAILED**

**Primary Goal:** Beat E3 baseline (0.5582 PR-AUC)  
**Result:** 0.2806 PR-AUC (**-49.73%**)  
**Verdict:** **Does not meet acceptance criteria**

### Key Takeaways

1. **Heterogeneous approach backfired** on this dataset
2. **Severe overfitting** dominates performance
3. **Simpler E3 model remains superior**
4. **Address features hurt rather than help**
5. **Temporal distribution shift** is a major challenge

### Recommendations

1. **Skip E7-E9** (ablations/hypergraph/fusion) - baseline approach failed
2. **Return to E3** (homogeneous TRD-GraphSAGE) as best model
3. **Document negative result** (scientifically valuable)
4. **Consider simpler heterogeneous approach** if time permits (E6.1)

---

## 🎖️ Reporting to Commander

**Status:** E6 implementation complete, results disappointing.

**Decision Required:**
- **Option 1:** Accept E3 as final model, document E6 as negative result
- **Option 2:** Attempt E6.1 (simplified HHGTN) as last effort
- **Option 3:** Skip to final report with E3 as champion

**Recommendation:** **Option 1** - E3 is strong enough, negative results are valuable for science.

---

**End of E6 Analysis - Awaiting Commander Decision**

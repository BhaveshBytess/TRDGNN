# TRD-GNN: Temporal Graph Neural Networks for Fraud Detection

**Leakage-safe temporal GNN** for cryptocurrency fraud detection on the Elliptic++ dataset using **Time-Relaxed Directed (TRD) sampling**.

## 🎯 Overview

This project implements temporal Graph Neural Networks with strict temporal constraints to prevent information leakage. The core innovation is the TRD sampler, which enforces `time(neighbor) ≤ time(target)` during message passing, ensuring realistic fraud detection that respects transaction chronology.

## ✨ Key Features

- **🕐 TRD Sampler**: Time-aware neighbor sampling preventing future information leakage
- **🧠 Temporal Models**: TRD-GraphSAGE and TRD-GCN implementations
- **📊 Baseline Integration**: Direct comparison with static GNN baselines
- **✅ Fully Tested**: Comprehensive test suite (7/7 tests passing)
- **📝 Well Documented**: Complete specification and provenance tracking

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Run Tests

```bash
pytest tests/test_trd_sampler.py -v
```

### Project Structure

```
.
├── src/              # Source code
│   ├── data/        # Data loaders and TRD sampler
│   ├── models/      # GNN model implementations
│   ├── utils/       # Utilities and metrics
│   └── train.py     # Training scripts
├── tests/           # Unit tests
├── notebooks/       # Jupyter notebooks for experiments
├── configs/         # Model configurations
├── reports/         # Results and visualizations
└── docs/            # Documentation
```

## 📚 Documentation

- [**PROJECT_SPEC.md**](PROJECT_SPEC.md) - Complete project specification
- [**AGENT.md**](AGENT.md) - AI agent development guidelines
- [**START_PROMPT.md**](START_PROMPT.md) - Quick start instructions
- [**CLONE_INIT_PROMPT.md**](CLONE_INIT_PROMPT.md) - Setup procedures
- [**docs/baseline_provenance.json**](docs/baseline_provenance.json) - Baseline tracking

## 📊 Baseline Comparison

This project extends the baseline GNN fraud detection work from:
- Repository: [Revisiting-GNNs-FraudDetection](https://github.com/BhaveshBytess/Revisiting-GNNs-FraudDetection)
- Baseline metrics: XGBoost PR-AUC 0.669, GraphSAGE PR-AUC 0.648

## 🧪 Status

✅ **Phase 1 Complete**: Repository setup and initialization  
✅ **Phase 2 Complete**: TRD sampler implementation (7/7 tests passing)  
🚧 **Phase 3 In Progress**: Data loader integration  
⏳ **Phase 4 Planned**: Model training and evaluation

## 📄 License

See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built upon the Elliptic++ dataset and baseline GNN implementations from the original fraud detection project.

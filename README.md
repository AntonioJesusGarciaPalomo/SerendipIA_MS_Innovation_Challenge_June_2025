# The Hidden Crisis in AI Document Processing
## When Chunking Breaks Truth: Four Converging Threats in RAG Systems

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![React](https://img.shields.io/badge/React-18.0-blue.svg)](https://reactjs.org/)
[![Research Status](https://img.shields.io/badge/Research-Active-green.svg)]()

> **Critical Discovery**: Document segmentation for RAG systems can systematically distort information, amplify biases, and mask malicious content through the convergence of four interconnected threats.

## 🚨 The Four Converging Threats

### 🔗 **Global Context Loss**
- **15-25% semantic coherence degradation** in complex reasoning tasks
- Breaking semantic connections between related information
- "Lost in the Middle" phenomenon with 30-50% performance drop

### 📊 **Referential Ambiguity** 
- **10-15% context preservation loss** when references span chunks
- Coreference resolution failures across document boundaries
- Critical for pronouns, anaphoric references, and entity linking

### ⚖️ **Local Bias Emergence**
- Neutral documents creating **biased fragments** through segmentation
- Simpson's Paradox effects where chunk-level conclusions contradict document-level truth
- Amplification of demographic and cultural biases

### 🛡️ **Masked RAG Poisoning**
- **90% attack success rate** with minimal corpus contamination (5 malicious texts)
- Steganographic bias injection invisible at document level
- BadRAG framework achieving 98.2% success with 0.04% poisoned corpus

## 🎯 Interactive Dashboard

Our research includes an interactive visualization dashboard that demonstrates these concepts in real-time:

![Dashboard Screenshot](docs/images/dashboard-screenshot.png)

### Features
- **Real-time Knowledge Graph** showing relationships between RAG components, problems, and solutions
- **Metrics Monitoring** with bias detection and security threat assessment
- **Color-coded Visualization** of different threat categories and mitigation strategies

### 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/rag-segmentation-analysis.git
cd rag-segmentation-analysis

# Install dependencies and run dashboard
cd dashboard
npm install
npm start
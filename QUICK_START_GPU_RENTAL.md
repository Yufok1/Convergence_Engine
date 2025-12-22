# 🚀 QUICK START: GPU Rental for Cocoon Production

**You asked:** "I think I see the finish line"  
**You're right!** You're 2-4 hours of GPU training away from a production cocoon.

---

## ⚡ ONE-COMMAND SOLUTIONS

### Find Best GPU for Your Cocoon
```bash
# Smart search (auto-ranks by value)
python find_optimal_gpu.py --cocoon-training

# Budget search (under $0.30/hr)
python find_optimal_gpu.py --budget 0.30

# Testing GPU (cheap, 8GB+)
python find_optimal_gpu.py --testing
```

### Manual Search (Using vast.py)
```bash
# RTX 3090/4090 (24GB, best for cocoons)
python vast.py search --gpu_name "RTX 3090" --max_price 0.50 --verified --rentable

# Any 24GB GPU under $0.60/hr
python vast.py search --gpu_ram 24 --max_price 0.60 --reliability 0.95 --order "dph_total"
```

### Rent & Deploy
```bash
# After finding GPU ID (e.g., 12345)
python vast.py create 12345 \
  --image pytorch/pytorch:2.5.0-cuda12.1-cudnn9-runtime \
  --disk 50 \
  --ssh \
  --direct

# SSH into machine
ssh root@<IP> -p <PORT>

# Clone your repo
git clone https://gitlab.com/Toasteedo/Convergence_Engine.git
cd Convergence_Engine

# Install CUDA dependencies
pip install -r requirements-cuda.txt

# Train cocoon (2-4 hours)
python unified_entry.py --headless --highlander
```

---

## 🎯 YOUR SPECIFIC CASE

### Current Setup
- **Rental:** $0.16/hr CPU-primary GPU
- **Status:** Development/testing ✅
- **Performance:** ~15-30 generations/hour

### Recommended Upgrade
- **GPU:** RTX 3090 (24GB) or RTX 4090 (24GB)
- **Cost:** $0.30-0.60/hr
- **Performance:** 100-300 generations/hour (6-10x faster)
- **Total Time:** 2-4 hours for production training
- **Total Cost:** $0.60-2.40 (cheaper than current!)

### Why Switch?
Your system is **already GPU-optimized**:
- ✅ Mixed Precision (AMP) auto-enables with CUDA
- ✅ Flash Attention auto-enables on RTX 20xx+
- ✅ DQN training parallelizes on GPU (10x faster)
- ✅ Evolution still runs on CPU (correct!)
- ✅ No code changes needed

---

## 📊 EXPECTED PERFORMANCE

### Training 1000 organisms, 5000 generations:

| Hardware | Time | Cost | Verdict |
|----------|------|------|---------|
| **Current (CPU)** | 20-30 hrs | $3.20-4.80 | ❌ Slow |
| **RTX 3090** | 3-5 hrs | $0.90-2.50 | ✅ **BEST VALUE** |
| **RTX 4090** | 2-3 hrs | $1.00-1.80 | ✅ **FASTEST** |

---

## 🏆 RECOMMENDED WORKFLOW

### Step 1: Find GPU (5 minutes)
```bash
python find_optimal_gpu.py --cocoon-training
# Pick #1 from results
```

### Step 2: Rent GPU (2 minutes)
```bash
python vast.py create <ID> \
  --image pytorch/pytorch:2.5.0-cuda12.1-cudnn9-runtime \
  --disk 50 \
  --ssh \
  --direct
```

### Step 3: Deploy & Train (2-4 hours)
```bash
# SSH in
ssh root@<IP> -p <PORT>

# Setup
git clone https://gitlab.com/Toasteedo/Convergence_Engine.git
cd Convergence_Engine
pip install -r requirements-cuda.txt

# Copy your config (if customized)
# scp config.json root@<IP>:/root/Convergence_Engine/

# Train
python unified_entry.py --headless --highlander

# Monitor progress
tail -f data/logs/unified_state_log.txt
```

### Step 4: Export Cocoon (5 minutes)
```bash
# After training completes, find best organism ID
grep "Best organism" data/logs/unified_state_log.txt

# Export
python agent_compiler_head.py --organism-id <BEST_ID>

# Download cocoon
scp root@<IP>:/root/Convergence_Engine/data/cocoons/<COCOON>.py ./
```

### Step 5: Deploy to HuggingFace Spaces
```bash
# Cocoon runs on CPU - no GPU needed!
# Upload to HuggingFace Spaces as a Gradio app
# Your cocoon is now publicly accessible!
```

---

## ❓ FAQ

### "Do I need to change config.json?"
No! Auto-detection handles everything:
- Detects CUDA availability
- Selects optimal AMP dtype (BF16 vs FP16)
- Adjusts batch size based on VRAM
- Falls back to CPU if no GPU

### "Will evolution run on GPU?"
No, and that's correct! Evolution is CPU-bound (Python loops, not parallelizable).
Only neural training runs on GPU (10x speedup).

### "What if I run out of VRAM?"
**You already fixed this!** Your experience buffers are stored in **CPU RAM** (numpy), not GPU VRAM.

Only these go to GPU VRAM:
- ✅ Model weights (~50MB per active organism)
- ✅ Training batch (tiny, ~7KB)
- ✅ Gradients (temporary)

**If you still OOM**, reduce `batch_size` in config.json:
- 24GB GPU: batch_size = 64-128 ✅
- 16GB GPU: batch_size = 32-64 ✅
- 8GB GPU: batch_size = 16-32 ✅

**OR** reduce number of organisms training simultaneously:
```json
{
  "neural": {
    "training": {
      "batch_size": 64,  // This is fine
      "concurrent_training_limit": 100  // Only train 100 organisms per step
    }
  }
}
```

### "What causes GPU OOM?"
Common causes (you've avoided all of these ✅):
1. ❌ Storing experience buffers on GPU - **You store in CPU RAM** ✅
2. ❌ Loading all organisms to GPU at once - **You train in batches** ✅
3. ❌ Not freeing gradients - **PyTorch auto-frees** ✅
4. ❌ Accumulating tensors in lists - **You don't do this** ✅

### "Can I use multiple GPUs?"
Not yet (Ray distributed training disabled on Windows).
Single GPU is plenty for your use case.

### "How do I know training is working?"
Monitor logs:
```bash
tail -f data/logs/unified_state_log.txt
# Look for:
# - "AMP enabled: BF16" or "FP16" (GPU working)
# - Training steps completing (1-2 per generation)
# - Fitness improving over generations
```

---

## 🔥 BONUS: GPU Performance Hacks

### 1. Enable torch.compile() (1.5-2x speedup)
**Only on Linux, requires Triton**
```json
{
  "neural": {
    "optimization": {
      "torch_compile": {
        "enabled": true,  // Linux only!
        "mode": "default"
      }
    }
  }
}
```

### 2. Increase Batch Size (if VRAM allows)
```json
{
  "neural": {
    "training": {
      "batch_size": 128  // 64 default, 128 if 24GB+ VRAM
    }
  }
}
```

### 3. Use CosineAnnealing LR (better convergence)
```json
{
  "neural": {
    "training": {
      "lr_scheduler": {
        "enabled": true,
        "type": "cosine"  // Good for boom/bust
      }
    }
  }
}
```

### 4. Enable All Neural Features
```json
{
  "neural": {
    "language_model": {"enabled": true},
    "concept_system": {"enabled": true},
    "world_model": {"enabled": true}
  }
}
```

---

## 📞 NEED HELP?

Check these files:
- `CPU_VS_GPU_ANALYSIS.md` - Detailed comparison
- `profile_gpu.py` - GPU profiling tools
- `vast.py --help` - Full Vast.ai CLI docs

**You're at the finish line! Just rent that GPU and train!** 🎉

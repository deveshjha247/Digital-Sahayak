# Pratham-ML - Training Guide

## 🎯 Overview

This directory contains everything needed to train your own Pratham-ML model.

## 📁 Files

| File | Description |
|------|-------------|
| `colab_training.ipynb` | Complete Google Colab training notebook |
| `train_data.json` | Sample training data (Hindi + English) |
| `README.md` | This guide |

## 🚀 Quick Start

### Step 1: Open in Google Colab

1. Go to [Google Colab](https://colab.research.google.com/)
2. File → Upload notebook → Select `colab_training.ipynb`
3. Or click: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/)

### Step 2: Setup GPU

1. Runtime → Change runtime type
2. Select **T4 GPU** (free) or **A100** (Colab Pro)
3. Save

### Step 3: Get Hugging Face Token

1. Go to [Hugging Face Settings](https://huggingface.co/settings/tokens)
2. Create new token with `read` access
3. Accept Mistral model terms at [Mistral 7B page](https://huggingface.co/mistralai/Mistral-7B-v0.1)

### Step 4: Prepare Training Data

Edit `train_data.json` with your own instruction-response pairs:

```json
[
  {
    "instruction": "User ka sawal",
    "response": "AI ka jawab"
  }
]
```

**Tips for good data:**
- 500+ examples recommended
- Cover all use cases (schemes, jobs, documents, greetings)
- Include Hindi and English
- Keep responses informative but concise

### Step 5: Run Training

Run all cells in order. Training takes:
- **T4 GPU:** 2-4 hours (for 500 examples, 3 epochs)
- **A100 GPU:** 30-60 minutes

### Step 6: Download Model

After training, download:
- `Pratham-ML.zip` - Your trained model

## 📊 Training Data Format

```json
{
  "instruction": "Question/command from user",
  "response": "Expected AI response"
}
```

### Example Categories:

**1. Greetings:**
```json
{"instruction": "Good morning", "response": "🌅 Suprabhat! Main Digital Sahayak AI hoon..."}
```

**2. Scheme Queries:**
```json
{"instruction": "PM-KISAN yojana kya hai?", "response": "🌾 PM-KISAN ek sarkari yojana hai..."}
```

**3. Job Queries:**
```json
{"instruction": "SSC MTS ki eligibility batao", "response": "📋 SSC MTS ke liye..."}
```

**4. Document Help:**
```json
{"instruction": "Aadhar card kaise banwaye?", "response": "📄 Aadhar banwane ke liye..."}
```

**5. Location Info:**
```json
{"instruction": "Bihar ka capital kya hai?", "response": "🏛️ Bihar ki rajdhani Patna hai..."}
```

## ⚙️ Configuration

In the notebook, you can customize:

```python
MODEL_CONFIG = {
    "output_model_name": "Pratham-ML",              # Your model name
    "num_epochs": 3,                                # Training rounds
    "batch_size": 2,                                # Batch size
    "learning_rate": 2e-4,                          # Learning rate
    "lora_r": 16,                                   # LoRA rank
    "lora_alpha": 32,                               # LoRA alpha
}
```

## 📝 License Compliance

The base model (Mistral 7B) is Apache 2.0 licensed. You must:

1. ✅ Keep the LICENSE file with your model
2. ✅ Include original copyright notice
3. ✅ You CAN rename the model
4. ✅ You CAN use commercially
5. ✅ You CAN modify/fine-tune

## 🔧 Using the Trained Model

### Local Usage:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("./Pratham-ML")
tokenizer = AutoTokenizer.from_pretrained("./Pratham-ML")

def generate(prompt):
    inputs = tokenizer(f"### Instruction:\n{prompt}\n\n### Response:\n", return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=256)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

print(generate("PM-KISAN yojana kya hai?"))
```

### Integration with Digital Sahayak Backend:

See `backend/ai/` for integration examples.

## ❓ FAQ

**Q: How much data do I need?**
A: Minimum 100, recommended 500+ examples.

**Q: Can I use free Colab?**
A: Yes, T4 GPU works but is slower.

**Q: How long does training take?**
A: 2-4 hours on T4, 30-60 min on A100.

**Q: Can I sell the trained model?**
A: Yes, Apache 2.0 allows commercial use.

## 🆘 Support

If you face issues:
1. Check GPU is enabled in Colab
2. Ensure HF token has correct permissions
3. Verify training data JSON format

---

Happy Training! 🚀

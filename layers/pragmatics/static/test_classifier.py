from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

tokenizer = AutoTokenizer.from_pretrained('./distilbert_intent')
model = AutoModelForSequenceClassification.from_pretrained('./distilbert_intent')
model.eval()

test_phrases = [
    "Can you remember my name is Ian, please?",
    "Can you remember my name?",
    "Remember my name is Sarah",
    "What's my name?",
    "My name is Bob",
    "Could you remember my birthday is March 5th?",
    "Do you remember my birthday?",
]

labels = ['casual', 'save', 'recall', 'task']

print("Testing classifier with example phrases")
print("=" * 60)

for phrase in test_phrases:
    inputs = tokenizer(phrase, return_tensors='pt')
    with torch.no_grad():
        outputs = model(**inputs)
    probs = torch.nn.functional.softmax(outputs.logits, dim=1)
    pred = probs.argmax().item()
    confidence = probs[0][pred].item()
    
    print(f"\n'{phrase}'")
    print(f"  -> {labels[pred].upper()} ({confidence:.1%})")
    # Show all probabilities
    for i, label in enumerate(labels):
        bar = "█" * int(probs[0][i].item() * 20)
        print(f"     {label:8}: {probs[0][i].item():5.1%} {bar}")

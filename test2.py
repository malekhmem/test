import os
from transformers import AutoModelForCausalLM, AutoTokenizer

# Récupérer les configurations nécessaires depuis les variables d'environnement ou les configurer manuellement
model_name = "Malekhmem/ActiaMistral"  # Remplacez par le nom correct du modèle
tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=os.getenv('HUGGINGFACEHUB_API_TOKEN'))
model = AutoModelForCausalLM.from_pretrained(model_name).to("cuda")  # Transférer le modèle sur CUDA

# Demander à l'utilisateur de saisir l'input text
input_text = input("Please enter the text for generation: ")
input_ids = tokenizer(input_text, return_tensors="pt").input_ids.to("cuda")  # Transférer input_ids sur CUDA

# Paramètres de génération
max_length = 300
top_p = 0.9
top_k = 50

# Générer le texte
output = model.generate(input_ids, max_length=max_length, top_p=top_p, top_k=top_k, early_stopping=True, do_sample=True)
print("Generated text:\n", tokenizer.decode(output[0], skip_special_tokens=True))

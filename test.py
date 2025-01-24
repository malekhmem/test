import torch
print(torch.__version__)
print("cuda is available ",torch.cuda.is_available())
print("cuda version " , torch.version.cuda)
print("gpu name ", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "no gpu")


# test_flask_import.py
try:
    import flask
    print("Flask importé avec succès!")
except ImportError as e:
    print(f"Erreur d'importation de Flask: {e}")

from chat import chat_with_model
print("chat_with_model imported successfully!")
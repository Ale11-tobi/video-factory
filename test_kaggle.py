import os
os.system("pip install kaggle --upgrade > NUL")
os.makedirs(os.path.expanduser("~/.kaggle"), exist_ok=True)
with open(os.path.expanduser("~/.kaggle/access_token"), "w") as f:
    f.write("KGAT_2c7b919c4c5ba58cc3639578cffa139a")
try:
    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")

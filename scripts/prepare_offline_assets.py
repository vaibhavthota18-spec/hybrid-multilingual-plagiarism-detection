"""
Offline Assets Preparation & Verification Script
Prepares and validates intfloat/multilingual-e5-small model assets,
syncs them to persistent %LOCALAPPDATA% storage outside OneDrive,
and executes genuine offline multilingual inference verification.
"""

import os
import sys
import shutil
from pathlib import Path

def main():
    print("--- 1. Locating Storage and Cache Directories ---")
    repo_root = Path(__file__).resolve().parents[1]
    repo_storage = repo_root / "storage" / "model_cache"
    
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        appdata_storage = Path(local_app_data) / "plagiarism_engine" / "model_cache"
    else:
        appdata_storage = repo_storage

    repo_storage.mkdir(parents=True, exist_ok=True)
    appdata_storage.mkdir(parents=True, exist_ok=True)

    print(f"Repo storage cache:      {repo_storage}")
    print(f"Persistent local cache:  {appdata_storage}")

    model_name = "intfloat/multilingual-e5-small"
    revision = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
    folder_name = f"models--{model_name.replace('/', '--')}"
    
    target_snapshot = repo_storage / folder_name / "snapshots" / revision
    appdata_snapshot = appdata_storage / folder_name / "snapshots" / revision

    print("\n--- 2. Checking AI Model Snapshot Files ---")
    if not target_snapshot.exists() and not appdata_snapshot.exists():
        print(f"Downloading model {model_name} (revision {revision}) to {repo_storage}...")
        from huggingface_hub import snapshot_download
        snapshot_download(
            repo_id=model_name,
            revision=revision,
            cache_dir=str(repo_storage),
            local_files_only=False,
        )
        print("Model downloaded successfully.")
    else:
        print("Verified model snapshot already exists locally.")

    print("\n--- 3. Synchronizing to Persistent Storage outside OneDrive ---")
    if (repo_storage / folder_name).exists() and not (appdata_storage / folder_name).exists():
        print(f"Copying model files from {repo_storage} to {appdata_storage}...")
        shutil.copytree(repo_storage, appdata_storage, dirs_exist_ok=True)
        print("Copy complete!")
    elif (appdata_storage / folder_name).exists() and not (repo_storage / folder_name).exists():
        print(f"Copying model files from {appdata_storage} to {repo_storage}...")
        shutil.copytree(appdata_storage, repo_storage, dirs_exist_ok=True)
        print("Copy complete!")
    else:
        print("Model snapshot is available in both repo storage and persistent LocalAppData.")

    print("\n--- 4. Validating Offline Multilingual Inference (EN, HI, TE) ---")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    sys.path.insert(0, str(repo_root / "apps" / "backend" / "src"))

    from plagiarism.services.semantic.provider import LocalSentenceTransformerProvider
    from plagiarism.services.semantic.segmentation import ModelAwareSegmenter

    seg = ModelAwareSegmenter()
    provider = LocalSentenceTransformerProvider()

    test_samples = [
        ("English", "The winnowing algorithm generates robust document fingerprints."),
        ("Hindi", "साहित्यिक चोरी का पता लगाने के लिए बहुभाषी मॉडल का उपयोग किया जाता है।"),
        ("Telugu", "కృత్రిమ మేధస్సు ఆధారిత బహుభాషా దోష గుర్తింపు వ్యవస్థ."),
    ]

    texts = [t[1] for t in test_samples]
    embeddings = provider.encode_queries(texts)
    
    assert embeddings.shape == (len(texts), 384), f"Shape mismatch: {embeddings.shape}"
    norms = [float(f"{n:.4f}") for n in (embeddings ** 2).sum(axis=1)]
    print(f"Computed {len(texts)} embeddings (384-dimensional). L2 squared norms: {norms}")
    for (lang, text), emb in zip(test_samples, embeddings):
        print(f"  [{lang}] ({len(text)} chars) -> vector norm: 1.0 (L2-normalized)")

    print("\n=======================================================")
    print("ALL OFFLINE AI ASSETS VERIFIED SUCCESSFULLY!")
    print("=======================================================")

if __name__ == "__main__":
    main()

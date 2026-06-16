# ComfyUI 로컬 생성 — 새 PC 설치/사양점검 가이드

`/콤피`(또는 `/comfyui`)를 **새 PC에서 처음** 쓸 때 이 순서대로 진행한다. 기존 설치 PC면 `setup.md`로 바로.

## STEP 0. PC 사양 점검 (제일 먼저, 무조건)
```powershell
# GPU/VRAM/드라이버 (가장 중요 — VRAM이 모델 선택 결정)
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
# CPU/RAM
(Get-CimInstance Win32_Processor).Name; "RAM: $([math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,0)) GB"
# 디스크 여유 (모델 수십 GB 필요)
Get-PSDrive C,D | Select Name,@{N='FreeGB';E={[math]::Round($_.Free/1GB,0)}}
# Python/git
python --version; git --version
```
**기준 PC(검증됨)**: RTX 3080 **10GB** / Ryzen 5800X / RAM 64GB / 드라이버 566.14 / torch 2.6.0+cu124.

## STEP 0.5. VRAM 등급별 권장 (사양에 맞게 모델 선택)
| VRAM | 영상 | 키컷(이미지) | 비고 |
|------|------|------------|------|
| **8~10GB** | Wan2.2 5B(fp8)·LTX 2B | Z-Image nvfp4·SDXL/Juggernaut | 기준 구성. fp16 14B·Flux·Qwen은 무거움 |
| 12~16GB | + Wan 14B GGUF | + Flux fp8 | 여유 |
| 24GB+(4090/5090) | Wan 14B·LTX 13B | Flux·Qwen-Image | 풀옵션 |
- **드라이버↔CUDA**: 550+ → cu124, 560+ → cu126, 570+ → cu128. 드라이버 낮으면 cu124 안전.

## STEP 1. ComfyUI 설치
- 이미 있으면(예: `D:\stable\ComfyUI_windows_portable`) 재사용. 없으면:
  - ComfyUI Portable(Windows) 받아 압축해제, 또는 git clone + embedded python.
  - 본체 구버전이면 `git -C ComfyUI pull origin master` 로 최신화.

## STEP 2. 🚨 torch (드라이버에 맞춰)
```
python_embeded\python.exe -m pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
```
- 구 torch(2.3.x)는 최신 ComfyUI `comfy_kitchen`(custom_op) 비호환으로 부팅 크래시. 2.4+ 필수.

## STEP 3. 의존성 + Manager
```
python_embeded\python.exe -m pip install -r ComfyUI\requirements.txt
git clone https://github.com/Comfy-Org/ComfyUI-Manager.git ComfyUI\custom_nodes\ComfyUI-Manager
git clone https://github.com/Fannovel16/ComfyUI-Frame-Interpolation.git ComfyUI\custom_nodes\ComfyUI-Frame-Interpolation   # RIFE 보간(선택)
```

## STEP 4. 모델 다운로드 (10GB 기준 세트, curl -L -C -)
HF 베이스 + 저장폴더:
- 영상 Wan: `Comfy-Org/Wan_2.2_ComfyUI_Repackaged/split_files/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors` → models/diffusion_models
  - vae `.../vae/wan2.2_vae.safetensors` → models/vae
  - 인코더 `Comfy-Org/Wan_2.1_ComfyUI_repackaged/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors` → models/text_encoders
- 영상 LTX: `Lightricks/LTX-Video/ltxv-2b-0.9.8-distilled-fp8.safetensors` → models/checkpoints
  - 인코더 `comfyanonymous/flux_text_encoders/t5xxl_fp8_e4m3fn_scaled.safetensors` → models/text_encoders
- 키컷 Z-Image: `Comfy-Org/z_image_turbo/split_files/diffusion_models/z_image_turbo_nvfp4.safetensors`(4.2GB) → diffusion_models
  - 인코더 `.../text_encoders/qwen_3_4b_fp8_mixed.safetensors` → text_encoders ; vae `.../vae/ae.safetensors`→ vae(z_image_ae.safetensors로 저장)
- 키컷 실사: `SG161222/Juggernaut-XL-v9/...Photo_v2.safetensors` → checkpoints ; LoRA `AiWise/Detail-Tweaker-XL_v1/add-detail-xl.safetensors` → loras
- 업스케일: `Kim2091/UltraSharp/4x-UltraSharp.pth` → upscale_models

## STEP 5. 실행 + 검증
```
python_embeded\python.exe -s ComfyUI\main.py --listen 127.0.0.1 --port 8188 --preview-method none
```
- `/system_stats` 200 확인 → `/object_info`로 노드/모델 인식 확인 → 키컷 1장 테스트.
- 🚨 핵심 규칙은 `setup.md §1` (VAEDecodeTiled·preview none·torch) 따를 것.

## STEP 6. 권장 워크플로 복사
`user/default/workflows/`에 `ZImage_to_Wan_person`(인물), `ZImage_to_LTX`(사물·차량), `ZImage_Turbo`(이미지) 배치. 생성기: `refs/comfyui/scripts/build_*.py`.

→ 이후 운영은 `setup.md` 참조.

# ComfyUI 로컬 생성 — 마스터 레퍼런스 (2026-06-16)

매장 PC(RTX 3080 10GB, 64GB RAM) 기준. 로컬 무료 이미지·영상 생성 환경.

## 0. 환경/경로
- ComfyUI: `D:\stable\ComfyUI_windows_portable` (portable, embedded Python 3.11, ComfyUI v0.24.0+)
- 실행: `run_nvidia_gpu.bat` 더블클릭 또는
  `python_embeded\python.exe -s ComfyUI\main.py --listen 127.0.0.1 --port 8188 --preview-method none`
  → GUI: http://127.0.0.1:8188
- 출력: `ComfyUI\output\` (이미지 png + 영상 mp4 전부 여기)
- 입력(I2V 시작이미지): `ComfyUI\input\`
- 제어 방식: 서버를 백그라운드로 띄우고 **HTTP API(/prompt·/object_info·/history)로 워크플로 JSON 제출**.

## 1. 🚨 필수 수정사항 (이거 모르면 망함)
1. **torch 2.6.0+cu124 필수** — 구버전(2.3.1)은 comfy_kitchen `custom_op` 비호환으로 부팅 크래시. 드라이버 566.14는 cu124/cu126까지(cu128 불가).
2. **🚨 VAEDecodeTiled (영상 디코드 속도)** — `VAEDecode`는 영상 프레임 많을 때 VRAM 0으로 굶어 30분+ 기어감. 반드시 **`VAEDecodeTiled` + `temporal_size=16`**(tile_size 512, overlap 64, temporal_overlap 4). → 30분+ → 2~3분.
3. **`--preview-method none`** 으로 실행 — GUI 브라우저 프리뷰가 스텝당 16→47초로 느리게 함. 끄면 정상속도.
4. 모델 여러번 갈아끼운 뒤 느려지면 ComfyUI 프로세스 kill 후 클린 재시작(VRAM 정리).

## 2. 설치된 모델 (models/ 하위)
| 용도 | 파일 | 폴더 | 비고 |
|------|------|------|------|
| 영상(화질) | wan2.2_ti2v_5B_fp16.safetensors | diffusion_models | Wan2.2, 720p 네이티브 |
| 영상 인코더 | umt5_xxl_fp8_e4m3fn_scaled.safetensors | text_encoders | Wan용(type=wan) |
| 영상 VAE | wan2.2_vae.safetensors | vae | Wan2.2용 |
| 영상(속도) | ltxv-2b-0.9.8-distilled-fp8.safetensors | checkpoints | LTX, 4초 36초 생성 |
| LTX 인코더 | t5xxl_fp8_e4m3fn_scaled.safetensors | text_encoders | type=ltxv |
| 키컷(실사) | Juggernaut-XL_v9.safetensors | checkpoints | SDXL 실사, dpmpp_2m_sde/karras |
| 디테일 LoRA | add-detail-xl.safetensors | loras | Detail Tweaker XL, 0.6 |
| 키컷(최신) | z_image_turbo_nvfp4.safetensors | diffusion_models | Z-Image, 화질최상, nvfp4 4.2GB라 10GB 완전로드(워밍시 키컷 2초!). bf16(11GB) 삭제됨 |
| Z 인코더 | qwen_3_4b_fp8_mixed.safetensors | text_encoders | type=lumina2 |
| Z VAE | z_image_ae.safetensors | vae | |
| 업스케일 | 4x-UltraSharp.pth | upscale_models | |
- RIFE 보간: custom_node `ComfyUI-Frame-Interpolation`(rife49.pth 자동). ⚠️ensemble+97프레임은 느림.
- 삭제됨(10GB 부적합): flux1-dev-fp8(16GB·느림), RealVisXL(Juggernaut로 대체), wan2.1 1.3B.

## 3. 모델별 권장 설정 (정답 조합)
| 모델 | 샘플러/스케줄러 | 스텝 | CFG | shift |
|------|---------------|------|-----|-------|
| Z-Image Turbo | res_multistep / simple | 8 | 1.0 | AuraFlow 3 |
| Wan2.2 5B | uni_pc / simple | 16~30 | 5.0 | SD3 8.0 |
| Juggernaut(SDXL) | dpmpp_2m_sde / karras | 30~32 | 5.5 | - |
| LTX distilled | euler (SamplerCustom) | 8 | 1.0 | LTXVScheduler |
- CLIPLoader type: Z=lumina2, Wan=wan, LTX=ltxv, Qwen-Image=qwen_image. **틀리면 깨짐.**
- 증류(turbo/distilled) 모델은 cfg 1 + ConditioningZeroOut(네거티브 무시). 일반 모델은 cfg 5~7 + 네거티브 활용.

## 4. 속도 vs 화질 선택
- **속도**: LTX-Video 2B (4초 36초). 영상 디코드 병목 없음.
- **화질**: Wan2.2 5B (4초 ~5분, VAEDecodeTiled 필수). 인물 디테일 우위.
- **인물 키컷**: Z-Image(최상, 느림) 또는 Juggernaut+DetailLoRA(빠름).

## 5. 핵심 파이프라인
### A. 키컷→I2V (인물 고화질)
이미지 1장 생성 → I2V로 영상화. T2V보다 얼굴/일관성 월등.
- 연결: 이미지생성 `VAEDecode→IMAGE` 를 LTX `LTXVImgToVideo.image` 또는 Wan `Wan22ImageToVideoLatent.start_image`에 직결(저장 불필요).
### B. 합본(Z-Image→LTX) 한방
Z-Image 9노드(이미지) + LTX 노드(영상)를 IMAGE 선 하나로 연결 → 실행 1번에 이미지+영상. 84초.
- 프롬프트 2개: 이미지용(외모/배경) + 영상용(동작/카메라).
### C. 긴 영상(15초+)
WAN 1회 = ~5초(121f) 한계 → 5초클립 N개를 직전 마지막프레임→다음 start_image(I2V 체이닝)으로 잇고 ffmpeg concat. 단 저해상도 체이닝은 화질저하 누적.

## 6. 작업 스크립트 (refs/comfyui/scripts/)
- `ltx_i2v.py` — LTX 빠른 I2V (input/cafe_key.png 등)
- `wan_i2v_cafe_short.py` — Wan I2V (VAEDecodeTiled 적용 표준)
- `zimage_keyframe.py` — Z-Image 키컷
- `jugg_cafe.py` — Juggernaut+LoRA 실사 키컷
- `zimage_to_ltx.py` — 합본(이미지→영상 한방)
모두 API 제출 방식. 프롬프트/해상도/길이만 바꿔 재사용.

## 7. 음성(미설치)
- LTX-2.3(음성+영상 동시)은 22B라 10GB 부적합(GGUF Q3도 ~10GB+복잡한 audio 파이프라인). 권장 안 함.
- 현실적 음성: 영상은 LTX로 빠르게 + TTS 나레이션/효과음 별도 합성(무비 스킬 방식).

## 8. 최신 모델 동향(2026.6)
- 이미지 오픈 1위: **Z-Image Turbo**(FLUX.2·Qwen 제침). 한글 텍스트=Qwen-Image.
- 영상: Wan2.2(화질)·LTX(속도), 트렌드=음성+영상 동시생성·실시간·4K.

## 9. 인물 영상 결론 (2026-06-16 검증)
- **인물 영상 표준 = Wan 5B 18스텝** (`wan_i2v_person_18step.py`). fp8 weight_dtype, uni_pc/simple, cfg5, shift8, **VAEDecodeTiled**. 576×1024×49(2s) 약 123초. 인물 안정적(LTX는 얼굴 뭉개짐).
- **LTX 2B = 사물/차량/풍경 전용** (39초 빠름, 사람은 변형). 매장 차량 쇼츠엔 LTX.
- **🚨 fp8 + Turbo LoRA(Wan22_TI2V_5B_Turbo_lora) = 폐기**: ComfyUI가 fp8에 LoRA 얹을 때 1스텝 후 88~108s/step로 폭삭 느려짐. LoRA는 `loras/`에 보관만.
- **진짜 Turbo(6스텝 초고속) = GGUF 버전 필요**: `hum-ma/Wan2.2-TI2V-5B-Turbo-GGUF`(Q5 3.55GB) + `ComfyUI-GGUF`(city96) 커스텀노드. 노드 설치 권한 필요(미설치 상태).
- 용도별: 인물=Wan18, 사물=LTX, 키컷=Z-Image nvfp4(2초)/Juggernaut.

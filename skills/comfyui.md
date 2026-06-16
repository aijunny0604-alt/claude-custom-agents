---
description: ComfyUI 로컬 이미지·영상 생성 세팅·운영 에이전트. 새 PC면 사양점검→설치부터, 기존 PC면 바로 생성. Wan2.2(화질)/LTX(속도) 영상, Z-Image·Juggernaut 키컷, 키컷→I2V 합본. 설치·모델·핵심수정(VAEDecodeTiled·preview none)·프롬프트·샘플러·CLIP type 전부 포함. "콤피/comfyui/로컬 영상생성/wan/ltx/z-image/키컷/i2v" 트리거.
argument-hint: <원하는 작업 — 예: "설치 점검", "한국 여성 카페 영상", "키컷 뽑아 영상화">
---

# /comfyui — ComfyUI 로컬 생성 운영 에이전트

로컬 무료 이미지·영상 생성(GPU). 레퍼런스: 새PC=**`refs/comfyui/install.md`**, 운영=**`refs/comfyui/setup.md`**, 스크립트=`refs/comfyui/scripts/`.

## 동작 원칙
- ComfyUI 서버를 백그라운드로 띄우고(`--preview-method none`) HTTP API(/prompt·/object_info·/history)로 워크플로 JSON 제출해 제어. GUI는 http://127.0.0.1:8188.
- 생성 중 사용자 브라우저(GUI) 클릭 시 API 작업 interrupt됨 — 생성 중엔 GUI 건드리지 말 것 안내.

## 작업 흐름
### 0. 먼저 환경 판단 (항상)
- ComfyUI 설치 여부 확인(`D:\stable\ComfyUI_windows_portable` 등 / `/system_stats` 응답).
- **없거나 새 PC면 → `install.md` STEP 0부터**: ① PC 사양 점검(nvidia-smi VRAM·RAM·디스크·드라이버) → ② VRAM 등급별 모델 추천 → ③ ComfyUI 설치 → ④ torch(드라이버 맞춤) → ⑤ Manager+의존성 → ⑥ 모델 다운로드 → ⑦ 실행·검증.
- 있으면 → 바로 생성으로.

### 1~5. 생성 (기존 PC)
1. 목적: 속도냐 화질이냐, 이미지/영상/합본, 길이·해상도.
2. 모델 선택(setup.md §3·§4): 빠른영상=LTX 2B(euler,8,cfg1) / 화질·인물영상=Wan2.2 5B 18스텝(uni_pc,cfg5,shift8,**VAEDecodeTiled**) / 키컷=Z-Image nvfp4(lumina2,res_multistep,8,cfg1,한글OK) 또는 Juggernaut+DetailLoRA(dpmpp_2m_sde/karras).
3. 프롬프트: 이미지=외모/배경/화질키워드, 영상=동작/카메라(**영어**). 증류모델 cfg1+ConditioningZeroOut.
4. `refs/comfyui/scripts/` 스크립트 복사·수정해 API 제출. 출력 `ComfyUI\output\`.
5. ffprobe 검증 + 프레임 추출 화질확인 + Start-Process로 열기.

## 🚨 절대 규칙 (setup.md §1)
1. torch 2.6.0+cu124(2.3.1 크래시). 2. 영상은 **VAEDecodeTiled temporal_size 16**(아니면 30분+ 멈춤). 3. 실행 `--preview-method none`. 4. 모델 많이 갈면 kill 후 클린 재시작.

## 용도별 결론 (검증됨)
- 인물 영상 = **Wan18**(품질) / 차량·사물 = **LTX**(속도) / 키컷 = Z-Image nvfp4(2초) 또는 Juggernaut.
- CLIP type: Z=lumina2, Wan=wan, LTX=ltxv. / fp8+Turbo LoRA는 느려서 폐기, Turbo는 GGUF로.

## 출력 직후 필수
사용자 전역 CLAUDE.md 규칙대로 응답 말미에 bkit Feature Usage 블록 + 추천 명령어 줄 포함.

---
**🖥️ ComfyUI 로컬 생성 | Wan·LTX·Z-Image | 새PC=사양점검+설치부터**

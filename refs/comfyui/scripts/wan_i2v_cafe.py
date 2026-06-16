import json, time, urllib.request, sys

SERVER = "http://127.0.0.1:8188"

def get(p):
    with urllib.request.urlopen(SERVER + p, timeout=60) as r: return json.loads(r.read())
def post(prompt):
    data = json.dumps({"prompt": prompt}).encode()
    req = urllib.request.Request(SERVER + "/prompt", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read())

# gentle natural cafe motion
POS = ("The young Korean woman in the cozy coffee shop gently smiles and turns her head to look softly "
       "toward the camera, slowly lifts the white ceramic cup and takes a small sip of her latte, her hair "
       "moving softly, warm golden sunlight from the window, blurred cafe background with subtle movement, "
       "calm relaxed atmosphere, smooth subtle cinematic camera movement, photorealistic, highly detailed.")
NEG = ("blurry, low quality, deformed face, distorted, extra limbs, extra fingers, bad anatomy, "
       "multiple people, watermark, text, logo, static, flicker, nudity, nsfw")

W, H, LEN = 704, 1280, 97  # ~4s @ 24fps
g = {}
g["1"]  = {"class_type": "UNETLoader", "inputs": {"unet_name": "wan2.2_ti2v_5B_fp16.safetensors", "weight_dtype": "fp8_e4m3fn"}}
g["2"]  = {"class_type": "CLIPLoader", "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan", "device": "default"}}
g["3"]  = {"class_type": "VAELoader", "inputs": {"vae_name": "wan2.2_vae.safetensors"}}
g["4"]  = {"class_type": "CLIPTextEncode", "inputs": {"text": POS, "clip": ["2", 0]}}
g["5"]  = {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["2", 0]}}
g["50"] = {"class_type": "LoadImage", "inputs": {"image": "cafe_key.png"}}
g["6"]  = {"class_type": "Wan22ImageToVideoLatent", "inputs": {"vae": ["3", 0], "width": W, "height": H,
            "length": LEN, "batch_size": 1, "start_image": ["50", 0]}}
g["7"]  = {"class_type": "ModelSamplingSD3", "inputs": {"model": ["1", 0], "shift": 8.0}}
g["8"]  = {"class_type": "KSampler", "inputs": {"model": ["7", 0], "positive": ["4", 0], "negative": ["5", 0],
            "latent_image": ["6", 0], "seed": 19920607, "steps": 30, "cfg": 5.0,
            "sampler_name": "uni_pc", "scheduler": "simple", "denoise": 1.0}}
g["9"]  = {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}}
g["13"] = {"class_type": "RIFE VFI", "inputs": {"ckpt_name": "rife49.pth", "frames": ["9", 0],
            "clear_cache_after_n_frames": 10, "multiplier": 2, "fast_mode": True, "ensemble": True,
            "scale_factor": 1.0, "dtype": "float32", "torch_compile": False, "batch_size": 1}}
g["14"] = {"class_type": "CreateVideo", "inputs": {"images": ["13", 0], "fps": 48.0}}
g["15"] = {"class_type": "SaveVideo", "inputs": {"video": ["14", 0], "filename_prefix": "cafe_i2v",
            "format": "mp4", "codec": "h264"}}

pid = post(g)["prompt_id"]
print("submitted", pid, flush=True)
t0 = time.time()
while True:
    time.sleep(5)
    try: hist = get("/history/" + pid)
    except Exception: continue
    if pid in hist:
        st = hist[pid].get("status", {})
        if st.get("completed") or st.get("status_str") == "success":
            print("DONE %ds" % int(time.time()-t0)); print("OUTPUTS:", json.dumps(hist[pid].get("outputs", {}))); sys.exit(0)
        if st.get("status_str") == "error":
            print("ERROR", json.dumps(st)[:1200]); sys.exit(3)
    if int(time.time()-t0) % 30 < 5: print("...%ds" % int(time.time()-t0), flush=True)
    if time.time()-t0 > 2400: print("timeout"); sys.exit(4)

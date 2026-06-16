import json, time, urllib.request, sys

SERVER = "http://127.0.0.1:8188"
def get(p):
    with urllib.request.urlopen(SERVER + p, timeout=60) as r: return json.loads(r.read())
def post(prompt):
    data = json.dumps({"prompt": prompt}).encode()
    req = urllib.request.Request(SERVER + "/prompt", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read())

obj = get("/object_info")
# verify ckpt provides VAE
ck_out = obj["CheckpointLoaderSimple"]["output_name"]
print("ckpt outputs:", ck_out)

POS = ("A graceful elegant Korean woman in her fifties sits in a cozy modern coffee shop by a window. "
       "She gently smiles and slowly turns her head toward the camera, then lifts a white ceramic cup and "
       "takes a small sip of her latte. Her hair moves softly. Warm golden afternoon sunlight streams "
       "through the window, soft bokeh of the cafe interior behind her. The camera slowly and smoothly "
       "pushes in. Cinematic, photorealistic, calm and warm atmosphere, natural movement.")
NEG = ("low quality, worst quality, deformed, distorted, disfigured, motion smear, motion artifacts, "
       "fused fingers, bad anatomy, weird hand, ugly, static, flicker, blurry")

W, H, LEN = 576, 1024, 97
g = {}
g["1"]  = {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "ltxv-2b-0.9.8-distilled-fp8.safetensors"}}
g["2"]  = {"class_type": "CLIPLoader", "inputs": {"clip_name": "t5xxl_fp8_e4m3fn_scaled.safetensors", "type": "ltxv", "device": "default"}}
g["3"]  = {"class_type": "CLIPTextEncode", "inputs": {"text": POS, "clip": ["2", 0]}}
g["4"]  = {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["2", 0]}}
g["5"]  = {"class_type": "LoadImage", "inputs": {"image": "cafe_key.png"}}
g["6"]  = {"class_type": "LTXVImgToVideo", "inputs": {"positive": ["3", 0], "negative": ["4", 0],
            "vae": ["1", 2], "image": ["5", 0], "width": W, "height": H, "length": LEN,
            "batch_size": 1, "strength": 1.0}}
g["7"]  = {"class_type": "LTXVConditioning", "inputs": {"positive": ["6", 0], "negative": ["6", 1], "frame_rate": 24.0}}
g["8"]  = {"class_type": "LTXVScheduler", "inputs": {"steps": 8, "max_shift": 2.05, "base_shift": 0.95,
            "stretch": True, "terminal": 0.1, "latent": ["6", 2]}}
g["9"]  = {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}}
g["10"] = {"class_type": "SamplerCustom", "inputs": {"model": ["1", 0], "add_noise": True, "noise_seed": 42424242,
            "cfg": 1.0, "positive": ["7", 0], "negative": ["7", 1], "sampler": ["9", 0],
            "sigmas": ["8", 0], "latent_image": ["6", 2]}}
g["11"] = {"class_type": "VAEDecode", "inputs": {"samples": ["10", 0], "vae": ["1", 2]}}
g["12"] = {"class_type": "CreateVideo", "inputs": {"images": ["11", 0], "fps": 24.0}}
g["13"] = {"class_type": "SaveVideo", "inputs": {"video": ["12", 0], "filename_prefix": "ltx_cafe", "format": "mp4", "codec": "h264"}}

pid = post(g)["prompt_id"]
print("submitted", pid, flush=True)
t0 = time.time()
while True:
    time.sleep(3)
    try: hist = get("/history/" + pid)
    except Exception: continue
    if pid in hist:
        st = hist[pid].get("status", {})
        if st.get("completed") or st.get("status_str") == "success":
            print("DONE %ds" % int(time.time()-t0)); print("OUTPUTS:", json.dumps(hist[pid].get("outputs", {}))); sys.exit(0)
        if st.get("status_str") == "error":
            print("ERROR", json.dumps(st)[:1500]); sys.exit(3)
    if int(time.time()-t0) % 20 < 3: print("...%ds" % int(time.time()-t0), flush=True)
    if time.time()-t0 > 600: print("timeout"); sys.exit(4)

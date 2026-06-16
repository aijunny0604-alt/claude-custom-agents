import json, time, urllib.request, sys

SERVER = "http://127.0.0.1:8188"
def get(p):
    with urllib.request.urlopen(SERVER + p, timeout=60) as r: return json.loads(r.read())
def post(prompt):
    data = json.dumps({"prompt": prompt}).encode()
    req = urllib.request.Request(SERVER + "/prompt", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read())

IMG_PROMPT = ("RAW candid photo, a beautiful young Korean woman with soft natural K-beauty makeup, long "
              "glossy dark hair, wearing a stylish beige trench coat, standing on a sunny Seoul street, "
              "cafes and blurred city in the background, natural skin texture, gentle smile, warm light, "
              "35mm, film grain, photorealistic, ultra detailed.")
VID_PROMPT = ("A young Korean woman in a beige trench coat stands on a sunny Seoul street and smiles, gently "
              "turning her head toward the camera as her hair sways softly in the breeze. Pedestrians and "
              "cafe lights blur behind her. The camera slowly pushes in. Cinematic, photorealistic, warm.")
VID_NEG = ("low quality, worst quality, deformed, distorted, motion smear, fused fingers, bad anatomy, ugly, "
           "static, flicker, blurry")

g = {}
# --- Z-Image (image gen) ---
g["1"]  = {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_nvfp4.safetensors", "weight_dtype": "default"}}
g["2"]  = {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b_fp8_mixed.safetensors", "type": "lumina2", "device": "default"}}
g["3"]  = {"class_type": "VAELoader", "inputs": {"vae_name": "z_image_ae.safetensors"}}
g["4"]  = {"class_type": "CLIPTextEncode", "inputs": {"text": IMG_PROMPT, "clip": ["2", 0]}}
g["5"]  = {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}}
g["6"]  = {"class_type": "EmptySD3LatentImage", "inputs": {"width": 576, "height": 1024, "batch_size": 1}}
g["7"]  = {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["1", 0], "shift": 3.0}}
g["8"]  = {"class_type": "KSampler", "inputs": {"model": ["7", 0], "positive": ["4", 0], "negative": ["5", 0],
            "latent_image": ["6", 0], "seed": 555, "steps": 8, "cfg": 1.0,
            "sampler_name": "res_multistep", "scheduler": "simple", "denoise": 1.0}}
g["9"]  = {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}}  # <-- IMAGE output
# --- LTX (video gen) — image comes straight from node 9, NO save/load ---
g["10"] = {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "ltxv-2b-0.9.8-distilled-fp8.safetensors"}}
g["11"] = {"class_type": "CLIPLoader", "inputs": {"clip_name": "t5xxl_fp8_e4m3fn_scaled.safetensors", "type": "ltxv", "device": "default"}}
g["12"] = {"class_type": "CLIPTextEncode", "inputs": {"text": VID_PROMPT, "clip": ["11", 0]}}
g["13"] = {"class_type": "CLIPTextEncode", "inputs": {"text": VID_NEG, "clip": ["11", 0]}}
g["14"] = {"class_type": "LTXVImgToVideo", "inputs": {"positive": ["12", 0], "negative": ["13", 0],
            "vae": ["10", 2], "image": ["9", 0], "width": 576, "height": 1024, "length": 97,
            "batch_size": 1, "strength": 1.0}}
g["15"] = {"class_type": "LTXVConditioning", "inputs": {"positive": ["14", 0], "negative": ["14", 1], "frame_rate": 24.0}}
g["16"] = {"class_type": "LTXVScheduler", "inputs": {"steps": 8, "max_shift": 2.05, "base_shift": 0.95,
            "stretch": True, "terminal": 0.1, "latent": ["14", 2]}}
g["17"] = {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}}
g["18"] = {"class_type": "SamplerCustom", "inputs": {"model": ["10", 0], "add_noise": True, "noise_seed": 777,
            "cfg": 1.0, "positive": ["15", 0], "negative": ["15", 1], "sampler": ["17", 0],
            "sigmas": ["16", 0], "latent_image": ["14", 2]}}
g["19"] = {"class_type": "VAEDecode", "inputs": {"samples": ["18", 0], "vae": ["10", 2]}}
g["20"] = {"class_type": "CreateVideo", "inputs": {"images": ["19", 0], "fps": 24.0}}
g["21"] = {"class_type": "SaveVideo", "inputs": {"video": ["20", 0], "filename_prefix": "zimg2ltx", "format": "mp4", "codec": "h264"}}
# also save the z-image keyframe for reference
g["22"] = {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": "zimg2ltx_key"}}

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
    if int(time.time()-t0) % 30 < 3: print("...%ds" % int(time.time()-t0), flush=True)
    if time.time()-t0 > 600: print("timeout"); sys.exit(4)

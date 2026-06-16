import json, time, urllib.request, sys

SERVER = "http://127.0.0.1:8188"
def get(p):
    with urllib.request.urlopen(SERVER + p, timeout=60) as r: return json.loads(r.read())
def post(prompt):
    data = json.dumps({"prompt": prompt}).encode()
    req = urllib.request.Request(SERVER + "/prompt", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read())

obj = get("/object_info")
clip_opts = obj["CLIPLoader"]["input"]["required"]["clip_name"][0]
CLIP = "qwen_3_4b_fp8_mixed.safetensors" if "qwen_3_4b_fp8_mixed.safetensors" in clip_opts else None
unet_opts = obj["UNETLoader"]["input"]["required"]["unet_name"][0]
print("z unet visible:", "z_image_turbo_nvfp4.safetensors" in unet_opts, "| clip:", CLIP)

POS = ("RAW candid photo, a beautiful young Korean woman with soft natural K-beauty makeup, long glossy "
       "dark hair, wearing a stylish beige trench coat, standing on a sunny Seoul street with cafes and "
       "blurred city background, natural realistic skin texture with visible pores, gentle smile, warm "
       "afternoon light, shallow depth of field, 35mm, film grain, photorealistic, ultra detailed.")

g = {}
g["1"] = {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_nvfp4.safetensors", "weight_dtype": "default"}}
g["2"] = {"class_type": "CLIPLoader", "inputs": {"clip_name": CLIP, "type": "lumina2", "device": "default"}}
g["3"] = {"class_type": "VAELoader", "inputs": {"vae_name": "z_image_ae.safetensors"}}
g["4"] = {"class_type": "CLIPTextEncode", "inputs": {"text": POS, "clip": ["2", 0]}}
g["5"] = {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}}
g["6"] = {"class_type": "EmptySD3LatentImage", "inputs": {"width": 768, "height": 1280, "batch_size": 1}}
g["7"] = {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["1", 0], "shift": 3.0}}
g["8"] = {"class_type": "KSampler", "inputs": {"model": ["7", 0], "positive": ["4", 0], "negative": ["5", 0],
          "latent_image": ["6", 0], "seed": 123456, "steps": 8, "cfg": 1.0,
          "sampler_name": "res_multistep", "scheduler": "simple", "denoise": 1.0}}
g["9"] = {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}}
g["10"] = {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": "zimage_kf"}}

pid = post(g)["prompt_id"]
print("submitted", pid, flush=True)
t0 = time.time()
while True:
    time.sleep(2)
    try: hist = get("/history/" + pid)
    except Exception: continue
    if pid in hist:
        st = hist[pid].get("status", {})
        if st.get("completed") or st.get("status_str") == "success":
            print("DONE %ds" % int(time.time()-t0)); print("OUTPUTS:", json.dumps(hist[pid].get("outputs", {}))); sys.exit(0)
        if st.get("status_str") == "error":
            print("ERROR", json.dumps(st)[:1500]); sys.exit(3)
    if time.time()-t0 > 300: print("timeout"); sys.exit(4)

import json, time, urllib.request, sys, shutil, os

SERVER = "http://127.0.0.1:8188"
OUT = r"D:\stable\ComfyUI_windows_portable\ComfyUI\output"
INP = r"D:\stable\ComfyUI_windows_portable\ComfyUI\input"

def get(p):
    with urllib.request.urlopen(SERVER + p, timeout=60) as r: return json.loads(r.read())
def post(prompt):
    data = json.dumps({"prompt": prompt}).encode()
    req = urllib.request.Request(SERVER + "/prompt", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read())

obj = get("/object_info")
samplers = obj["KSampler"]["input"]["required"]["sampler_name"][0]
scheds = obj["KSampler"]["input"]["required"]["scheduler"][0]
sampler = "dpmpp_2m_sde" if "dpmpp_2m_sde" in samplers else ("dpmpp_2m" if "dpmpp_2m" in samplers else samplers[0])
sched = "karras" if "karras" in scheds else scheds[0]

# Elegant 50s Korean woman in a cozy modern coffee shop (generic, no brand logos) — detailed prompt
POS = ("RAW candid lifestyle photograph of a graceful elegant Korean woman in her early fifties, refined "
       "mature beauty, healthy radiant skin with natural fine smile lines and realistic age-appropriate "
       "texture, soft natural makeup, warm gentle eyes, elegant shoulder-length wavy dark hair with a few "
       "subtle natural grey strands, tasteful pearl earrings and a thin elegant necklace, wearing a "
       "sophisticated beige cashmere knit cardigan over a silk blouse, sitting at a warm wooden table "
       "beside a large window inside a cozy Scandinavian-style modern coffee shop, both hands gently "
       "cradling a white ceramic cup of latte with delicate latte art, a small green monstera plant, warm "
       "hanging pendant lights and softly blurred customers in the background, warm golden afternoon "
       "sunlight streaming through the window creating a soft glowing rim light on her hair, gentle warm "
       "smile, looking slightly off-camera, cozy relaxed cafe atmosphere, shot on a 35mm full-frame camera "
       "at f/1.8, shallow depth of field, creamy bokeh, Fujifilm film simulation, fine film grain, natural "
       "realistic skin texture with visible pores, ultra detailed, photorealistic, lifestyle magazine "
       "editorial quality.")
NEG = ("airbrushed, plastic skin, doll, instagram filter, cartoon, anime, illustration, painting, 3d render, "
       "cgi, deformed, disfigured, bad anatomy, extra fingers, extra limbs, fused fingers, mutated hands, "
       "blurry, low quality, lowres, jpeg artifacts, watermark, text, logo, brand, signature, ugly, "
       "overexposed, nude, nsfw")

g = {}
g["1"] = {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "Juggernaut-XL_v9.safetensors"}}
g["2"] = {"class_type": "LoraLoader", "inputs": {"model": ["1", 0], "clip": ["1", 1],
          "lora_name": "add-detail-xl.safetensors", "strength_model": 0.6, "strength_clip": 0.6}}
g["3"] = {"class_type": "CLIPTextEncode", "inputs": {"text": POS, "clip": ["2", 1]}}
g["5"] = {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["2", 1]}}
g["6"] = {"class_type": "EmptyLatentImage", "inputs": {"width": 704, "height": 1280, "batch_size": 1}}
g["7"] = {"class_type": "KSampler", "inputs": {"model": ["2", 0], "positive": ["3", 0], "negative": ["5", 0],
          "latent_image": ["6", 0], "seed": 20240614, "steps": 32, "cfg": 5.0,
          "sampler_name": sampler, "scheduler": sched, "denoise": 1.0}}
g["8"] = {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["1", 2]}}
g["9"] = {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "cafe_keyframe"}}

pid = post(g)["prompt_id"]
print("submitted", pid, "sampler", sampler, sched, flush=True)
t0 = time.time()
while True:
    time.sleep(3)
    try: hist = get("/history/" + pid)
    except Exception: continue
    if pid in hist:
        st = hist[pid].get("status", {})
        if st.get("completed") or st.get("status_str") == "success":
            outs = hist[pid].get("outputs", {})
            fn = None
            for node in outs.values():
                for im in node.get("images", []):
                    if im["filename"].lower().endswith((".png",".jpg",".jpeg")):
                        fn = os.path.join(OUT, im.get("subfolder",""), im["filename"])
            print("DONE %ds ->" % int(time.time()-t0), fn)
            if fn and os.path.exists(fn):
                shutil.copyfile(fn, os.path.join(INP, "cafe_key.png"))
                print("copied to input/cafe_key.png")
            sys.exit(0)
        if st.get("status_str") == "error":
            print("ERROR", json.dumps(st)[:1200]); sys.exit(3)
    if time.time()-t0 > 600: print("timeout"); sys.exit(4)

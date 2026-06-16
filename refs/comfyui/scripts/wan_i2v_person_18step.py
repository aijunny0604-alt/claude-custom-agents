import json,time,urllib.request,sys
S="http://127.0.0.1:8188"
def get(p): return json.loads(urllib.request.urlopen(S+p,timeout=60).read())
def post(g):
    d=json.dumps({"prompt":g}).encode()
    r=urllib.request.Request(S+"/prompt",data=d,headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(r,timeout=60).read())
POS="The Korean woman in the beige trench coat smiles warmly and her long hair flows gently in the breeze as she slowly turns toward the camera, soft city light behind her, smooth subtle camera movement, photorealistic, highly detailed."
NEG="blurry, low quality, deformed face, distorted, extra limbs, bad anatomy, multiple people, watermark, text, static, flicker, nsfw"
g={}
g["1"]={"class_type":"UNETLoader","inputs":{"unet_name":"wan2.2_ti2v_5B_fp16.safetensors","weight_dtype":"fp8_e4m3fn"}}
g["2"]={"class_type":"CLIPLoader","inputs":{"clip_name":"umt5_xxl_fp8_e4m3fn_scaled.safetensors","type":"wan","device":"default"}}
g["3"]={"class_type":"VAELoader","inputs":{"vae_name":"wan2.2_vae.safetensors"}}
g["4"]={"class_type":"CLIPTextEncode","inputs":{"text":POS,"clip":["2",0]}}
g["5"]={"class_type":"CLIPTextEncode","inputs":{"text":NEG,"clip":["2",0]}}
g["6"]={"class_type":"LoadImage","inputs":{"image":"korean_key.png"}}
g["7"]={"class_type":"Wan22ImageToVideoLatent","inputs":{"vae":["3",0],"width":576,"height":1024,"length":49,"batch_size":1,"start_image":["6",0]}}
g["8"]={"class_type":"ModelSamplingSD3","inputs":{"model":["1",0],"shift":8.0}}
g["9"]={"class_type":"KSampler","inputs":{"model":["8",0],"positive":["4",0],"negative":["5",0],"latent_image":["7",0],"seed":77,"steps":18,"cfg":5.0,"sampler_name":"uni_pc","scheduler":"simple","denoise":1.0}}
g["10"]={"class_type":"VAEDecodeTiled","inputs":{"samples":["9",0],"vae":["3",0],"tile_size":512,"overlap":64,"temporal_size":16,"temporal_overlap":4}}
g["11"]={"class_type":"CreateVideo","inputs":{"images":["10",0],"fps":24.0}}
g["12"]={"class_type":"SaveVideo","inputs":{"video":["11",0],"filename_prefix":"wan_a18","format":"mp4","codec":"h264"}}
pid=post(g)["prompt_id"]; print("submitted",pid,flush=True); t0=time.time()
while True:
    time.sleep(3)
    try: h=get("/history/"+pid)
    except: continue
    if pid in h:
        st=h[pid].get("status",{})
        if st.get("completed") or st.get("status_str")=="success": print("DONE %ds"%int(time.time()-t0)); sys.exit(0)
        if st.get("status_str")=="error": print("ERR",json.dumps(st)[:600]); sys.exit(3)
    if int(time.time()-t0)%30<3: print("...%ds"%int(time.time()-t0),flush=True)
    if time.time()-t0>600: print("timeout"); sys.exit(4)

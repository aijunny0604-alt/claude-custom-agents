import json, os

POS = ("RAW candid photo, a beautiful young Korean woman with soft natural K-beauty makeup, long glossy "
       "dark hair, wearing a stylish beige trench coat, standing on a sunny Seoul street with cafes and "
       "blurred city background, natural realistic skin texture, gentle smile, warm afternoon light, "
       "35mm, film grain, photorealistic, ultra detailed.")

def node(nid, ntype, pos, inputs, outputs, widgets, title=None):
    n = {"id": nid, "type": ntype, "pos": pos, "size": [300, 130], "flags": {}, "order": nid,
         "mode": 0, "inputs": inputs, "outputs": outputs,
         "properties": {"Node name for S&R": ntype}, "widgets_values": widgets}
    if title: n["title"] = title
    return n

def out(name, t, links): return {"name": name, "type": t, "slot_index": 0, "links": links}
def inp(name, t, link): return {"name": name, "type": t, "link": link}

nodes = [
    node(1, "UNETLoader", [40, 40], [], [out("MODEL","MODEL",[1])], ["z_image_turbo_nvfp4.safetensors","default"]),
    node(2, "CLIPLoader", [40, 200], [], [out("CLIP","CLIP",[2])], ["qwen_3_4b_fp8_mixed.safetensors","lumina2","default"]),
    node(3, "VAELoader", [40, 380], [], [out("VAE","VAE",[3])], ["z_image_ae.safetensors"]),
    node(4, "CLIPTextEncode", [400, 180], [inp("clip","CLIP",2)], [out("CONDITIONING","CONDITIONING",[4,5])], [POS], "CLIP Text Encode (Prompt)"),
    node(5, "ConditioningZeroOut", [400, 420], [inp("conditioning","CONDITIONING",4)], [out("CONDITIONING","CONDITIONING",[6])], []),
    node(6, "EmptySD3LatentImage", [400, 560], [], [out("LATENT","LATENT",[7])], [768,1280,1]),
    node(7, "ModelSamplingAuraFlow", [840, 40], [inp("model","MODEL",1)], [out("MODEL","MODEL",[8])], [3]),
    node(8, "KSampler", [840, 200], [inp("model","MODEL",8), inp("positive","CONDITIONING",5), inp("negative","CONDITIONING",6), inp("latent_image","LATENT",7)], [out("LATENT","LATENT",[9])], [123456,"randomize",8,1,"res_multistep","simple",1]),
    node(9, "VAEDecode", [1200, 200], [inp("samples","LATENT",9), inp("vae","VAE",3)], [out("IMAGE","IMAGE",[10])], []),
    node(10, "SaveImage", [1420, 200], [inp("images","IMAGE",10)], [], ["zimage_kf"]),
]
# links: [id, from_node, from_slot, to_node, to_slot, type]
links = [
    [1,1,0,7,0,"MODEL"],
    [2,2,0,4,0,"CLIP"],
    [3,3,0,9,1,"VAE"],
    [4,4,0,5,0,"CONDITIONING"],
    [5,4,0,8,1,"CONDITIONING"],
    [6,5,0,8,2,"CONDITIONING"],
    [7,6,0,8,3,"LATENT"],
    [8,7,0,8,0,"MODEL"],
    [9,8,0,9,0,"LATENT"],
    [10,9,0,10,0,"IMAGE"],
]
wf = {"id":"zimg-turbo-flat","revision":0,"last_node_id":10,"last_link_id":10,
      "nodes":nodes,"links":links,
      "groups":[{"id":1,"title":"Z-Image Turbo (8-step, cfg1)","bounding":[20,-30,1700,760],"color":"#3f789e","font_size":24,"flags":{}}],
      "config":{},"extra":{},"version":0.4}

wfdir = r"D:\stable\ComfyUI_windows_portable\ComfyUI\user\default\workflows"
os.makedirs(wfdir, exist_ok=True)
p = os.path.join(wfdir, "ZImage_Turbo.json")
with open(p,"w",encoding="utf-8") as f: json.dump(wf,f,ensure_ascii=False,indent=2)
print("WROTE", p)

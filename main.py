
import numpy as np
import os
import folder_paths
from PIL import Image, ImageOps, ImageSequence
import hashlib

import inspect
from server import PromptServer
import folder_paths
from server import PromptServer
from aiohttp import web

from .sdxl_prompt_styler import SDXLPromptStyler, SDXLPromptStylerAdvanced



def install_js():
    "初始化js"
    def get_ext_dir(subpath=None, mkdir=False):
        dir = os.path.dirname(__file__)
        if subpath is not None:
            dir = os.path.join(dir, subpath)

        dir = os.path.abspath(dir)

        if mkdir and not os.path.exists(dir):
            os.makedirs(dir)

        return dir

    def get_comfy_dir(subpath=None, mkdir=False):
        dir = os.path.dirname(inspect.getfile(PromptServer))
        if subpath is not None:
            dir = os.path.join(dir, subpath)

        dir = os.path.abspath(dir)

        if mkdir and not os.path.exists(dir):
            os.makedirs(dir)
        return dir
    
    def should_install_js():
        return not hasattr(PromptServer.instance, "supports") or "custom_nodes_from_web" not in PromptServer.instance.supports

    src_dir = get_ext_dir("web/js")
    if not os.path.exists(src_dir):
        return

    should_install_js()

    dst_dir = get_comfy_dir("web/extensions/promptPreview")

    linked = os.path.islink(dst_dir)

    return linked


@PromptServer.instance.routes.get("/preview/{name}")
async def view(request):
    name = request.match_info["name"]

    image_path = name
    filename = os.path.basename(image_path)
    return web.FileResponse(image_path, headers={"Content-Disposition": f"filename=\"{filename}\""})


def populate_items(styles, item_type):
    for idx, item_name in enumerate(styles):
        current_directory = os.path.dirname(os.path.abspath(__file__))
        preview_path = os.path.join(current_directory, item_type, item_name + ".png")

        if len(item_name.split('-')) > 1:
            content = f"{item_name.split('-')[0]} /{item_name}"
        else:
            content = item_name

        if os.path.exists(preview_path):
            styles[idx] = {
                "content": content,
                "preview": preview_path
            }
        else:
            print(f"Warning: Preview image '{item_name}.png' not found for item '{item_name}'")
            styles[idx] = {
                "content": content,
                "preview": None
            }

class SDXLPromptStylerPreview(SDXLPromptStyler):
    @classmethod
    def INPUT_TYPES(s):
        types = super().INPUT_TYPES()
        style = types["required"]["style"][0]
        populate_items(style, "style-preview")
        return types
    
    def prompt_styler(self, **kwargs):
        kwargs["style"] = kwargs["style"]["content"].split("/")[-1]
        return super().prompt_styler(**kwargs)


class SDXLPromptStylerAdvancedPreview(SDXLPromptStylerAdvanced):
    @classmethod
    def INPUT_TYPES(s):
        types = super().INPUT_TYPES()
        style = types["required"]["style"][0]
        populate_items(style, "style-preview")
        return types
    
    def prompt_styler(self, **kwargs):
        kwargs["style"] = kwargs["style"]["content"].split("/")[-1]
        return super().prompt_styler(**kwargs)

# 初始化js
install_js()

# NODE MAPPING
NODE_CLASS_MAPPINGS = {
    "SDXLPromptStylerPreview": SDXLPromptStylerPreview,
    "SDXLPromptStylerAdvancedPreview": SDXLPromptStylerAdvancedPreview
}

NODE_DISPLAY_NAME_MAPPINGS = {    
    "SDXLPromptStylerPreview": "SDXL Prompt Styler (Preview)",
    "SDXLPromptStylerAdvancedPreview": "SDXL Prompt Styler Advanced (Preview)"
}

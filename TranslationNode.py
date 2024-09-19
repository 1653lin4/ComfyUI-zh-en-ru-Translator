import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer
import os
import folder_paths
import re

class ZhEnRuTranslatorNode:
    def __init__(self):
        self.use_gpu = True
        self.model_name = "t5_translate_en_ru_zh_small_1024"
        self.MODELS_DIR = os.path.join(folder_paths.models_dir, "Translation")
        self.model_path = os.path.join(self.MODELS_DIR, self.model_name)
        self.set_device()
        self.load_download_model()
        self.max_segment_length = 1024

    def set_device(self):
        self.device = torch.device("cuda" if self.use_gpu and torch.cuda.is_available() else "cpu")

    def load_download_model(self):
        try:
            self.model = T5ForConditionalGeneration.from_pretrained(self.model_path, local_files_only=True).to(self.device)
            self.tokenizer = T5Tokenizer.from_pretrained(self.model_path, local_files_only=True)
        except Exception as e:
            error_message = f"无法加载模型 {self.model_name}。请确保您已经下载了所需的模型文件。\n预期的模型路径: {self.model_path}\n错误详情: {str(e)}"
            print(error_message)
            raise RuntimeError(error_message)

    def split_text(self, text):        
        # 直接按换行符分割文本
        lines = text.split('\n')
        
        segments = []
        for line in lines:
            line = line.strip()
            if line:
                # 进一步分割每一行，考虑句号、问号和感叹号
                sub_segments = re.split(r'([。？?！!])', line)
                for i in range(0, len(sub_segments) - 1, 2):
                    if i + 1 < len(sub_segments):
                        segments.append(sub_segments[i] + sub_segments[i+1])
                    else:
                        segments.append(sub_segments[i])
                # 如果行不是以句号、问号或感叹号结束，添加整行
                if not line.endswith(('。', '？', '?', '！', '!')):
                    segments.append(line)
            else:
                # 保留空行
                segments.append('')
        
        return segments

    def translate_segment(self, segment, target_language):
        prefix = f"translate to {target_language}: "
        full_input = prefix + segment
        inputs = self.tokenizer(full_input, return_tensors="pt", padding=True, truncation=True, max_length=1024).to(self.device)
        with torch.no_grad():
            outputs = self.model.generate(**inputs)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

    @classmethod
    def INPUT_TYPES(s):
        return {            
            "required": {
                "use_gpu": ("BOOLEAN", {"default": True, "label": "使用GPU"}),
                "target_language": (["en", "zh", "ru"], {"default": "en", "label": "目标语言"}),
                "input_text": ("STRING", {"multiline": True, "default": "", "placeholder": "输入要翻译的文本"}),                
            },
            "optional": {
                "optional_input_text": ("STRING", {"forceInput": True, "default": "", "placeholder": "连接的输入（如果提供则优先使用）"}),
            }
        }

    OUTPUT_NODE = True
    RETURN_TYPES = ("STRING",)
    FUNCTION = "translate"
    CATEGORY = "text_Translator"

    def translate(self, target_language, input_text, use_gpu, optional_input_text=""):
        if self.use_gpu != use_gpu:
            self.use_gpu = use_gpu
            self.set_device()
            self.model = self.model.to(self.device)

        text_to_translate = optional_input_text if optional_input_text.strip() else input_text

        if not text_to_translate.strip():
            return {"ui": {"text": ""}, "result": ("",)}

        segments = self.split_text(text_to_translate)
        
        translated_segments = []
        for segment in segments:
            if segment.strip():
                # 翻译非空段落
                translated = self.translate_segment(segment, target_language)
                translated_segments.append(translated)
            else:
                # 保留空行
                translated_segments.append('')

        # 使用换行符合并翻译后的段落
        final_text = '\n'.join(translated_segments)
        final_text = re.sub(r'\n{3,}', '\n\n', final_text)

        return {"ui": {"text": final_text}, "result": (final_text,)}

# 节点类映射
NODE_CLASS_MAPPINGS = {
    "zh_en_ru_Translator": ZhEnRuTranslatorNode
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "zh_en_ru_Translator": "zh_en_ru_Translator"
}

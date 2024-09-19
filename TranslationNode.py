import torch  # 导入PyTorch库,用于深度学习计算
from transformers import T5ForConditionalGeneration, T5Tokenizer  # 导入Transformers库中的T5模型和分词器
import os  # 导入操作系统模块,用于文件路径操作
import folder_paths  # 导入ComfyUI的文件路径模块
import re  # 导入正则表达式模块,用于文本处理

class ZhEnRuTranslatorNode:
    def __init__(self):
        self.use_gpu = True  # 默认使用GPU
        self.model_name = "t5_translate_en_ru_zh_small_1024"  # 设置模型名称
        self.MODELS_DIR = os.path.join(folder_paths.models_dir, "Translation")  # 设置模型目录路径
        self.model_path = os.path.join(self.MODELS_DIR, self.model_name)  # 设置完整的模型路径
        self.set_device()  # 设置计算设备
        self.load_download_model()  # 加载模型

    def set_device(self):
        # 设置计算设备为GPU(如果可用)或CPU
        self.device = torch.device("cuda" if self.use_gpu and torch.cuda.is_available() else "cpu")

    def load_download_model(self):
        try:
            # 从本地加载模型和分词器
            self.model = T5ForConditionalGeneration.from_pretrained(self.model_path, local_files_only=True).to(self.device)
            self.tokenizer = T5Tokenizer.from_pretrained(self.model_path, local_files_only=True)
        except Exception as e:
            # 如果加载失败,抛出异常并提供详细错误信息
            error_message = f"无法加载模型 {self.model_name}。请确保您已经下载了所需的模型文件。\n预期的模型路径: {self.model_path}\n错误详情: {str(e)}\n\n请下载所需的模型文件并将其放置在 ComfyUI 的 models/Translation 目录下。\n如果您在中国大陆，建议选择 'hf-mirror.com' 或 'modelscope.cn' 作为模型源。\n如果您在其他地区，可以选择 'huggingface.co' 作为模型源。\n确保在下载完成后再次运行此节点。"
            print(error_message)
            raise RuntimeError(error_message)

    def preprocess_text(self, text):
        # 将中文句号逗号，但保留换行符  
        text = re.sub(r'([。])', ', ', text)            
        text = text.replace('\n', '[NEWLINE]')  # 将换行符替换为特殊标记
        return text.strip()  # 返回处理后的文本,去除首尾空白

    def postprocess_text(self, text):
        # 将特殊标记还原为换行符
        text = text.replace('[NEWLINE]', '\n')
        return text.strip()  # 返回处理后的文本,去除首尾空白

    def translate_segment(self, segment, target_language):
        prefix = f"translate to {target_language}: "  # 添加翻译指令前缀
        full_input = prefix + segment  # 组合完整输入
        # 对输入进行编码,并移到指定设备(GPU或CPU)
        inputs = self.tokenizer(full_input, return_tensors="pt", padding=True, truncation=True, max_length=1024).to(self.device)
        with torch.no_grad():
            outputs = self.model.generate(**inputs)  # 生成翻译输出
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)  # 解码并返回翻译结果

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
        }  # 定义节点的输入类型和UI显示

    OUTPUT_NODE = True  # 指定这是一个输出节点
    RETURN_TYPES = ("STRING",)  # 定义返回类型
    FUNCTION = "translate"  # 指定执行的函数名
    CATEGORY = "text_Translator"  # 节点分类

    def translate(self, target_language, input_text, use_gpu, optional_input_text=""):
        if self.use_gpu != use_gpu:
            self.use_gpu = use_gpu
            self.set_device()
            self.model = self.model.to(self.device)  # 如果GPU使用状态改变,重新设置设备

        text_to_translate = optional_input_text if optional_input_text.strip() else input_text  # 选择要翻译的文本
        
        if not text_to_translate.strip():
            return {"ui": {"text": ""}, "result": ("",)}  # 如果没有输入文本,返回空结果
        
        preprocessed_text = self.preprocess_text(text_to_translate)  # 预处理文本
        translated_text = self.translate_segment(preprocessed_text, target_language)  # 翻译文本
        final_text = self.postprocess_text(translated_text)  # 后处理翻译结果

        return {"ui": {"text": final_text}, "result": (final_text,)}  # 返回翻译结果

# 节点类映射
NODE_CLASS_MAPPINGS = {
    "zh_en_ru_Translator": ZhEnRuTranslatorNode
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "zh_en_ru_Translator": "zh_en_ru_Translator"
}
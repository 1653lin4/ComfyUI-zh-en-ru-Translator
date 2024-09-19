"""
@File          :DownloadModelsNode.py
@Description   :DownloadModels
@Author        :1653lin4
"""

import os
import requests
from tqdm import tqdm
import concurrent.futures
import time
import folder_paths  

class DownloadModels:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {},
            "optional": {
                "model_source": (["hf-mirror.com", "modelscope.cn", "huggingface.co"], {"default": "hf-mirror.com"}),
                "enable_proxy": ("BOOLEAN", {"default": False})
            }
        }
    
    RETURN_TYPES = ()
    FUNCTION = "download_models"
    CATEGORY = "text_Translator"
    OUTPUT_NODE = True

    @staticmethod
    def get_model_urls(model_source):
        """返回选定模型源的URL字典"""   # """---修改位置---"""
        source_urls = {
            "hf-mirror.com": {
                "base_url": "https://hf-mirror.com",
                "t5_translate_en_ru_zh_small_1024": "https://hf-mirror.com/utrobinmv/t5_translate_en_ru_zh_small_1024/resolve/main/"
            },
            "modelscope.cn": {
                "base_url": "https://modelscope.cn",
                "t5_translate_en_ru_zh_small_1024": "https://modelscope.cn/api/v1/models/cubeai/t5_translate_en_ru_zh_small_1024/repo?Revision=master&FilePath="
            },
            "huggingface.co": {
                "base_url": "https://huggingface.co",
                "t5_translate_en_ru_zh_small_1024": "https://huggingface.co/utrobinmv/t5_translate_en_ru_zh_small_1024/resolve/main/"
            }
        }
        return source_urls.get(model_source, {})

    @staticmethod
    def check_url_accessibility(session, url):
        """检查URL是否可访问"""
        try:
            response = session.get(url, timeout=10, allow_redirects=True)
            print(f"正在检查 URL: {url}")
            print(f"响应状态码: {response.status_code}")
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"请求异常: {str(e)}")
            return False

    @staticmethod
    def download_file(session, url, local_path, model, file, total_progress=None):
        """下载单个文件并更新总进度，支持断点续传"""
        temp_path = local_path + '.tmp'
        headers = {}
        mode = 'ab'
        initial_pos = 0

        # 检查临时文件是否存在，支持断点续传
        if os.path.exists(temp_path):
            initial_pos = os.path.getsize(temp_path)
            headers['Range'] = f'bytes={initial_pos}-'
        else:
            mode = 'wb'

        try:
            response = session.get(url, stream=True, headers=headers)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0)) + initial_pos

            print(f"开始下载 {model} - {file}")
            start_time = time.time()

            with open(temp_path, mode) as f:
                for data in response.iter_content(chunk_size=8192):  # 使用8K的分块大小
                    size = f.write(data)
                    if total_progress:
                        total_progress.update(size)

            # 下载完成后，重命名临时文件
            os.replace(temp_path, local_path)
            
            end_time = time.time()
            download_time = end_time - start_time
            print(f"{file} 下载完成，耗时 {download_time:.2f} 秒")
            
            return f"{file} 下载成功"
        except requests.RequestException as e:
            return f"{file} 下载失败: 网络错误 - {str(e)}"
        except Exception as e:
            return f"{file} 下载失败: {str(e)}"

    def calculate_total_size(self, session, model_urls, models_to_download, files_to_download):
        """计算所有文件的总大小"""
        total_size = 0
        for model in models_to_download:
            base_url = model_urls.get(model, "")
            if not base_url:
                continue
            for file in files_to_download:
                url = base_url + file
                try:
                    response = session.head(url)
                    total_size += int(response.headers.get('content-length', 0))
                except:
                    pass
        return total_size

    def download_model_files(self, session, model, base_url, files_to_download, model_path, total_progress, executor):
        """下载单个模型的所有文件"""
        futures = []
        for file in files_to_download:
            url = base_url + file
            local_path = os.path.join(model_path, file)
            if not os.path.exists(local_path):
                futures.append(executor.submit(
                    self.download_file, session, url, local_path, model, file, total_progress
                ))
            else:
                print(f"{file} 已存在，跳过下载")
                total_progress.update(os.path.getsize(local_path))
        return futures

    def generate_ui_text(self, models_to_download, files_to_download):
        """生成UI显示文本"""
        ui_text = "下载结果:\n\n"
        for model in models_to_download:
            model_path = os.path.join(folder_paths.models_dir, "Translation", model)    # """---修改位置---"""
            ui_text += f"模型: {model}\n"
            ui_text += f"下载目录: {model_path}\n"
            for file in files_to_download:
                file_path = os.path.join(model_path, file)
                if os.path.exists(file_path):
                    ui_text += f"  - {file}: 下载成功\n"
                else:
                    ui_text += f"  - {file}: 下载失败或未下载\n"
            ui_text += "\n"
        return ui_text

    def download_models(self, model_source="hf-mirror.com", enable_proxy=False):
        """下载翻译模型的主函数"""
        session = requests.Session()
        if not enable_proxy:
            session.trust_env = False

        model_urls = self.get_model_urls(model_source)
        if not model_urls:
            return {"ui": {"text": f"错误：无法获取模型源 {model_source} 的URL。"}}

        base_url = model_urls.get("base_url")
        if not base_url or not self.check_url_accessibility(session, base_url):
            return {"ui": {"text": f"错误：无法访问所选模型源 {model_source}，请检查网络连接或尝试其他源。"}}

        # """---修改位置---"""
        models_to_download = ["t5_translate_en_ru_zh_small_1024"]
        files_to_download = [
            "config.json",
            "model.safetensors",
            "tokenizer_config.json",
            "spiece.model",
            "special_tokens_map.json",
            "added_tokens.json",
            "generation_config.json"
        ]

        all_results = []
        total_size = self.calculate_total_size(session, model_urls, models_to_download, files_to_download)

        with tqdm(total=total_size, unit='iB', unit_scale=True, desc="总进度") as total_progress:
            with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
                futures = []
                for model in models_to_download:
                    base_url = model_urls.get(model, "")
                    if not base_url:
                        all_results.append(f"错误：无法获取模型 {model} 的下载链接")
                        continue

                    """---修改位置---"""
                    models_dir = folder_paths.models_dir
                    translation_dir = os.path.join(models_dir, "Translation")
                    os.makedirs(translation_dir, exist_ok=True)
                    model_path = os.path.join(translation_dir, model)
                    os.makedirs(model_path, exist_ok=True)
                    
                    futures.extend(self.download_model_files(session, model, base_url, files_to_download, model_path, total_progress, executor))

                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    all_results.append(result)

        ui_text = self.generate_ui_text(models_to_download, files_to_download)
        return {"ui": {"text": ui_text}}

NODE_CLASS_MAPPINGS = {
    "zh_en_ru_DownloadModels": DownloadModels
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "zh_en_ru_DownloadModels": "zh_en_ru_DownloadModels"
}
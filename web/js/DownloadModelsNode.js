import { app } from "/scripts/app.js"; // 导入ComfyUI的主应用对象
import { ComfyWidgets } from "/scripts/widgets.js"; // 导入ComfyWidgets，用于创建自定义UI小部件

app.registerExtension({ // 注册一个新的ComfyUI扩展
    name: "Comfy.DownloadModels", // 设置扩展的名称
    async beforeRegisterNodeDef(nodeType, nodeData, app) { // 在节点定义注册前执行的异步函数
        if (nodeData.name === "zh_en_ru_DownloadModels") { // 使用该JS文件的类名称
        // if (nodeData.category.startsWith("HF模型下载器_国内")) {  // 使用 startsWith 来检查类别
        const onNodeCreated = nodeType.prototype.onNodeCreated; // 保存原始的onNodeCreated方法
        nodeType.prototype.onNodeCreated = function() { // 重写onNodeCreated方法
            onNodeCreated?.apply(this, arguments); // 调用原始的onNodeCreated方法（如果存在）
            this.size = [300, 150]; // 设置节点的初始大小为300x150
            this.setDirtyCanvas(true, true); // 标记画布需要重绘，确保大小变化立即生效
        };

        const onExecuted = nodeType.prototype.onExecuted; // 保存原始的onExecuted方法
        nodeType.prototype.onExecuted = function (message) { // 重写onExecuted方法
            onExecuted?.apply(this, arguments); // 调用原始的onExecuted方法（如果存在）
            if (message.text) { // 如果消息中包含文本，则处理结果
                handleHFDownloaderResult.call(this, message, app); // 调用处理结果的函数
            }
        };
    }
}
});

function handleHFDownloaderResult(message, app) { // 处理HFDownloader结果的主函数
    ensureResultWidgetExists.call(this, app); // 确保结果显示小部件存在
    const outputText = processMessageText(message.text); // 处理消息文本
    updateResultWidget.call(this, outputText); // 更新结果小部件的显示
    adjustNodeSize.call(this); // 调整节点大小以适应内容
}

function ensureResultWidgetExists(app) { // 确保结果显示小部件存在的函数
    if (!this.resultWidget) { // 如果结果小部件不存在，创建一个新的
        this.resultWidget = ComfyWidgets.STRING(this, "result", ["STRING", { multiline: true }], app).widget; // 使用ComfyWidgets创建一个新的STRING类型小部件
        this.resultWidget.inputEl.readOnly = true; // 设置输入元素为只读
        this.resultWidget.inputEl.style.opacity = 0.6; // 设置输入元素的不透明度
    }
}

function processMessageText(text) { // 处理消息文本的函数
    if (Array.isArray(text)) { // 如果文本是数组，将其连接成字符串
        return text.join('');
    } else if (typeof text !== 'string') { // 如果文本不是字符串，强制转换为字符串
        return String(text);
    }
    return text; // 如果已经是字符串，直接返回
}

function updateResultWidget(text) { // 更新结果小部件显示的函数
    this.resultWidget.value = text; // 更新小部件的值为新的下载结果
    this.resultWidget.inputEl.style.height = 'auto'; // 重置文本框高度
    this.resultWidget.inputEl.style.height = this.resultWidget.inputEl.scrollHeight + 'px'; // 调整文本框高度以适应内容
}

function adjustNodeSize() { // 调整节点大小的函数
    requestAnimationFrame(() => { // 在下一帧中执行UI更新，以确保DOM已经准备好
        const sz = this.computeSize(); // 计算节点新的大小
        if (this.size[0] < sz[0] || this.size[1] < sz[1]) { // 如果新的大小大于当前大小，则调整节点大小
            this.size = sz;
            this.graph.setDirtyCanvas(true, true); // 标记画布需要重绘
        }
    });
}
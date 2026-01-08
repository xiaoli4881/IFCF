import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import torch
import os
import shutil
import uuid
from pathlib import Path
from PIL import Image
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import zipfile
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 尝试添加中文字体支持
try:
    # Windows系统SimHei字体路径
    simhei_path = "E:\\pony\\AI\\Image_Feature_Clustering_Function\\SimHei.ttf"
    if os.path.exists(simhei_path):
        matplotlib.font_manager.fontManager.addfont(simhei_path)
        font_name = matplotlib.font_manager.FontProperties(fname=simhei_path).get_name()
        plt.rcParams['font.sans-serif'] = [font_name]
    else:
        # 尝试其他可能的路径
        possible_paths = [
            "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Linux
            "/System/Library/Fonts/PingFang.ttc",  # MacOS
        ]
        for path in possible_paths:
            if os.path.exists(path):
                matplotlib.font_manager.fontManager.addfont(path)
                font_name = matplotlib.font_manager.FontProperties(fname=path).get_name()
                plt.rcParams['font.sans-serif'] = [font_name]
                break
    
    # 解决负号显示问题
    plt.rcParams['axes.unicode_minus'] = False
    print("中文字体已配置")
except Exception as e:
    print(f"中文字体配置失败: {e}")

# 导入transformers
try:
    from transformers import AutoImageProcessor, AutoModel
except ImportError:
    print("尝试从transformers导入...")
    from transformers import ViTImageProcessor, ViTModel

app = FastAPI(
    title="图像聚类API",
    description="基于DINOv3/ViT的图像特征提取和聚类API",
    version="1.0.0",
    max_request_size=100 * 1024 * 1024*1024
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],   # 允许所有方法
    allow_headers=["*"],   # 允许所有头
)

# 全局配置
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
UPLOAD_FOLDER = "uploaded_images"
RESULTS_FOLDER = "clustering_results"

# 创建必要的目录
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
Path(RESULTS_FOLDER).mkdir(exist_ok=True)

# 模型变量
processor = None
model = None
device = None

class ClusteringResponse(BaseModel):
    """聚类响应模型"""
    task_id: str
    status: str
    num_images: int
    num_clusters: int
    download_url: str
    visualization_url: str
    info_url: str
    clusters: Dict[str, Any]

def load_model():
    """加载模型"""
    global processor, model, device
    
    try:
        # 设置设备
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"使用设备: {device}")
        
        # 尝试加载本地DINOv3模型
        try:
            model_path = r"E:\pony\AI\Image_Feature_Clustering_Function\model"
            if os.path.exists(model_path):
                print("加载本地DINOv3模型...")
                processor = AutoImageProcessor.from_pretrained(model_path)
                model = AutoModel.from_pretrained(model_path)
                model_name = "DINOv3"
            else:
                raise FileNotFoundError("本地模型路径不存在")
        except Exception as e:
            print(f"本地模型加载失败: {e}")
            print("加载在线ViT模型作为备用...")
            processor = ViTImageProcessor.from_pretrained("google/vit-base-patch16-224")
            model = ViTModel.from_pretrained("google/vit-base-patch16-224")
            model_name = "ViT-base"
        
        model = model.to(device)
        model.eval()
        print(f"{model_name} 模型加载成功!")
        
    except Exception as e:
        print(f"模型加载失败: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """启动时加载模型"""
    try:
        load_model()
    except Exception as e:
        print(f"启动失败: {e}")

def extract_features_from_images(images: List[Image.Image]) -> np.ndarray:
    """从PIL图像中提取特征"""
    if not images:
        raise ValueError("没有图片数据")
    
    print(f"提取{len(images)}张图片的特征...")
    
    try:
        # 处理输入
        inputs = processor(images=images, return_tensors="pt").to(device)
        
        # 提取特征
        with torch.no_grad():
            outputs = model(**inputs)
        
        # 获取特征
        if hasattr(outputs, 'pooler_output'):
            features = outputs.pooler_output.cpu().numpy()
        elif hasattr(outputs, 'last_hidden_state'):
            # 如果没有pooler_output，使用平均池化
            features = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
        else:
            raise ValueError("模型输出格式不支持")
        
        # 清理
        del inputs, outputs
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        print(f"特征提取完成，形状: {features.shape}")
        return features
        
    except RuntimeError as e:
        if "out of memory" in str(e):
            error_msg = f"GPU内存不足！当前图片数量: {len(images)}"
            print(error_msg)
            raise MemoryError(error_msg)
        raise

@app.post("/cluster")
async def cluster_images(
    k_clusters: int = Form(5, ge=2, le=20),
    method: str = Form("pca"),
    files: List[UploadFile] = File(...)
):
    if processor is None or model is None:
        raise HTTPException(500, "模型未加载")
    
    if not files or len(files) == 0:
        raise HTTPException(400, "请上传图片文件")
    
    # 生成任务ID
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    task_dir = Path(RESULTS_FOLDER) / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        images = []
        file_names = []
        saved_paths = []
        
        print(f"开始处理 {len(files)} 个文件...")
        
        # 1. 限制最大处理数量
        MAX_FILES = 2000
        if len(files) > MAX_FILES:
            raise HTTPException(400, f"单次最多处理{MAX_FILES}个文件，当前{len(files)}个")
        
        # 2. 内存监控
        import psutil
        process = psutil.Process()
        
        # 3. 保存和加载图片
        for i, file in enumerate(files[:MAX_FILES]):
            memory_usage = process.memory_info().rss / 1024 / 1024
            if memory_usage > 4000:
                print(f"警告：内存使用过高 ({memory_usage:.1f} MB)")
            
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in SUPPORTED_FORMATS:
                print(f"跳过不支持的文件格式: {file.filename}")
                continue
            
            try:
                safe_filename = f"img_{i:04d}{file_ext}"
                file_path = task_dir / safe_filename
                
                with open(file_path, "wb") as f:
                    while True:
                        chunk = await file.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                
                with Image.open(file_path) as img:
                    rgb_img = img.convert('RGB')
                    
                    
                    max_size = 1024
                    if max(rgb_img.size) > max_size:
                        ratio = max_size / max(rgb_img.size)
                        new_size = tuple(int(dim * ratio) for dim in rgb_img.size)
                        rgb_img = rgb_img.resize(new_size, Image.Resampling.LANCZOS)
                    
                    img_array = np.array(rgb_img) / 255.0
                    img_normalized = Image.fromarray((img_array * 255).astype(np.uint8))
                    
                    images.append(img_normalized)
                    file_names.append(file.filename)
                    saved_paths.append(str(file_path))
                
                del img_array
                
                print(f"已处理: {file.filename} ({i+1}/{min(len(files), MAX_FILES)})")
                
            except Exception as e:
                print(f"处理文件 {file.filename} 失败: {e}")
                continue
        
        if not images:
            raise HTTPException(400, "没有成功加载任何图片文件")
        
        print(f"成功加载 {len(images)} 张图片，开始特征提取...")
        
        # 4. 特征提取
        import gc
        gc.collect()
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        features = extract_features_from_images(images)
        
        del images
        gc.collect()
        
        print(f"特征提取完成，特征维度: {features.shape}")
        
        # 5. 聚类
        n_clusters = min(k_clusters, len(features))
        print(f"开始K-means聚类，K={n_clusters}...")
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10, verbose=1)
        labels = kmeans.fit_predict(features)
        
        print(f"聚类完成，共 {n_clusters} 个聚类")
        
        # 6. 降维可视化
        if method == "pca":
            reducer = PCA(n_components=2, random_state=42)
        elif method == "tsne":
            perplexity = min(30, len(features)-1)
            if len(features) > 100:
                perplexity = 30
            elif len(features) > 50:
                perplexity = 15
            else:
                perplexity = 5
            reducer = TSNE(n_components=2, random_state=42, 
                          perplexity=perplexity, n_iter=1000)
        else:
            reducer = PCA(n_components=2, random_state=42)
        
        print(f"开始{method.upper()}降维...")
        features_2d = reducer.fit_transform(features)
        
        del features
        gc.collect()
        
        
        # 7. 保存可视化 - 使用鲜艳的彩虹色
        plt.figure(figsize=(14, 10))

        # 获取唯一的聚类标签
        unique_labels = np.unique(labels)
        n_clusters = len(unique_labels)

        # 创建鲜艳的彩虹色调色板
        if n_clusters <= 10:
            # 对于少量聚类，使用Set2或Set3的鲜艳颜色
            colors = plt.cm.Set3(np.linspace(0, 1, max(12, n_clusters)))[:n_clusters]
        elif n_clusters <= 20:
            # 使用tab20c的鲜艳颜色
            colors = plt.cm.tab20c(np.arange(n_clusters))
        elif n_clusters <= 40:
            # 结合tab20c和tab20b
            colors1 = plt.cm.tab20c(np.arange(min(20, n_clusters)))
            if n_clusters > 20:
                colors2 = plt.cm.tab20b(np.arange(n_clusters - 20))
                colors = np.vstack([colors1, colors2])
            else:
                colors = colors1
        else:
            # 对于大量聚类，使用HSV彩虹色，确保颜色鲜艳
            # 调整起始位置和范围以避免红色和紫色过于相似
            h_start = 0.0  # 从红色开始
            h_end = 0.85   # 结束于蓝色/紫色之前，避免和红色太接近
            hues = np.linspace(h_start, h_end, n_clusters)
            
            # 固定饱和度和亮度为高值，确保颜色鲜艳
            saturation = 0.8  # 高饱和度
            lightness = 0.6   # 中等亮度，确保鲜艳
            
            colors = []
            for h in hues:
                # 将HSL转换为RGB
                r, g, b = colorsys.hls_to_rgb(h, lightness, saturation)
                colors.append([r, g, b, 1.0])  # 完全不透明
            
            colors = np.array(colors)

        # 确保颜色足够鲜艳 - 进行后处理增强
        import colorsys
        enhanced_colors = []
        for color in colors:
            r, g, b = color[0], color[1], color[2]
            
            # 转换到HSL空间
            h, l, s = colorsys.rgb_to_hls(r, g, b)
            
            # 增强饱和度（但不超出合理范围）
            s = min(0.95, s * 1.3)
            
            # 调整亮度到最佳鲜艳范围
            l = min(0.85, max(0.4, l * 1.1))
            
            # 转换回RGB
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            
            # 确保颜色值在有效范围内
            r = min(1.0, max(0.0, r))
            g = min(1.0, max(0.0, g))
            b = min(1.0, max(0.0, b))
            
            enhanced_colors.append([r, g, b, color[3] if len(color) > 3 else 1.0])

        colors = np.array(enhanced_colors)
        
        
        
        # 创建散点图
        scatter_plots = []
        for i, label in enumerate(unique_labels):
            mask = labels == label
            scatter = plt.scatter(
                features_2d[mask, 0], 
                features_2d[mask, 1],
                c=[colors[i]], 
                alpha=0.85,  # 增加透明度
                s=80,  # 增大点的大小
                edgecolors='black',  # 黑色边框
                linewidth=1.2,  # 边框宽度
                label=f'聚类 {label}',
                marker='o'  # 圆形标记
            )
            scatter_plots.append(scatter)
        
        # 添加标题和标签
        plt.title(f'图像聚类可视化结果 (K={n_clusters}, 方法={method.upper()})', 
                 fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('维度 1', fontsize=14)
        plt.ylabel('维度 2', fontsize=14)
        plt.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        
        # 添加图例
        if len(unique_labels) <= 15:
            plt.legend(loc='upper right', fontsize=10, framealpha=0.95, 
                      fancybox=True, shadow=True)
        
        # 添加颜色条
        if len(unique_labels) > 1:
            try:
                # 创建自定义颜色映射
                from matplotlib.colors import ListedColormap
                custom_cmap = ListedColormap(colors)
                
                # 创建规范化器
                norm = plt.Normalize(vmin=min(unique_labels), vmax=max(unique_labels))
                
                # 创建ScalarMappable
                sm = plt.cm.ScalarMappable(cmap=custom_cmap, norm=norm)
                sm.set_array([])
                
                # 添加颜色条
                cbar = plt.colorbar(sm, ax=plt.gca(), 
                                  boundaries=np.arange(min(unique_labels)-0.5, max(unique_labels)+1.5, 1),
                                  spacing='proportional')
                cbar.set_ticks(unique_labels)
                cbar.set_label('聚类标签', fontsize=12)
                cbar.ax.tick_params(labelsize=10)
            except Exception as e:
                print(f"颜色条创建失败: {e}")
        
        # 设置背景色为浅灰色，增强对比度
        plt.gca().set_facecolor('#f5f5f5')
        plt.gca().patch.set_alpha(0.8)
        
        plt.tight_layout()
        
        # 保存图像
        viz_path = task_dir / "visualization.png"
        plt.savefig(viz_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"可视化图表已保存: {viz_path}")
        
        # 8. 将图片分类到聚类文件夹
        clusters_dir = task_dir / "clusters"
        clusters_dir.mkdir(exist_ok=True)

        cluster_stats = {}
        for i, (img_path, original_name, label) in enumerate(zip(saved_paths, file_names, labels)):
            cluster_dir = clusters_dir / f"cluster_{label}"
            cluster_dir.mkdir(exist_ok=True)
            
            try:
                ext = os.path.splitext(original_name)[1]
                safe_original_name = os.path.basename(original_name).replace("\\", "_").replace("/", "_")
                safe_name = f"{label:02d}_{i:04d}_{safe_original_name}"
                
                if len(safe_name) > 255:
                    safe_name = safe_name[:250] + ext
                
                shutil.copy2(img_path, cluster_dir / safe_name)
                cluster_stats[label] = cluster_stats.get(label, 0) + 1
                
            except Exception as e:
                print(f"复制文件失败 {img_path}: {e}")
                try:
                    simple_name = f"img_{i:04d}{os.path.splitext(original_name)[1]}"
                    shutil.copy2(img_path, cluster_dir / simple_name)
                    cluster_stats[label] = cluster_stats.get(label, 0) + 1
                except Exception as e2:
                    print(f"备用方案也失败: {e2}")        
        
        # 9. 保存聚类信息
        clusters_info = {}
        for label, count in cluster_stats.items():
            clusters_info[f"cluster_{label}"] = {
                "id": int(label),
                "count": count,
                "percentage": count / len(saved_paths) * 100,
                "examples": []
            }
        
        for label in cluster_stats.keys():
            cluster_examples = []
            for i, (original_name, file_label) in enumerate(zip(file_names, labels)):
                if file_label == label and len(cluster_examples) < 3:
                    cluster_examples.append(original_name)
            if cluster_examples:
                clusters_info[f"cluster_{label}"]["examples"] = cluster_examples
        
        info_json = {
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "num_images": len(saved_paths),
            "num_clusters": n_clusters,
            "method": method,
            "clusters": clusters_info,
            "file_list": [
                {
                    "original_name": file_names[i],
                    "cluster": int(labels[i]),
                    "dimensions": {
                        "x": float(features_2d[i, 0]),
                        "y": float(features_2d[i, 1])
                    }
                }
                for i in range(len(file_names))
            ]
        }
        
        info_path = task_dir / "info.json"
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info_json, f, ensure_ascii=False, indent=2)
        
        print(f"聚类信息已保存: {info_path}")
        
        # 10. 创建压缩包
        zip_path = task_dir / f"results_{task_id}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in [viz_path, info_path]:
                if file.exists():
                    zipf.write(file, file.relative_to(task_dir))
            
            if clusters_dir.exists():
                for root, dirs, files_in_dir in os.walk(clusters_dir):
                    for file_in_dir in files_in_dir:
                        file_path = os.path.join(root, file_in_dir)
                        arcname = os.path.relpath(file_path, task_dir)
                        zipf.write(file_path, arcname)
        
        print(f"结果压缩包已创建: {zip_path}")
        
        # 11. 清理原始图片文件
        for img_path in saved_paths:
            try:
                os.remove(img_path)
            except:
                pass
        
        print(f"任务 {task_id} 处理完成！")
        
        return ClusteringResponse(
            task_id=task_id,
            status="success",
            num_images=len(saved_paths),
            num_clusters=n_clusters,
            download_url=f"/download/{task_id}",
            visualization_url=f"/visualization/{task_id}",
            info_url=f"/info/{task_id}",
            clusters=clusters_info
        )
        
    except Exception as e:
        print(f"聚类失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"处理失败: {str(e)}")

# 保持原有的API端点不变
@app.get("/download/{task_id}")
async def download_results(task_id: str):
    task_dir = Path(RESULTS_FOLDER) / task_id
    zip_file = task_dir / f"results_{task_id}.zip"
    
    if not zip_file.exists():
        raise HTTPException(404, "任务不存在")
    
    return FileResponse(
        path=zip_file,
        filename=f"clustering_results_{task_id}.zip",
        media_type="application/zip"
    )

@app.get("/visualization/{task_id}")
async def get_visualization(task_id: str):
    task_dir = Path(RESULTS_FOLDER) / task_id
    viz_file = task_dir / "visualization.png"
    
    if not viz_file.exists():
        raise HTTPException(404, "可视化图不存在")
    
    return FileResponse(viz_file)

@app.get("/info/{task_id}")
async def get_info(task_id: str):
    task_dir = Path(RESULTS_FOLDER) / task_id
    info_file = task_dir / "info.json"
    
    if not info_file.exists():
        raise HTTPException(404, "任务信息不存在")
    
    with open(info_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return JSONResponse(data)

@app.get("/tasks")
async def list_tasks():
    tasks = []
    
    for task_dir in Path(RESULTS_FOLDER).iterdir():
        if task_dir.is_dir():
            info_file = task_dir / "info.json"
            if info_file.exists():
                try:
                    with open(info_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    tasks.append({
                        "task_id": task_dir.name,
                        "num_images": data.get("num_images", 0),
                        "num_clusters": data.get("num_clusters", 0),
                        "timestamp": data.get("timestamp", "")
                    })
                except:
                    continue
    
    tasks.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return {"tasks": tasks[:20]}

@app.get("/health")
async def health_check():
    status = "healthy" if (processor and model) else "error"
    
    return {
        "status": status,
        "model": "DINOv3/ViT",
        "device": str(device),
        "endpoints": {
            "cluster": "POST /cluster",
            "download": "GET /download/{task_id}",
            "tasks": "GET /tasks",
            "health": "GET /health"
        }
    }

@app.get("/")
async def root():
    return {
        "name": "图像聚类API",
        "version": "1.0.0",
        "description": "基于深度学习的图像特征聚类服务",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "cluster": "POST /cluster",
            "health": "GET /health"
        },
        "usage": "请访问 /docs 查看API文档和使用方法"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
    
    
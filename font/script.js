// // script.js - 修复版
// document.addEventListener('DOMContentLoaded', function() {
//     // 配置
//     const API_BASE_URL = 'http://localhost:8000';
//     let selectedFiles = [];
//     let currentTaskId = null;
    
//     // 元素引用
//     const elements = {
//         folderBtn: document.getElementById('folder-select-btn'),
//         folderInput: document.getElementById('folder-input'),
//         folderInfo: document.getElementById('folder-info'),
//         folderPath: document.getElementById('folder-path'),
//         fileCount: document.getElementById('file-count'),
//         totalSize: document.getElementById('total-size'),
//         kSlider: document.getElementById('k-clusters'),
//         kValue: document.getElementById('k-value'),
//         methodSelect: document.getElementById('method'),
//         startBtn: document.getElementById('start-btn'),
//         errorMsg: document.getElementById('error-message'),
//         progressContainer: document.getElementById('progress-container'),
//         progressFill: document.getElementById('progress-fill'),
//         progressText: document.getElementById('progress-text'),
//         progressPercent: document.getElementById('progress-percent'),
//         resultsPlaceholder: document.getElementById('results-placeholder'),
//         resultsContent: document.getElementById('results-content'),
//         visualizationImg: document.getElementById('visualization-img'),
//         clustersContainer: document.getElementById('clusters-container'),
//         taskInfo: document.getElementById('task-info'),
//         downloadBtn: document.getElementById('download-btn'),
//         statusDot: document.getElementById('status-dot'),
//         statusText: document.getElementById('status-text')
//     };
    
//     // 初始化
//     init();
    
//     function init() {
//         // 检查API连接
//         checkAPIStatus();
        
//         // 文件夹选择
//         elements.folderBtn.addEventListener('click', () => elements.folderInput.click());
        
//         // 文件夹选择变化
//         elements.folderInput.addEventListener('change', handleFolderSelect);
        
//         // K值滑块
//         elements.kSlider.addEventListener('input', updateKValue);
        
//         // 开始按钮
//         elements.startBtn.addEventListener('click', startClustering);
        
//         // 初始化K值显示
//         updateKValue();
//     }
    
//     // 检查API状态
//     async function checkAPIStatus() {
//         try {
//             console.log('检查API连接...');
//             const response = await fetch(`${API_BASE_URL}/health`);
//             console.log('API响应状态:', response.status);
            
//             if (response.ok) {
//                 const data = await response.json();
//                 console.log('API健康信息:', data);
//                 setStatus('connected', 'API连接正常');
//             } else {
//                 console.error('API返回错误状态:', response.status);
//                 setStatus('error', `API连接失败: ${response.status}`);
//             }
//         } catch (error) {
//             console.error('API连接错误:', error);
//             setStatus('error', '无法连接到API，请确保服务已启动');
//         }
//     }
    
//     // 设置状态
//     function setStatus(type, message) {
//         elements.statusDot.className = 'status-dot';
//         elements.statusText.textContent = message;
        
//         if (type === 'connected') {
//             elements.statusDot.classList.add('connected');
//             elements.statusDot.style.background = '#28a745';
//         } else if (type === 'error') {
//             elements.statusDot.style.background = '#dc3545';
//         }
//     }
    
//     // 处理文件夹选择
//     function handleFolderSelect(event) {
//         const files = Array.from(event.target.files);
        
//         if (files.length === 0) {
//             showError('请选择一个文件夹');
//             elements.startBtn.disabled = true;
//             return;
//         }
        
//         // 过滤图片文件
//         const imageFiles = files.filter(file => {
//             const fileName = file.name.toLowerCase();
//             return fileName.endsWith('.jpg') || 
//                    fileName.endsWith('.jpeg') || 
//                    fileName.endsWith('.png') || 
//                    fileName.endsWith('.bmp') ||
//                    fileName.endsWith('.tiff') ||
//                    fileName.endsWith('.tif') ||
//                    fileName.endsWith('.webp');
//         });
        
//         if (imageFiles.length === 0) {
//             showError('文件夹中没有找到支持的图片文件');
//             elements.startBtn.disabled = true;
//             return;
//         }
        
//         // 保存文件
//         selectedFiles = imageFiles;
        
//         // 更新显示
//         const folderName = files[0].webkitRelativePath?.split('/')[0] || '选择的文件夹';
//         const totalSize = imageFiles.reduce((sum, file) => sum + file.size, 0);
        
//         elements.folderPath.textContent = folderName;
//         elements.fileCount.textContent = `${imageFiles.length} 个图片文件`;
//         elements.totalSize.textContent = `总大小: ${formatFileSize(totalSize)}`;
        
//         elements.folderInfo.style.display = 'block';
//         elements.startBtn.disabled = false;
        
//         showError(''); // 清除错误信息
//     }
    
//     // 更新K值显示
//     function updateKValue() {
//         elements.kValue.textContent = elements.kSlider.value;
//     }
    
//     // 开始聚类分析
//     async function startClustering() {
//         if (selectedFiles.length === 0) {
//             showError('请先选择文件夹');
//             return;
//         }
        
//         // 禁用按钮，显示进度条
//         elements.startBtn.disabled = true;
//         elements.startBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 处理中...';
//         elements.progressContainer.style.display = 'block';
        
//         try {
//             // 步骤1：准备数据
//             updateProgress(10, '正在准备文件...');
            
//             const formData = new FormData();
//             formData.append('k_clusters', elements.kSlider.value);
//             formData.append('method', elements.methodSelect.value);
//             formData.append('normalization_method', 'simple');
            
//             // 添加文件（限制数量，避免过大）
//             const maxFiles = Math.min(selectedFiles.length, 50); // 限制最多50个文件
//             for (let i = 0; i < maxFiles; i++) {
//                 formData.append('files', selectedFiles[i]);
//             }
            
//             console.log(`上传 ${maxFiles} 个文件到API...`);
            
//             // 步骤2：上传到API
//             updateProgress(30, '正在上传文件到API...');
            
//             const response = await fetch(`${API_BASE_URL}/cluster`, {
//                 method: 'POST',
//                 body: formData
//             });
            
//             if (!response.ok) {
//                 let errorMessage = '上传失败';
//                 try {
//                     const errorData = await response.json();
//                     errorMessage = errorData.detail || errorMessage;
//                 } catch (e) {
//                     errorMessage = `HTTP ${response.status}: ${response.statusText}`;
//                 }
//                 throw new Error(errorMessage);
//             }
            
//             const result = await response.json();
//             console.log('API返回结果:', result);
//             currentTaskId = result.task_id;
            
//             // 模拟进度更新
//             const steps = [
//                 { percent: 50, message: '正在提取图像特征...' },
//                 { percent: 65, message: '正在聚类分析...' },
//                 { percent: 80, message: '正在生成可视化图表...' },
//                 { percent: 95, message: '正在整理结果文件...' },
//                 { percent: 100, message: '处理完成!' }
//             ];
            
//             for (const step of steps) {
//                 await delay(1000); // 等待1秒
//                 updateProgress(step.percent, step.message);
//             }
            
//             // 显示结果
//             await showResults(result);
            
//         } catch (error) {
//             showError(`处理失败: ${error.message}`);
//             console.error('聚类分析错误:', error);
            
//             // 重置进度条
//             elements.progressContainer.style.display = 'none';
//         } finally {
//             // 重置按钮
//             elements.startBtn.disabled = false;
//             elements.startBtn.innerHTML = '<i class="fas fa-play-circle"></i> 开始聚类分析';
//         }
//     }
    
//     // 显示结果
//     async function showResults(result) {
//         // 隐藏占位符，显示内容
//         elements.resultsPlaceholder.style.display = 'none';
//         elements.resultsContent.style.display = 'block';
        
//         try {
//             // 显示可视化图
//             const vizUrl = `${API_BASE_URL}/visualization/${result.task_id}?t=${Date.now()}`;
//             elements.visualizationImg.src = vizUrl;
            
//             // 显示聚类统计
//             displayClusterStats(result.clusters);
            
//             // 显示任务信息
//             elements.taskInfo.innerHTML = `
//                 <p><strong>任务ID:</strong> ${result.task_id}</p>
//                 <p><strong>处理图片:</strong> ${result.num_images} 张</p>
//                 <p><strong>聚类数量:</strong> ${result.num_clusters} 组</p>
//                 <p><strong>处理时间:</strong> ${new Date().toLocaleString('zh-CN')}</p>
//             `;
            
//             // 显示下载按钮
//             elements.downloadBtn.href = `${API_BASE_URL}/download/${result.task_id}`;
//             elements.downloadBtn.style.display = 'inline-block';
            
//         } catch (error) {
//             console.error('显示结果错误:', error);
//             showError('显示结果时出错: ' + error.message);
//         }
//     }
    
//     // 显示聚类统计
//     function displayClusterStats(clusters) {
//         const colors = [
//             '#4a6ee0', '#28a745', '#fd7e14', '#dc3545', '#6f42c1',
//             '#20c997', '#ffc107', '#e83e8c', '#17a2b8', '#6610f2'
//         ];
        
//         elements.clustersContainer.innerHTML = '';
        
//         if (!clusters) {
//             elements.clustersContainer.innerHTML = '<p>没有聚类数据</p>';
//             return;
//         }
        
//         Object.entries(clusters).forEach(([clusterName, clusterInfo], index) => {
//             const color = colors[index % colors.length];
            
//             const card = document.createElement('div');
//             card.className = 'cluster-card';
//             card.innerHTML = `
//                 <div class="cluster-color" style="background-color: ${color}"></div>
//                 <div class="cluster-name">${clusterName}</div>
//                 <div class="cluster-count">${clusterInfo.count || 0}</div>
//                 <div class="cluster-percentage">${(clusterInfo.percentage || 0).toFixed(1)}%</div>
//             `;
            
//             elements.clustersContainer.appendChild(card);
//         });
//     }
    
//     // 更新进度
//     function updateProgress(percent, message) {
//         elements.progressFill.style.width = `${percent}%`;
//         elements.progressText.textContent = message;
//         elements.progressPercent.textContent = `${percent}%`;
//     }
    
//     // 显示错误信息
//     function showError(message) {
//         if (message) {
//             elements.errorMsg.textContent = message;
//             elements.errorMsg.style.display = 'block';
//         } else {
//             elements.errorMsg.style.display = 'none';
//         }
//     }
    
//     // 工具函数
//     function formatFileSize(bytes) {
//         if (bytes === 0) return '0 B';
//         const k = 1024;
//         const sizes = ['B', 'KB', 'MB', 'GB'];
//         const i = Math.floor(Math.log(bytes) / Math.log(k));
//         return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
//     }
    
//     function delay(ms) {
//         return new Promise(resolve => setTimeout(resolve, ms));
//     }
    
//     // 添加调试信息
//     console.log('前端脚本已加载');
// });



// script.js - 修复版
document.addEventListener('DOMContentLoaded', function() {
    // 配置
    const API_BASE_URL = 'http://localhost:8000';
    let selectedFiles = [];
    let currentTaskId = null;
    
    // 元素引用
    const elements = {
        folderBtn: document.getElementById('folder-select-btn'),
        folderInput: document.getElementById('folder-input'),
        folderInfo: document.getElementById('folder-info'),
        folderPath: document.getElementById('folder-path'),
        fileCount: document.getElementById('file-count'),
        totalSize: document.getElementById('total-size'),
        kSlider: document.getElementById('k-clusters'),
        kValue: document.getElementById('k-value'),
        methodSelect: document.getElementById('method'),
        startBtn: document.getElementById('start-btn'),
        errorMsg: document.getElementById('error-message'),
        progressContainer: document.getElementById('progress-container'),
        progressFill: document.getElementById('progress-fill'),
        progressText: document.getElementById('progress-text'),
        progressPercent: document.getElementById('progress-percent'),
        resultsPlaceholder: document.getElementById('results-placeholder'),
        resultsContent: document.getElementById('results-content'),
        visualizationImg: document.getElementById('visualization-img'),
        clustersContainer: document.getElementById('clusters-container'),
        taskInfo: document.getElementById('task-info'),
        downloadBtn: document.getElementById('download-btn'),
        statusDot: document.getElementById('status-dot'),
        statusText: document.getElementById('status-text')
    };
    
    // 初始化
    init();
    
    function init() {
        console.log('前端初始化...');
        
        // 检查API连接
        checkAPIStatus();
        
        // 文件夹选择
        elements.folderBtn.addEventListener('click', () => {
            console.log('点击文件夹选择按钮');
            elements.folderInput.click();
        });
        
        // 文件夹选择变化
        elements.folderInput.addEventListener('change', handleFolderSelect);
        
        // K值滑块
        elements.kSlider.addEventListener('input', updateKValue);
        
        // 开始按钮
        elements.startBtn.addEventListener('click', startClustering);
        
        // 初始化K值显示
        updateKValue();
        
        console.log('前端初始化完成');
    }
    
    // 检查API状态
    async function checkAPIStatus() {
        console.log('开始检查API连接...');
        
        try {
            const response = await fetch(`${API_BASE_URL}/health`);
            
            if (response.ok) {
                const data = await response.json();
                console.log('API健康信息:', data);
                setStatus('connected', 'API连接正常');
                return true;
            } else {
                console.error('API返回错误状态:', response.status);
                setStatus('error', `API连接失败: HTTP ${response.status}`);
                return false;
            }
        } catch (error) {
            console.error('API连接错误:', error);
            setStatus('error', '无法连接到API，请确保服务已启动');
            return false;
        }
    }
    
    // 设置状态
    function setStatus(type, message) {
        elements.statusDot.className = 'status-dot';
        elements.statusText.textContent = message;
        
        if (type === 'connected') {
            elements.statusDot.classList.add('connected');
            elements.statusDot.style.background = '#28a745';
            elements.startBtn.disabled = false;
        } else if (type === 'error') {
            elements.statusDot.style.background = '#dc3545';
            elements.startBtn.disabled = true;
        }
    }
    
    // 处理文件夹选择
    function handleFolderSelect(event) {
        console.log('文件夹选择变化:', event.target.files);
        
        const files = Array.from(event.target.files);
        
        if (files.length === 0) {
            showError('请选择一个文件夹');
            elements.startBtn.disabled = true;
            return;
        }
        
        // 过滤图片文件
        const imageFiles = files.filter(file => {
            const fileName = file.name.toLowerCase();
            return fileName.endsWith('.jpg') || 
                   fileName.endsWith('.jpeg') || 
                   fileName.endsWith('.png') || 
                   fileName.endsWith('.bmp') ||
                   fileName.endsWith('.tiff') ||
                   fileName.endsWith('.tif') ||
                   fileName.endsWith('.webp');
        });
        
        console.log(`找到 ${imageFiles.length} 个图片文件`);
        
        if (imageFiles.length === 0) {
            showError('文件夹中没有找到支持的图片文件');
            elements.startBtn.disabled = true;
            return;
        }
        
        // 保存文件 - 这里只保存文件对象，不依赖webkitRelativePath
        selectedFiles = imageFiles;
        
        // 获取文件夹名（从第一个文件的webkitRelativePath）
        let folderName = '选择的文件夹';
        if (files[0].webkitRelativePath) {
            folderName = files[0].webkitRelativePath.split('/')[0];
        }
        
        // 更新显示
        const totalSize = imageFiles.reduce((sum, file) => sum + file.size, 0);
        
        elements.folderPath.textContent = folderName;
        elements.fileCount.textContent = `${imageFiles.length} 个图片文件`;
        elements.totalSize.textContent = `总大小: ${formatFileSize(totalSize)}`;
        
        elements.folderInfo.style.display = 'block';
        
        showError(''); // 清除错误信息
        
        // 显示文件预览
        displayFilePreview(imageFiles);
    }
    
    // 显示文件预览
    function displayFilePreview(files) {
        const previewContainer = elements.folderInfo.querySelector('.preview-content');
        if (!previewContainer) {
            const previewDiv = document.createElement('div');
            previewDiv.className = 'preview-content';
            previewDiv.innerHTML = `
                <h4>文件预览（最多显示10个）:</h4>
                <div class="file-list" id="file-preview-list"></div>
            `;
            elements.folderInfo.appendChild(previewDiv);
        }
        
        const fileList = document.getElementById('file-preview-list') || 
                         document.createElement('div');
        fileList.innerHTML = '';
        
        // 显示前10个文件
        const maxPreview = 10;
        files.slice(0, maxPreview).forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-preview-item';
            fileItem.innerHTML = `
                <i class="fas fa-image"></i>
                <span class="file-name">${file.name}</span>
                <span class="file-size">(${formatFileSize(file.size)})</span>
            `;
            fileList.appendChild(fileItem);
        });
        
        if (files.length > maxPreview) {
            const moreText = document.createElement('div');
            moreText.className = 'more-files';
            moreText.textContent = `... 还有 ${files.length - maxPreview} 个文件`;
            fileList.appendChild(moreText);
        }
    }
    
    // 更新K值显示
    function updateKValue() {
        elements.kValue.textContent = elements.kSlider.value;
    }
    
    // 开始聚类分析
    async function startClustering() {
        console.log('开始聚类分析...');
        
        if (selectedFiles.length === 0) {
            showError('请先选择文件夹');
            return;
        }
        
        // 检查API状态
        const apiOk = await checkAPIStatus();
        if (!apiOk) {
            showError('API连接失败，无法开始处理');
            return;
        }
        
        // 禁用按钮，显示进度条
        elements.startBtn.disabled = true;
        elements.startBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 处理中...';
        elements.progressContainer.style.display = 'block';
        
        try {
            // 步骤1：准备数据
            updateProgress(10, '正在准备文件...');
            
            const formData = new FormData();
            formData.append('k_clusters', elements.kSlider.value);
            formData.append('method', elements.methodSelect.value);
            
            // 添加文件（限制数量，避免过大）
            const maxFiles = Math.min(selectedFiles.length, 50); // 限制最多50个文件
            console.log(`准备上传 ${maxFiles} 个文件`);
            
            for (let i = 0; i < maxFiles; i++) {
                // 直接添加文件对象，不修改文件名
                formData.append('files', selectedFiles[i]);
            }
            
            // 步骤2：上传到API
            updateProgress(30, '正在上传文件到API...');
            console.log('开始上传到API...');
            
            const response = await fetch(`${API_BASE_URL}/cluster`, {
                method: 'POST',
                body: formData
            });
            
            console.log('API响应状态:', response.status);
            
            if (!response.ok) {
                let errorMessage = '上传失败';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorMessage;
                    console.error('API错误详情:', errorData);
                } catch (e) {
                    errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                }
                throw new Error(errorMessage);
            }
            
            const result = await response.json();
            console.log('API返回结果:', result);
            currentTaskId = result.task_id;
            
            // 模拟进度更新
            const steps = [
                { percent: 50, message: '正在提取图像特征...' },
                { percent: 65, message: '正在聚类分析...' },
                { percent: 80, message: '正在生成可视化图表...' },
                { percent: 95, message: '正在整理结果文件...' },
                { percent: 100, message: '处理完成!' }
            ];
            
            for (const step of steps) {
                await delay(800); // 等待800ms
                updateProgress(step.percent, step.message);
            }
            
            // 显示结果
            await showResults(result);
            
        } catch (error) {
            console.error('聚类分析错误:', error);
            showError(`处理失败: ${error.message}`);
            
            // 重置进度条
            elements.progressContainer.style.display = 'none';
        } finally {
            // 重置按钮
            elements.startBtn.disabled = false;
            elements.startBtn.innerHTML = '<i class="fas fa-play-circle"></i> 开始聚类分析';
        }
    }
    
    // 显示结果
    async function showResults(result) {
        console.log('显示结果:', result);
        
        // 隐藏占位符，显示内容
        elements.resultsPlaceholder.style.display = 'none';
        elements.resultsContent.style.display = 'block';
        
        try {
            // 显示可视化图（添加时间戳避免缓存）
            const vizUrl = `${API_BASE_URL}/visualization/${result.task_id}?t=${Date.now()}`;
            console.log('可视化图URL:', vizUrl);
            
            elements.visualizationImg.src = vizUrl;
            elements.visualizationImg.onerror = function() {
                console.error('可视化图加载失败');
                this.src = ''; // 清除失败的src
                showError('可视化图加载失败');
            };
            
            // 显示聚类统计
            displayClusterStats(result.clusters);
            
            // 显示任务信息
            elements.taskInfo.innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                    <div class="info-item">
                        <strong>任务ID:</strong><br>${result.task_id}
                    </div>
                    <div class="info-item">
                        <strong>处理图片:</strong><br>${result.num_images} 张
                    </div>
                    <div class="info-item">
                        <strong>聚类数量:</strong><br>${result.num_clusters} 组
                    </div>
                    <div class="info-item">
                        <strong>处理时间:</strong><br>${new Date().toLocaleString('zh-CN')}
                    </div>
                </div>
            `;
            
            // 显示下载按钮
            elements.downloadBtn.href = `${API_BASE_URL}/download/${result.task_id}`;
            elements.downloadBtn.style.display = 'inline-block';
            elements.downloadBtn.onclick = function() {
                console.log('开始下载结果');
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 下载中...';
            };
            
        } catch (error) {
            console.error('显示结果错误:', error);
            showError('显示结果时出错: ' + error.message);
        }
    }
    
    // 显示聚类统计
    function displayClusterStats(clusters) {
        console.log('显示聚类统计:', clusters);
        
        const colors = [
            '#4a6ee0', '#28a745', '#fd7e14', '#dc3545', '#6f42c1',
            '#20c997', '#ffc107', '#e83e8c', '#17a2b8', '#6610f2'
        ];
        
        elements.clustersContainer.innerHTML = '';
        
        if (!clusters) {
            console.warn('没有聚类数据');
            elements.clustersContainer.innerHTML = '<p>没有聚类数据</p>';
            return;
        }
        
        // 按聚类ID排序
        const sortedClusters = Object.entries(clusters)
            .sort(([a], [b]) => {
                const aNum = parseInt(a.replace('cluster_', ''));
                const bNum = parseInt(b.replace('cluster_', ''));
                return aNum - bNum;
            });
        
        sortedClusters.forEach(([clusterName, clusterInfo], index) => {
            const color = colors[index % colors.length];
            
            const card = document.createElement('div');
            card.className = 'cluster-card';
            
            // 构建示例文件显示
            let examplesHtml = '';
            if (clusterInfo.examples && clusterInfo.examples.length > 0) {
                examplesHtml = `
                    <div class="examples" style="margin-top: 10px; font-size: 0.8rem; color: #666;">
                        <div style="margin-bottom: 5px;">示例:</div>
                        ${clusterInfo.examples.slice(0, 3).map(name => 
                            `<div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">• ${name}</div>`
                        ).join('')}
                    </div>
                `;
            }
            
            card.innerHTML = `
                <div class="cluster-color" style="background-color: ${color}"></div>
                <div class="cluster-name">${clusterName}</div>
                <div class="cluster-count">${clusterInfo.count || 0}</div>
                <div class="cluster-percentage">${(clusterInfo.percentage || 0).toFixed(1)}%</div>
                ${examplesHtml}
            `;
            
            elements.clustersContainer.appendChild(card);
        });
    }
    
    // 更新进度
    function updateProgress(percent, message) {
        elements.progressFill.style.width = `${percent}%`;
        elements.progressText.textContent = message;
        elements.progressPercent.textContent = `${percent}%`;
    }
    
    // 显示错误信息
    function showError(message) {
        console.log('显示错误信息:', message);
        
        if (message) {
            elements.errorMsg.textContent = message;
            elements.errorMsg.style.display = 'block';
        } else {
            elements.errorMsg.style.display = 'none';
        }
    }
    
    // 工具函数
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    function delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    console.log('前端脚本加载完成');
});
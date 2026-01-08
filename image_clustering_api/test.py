# # test.py
# import requests
# import time

# def test_api():
#     """测试API是否正常工作"""
    
#     BASE_URL = "http://localhost:8000"
    
#     print("测试图像聚类API...")
#     print("=" * 60)
    
#     # 1. 测试根目录
#     print("1. 测试根目录...")
#     try:
#         response = requests.get(f"{BASE_URL}/")
#         if response.status_code == 200:
#             print("✓ 根目录访问正常")
#             print(f"  响应: {response.json()}")
#         else:
#             print(f"✗ 根目录访问失败: {response.status_code}")
#     except Exception as e:
#         print(f"✗ 连接失败: {e}")
#         return
    
#     # 2. 测试健康检查
#     print("\n2. 测试健康检查...")
#     try:
#         response = requests.get(f"{BASE_URL}/health")
#         if response.status_code == 200:
#             health = response.json()
#             print(f"✓ 服务状态: {health.get('status')}")
#             print(f"  模型: {health.get('model')}")
#             print(f"  设备: {health.get('device', 'unknown')}")
#         else:
#             print(f"✗ 健康检查失败: {response.status_code}")
#     except Exception as e:
#         print(f"✗ 健康检查失败: {e}")
    
#     # 3. 测试任务列表
#     print("\n3. 测试任务列表...")
#     try:
#         response = requests.get(f"{BASE_URL}/tasks")
#         if response.status_code == 200:
#             tasks = response.json()
#             print(f"✓ 有 {len(tasks.get('tasks', []))} 个历史任务")
#         else:
#             print(f"✗ 任务列表失败: {response.status_code}")
#     except Exception as e:
#         print(f"✗ 任务列表失败: {e}")
    
#     # 4. 测试文档页面
#     print("\n4. API文档地址:")
#     print(f"   Swagger UI: {BASE_URL}/docs")
#     print(f"   ReDoc: {BASE_URL}/redoc")
    
#     print("\n" + "=" * 60)
#     print("测试完成！")
#     print("\n使用说明:")
#     print("1. 访问 http://localhost:8000/docs 查看API文档")
#     print("2. 使用POST /cluster/images 进行图像聚类")
#     print("3. 提供文件夹路径或上传文件")
#     print("4. 下载结果压缩包")

# if __name__ == "__main__":
#     test_api()


# test_simple.py
import requests
import os

def test_basic():
    """基础测试"""
    BASE_URL = "http://localhost:8000"
    
    print("测试图像聚类API...")
    print("=" * 60)
    
    # 1. 测试根目录
    print("1. 测试API根目录:")
    try:
        resp = requests.get(f"{BASE_URL}/")
        if resp.status_code == 200:
            print(f"   ✓ 成功: {resp.json()}")
        else:
            print(f"   ✗ 失败: {resp.status_code}")
    except Exception as e:
        print(f"   ✗ 异常: {e}")
    
    # 2. 测试健康检查
    print("\n2. 测试健康检查:")
    try:
        resp = requests.get(f"{BASE_URL}/health")
        if resp.status_code == 200:
            health = resp.json()
            print(f"   ✓ 状态: {health.get('status')}")
        else:
            print(f"   ✗ 失败: {resp.status_code}")
    except Exception as e:
        print(f"   ✗ 异常: {e}")
    
    # 3. 测试任务列表
    print("\n3. 测试任务列表:")
    try:
        resp = requests.get(f"{BASE_URL}/tasks")
        if resp.status_code == 200:
            tasks = resp.json()
            print(f"   ✓ 找到 {len(tasks.get('tasks', []))} 个任务")
        else:
            print(f"   ✗ 失败: {resp.status_code}")
    except Exception as e:
        print(f"   ✗ 异常: {e}")
    
    print("\n" + "=" * 60)
    print("API文档:")
    print(f"  Swagger UI: {BASE_URL}/docs")
    print(f"  ReDoc: {BASE_URL}/redoc")
    
    print("\n使用示例:")
    print("1. 使用文件夹路径聚类:")
    print('   curl -X POST "http://localhost:8000/cluster" \\')
    print('     -F "k_clusters=5" \\')
    print('     -F "method=pca" \\')
    print('     -F "folder_path=/path/to/images"')
    
    print("\n2. 上传文件聚类:")
    print('   curl -X POST "http://localhost:8000/cluster" \\')
    print('     -F "k_clusters=3" \\')
    print('     -F "method=tsne" \\')
    print('     -F "files=@image1.jpg" \\')
    print('     -F "files=@image2.jpg"')

def test_with_folder():
    """使用文件夹测试聚类"""
    BASE_URL = "http://localhost:8000"
    
    # 替换为您的测试文件夹路径
    test_folder = r"E:\pony\AI\Image_Feature_Clustering_Function\hymenoptera_data\val_data\ants"
    
    if not os.path.exists(test_folder):
        print(f"\n测试文件夹不存在: {test_folder}")
        print("请修改test_with_folder函数中的路径")
        return
    
    print(f"\n使用文件夹测试聚类: {test_folder}")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/cluster",
            data={
                "k_clusters": 3,
                "method": "pca"
            },
            files={
                "folder_path": (None, test_folder)
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ 聚类成功!")
            print(f"  任务ID: {result['task_id']}")
            print(f"  处理图片: {result['num_images']} 张")
            print(f"  聚类数量: {result['num_clusters']}")
            print(f"  下载链接: {BASE_URL}{result['download_url']}")
            print(f"  可视化图: {BASE_URL}{result['visualization_url']}")
            
            # 显示聚类统计
            print(f"\n聚类统计:")
            for cluster_id, info in result['clusters'].items():
                print(f"  {cluster_id}: {info['count']} 张图片 ({info['percentage']:.1f}%)")
        else:
            print(f"✗ 聚类失败: {response.status_code}")
            print(f"  错误信息: {response.text}")
            
    except Exception as e:
        print(f"✗ 请求异常: {e}")

if __name__ == "__main__":
    test_basic()
    
    # 取消注释下面这行来测试实际聚类
    # test_with_folder()
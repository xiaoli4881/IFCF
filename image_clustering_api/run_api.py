# import uvicorn

# if __name__ == "__main__":
#     print("启动图像聚类API服务...")
#     print("文档地址: http://localhost:8000/docs")
#     print("按 Ctrl+C 停止服务")
    
#     uvicorn.run(
#         "main:app",
#         host="0.0.0.0",
#         port=8000,
#         reload=True,
#         log_level="info"
#     )
    
    
import uvicorn

if __name__ == "__main__":
    print("启动图像聚类API服务...")
    print("文档地址: http://localhost:8000/docs")
    print("按 Ctrl+C 停止服务")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        limit_concurrency=100,
        limit_max_requests=1000,
        timeout_keep_alive=30,
        reload=True,
        log_level="info"
    )
    
    
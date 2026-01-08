from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

API_URL = "http://10.162.249.248:4434/v1/chat/completions"
API_SECRET = "GHstkE5dVCjqT3v323qxyRrHS01RLstxmMquks1gyGtiB7-jCw"
API_ID = "15fdd354-8cfe-405a-8675-56ba3a41e577"

# 修改路由以匹配前端请求
@app.route('/v1/chat/completions', methods=['POST', 'OPTIONS'])
def proxy_analyze():
    if request.method == 'OPTIONS':
        # 处理预检请求
        return '', 200
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_SECRET}",
            "API-ID": API_ID
        }
        
        response = requests.post(
            API_URL,
            headers=headers,
            json=request.json,
            timeout=60
        )
        
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 添加根路由用于测试
@app.route('/')
def index():
    return jsonify({
        "message": "代理服务器正在运行",
        "endpoint": "/v1/chat/completions",
        "target": API_URL
    })

if __name__ == '__main__':
    app.run(port=3000, debug=True)

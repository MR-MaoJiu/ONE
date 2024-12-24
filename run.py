import os
import sys

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 启动FastAPI应用
if __name__ == "__main__":
    import uvicorn
    from api.main import app
    
    uvicorn.run(app, host="0.0.0.0", port=8000) 
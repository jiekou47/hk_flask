# 导入 Flask 模块
from flask import Flask, request, render_template, jsonify
from Save import *

import os
import base64
import threading
import cv2
# 创建 Flask 应用实例
app = Flask(__name__)

cam_ip = 44
File_Path = f"/home/advantech/mv/{str(cam_ip)}/Image_w5120_h5120_fn.jpg"




cam = CamHolder()


# 定义主页路由
@app.route('/start_cam')
def start_cam():
    # 返回主页内容
    main_loop(cam,cam_ip)

    
@app.route('/hello')
def hello():
    # 返回主页内容
    

    return 'hello world'
@app.route('/getImage')
def get_image():
    file_path = File_Path

    # 等待摄像机实例准备就绪，设置超时时间（例如 30 秒）
    # 这可以防止在 cam.instance 仍为 None 时发生 AttributeError
    print(f"Waiting for cam instance to be ready, ID: {id(cam)}")
    print(cam.instance.is_saving)
    if not cam.ready_event.wait(timeout=30): # 等待事件，最长等待 30 秒
        return jsonify({"error": "error1"}), 503 # Service Unavailable

    # 现在 cam.instance 应该是一个有效的对象
    if cam.instance is None:
        # 理论上，如果 ready_event 被正确设置，这种情况不应该发生，
        # 但作为备用，仍然处理一下。
        return jsonify({"error": "error1"}), 500

    # 检查文件路径是否提供（尽管这里是硬编码的）
    if not file_path:
        return jsonify({"error": "文件路径缺失。"}), 400

    # 检查文件是否存在
    if not os.path.exists(file_path):
        return jsonify({"error": "文件未找到。"}), 404

 
    # cam.new_image_event.clear() # 每次请求前清除，确保等待的是“新的”图像
    # if not cam.new_image_event.wait(timeout=2): # 等待新图像，超时10秒
    #     print("DEBUG: 未能在规定时间内获取新图像（new_image_event timeout）。")
    #     # 这里可以返回旧图像，或者返回错误
    #     # return jsonify({"error": "未能在规定时间内获取新图像。"}), 504 
    # else:
    #     print("DEBUG: New image event received.")

    file_content = None
    print(time.time())
    try:
        while cam.instance.is_saving:
            print("DEBUG: Waiting for camera to finish saving...")
            time.sleep(0.1)
        cam.instance.is_saving = True  # 设置保存标志
        cam.instance.grab_frame()  # 设置读取标志
        print(f"DEBUG: Grabbed frame from camera {cam_ip}")
        with cam.image_file_lock: # 获取锁
           
            #print(f"DEBUG: Grabbed frame from camera {cam_ip}")
            print(f"DEBUG: Acquired file lock for reading {file_path}")
            # 不再需要 is_reading 标志，锁已经保证了互斥
            with open(file_path, 'rb') as file:
                file_content = file.read()
            #file_content = cv2.imread(file_path)
            print(f"DEBUG: Successfully read file {file_path}")
    except Exception as e:
        print(f"DEBUG: 读取文件失败: {str(e)}")
        return jsonify({"error": f"读取文件失败: {str(e)}"}), 500
    finally:
        # 锁会在 with 语句块结束时自动释放
        cam.instance.is_saving = False  # 清除保存标志
        print(f"DEBUG: Released file lock for reading {file_path}")
            
   
    print(time.time())
    # 将文件内容编码为 Base64
    base64_content = base64.b64encode(file_content).decode('utf-8')

    # 返回 Base64 编码的文件内容
    return jsonify({"image_data": base64_content})

# 定义用户信息页面路由
@app.route('/getImage1')
def get_image1():
   
    file_path = File_Path

    if not file_path:
        return jsonify({"error": "File path is required"}), 400

    # 检查文件是否存在
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    # 读取文件内容
    while cam.instance.is_saving:
        pass
    try:
        cam.instance.is_reading = True
        with open(file_path, 'rb') as file:
            file_content = file.read()
        cam.instance.is_reading = False
    except Exception as e:
        return jsonify({"error": f"Failed to read file: {str(e)}"}), 500

    # 将文件内容编码为 Base64
    base64_content = base64.b64encode(file_content).decode('utf-8')

    # 返回 Base64 编码的文件内容
    return jsonify({"image_data": base64_content})

  

# 定义一个表单提交页面
@app.route('/stop', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        # 获取表单数据
        name = request.form.get('name')
        email = request.form.get('email')
        # 返回提交结果
        return f'Form submitted: Name={name}, Email={email}'
    else:
        # 返回表单页面
        return '''
            <form method="post">
                Name: <input type="text" name="name"><br>
                Email: <input type="text" name="email"><br>
                <input type="submit" value="Submit">
            </form>
        '''

# 定义一个 JSON API 接口
@app.route('/api/data', methods=['GET'])
def api_data():
    # 返回 JSON 数据
    data = {'key': 'value'}
    return jsonify(data)

# 定义一个模板渲染页面
@app.route('/template')
def template():
    # 渲染模板页面
    return render_template('template.html', title='Template Page', message='Hello from template!')

# 启动 Flask 应用
if __name__ == '__main__':
    #main_loop(cam,cam_ip)
    

    print(f"Flask app's cam object ID: {id(cam)}")
    print(cam.instance)
    threading.Thread(target=main_loop, args=(cam_ip,cam), daemon=True).start()
    time.sleep(10)
    print(cam.instance.is_saving)
    app.run(debug=True,use_reloader=False,port=5002,host='0.0.0.0')
    


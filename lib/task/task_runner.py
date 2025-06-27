import json
from datetime import datetime
import time

import cv2
import mss
import numpy as np
from PIL import Image


def load_tasks(json_path='tasks.json'): 
    try:
        with open(json_path, 'r') as f:
            tasks = json.load(f)
        return tasks
    except Exception as e:
        print(f'JSON 로드 실패: {e}')
        return []

def capture_screenshots():
    print('📸 모든 화면 캡처 중...')
    save_path = 'data/screenshot'
    screenshots = []
    with mss.mss() as sct:
        monitors = sct.monitors[1:]  # 첫 번째는 전체 화면이므로 제외
        print(f'📸 감지된 모니터 수: {len(monitors)}')
        for idx, monitor in enumerate(monitors):
            try: 
                screenshot = sct.grab(monitor)
                img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
                img_np = np.array(img)
                img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                # filename = f'{save_path}/screenshot_monitor_{idx}_{timestamp}.png'
                # cv2.imwrite(filename, img_cv)
                screenshots.append({
                    'id': idx,
                    'image': img,
                    'cv_image': img_cv,
                    'offset_x': monitor['left'],
                    'offset_y': monitor['top'],
                    'width': monitor['width'],
                    'height': monitor['height']
                })
                print(f'✅ 모니터 {idx} 캡처 완료: {monitor["width"]}x{monitor["height"]} at ({monitor["left"]}, {monitor["top"]})')
            except Exception as e:
                print(f'모니터 {idx} 캡처 실패: {e}')
    return screenshots

def waiting_capture_screenshot_search(task, current_mouse_pos, max_wait_time=20, interval=1.0):
    """
    스크린샷을 주기적으로 캡처하여 원하는 이미지를 찾을 때까지 대기하는 함수
    
    Args:
        task (dict): 수행할 작업 정보
        current_mouse_pos (dict): 현재 마우스 위치 {'x': x, 'y': y}
        max_wait_time (int): 최대 대기 시간(초), 기본값 20초
        interval (float): 스크린샷 캡처 간격(초), 기본값 1초
    
    Returns:
        tuple: (성공 여부(bool), 찾은 위치 정보(dict))
    """
    start_time = time.time()
    
    while True:
        # 최대 대기 시간 체크
        if time.time() - start_time > max_wait_time:
            print(f"⏰ 제한 시간 {max_wait_time}초 초과")
            return False, None
        
        try:
            # 스크린샷 캡처
            screenshots = capture_screenshots()
            if not screenshots:
                print('❌ 스크린 캡처 실패')
                return False, None
            
            # 이미지 검색 수행
            success, pos = search(task, screenshots, current_mouse_pos)
            
            if success:
                print(f"✅ 이미지 '{task.get('image_path')}' 찾음")
                return True, pos
            
            # 실패시 대기 후 재시도
            print(f"🔄 이미지 검색 재시도 중... (경과 시간: {int(time.time() - start_time)}초)")
            time.sleep(interval)
            
        except Exception as e:
            print(f"❌ 검색 중 오류 발생: {e}")
            return False, None

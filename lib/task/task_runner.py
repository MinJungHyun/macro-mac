import json
from datetime import datetime

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
                filename = f'{save_path}/screenshot_monitor_{idx}_{timestamp}.png'
                cv2.imwrite(filename, img_cv)
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

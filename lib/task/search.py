import json
import os
from datetime import datetime
import time
import pyperclip
import cv2
import mss
import pyautogui
from PIL import Image


def action(task, mouse_pos=None):
     
    time.sleep(0.2)
    print(f'🔍 현재의 마우스 위치: {mouse_pos["x"]}, {mouse_pos["y"]}')
    action = task.get('action', 'move')  
    
    if action == 'click':  
        # 클릭 전에 딜레이 추가
        pyautogui.click(mouse_pos['x'], mouse_pos['y'])  
        return True, mouse_pos
    
    elif action == 'move':  
        offset = task.get('offset')
        pyautogui.moveRel(offset['x'], offset['y']) 
        return True, {'x': mouse_pos['x'] + offset['x'], 'y': mouse_pos['y'] + offset['y']}
    
    elif action == 'text': 
        text = task.get('text', '')
        pyautogui.click(mouse_pos['x'], mouse_pos['y']) 
        pyautogui.typewrite(text)
        return True, mouse_pos
    
    elif action == 'paste': 
        pyautogui.click(mouse_pos['x'], mouse_pos['y']) 
        pyautogui.hotkey('command', 'v')
        return True, mouse_pos

    elif action == 'hotkey': 
        key_combination = task.get('key_combination', [])
        pyautogui.click(mouse_pos['x'], mouse_pos['y']) 
        pyautogui.hotkey(*key_combination)
        return True, mouse_pos
    
    
    elif action == 'keypress': 
        key = task.get('key')
        pyautogui.click(mouse_pos['x'], mouse_pos['y']) 
        pyautogui.press(key)
        return True, mouse_pos
    
    
    elif action == 'clipboard':
        ## 클립보드 데이터를 가져온다
        clipboard_data = pyperclip.paste()
        print(f'📋 클립보드 데이터: {clipboard_data}')
        
        return True, mouse_pos
    
    else:
        print(f'❌ 알 수 없는 액션: {action}')
        return False

     
def search(task, screenshots, mouse_pos=None):
    image_path = task.get('image_path')
    confidence = task.get('confidence', 0.98)
    capture_size = task.get('capture_size', (200, 200))

    if not os.path.exists(image_path):
        print(f'❌ 이미지 파일 없음: {image_path}')
        return False, None

    target_img = cv2.imread(image_path)
    if target_img is None:
        print(f'❌ 타겟 이미지 로드 실패: {image_path}')
        return False, None

    target_height, target_width = target_img.shape[:2]
    print(f'🔍 타겟 이미지: {image_path}, 크기: {target_width}x{target_height}, 유사도 기준: {confidence}')

    scales = [1.0]
    for screen in screenshots:
        # 모든 모니터에서 검색하도록 변경 (또는 특정 모니터 지정)
        # if screen['id'] != 1:  # 이 조건을 제거하거나 수정
        #     continue

        monitor_id = screen['id']
        offset_x = screen['offset_x']
        offset_y = screen['offset_y']
        screen_img = screen['cv_image']  # 원본 그대로 사용
        
        print(f'🔍 모니터 {monitor_id}에서 검색 중... (오프셋: {offset_x}, {offset_y})')

        try:
            for scale in scales:
                resized = cv2.resize(target_img, (0, 0), fx=scale, fy=scale)
                resized_h, resized_w = resized.shape[:2]

                result = cv2.matchTemplate(screen_img, resized, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

                if max_val >= confidence:
                    top_left = max_loc
                    center_x = top_left[0] + (resized_w // 2)
                    center_y = top_left[1] + (resized_h // 2)
                    absolute_x = center_x + offset_x
                    absolute_y = center_y + offset_y

                    # 디버그 정보 출력
                    print(f'🔍 매칭 결과: 모니터 {monitor_id}')
                    print(f'   - 모니터 오프셋: ({offset_x}, {offset_y})')
                    print(f'   - 모니터 내 상대좌표: ({center_x}, {center_y})')
                    print(f'   - 계산된 절대좌표: ({absolute_x}, {absolute_y})')

                    debug_img = screen_img.copy()
                    cv2.rectangle(debug_img, top_left, (top_left[0] + resized_w, top_left[1] + resized_h), (0, 255, 0), 2)
                    cv2.putText(debug_img, f'({absolute_x}, {absolute_y})', (top_left[0], top_left[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    cv2.imwrite(f'data/debug/debug_matched_location_{monitor_id}_{timestamp}.png', debug_img)

                    # 해당 모니터에서만 캡처하도록 수정
                    with mss.mss() as sct:
                        capture_width, capture_height = capture_size
                        
                        # 해당 모니터 정보 가져오기
                        monitor_info = sct.monitors[monitor_id + 1]  # monitors[0]은 전체화면이므로 +1
                        
                        # 모니터 내에서의 캡처 영역 계산
                        capture_left = center_x - capture_width // 2
                        capture_top = center_y - capture_height // 2
                        
                        # 모니터 경계 내로 제한
                        capture_left = max(0, min(capture_left, monitor_info['width'] - capture_width))
                        capture_top = max(0, min(capture_top, monitor_info['height'] - capture_height))
                        
                        # 전체 화면 좌표계로 변환
                        region = {
                            'left': monitor_info['left'] + capture_left,
                            'top': monitor_info['top'] + capture_top,
                            'width': capture_width,
                            'height': capture_height
                        }
                        
                        print(f'   - 캡처 영역: {region}')
                        
                        screenshot = sct.grab(region)
                        img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
                        capture_filename = f'data/found/found_image_{monitor_id}_{timestamp}.png'
                        img.save(capture_filename)
                        print(f'📸 발견된 위치 캡처 저장: {capture_filename} (모니터 {monitor_id})')

                    print(f'🖱 마우스 이동: {absolute_x}, {absolute_y} (모니터 {monitor_id})')
                    pyautogui.moveTo(absolute_x, absolute_y)
                    
                    # mouse_pos 업데이트
                    mouse_pos = {'x': absolute_x, 'y': absolute_y}
                    print(f'📍 mouse_pos 업데이트: {mouse_pos}')
                    
                    return True, {'x': absolute_x, 'y': absolute_y, 'monitor_id': monitor_id, 'capture_file': capture_filename}
        except Exception as e:
            print(f'❌ 매칭 실패 (모니터 {monitor_id}): {e}')
    print(f'❌ 이미지 못 찾음: {image_path}')
    return False, None
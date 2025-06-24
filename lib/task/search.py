import json
import os
from datetime import datetime

import cv2
import mss
import pyautogui
from PIL import Image


def action(task, mouse_pos=None):
     
    action = task.get('action', 'move')
    key = task.get('key', '')
    text = task.get('text', '')
    
    
    # action 출력을 스크린샷 for문 이전으로 이동
    print(f'🎯 실행할 액션: {action}') 
    if action == 'click': 
        print(f'🖱 클릭 위치: {mouse_pos}')
        pyautogui.click(mouse_pos['x'], mouse_pos['y']) 
        return True
    
    elif action == 'type':
        print('⌨ 텍스트 입력 실행...')
        pyautogui.click(mouse_pos['x'], mouse_pos['y']) 
        pyautogui.typewrite(text)
        return True
    
    elif action == 'paste':
        print('📋 붙여넣기 실행...')
        pyautogui.click(mouse_pos['x'], mouse_pos['y']) 
        pyautogui.hotkey('command', 'v')
        return True
    
    elif action == 'keypress':
        print('🔑 키 입력 실행...')
        pyautogui.click(mouse_pos['x'], mouse_pos['y']) 
        pyautogui.press(key)
        return True    
    
    return False

def search_move(task, screenshots, mouse_pos=None):
    image_path = task.get('image_path')
    action = task.get('action', 'move')
    key = task.get('key', 'a')
    confidence = task.get('confidence', 0.98)
    text = task.get('text', '')
    capture_size = task.get('capture_size', (200, 200))

    # 이전 마우스 위치 출력
    if mouse_pos:
        print(f'🖱 이전 마우스 위치: {mouse_pos}')
    
    if not os.path.exists(image_path):
        print(f'❌ 이미지 파일 없음: {image_path}')
        return False, None

    target_img = cv2.imread(image_path)
    if target_img is None:
        print(f'❌ 타겟 이미지 로드 실패: {image_path}')
        return False, None

    target_height, target_width = target_img.shape[:2]
    print(f'🔍 타겟 이미지: {image_path}, 크기: {target_width}x{target_height}, 유사도 기준: {confidence}')

    scales = [1.0]  # 정확도 중심으로 스케일은 고정

    for screen in screenshots:
        if screen['id'] != 1:  # 모니터 2번만 (id=1)
            continue

        monitor_id = screen['id']
        offset_x = screen['offset_x']
        offset_y = screen['offset_y']
        screen_img = screen['cv_image']  # 원본 그대로 사용

        try:
            for scale in scales:
                resized = cv2.resize(target_img, (0, 0), fx=scale, fy=scale)
                resized_h, resized_w = resized.shape[:2]

                result = cv2.matchTemplate(screen_img, resized, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

                if max_val >= confidence:
                    top_left = max_loc
                    bottom_right = (top_left[0] + resized_w, top_left[1] + resized_h)
                    center_x = top_left[0] + (resized_w // 2 )
                    center_y = top_left[1] + (resized_h // 2 )
                    abs_x = center_x 
                    abs_y = center_y

                    # 매칭 위치 디버깅 이미지 저장
                    debug_img = screen_img.copy()
                    cv2.rectangle(debug_img, top_left, bottom_right, (0, 255, 0), 2)
                    cv2.imwrite(f'debug_matched_location_{monitor_id}_{timestamp}.png', debug_img)

                    # 주변 영역 캡처 저장
                    with mss.mss() as sct:
                        capture_width, capture_height = capture_size
                        left = max(0, abs_x - capture_width)
                        top = max(0, abs_y - capture_height)
                        region = {'left': left, 'top': top, 'width': capture_width, 'height': capture_height}
                        screenshot = sct.grab(region)
                        img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
                        capture_filename = f'found_image_{monitor_id}_{timestamp}.png'
                        img.save(capture_filename)
                        print(f'📸 발견된 위치 캡처 저장: {capture_filename}')

                    # action에 따른 처리 - move만 이동, 나머지는 바로 실행 후 즉시 종료
                    result_data = {
                        'x': center_x, 'y': center_y,
                        'monitor_id': monitor_id,
                        'capture_file': capture_filename
                    }
                     
                    
                    # 기본적으로는 move 처리 
                    print(f'🖱 기본 마우스 이동... {center_x} : {center_y} ')
                    pyautogui.moveTo(center_x, center_y)
                    return True, result_data
        except Exception as e:
            print(f'❌ 매칭 실패 (모니터 {monitor_id}): {e}')
    print(f'❌ 이미지 못 찾음: {image_path}')
    return False, None

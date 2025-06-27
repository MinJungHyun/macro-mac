import json
import os
from datetime import datetime
import time
import pyperclip
import cv2
import mss
import pyautogui
from PIL import Image
from lib.task.task_runner import capture_screenshots

debug_log = False

def action(task, mouse_pos=None):
     
    time.sleep(0.02)
    if debug_log == True:
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
        pyautogui.typewrite(text)
        return True, mouse_pos
    
    elif action == 'paste': 
        pyautogui.hotkey('command', 'v')
        return True, mouse_pos

    elif action == 'hotkey': 
        key_combination = task.get('key_combination', [])
        pyautogui.hotkey(*key_combination)
        return True, mouse_pos
    
    
    elif action == 'keypress': 
        key = task.get('key')
        pyautogui.press(key)
        return True, mouse_pos
    
    
    elif action == 'clipboard':
        ## 클립보드 데이터를 가져온다
        clipboard_data = pyperclip.paste()
        if debug_log == True:
            print(f'📋 클립보드 데이터: {clipboard_data}')
        
        return True, {'x': mouse_pos['x'], 'y': mouse_pos['y'], 'clipboard_data': clipboard_data}
    elif action == 'sleep':
        duration = task.get('duration', 1)
        if debug_log == True:
            print(f'⏳ {duration}초 대기 중...')
        time.sleep(duration)
        return True, mouse_pos
    else:
        if debug_log == True:
            print(f'❌ 알 수 없는 액션: {action}')
        return False

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
        
     
def search(task, screenshots, mouse_pos=None):
    image_paths = task.get('image_paths') or [task.get('image_path')]
    confidence = task.get('confidence', 0.98)
    capture_size = task.get('capture_size', (200, 200))
    find_mode = task.get('find_mode', 'first')  # 'first', 'top', 'bottom', 'left', 'right'
    if debug_log == True:
        print(f'🔍 이미지 검색 시작: {image_paths}, 유사도 기준: {confidence}, 캡처 크기: {capture_size}, 찾기 모드: {find_mode}')

    found_matches = []

    for image_path in image_paths:
        if not os.path.exists(image_path):
            if debug_log == True:
                print(f'❌ 이미지 파일 없음: {image_path}')
            continue

        target_img = cv2.imread(image_path)
        if target_img is None:
            if debug_log == True:
                print(f'❌ 타겟 이미지 로드 실패: {image_path}')
            continue

        target_height, target_width = target_img.shape[:2]
        if debug_log == True:
            print(f'🔍 타겟 이미지: {image_path}, 크기: {target_width}x{target_height}, 유사도 기준: {confidence}')

        scales = [1.0]
        for screen in screenshots:
            monitor_id = screen['id']
            offset_x = screen['offset_x']
            offset_y = screen['offset_y']
            screen_img = screen['cv_image']

            if debug_log == True:
                print(f'🔍 모니터 {monitor_id}에서 검색 중... (오프셋: {offset_x}, {offset_y})')

            try:
                for scale in scales:
                    resized = cv2.resize(target_img, (0, 0), fx=scale, fy=scale)
                    resized_h, resized_w = resized.shape[:2]

                    result = cv2.matchTemplate(screen_img, resized, cv2.TM_CCOEFF_NORMED)
                    loc = zip(*((result >= confidence).nonzero()[::-1]))

                    for pt in loc:
                        top_left = pt
                        center_x = top_left[0] + (resized_w // 2)
                        center_y = top_left[1] + (resized_h // 2)
                        absolute_x = center_x + offset_x
                        absolute_y = center_y + offset_y

                        found_matches.append({
                            'monitor_id': monitor_id,
                            'offset_x': offset_x,
                            'offset_y': offset_y,
                            'center_x': center_x,
                            'center_y': center_y,
                            'absolute_x': absolute_x,
                            'absolute_y': absolute_y,
                            'image_path': image_path,
                            'resized_w': resized_w,
                            'resized_h': resized_h,
                            'top_left': top_left,
                            'screen_img': screen_img
                        })
            except Exception as e:
                if debug_log == True:
                    print(f'❌ 매칭 실패 (모니터 {monitor_id}): {e}')

    if not found_matches:
        if debug_log == True:
            print(f'❌ 이미지 못 찾음: {image_paths}')
        return False, None

    # 찾은 위치 중에서 조건에 따라 선택
    if find_mode == 'top':
        found_matches.sort(key=lambda m: m['absolute_y'])
    elif find_mode == 'bottom':
        found_matches.sort(key=lambda m: m['absolute_y'], reverse=True)
    elif find_mode == 'left':
        found_matches.sort(key=lambda m: m['absolute_x'])
    elif find_mode == 'right':
        found_matches.sort(key=lambda m: m['absolute_x'], reverse=True)
    # 'first'는 정렬하지 않음
    match = found_matches[0]

    monitor_id = match['monitor_id']
    offset_x = match['offset_x']
    offset_y = match['offset_y']
    center_x = match['center_x']
    center_y = match['center_y']
    absolute_x = match['absolute_x']
    absolute_y = match['absolute_y']
    image_path = match['image_path']
    resized_w = match['resized_w']
    resized_h = match['resized_h']
    top_left = match['top_left']
    screen_img = match['screen_img']

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    debug_img = screen_img.copy()
    cv2.rectangle(debug_img, top_left, (top_left[0] + resized_w, top_left[1] + resized_h), (0, 255, 0), 2)
    cv2.putText(debug_img, f'({absolute_x}, {absolute_y})', (top_left[0], top_left[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    # cv2.imwrite(f'data/debug/debug_matched_location_{monitor_id}_{timestamp}.png', debug_img)

    with mss.mss() as sct:
        capture_width, capture_height = capture_size
        monitor_info = sct.monitors[monitor_id + 1]
        capture_left = center_x - capture_width // 2
        capture_top = center_y - capture_height // 2
        capture_left = max(0, min(capture_left, monitor_info['width'] - capture_width))
        capture_top = max(0, min(capture_top, monitor_info['height'] - capture_height))
        region = {
            'left': monitor_info['left'] + capture_left,
            'top': monitor_info['top'] + capture_top,
            'width': capture_width,
            'height': capture_height
        }
        if debug_log == True:
            print(f'   - 캡처 영역: {region}')
        screenshot = sct.grab(region)
        img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
        capture_filename = f'data/found/found_image_{monitor_id}_{timestamp}.png'
        # img.save(capture_filename)
        if debug_log == True:
            print(f'📸 발견된 위치 캡처 저장: {capture_filename} (모니터 {monitor_id})')

    if debug_log == True:
        print(f'🖱 마우스 이동: {absolute_x}, {absolute_y} (모니터 {monitor_id})')
    pyautogui.moveTo(absolute_x, absolute_y)
    mouse_pos = {'x': absolute_x, 'y': absolute_y}
    if debug_log == True:
        print(f'📍 mouse_pos 업데이트: {mouse_pos}')

    return True, {'x': absolute_x, 'y': absolute_y, 'monitor_id': monitor_id, 'capture_file': capture_filename}
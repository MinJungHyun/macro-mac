import json
import os
from datetime import datetime
import time

import cv2
import mss
import numpy as np
import pyautogui
from PIL import Image

from lib.task.search import action, search
# lib 모듈에서 필요한 함수들 import
from lib.task.task_runner import capture_screenshots, load_tasks

# PyAutoGUI 설정
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

# macOS Retina 디스플레이 스케일링 팩터
RETINA_SCALE = 2 if 'Retina' in os.popen('system_profiler SPDisplaysDataType').read() else 1


def test_mouse_control():
    debug = False
    """마우스 제어가 제대로 작동하는지 테스트"""
    if( debug ):
        print('🧪 마우스 제어 테스트 시작...')
    try:
        # 현재 마우스 위치 확인
        current_pos = pyautogui.position()
        if( debug ):
            print(f'현재 마우스 위치: {current_pos}')
        
        # 상대적으로 안전한 위치로 이동 테스트 (현재 위치에서 조금만 이동)
        test_x = current_pos.x + 10
        test_y = current_pos.y + 10
        
        if( debug ):
            print(f'테스트 위치로 이동: ({test_x}, {test_y})')
        pyautogui.moveTo(test_x, test_y, duration=1)
        time.sleep(0.5)
        
        # 이동 후 위치 확인
        new_pos = pyautogui.position()

        if( debug ):
            print(f'이동 후 마우스 위치: {new_pos}')
        
        if new_pos.x == test_x and new_pos.y == test_y:
            print('✅ 마우스 제어 정상 작동')
            return True
        else:
            print('❌ 마우스 제어 실패 - 접근성(손쉬운 사용) 권한을 확인하세요') 
            return False
            
    except Exception as e:
        print(f'❌ 마우스 제어 오류: {e}')
        return False


def main():
    # 먼저 마우스 제어 테스트
    # if not test_mouse_control():
    #     print('⚠️ 마우스 제어가 작동하지 않습니다.')
    #     print('터미널 또는 Python을 허용해주세요.')
    #     return
    
    try:
        screenshots = capture_screenshots()
        if not screenshots:
            print('❌ 스크린 캡처 실패')
            return
        tasks = load_tasks()
        if not tasks:
            print('❌ 작업 목록이 비어 있음')
            return
        
        # 현재 마우스 위치 저장
        mouse_pos = pyautogui.position()
        print(f'==============================')
        print(f'초기 마우스 위치: {mouse_pos}')
        print(f'==============================')
        
        index = 1
        for task in tasks:
            print(f'🔄 작업 {index} 시작: {task}')
            index += 1
            if task.get('action') == 'search': 
                success, pos = search(task, screenshots, mouse_pos)
                if success:
                    mouse_pos = { 'x': pos['x'], 'y': pos['y'] }
                    print(f'작업 완료: {task["image_path"]} on monitor {pos["monitor_id"]}, 캡처 파일: {pos.get("capture_file", "없음")}')
                     
                else:
                    print(f'작업 실패: {task["image_path"]}')
                    continue
            else:
                success, pos = action(task, mouse_pos)
                if success:
                    # 액션 후 실제 마우스 위치 확인
                    if pos['x'] and pos['y']:
                        mouse_pos = { 'x': pos['x'], 'y': pos['y'] }

                    actual_pos = pyautogui.position()
                    print(f'🔍 액션후 마우스 위치: {actual_pos.x}, {actual_pos.y}')
            print(f'==============================')
              
    except Exception as e:
        print(f'실행 중 오류: {e}')

if __name__ == '__main__':
    main()

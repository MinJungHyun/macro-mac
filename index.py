import json
import os
from datetime import datetime

import cv2
import mss
import numpy as np
import pyautogui
from PIL import Image

from lib.task.search import action, search_move
# lib 모듈에서 필요한 함수들 import
from lib.task.task_runner import capture_screenshots, load_tasks

# PyAutoGUI 설정
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

# macOS Retina 디스플레이 스케일링 팩터
RETINA_SCALE = 2 if 'Retina' in os.popen('system_profiler SPDisplaysDataType').read() else 1




def main():
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
        print(' 작업 시작')
        
        index = 1
        for task in tasks:
            print(f'🔄 작업 {index} 시작: {task}')
            index += 1
            if task.get('action') == 'search_move': 
                success, pos = search_move(task, screenshots, mouse_pos)
                if success:
                    mouse_pos = { 'x': pos['x'], 'y': pos['y'] }
                    print(f'작업 완료: {task["image_path"]} on monitor {pos["monitor_id"]}, 캡처 파일: {pos.get("capture_file", "없음")}')
                else:
                    print(f'작업 실패: {task["image_path"]}')
                    continue
            else:
                action(task, mouse_pos)
            print(f'==============================')
              
    except Exception as e:
        print(f'실행 중 오류: {e}')

if __name__ == '__main__':
    main()

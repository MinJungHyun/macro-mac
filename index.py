import json
import os
from datetime import datetime
import time

import cv2
import mss
import numpy as np
import pyautogui
from PIL import Image

from lib.task.search import action, search, waiting_capture_screenshot_search
# lib 모듈에서 필요한 함수들 import
from lib.task.task_runner import capture_screenshots, load_tasks
from lib.task.outmall_review import load_out_mall_reviews, update_out_mall_review
import pyperclip

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

debug_log = False

def main():
    # 먼저 마우스 제어 테스트
    # if not test_mouse_control():
    #     print('⚠️ 마우스 제어가 작동하지 않습니다.')
    #     print('터미널 또는 Python을 허용해주세요.')
    #     return
    
    reviews = load_out_mall_reviews('알코소')
    # reviews = load_out_mall_reviews('메뉴')
    # print(reviews)
    
    for review in reviews:
        print(f'==============================')
        print(f'리뷰 AI 작성 매크로 진행중: {reviews.index(review)+1} / {len(reviews)}')
        
        review_text = (
            f"작성일: {review['created_at']}\n"
            f"상품이름: {review['product_name']}\n"
            f"평점: {review['rating']}\n"
            f"작성자: {review['user_name']}\n"
            f"내용: {review['contents']}\n"
        )
        pyperclip.copy(review_text)
        if debug_log == True:
            print("✅ 리뷰가 클립보드에 복사되었습니다.")
        
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
            # print(f'==============================')
            # print(f'초기 마우스 위치: {mouse_pos}')
            # print(f'==============================')
            
            index = 1
            review_answer = None
            for task in tasks:
                if debug_log == True:
                    print(f'🔄 작업 {index} 시작: {task}')
                index += 1
                if( task.get('action') == 'break' ):
                    print('🔴 Break task로 인한 작업 중단')
                    break
                elif( task.get('action') == 'screenshots' ):
                    screenshots = capture_screenshots()
                    if not screenshots:
                        print('❌ 스크린 캡처 실패')
                        return
                elif task.get('action') == 'waiting_capture_screenshot_search': 
                    # 스크린샷을 주기적으로 캡처하여 원하는 이미지를 찾을 때까지 대기
                    success, pos = waiting_capture_screenshot_search(task, mouse_pos)
                    if success:
                        mouse_pos = { 'x': pos['x'], 'y': pos['y'] }
                        if debug_log == True:
                            print(f'작업 완료: {task["image_path"]} on monitor {pos["monitor_id"]}, 캡처 파일: {pos.get("capture_file", "없음")}')
                    else:
                        print(f'작업 실패: {task["image_path"]}')
                        continue
                elif task.get('action') == 'search': 
                    success, pos = search(task, screenshots, mouse_pos)
                    if success:
                        mouse_pos = { 'x': pos['x'], 'y': pos['y'] }
                        if debug_log == True:
                            print(f'작업 완료: {task["image_path"]} on monitor {pos["monitor_id"]}, 캡처 파일: {pos.get("capture_file", "없음")}')
                        
                    else:
                        print(f'작업 실패: {task["image_path"]}')
                        continue
                else:
                    success, pos = action(task, mouse_pos)
                    if task['action'] == 'clipboard':
                        review_answer = pos.get('clipboard_data', None)
                    if success:
                        # 액션 후 실제 마우스 위치 확인
                        if pos['x'] and pos['y']:
                            mouse_pos = { 'x': pos['x'], 'y': pos['y'] }

                        actual_pos = pyautogui.position()
                        if debug_log == True:
                            print(f'🔍 액션후 마우스 위치: {actual_pos.x}, {actual_pos.y}')
                if debug_log == True:
                    print(f'==============================')
        
            if debug_log == True:
                print('clipboard에 복사된 리뷰 내용:')
            if debug_log == True:
                print(review_answer)
            if review_answer:
                update_out_mall_review(review['id'], review_answer)

        except Exception as e:
            print(f'실행 중 오류: {e}')

if __name__ == '__main__':
    main()

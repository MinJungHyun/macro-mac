import pymysql
from pymysql.cursors import DictCursor
import atexit

class DatabaseConnection:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance.initialize()
            # 프로그램 종료 시 자동으로 연결 종료
            atexit.register(cls._instance.close_connection)
        return cls._instance
    
    def initialize(self):
        self.conn = pymysql.connect(
            host='1',
            user='1',
            password='11',
            database='1',
            charset='1',
            cursorclass=DictCursor
        )
        
    def get_connection(self):
        try:
            self.conn.ping(reconnect=True)
        except:
            self.initialize()
        return self.conn
    
    @classmethod
    def get_instance(cls):
        return cls._instance
    
    def close_connection(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            DatabaseConnection._instance = None
    
    def execute_query(self, sql, params=None):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                return cursor.fetchall()
        except Exception as e:
            print(f"쿼리 실행 중 오류 발생: {e}")
            return None

def load_out_mall_reviews(keyword: str):
    db = DatabaseConnection()
    try:
        sql = """
SELECT
	created_at,
    product_name,
    rating,
    user_name,
    contents
FROM ecommerce_data.out_mall_review
WHERE confirm_fl = 'N' AND product_name LIKE '%{keyword}%';
        """
        print(f"쿼리 실행: {sql.format(keyword=keyword)}")
        results = db.execute_query(sql.format(keyword=keyword))
        
        if results:
            # for row in results:
            #     print(row)
            print(f"쿼리 실행 성공: {len(results)}개의 결과를 가져왔습니다.")
        return results
    except Exception as e:
        print(f"처리 중 오류 발생: {e}")
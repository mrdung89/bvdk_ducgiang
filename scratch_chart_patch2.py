import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\models\db_manager.py', 'r', encoding='utf-8') as f:
    c = f.read()

new_chart = '''    def get_chart_data_7days(self, start_str, end_str):
        # start_str might be "2026-09-09 00:00:00", we just need "2026-09-09"
        d1 = start_str.split()[0]
        d2 = end_str.split()[0]
        sql = """
            SELECT r.date as ngay, m.name as ten_may, COUNT(*) as so_me
            FROM runs r JOIN machines m ON r.machine_id = m.id 
            WHERE r.date BETWEEN %s AND %s
            GROUP BY r.date, m.name ORDER BY r.date
        """
        return self.fetch_all(sql, (d1, d2)) or []
        
    def get_realtime_machines'''

c = c.replace('    def get_realtime_machines', new_chart)

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\models\db_manager.py', 'w', encoding='utf-8') as f:
    f.write(c)

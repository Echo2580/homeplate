"""SQLite regression tests; every test runs in an isolated project copy."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SQLiteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / "project"
        self.project.mkdir()
        shutil.copytree(ROOT / "app", self.project / "app",
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT / "templates", self.project / "templates")
        (self.project / "static").mkdir()
        self.env = dict(os.environ, PYTHONPATH=str(self.project),
                        PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8",
                        DATABASE_URL="", ACCESS_PASSWORD="", AI_API_KEY="",
                        AI_API_BASE="")

    def run_python(self, source, *, cwd=None, database_url=""):
        result = subprocess.run(
            [sys.executable, "-c", textwrap.dedent(source)],
            cwd=cwd or self.project,
            env=dict(self.env, DATABASE_URL=database_url),
            capture_output=True, text=True, encoding="utf-8", timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_first_start_creates_database_and_tables_without_env(self):
        self.run_python("""
            from fastapi.testclient import TestClient
            from app.main import app
            from app.database import engine
            from sqlalchemy import inspect
            from pathlib import Path
            with TestClient(app) as client:
                assert client.get('/healthz').json()['database'] == 'ok'
                assert client.get('/api/devices').json() == []
                assert client.get('/').status_code == 200
                assert set(inspect(engine).get_table_names()) == {'devices', 'maintenance_tasks'}
                assert Path('data/homeplate.db').is_file()
        """)

    def test_relative_database_path_is_anchored_to_project(self):
        elsewhere = Path(self.temp.name) / "elsewhere"
        elsewhere.mkdir()
        self.run_python("""
            from app.database import engine
            from app.init_db import initialize_database
            from pathlib import Path
            initialize_database()
            root = Path(__import__('app').__file__).resolve().parent.parent
            assert Path(engine.url.database) == root / 'nested' / 'storage.db'
            assert not (Path.cwd() / 'nested').exists()
        """, cwd=elsewhere, database_url="sqlite:///nested/storage.db")

    def test_mysql_configuration_fails_with_actionable_message(self):
        self.run_python("""
            try:
                import app.database
            except ValueError as exc:
                assert 'SQLite' in str(exc)
            else:
                raise AssertionError('A stale MySQL URL must not silently remain active')
        """, database_url="mysql+pymysql://unused:unused@127.0.0.1/unused")

    def test_foreign_keys_rollback_and_independent_connections(self):
        self.run_python("""
            from app.database import engine, SessionLocal
            from app.init_db import initialize_database
            from sqlalchemy import text
            from sqlalchemy.exc import IntegrityError
            initialize_database()
            with engine.connect() as first, engine.connect() as second:
                for conn in (first, second):
                    assert conn.scalar(text('PRAGMA foreign_keys')) == 1
                    assert conn.scalar(text('PRAGMA busy_timeout')) >= 5000
                    assert conn.scalar(text('PRAGMA journal_mode')) == 'delete'
            with SessionLocal() as session:
                try:
                    session.execute(text("INSERT INTO maintenance_tasks (device_id,title,interval_months,next_date) VALUES (999,'orphan',1,'2026-12-01')"))
                    session.commit()
                except IntegrityError:
                    session.rollback()
                else:
                    raise AssertionError('Orphan task accepted')
                session.execute(text("INSERT INTO devices (name) VALUES ('rolled back')"))
                session.rollback()
                assert session.scalar(text('SELECT COUNT(*) FROM devices')) == 0
        """)

    def test_device_task_photo_and_page_roundtrip(self):
        self.run_python("""
            import base64
            from datetime import date
            from pathlib import Path
            from fastapi.testclient import TestClient
            from app.main import app
            from app.database import SessionLocal
            from app.models import MaintenanceTask, add_months
            png = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==')
            with TestClient(app) as client:
                photo = client.post('/api/photo', files={'image': ('nameplate.png', png, 'image/png')})
                assert photo.status_code == 200
                result = client.post('/api/devices', json={
                    'name':'测试空调','brand':'测试品牌','category':'空调',
                    'purchase_date':'2024-02-29','warranty_months':12,
                    'photo_token':photo.json()['token'],
                })
                assert result.status_code == 200, result.text
                did = result.json()['id']
                assert result.json()['photo_saved'] is True
                assert Path(f'static/uploads/device_{did}.png').read_bytes() == png
                for path in ['/', '/add', '/add/confirm', f'/devices/{did}']:
                    assert client.get(path).status_code == 200, path
                assert '2025-02-28' in client.get(f'/devices/{did}').text
                assert client.patch(f'/api/devices/{did}', json={'name':'修改后的空调'}).status_code == 200
                assert client.get(f'/api/devices/{did}').json()['name'] == '修改后的空调'
                assert client.post('/api/devices', json={'name':'a' * 101}).status_code == 422
                with SessionLocal() as session:
                    task = session.query(MaintenanceTask).filter_by(device_id=did).one()
                    tid = task.id
                assert client.patch(f'/api/tasks/{tid}', json={'interval_months':3,'next_date':'2026-12-01'}).status_code == 200
                completed = client.post(f'/api/tasks/{tid}/complete').json()
                assert completed['last_done_at'] == date.today().isoformat()
                assert completed['next_date'] == add_months(date.today(),3).isoformat()
                extra = client.post('/api/tasks', json={'device_id':did,'title':'检查','interval_months':6})
                assert extra.status_code == 200
                assert client.delete('/api/tasks/' + str(extra.json()['task_id'])).status_code == 200
                assert client.delete(f'/api/devices/{did}').status_code == 200
                assert not Path(f'static/uploads/device_{did}.png').exists()
                with SessionLocal() as session:
                    assert session.query(MaintenanceTask).count() == 0
                assert client.get('/api/devices').json() == []
        """)

    def test_restart_keeps_records_ids_dates_and_backup(self):
        self.run_python("""
            from datetime import date
            from fastapi.testclient import TestClient
            from app.main import app
            from app.database import SessionLocal
            from app.models import Device, MaintenanceTask
            with TestClient(app):
                with SessionLocal() as session:
                    session.add(Device(id=41,name='保留设备',purchase_date=date(2024,2,29),warranty_months=12))
                    session.flush()
                    session.add(MaintenanceTask(id=73,device_id=41,title='保留任务',interval_months=6,next_date=date(2027,1,31)))
                    session.commit()
        """)
        self.run_python("""
            import sqlite3
            from contextlib import closing
            from datetime import date
            from fastapi.testclient import TestClient
            from app.main import app
            from app.database import SessionLocal
            from app.models import Device, MaintenanceTask
            with TestClient(app) as client:
                with SessionLocal() as session:
                    assert session.get(Device,41).purchase_date == date(2024,2,29)
                    assert session.get(MaintenanceTask,73).next_date == date(2027,1,31)
                created = client.post('/api/devices',json={'name':'新设备'})
                assert created.status_code == 200
                assert created.json()['id'] > 41
            with closing(sqlite3.connect('data/homeplate.db')) as source, closing(sqlite3.connect('data/restored.db')) as backup:
                source.backup(backup)
                assert backup.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
                assert backup.execute('SELECT COUNT(*) FROM devices').fetchone()[0] == 2
                assert backup.execute('SELECT device_id FROM maintenance_tasks WHERE id=73').fetchone()[0] == 41
        """)

    def test_short_concurrent_writes_complete_without_data_loss(self):
        self.run_python("""
            import threading,time
            from concurrent.futures import ThreadPoolExecutor
            from app.database import engine
            from app.init_db import initialize_database
            from sqlalchemy import text
            initialize_database()
            held = threading.Event()
            def first():
                with engine.begin() as conn:
                    conn.execute(text("INSERT INTO devices (name) VALUES ('first')"))
                    held.set()
                    time.sleep(0.2)
            def second():
                assert held.wait(5)
                with engine.begin() as conn:
                    conn.execute(text("INSERT INTO devices (name) VALUES ('second')"))
            with ThreadPoolExecutor(max_workers=2) as pool:
                a=pool.submit(first)
                b=pool.submit(second)
                a.result(timeout=10)
                b.result(timeout=10)
            with engine.connect() as conn:
                assert conn.scalar(text('SELECT COUNT(*) FROM devices')) == 2
        """)

    def test_concurrent_read_then_update_requests_both_succeed(self):
        self.run_python("""
            import threading
            from concurrent.futures import ThreadPoolExecutor
            from app.database import SessionLocal
            from app.init_db import initialize_database
            from app.models import Device
            initialize_database()
            with SessionLocal() as session:
                session.add_all([Device(id=1,name='first'),Device(id=2,name='second')])
                session.commit()
            ready=threading.Barrier(2)
            def update(did):
                with SessionLocal() as session:
                    device=session.get(Device,did)
                    ready.wait(timeout=5)
                    device.name='updated-'+str(did)
                    session.commit()
            with ThreadPoolExecutor(max_workers=2) as pool:
                results=[pool.submit(update,did) for did in (1,2)]
                for result in results:result.result(timeout=10)
            with SessionLocal() as session:
                assert [session.get(Device,did).name for did in (1,2)]==['updated-1','updated-2']
        """)


if __name__ == '__main__':
    unittest.main()

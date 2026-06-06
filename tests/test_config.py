import unittest

from config import build_database_settings


class DatabaseSettingsTests(unittest.TestCase):
    def test_falls_back_to_sqlite_when_postgres_is_unavailable(self):
        settings = build_database_settings(
            env={
                'DB_HOST': 'localhost',
                'DB_PORT': '5433',
                'DB_NAME': 'easivisi',
                'DB_USER': 'postgres',
                'DB_PASSWORD': 'secret',
            },
            probe=lambda host, port, timeout: False,
        )

        self.assertTrue(settings['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///'))
        self.assertEqual(settings['SQLALCHEMY_ENGINE_OPTIONS'], {})

    def test_uses_postgres_when_probe_succeeds(self):
        settings = build_database_settings(
            env={
                'DB_HOST': 'db.example.local',
                'DB_PORT': '5432',
                'DB_NAME': 'easivisi',
                'DB_USER': 'postgres',
                'DB_PASSWORD': 'secret',
            },
            probe=lambda host, port, timeout: True,
        )

        self.assertEqual(
            settings['SQLALCHEMY_DATABASE_URI'],
            'postgresql://postgres:secret@db.example.local:5432/easivisi',
        )
        self.assertIn('pool_size', settings['SQLALCHEMY_ENGINE_OPTIONS'])


if __name__ == '__main__':
    unittest.main()
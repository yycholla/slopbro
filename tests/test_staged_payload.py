import contextlib
import io
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import slopbro


class StagedPayloadTests(unittest.TestCase):
    def test_cli_forwards_valid_staging_directory(self):
        with patch.object(slopbro, 'run') as runner:
            slopbro.main(['--staged-dir', '/tmp/slopbro-stage-123456', 'tv.local'])
        self.assertEqual(runner.call_args.kwargs['staged_dir'], '/tmp/slopbro-stage-123456')

    def test_cli_rejects_unsafe_paths_and_incompatible_mode(self):
        for path in ['', '/tmp/slopbro-stage-1;id', '/tmp/slopbro-stage-1/../other', '/media/internal/downloads']:
            with self.subTest(path=path), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                slopbro.main(['--staged-dir', path, 'tv.local'])
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            slopbro.main(['--staged-dir', '/tmp/slopbro-stage-123', '--test-server', 'payload'])

    def test_url_carries_staged_path_and_existing_bypass(self):
        url = slopbro.build_self_hosted_url('tv.local', 8080,
            local_ip_override='127.0.0.1', staged_dir='/tmp/slopbro-stage-123')
        query = parse_qs(urlsplit(url).query)
        self.assertEqual(query['staged-dir'], ['/tmp/slopbro-stage-123'])
        self.assertEqual(query['fake-service-path'], [slopbro.DEFAULT_FAKE_SERVICE_PATH])
        default = slopbro.build_self_hosted_url('tv.local', 8080, local_ip_override='127.0.0.1')
        self.assertNotIn('staged-dir', parse_qs(urlsplit(default).query))

    def test_staged_runner_keeps_serving_until_interrupt_and_cleans_up(self):
        with patch.object(slopbro, 'resolve_asset_root', return_value=('root', 'dir', False, True)), \
             patch.object(slopbro, 'RequestedFilesTracker') as tracker, \
             patch.object(slopbro, 'start_http_server') as server, \
             patch.object(slopbro, 'build_self_hosted_url', return_value='http://fixture') as url, \
             patch.object(slopbro.WebSocket, 'connect'), \
             patch.object(slopbro, 'SSAPClient') as client, \
             patch.object(slopbro, 'load_client_key', return_value='key'), \
             patch.object(slopbro, 'verify_app_present', return_value=('overlay', 'interactiveUrl')), \
             patch.object(slopbro, 'launch_app', return_value={'returnValue': True}), \
             patch.object(slopbro.threading, 'Event') as keepalive, \
             contextlib.redirect_stdout(io.StringIO()):
            client.return_value.register.return_value = 'key'
            keepalive.return_value.wait.side_effect = KeyboardInterrupt
            slopbro.run('tv.local', staged_dir='/tmp/slopbro-stage-123')
        self.assertEqual(url.call_args.kwargs['staged_dir'], '/tmp/slopbro-stage-123')
        tracker.return_value.wait_for_all.assert_not_called()
        keepalive.return_value.wait.assert_called_once_with()
        client.return_value.close.assert_called_once_with()
        server.return_value.shutdown.assert_called_once_with()
        server.return_value.server_close.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()

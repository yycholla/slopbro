import unittest
from unittest.mock import Mock, call, patch

import slopbro


class FreshLaunchTests(unittest.TestCase):
    def test_cli_forwards_fresh_launch_and_runner_accepts_it(self):
        import inspect
        self.assertIn('fresh_launch', inspect.signature(slopbro.run).parameters)
        with patch.object(slopbro, 'run') as runner:
            slopbro.main(['--fresh-launch', 'tv.local'])
        self.assertTrue(runner.call_args.kwargs['fresh_launch'])

    def test_cli_forwards_loopback_bind_and_rejects_invalid_addresses(self):
        import inspect
        self.assertIn('bind_ip', inspect.signature(slopbro.run).parameters)
        with patch.object(slopbro, 'run') as runner:
            slopbro.main(['--bind-ip', '127.0.0.1', 'tv.local'])
        self.assertEqual(runner.call_args.kwargs['bind_ip'], '127.0.0.1')
        with patch.object(slopbro.sys, 'stderr', new=__import__('io').StringIO()):
            with self.assertRaises(SystemExit):
                slopbro.main(['--bind-ip', 'not-an-address', 'tv.local'])

    def test_real_runner_applies_bind_to_http_server_before_connecting(self):
        with patch.object(slopbro, 'required_files', return_value=[]), \
             patch.object(slopbro, 'resolve_asset_root', return_value=('root','dir',False,True)), \
             patch.object(slopbro, 'start_http_server') as server, \
             patch.object(slopbro, 'build_self_hosted_url', return_value='http://127.0.0.1/page'), \
             patch.object(slopbro.WebSocket, 'connect', side_effect=OSError('offline fixture')):
            with self.assertRaises(SystemExit):
                slopbro.run('tv.local', bind_ip='127.0.0.1')
        self.assertEqual(server.call_args.kwargs.get('bind_host'), '127.0.0.1')

    def test_close_uses_returned_session_before_launching_payload(self):
        client = Mock()
        client.request.side_effect = [
            {'type':'response','payload':{'returnValue':True,'sessionId':'session-1'}},
            {'type':'response','payload':{'returnValue':True}},
            {'type':'response','payload':{'returnValue':True,'sessionId':'session-2'}},
        ]
        with patch.object(slopbro.time, 'sleep'):
            result = slopbro.launch_app_fresh(client, 'overlay', {'interactiveUrl':'http://host/page'})
        self.assertEqual(result['sessionId'], 'session-2')
        self.assertEqual(client.request.call_args_list, [
            call('ssap://system.launcher/launch', {'id':'overlay','params':{}}),
            call('ssap://system.launcher/close', {'id':'overlay','sessionId':'session-1'}),
            call('ssap://system.launcher/launch', {'id':'overlay','params':{'interactiveUrl':'http://host/page'}}),
        ])

    def test_denied_close_does_not_claim_a_fresh_launch(self):
        client = Mock()
        client.request.side_effect = [
            {'type':'response','payload':{'returnValue':True,'sessionId':'session-1'}},
            {'type':'error','error':'403 denied'},
        ]
        with self.assertRaises(slopbro.SSAPError):
            slopbro.launch_app_fresh(client, 'overlay', {'interactiveUrl':'http://host/page'})
        self.assertEqual(client.request.call_count, 2)

    def test_missing_session_does_not_close_an_unidentified_session(self):
        client = Mock()
        client.request.return_value = {'type':'response','payload':{'returnValue':True}}
        with self.assertRaises(slopbro.SSAPError):
            slopbro.launch_app_fresh(client, 'overlay', {})
        self.assertEqual(client.request.call_count, 1)


if __name__ == '__main__':
    unittest.main()

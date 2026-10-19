import pathlib
import socket
import tempfile
import unittest
import urllib.request

import slopbro


class BrowserPreconnectTests(unittest.TestCase):
    def test_idle_preconnect_does_not_block_payload_request(self):
        with tempfile.TemporaryDirectory() as folder:
            pathlib.Path(folder, 'index.html').write_bytes(b'payload fixture')
            tracker = slopbro.RequestedFilesTracker(['index.html'])
            server = slopbro.start_http_server(folder, tracker, ['index.html'],
                False, True, bind_host='127.0.0.1', preferred_port=0)
            idle = socket.create_connection(server.server_address, timeout=1)
            try:
                url = 'http://127.0.0.1:%s/index.html' % server.server_port
                with urllib.request.urlopen(url, timeout=1) as response:
                    self.assertEqual(response.read(), b'payload fixture')
                self.assertTrue(tracker.wait_for_all(0))
            finally:
                idle.close()
                server.shutdown()
                server.server_close()


if __name__ == '__main__':
    unittest.main()

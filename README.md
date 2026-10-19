# SlopBro

Some of the Python was written by an LLM. (You think I wanted to write a
Python 2.7/3.x-compatible WebSocket client?) The rest is good, old-fashioned
**human** slop. It's the spirit of the times, you know?

## Overview

SlopBro is a proof-of-concept exploit for the jsserver vulnerability in
LG TVs.

~~I tried to make it compatible with Python 2.7 and 3.x with no dependencies
outside the standard library so that it could be run on all versions of
webOS TV. Unfortunately, the Python 2.7 environment on webOS 6 (and
presumably older) is missing the HTTP server stuff, so it was kind of a
waste of time. Oh well.~~

Python 2 support has now been dropped. SSAP never worked right via loopback
anyway. The script still uses only the standard library.

I've only lightly tested it (remember: slop!), but people have gotten it
to work on a bunch of webOS versions.

SlopBro has been used successfully against webOS 4–11 and now includes
a workaround for LG's attempt to patch the jsserver vulnerability.
(While it might work all the way back to webOS 3.4.2, I recommend using
[dejavuln-autoroot](https://github.com/throwaway96/dejavuln-autoroot) for
webOS 3.5 and 4.x.)

### How it works

`slopbro.py` is the main script. It performs the following steps:

1. Starts an HTTP server to serve the exploit page and payloads.
2. Opens an SSAP connection to the TV.
3. Launches a WAM app pointing at the exploit page `index.html`.

Pages running in the context of certain WAM apps can make privileged
Luna requests. When loaded on the TV, `index.html` does the following:

1. Displays status and debug info on the TV screen.
2. Downloads files for a fake `com.webos.service.jsserver` package from the
   HTTP server.
3. Runs the package using the jsserver vulnerability.

The entry point of the fake `com.webos.service.jsserver` package is `main.js`,
which is executed with root privileges. It is responsible for launching
`autoroot.sh`, which installs Homebrew Channel and enables persistence.

## Running

Run the script with Python 3, passing the IP address of your TV:

```bash
python slopbro.py [--debug] [--curl-insecure] [--fake-service-path <PATH>|--no-fake-service-path] [--local-ip <LOCAL IP>] [--webos-version <VERSION>] [--asset-source <auto|dir|embedded>] [--test-server <simple|payload>] [<TV IP ADDRESS>]
```

Use `python3 slopbro.py --help` for the full option reference.

Accept the pairing prompt on the target TV. (The credentials will be saved in
a `.key` file for future use.)

### Options

The `--fresh-launch` option handles overlays that accept a relaunch but do
not reload their initial script. It obtains the selected overlay's session ID,
waits one second for initial creation, closes that exact session, waits another
second, then launches the payload. An
unconfirmed close stops the attempt. Verify the TV's autoroot result separately;
page loading alone does not prove successful rooting.

The local HTTP server also handles concurrent connections so an idle browser
preconnection cannot block the payload download.

`--bind-ip 127.0.0.1` binds the payload server only to the PC's loopback interface.
Combine it with an already established SSH reverse tunnel and `--local-ip` set to
the tunnel's TV-side address. The advertised address and local binding are
different settings. This option does not create a tunnel or change any firewall.

The `--debug` option enables extra output on the TV screen as well as in
`autoroot.log`. The page also sends its status and debug messages back to the
serving PC in this mode, including a delayed status query for a stalled download.

`--staged-dir /tmp/slopbro-stage-<digits>` bypasses the TV download manager.
This is an optional workaround when the overlay loads but its download ticket
remains at zero bytes. It requires a working developer SSH connection. Before
running SlopBro, create a fresh directory with that name in the TV's shared
`/tmp`, then upload the reviewed `wwwroot/autoroot.sh`, `wwwroot/main.js`, and
`wwwroot/package.json` into it. Use LF line endings and readable file permissions;
verify the uploaded files match your local copies. Do not use files from an
untrusted or reused directory. The launcher does not upload or validate those
files for you. The page uses the staged directory as the service working directory
and launches the same payload without issuing download-manager requests.

For example, after staging those three files at `/tmp/slopbro-stage-123456`:

```bash
python3 slopbro.py --fresh-launch --staged-dir /tmp/slopbro-stage-123456 --debug --webos-version 6.5 <TV-IP>
```

The page still needs HTTP access to the PC. If using a developer SSH reverse
tunnel instead of a direct LAN connection, create it separately and pass the
appropriate `--bind-ip` and `--local-ip`. In staged mode the server stays running
for diagnostics until Ctrl+C; it does not wait for payload downloads that were
deliberately skipped. Verify the autoroot logs separately: a successful service
launch is not proof of successful installation or persistence after reboot.

The `--curl-insecure` option passes `-k` to `curl` when downloading Homebrew
Channel, disabling TLS certificate verification. Use it only when necessary
(e.g., when your TV does not have the correct date due to SDP being blocked).

The `--fake-service-path` option specifies the fake service path used to
bypass the service launch patch. It defaults to
`/usr/palm/services/com.palm.service.devmode`. Use `--no-fake-service-path` to
disable the bypass and omit the `fake-service-path` query parameter.

The `--local-ip` option allows you to specify the local IP address manually,
which can be useful if the script guesses the wrong IP address.

The `--webos-version` option specifies the TV's webOS version and limits the
target apps to those configured for that major version. Dotted versions such
as `6.5` are accepted and treated as major version `6`.

*The version is not currently auto-detected, so you may need to specify it if
the selected app fails.*

The `--asset-source` option allows you to specify where the script should look
for assets (`auto`, `dir`, `embedded`).

The `--test-server` option starts the local HTTP server and prints its URL
instead of connecting to the TV over SSAP, so you can test connectivity
manually by opening the URL in a browser. It doesn't pair with or launch
anything on the TV. The `<TV IP ADDRESS>` argument is optional but
recommended in both modes below; if omitted, the script guesses a
LAN-facing local IP, which may be wrong. Two modes are available:

- `simple`: serves a fixed plain-text response to confirm basic HTTP
  reachability only.
- `payload`: serves the real exploit/payload files (same as a normal run)
  without doing any SSAP pairing or launching, so you can load `index.html`
  directly in a browser to examine the payload itself.

## Packaging

In addition to serving files from the `wwwroot` directory, SlopBro can be
distributed as a single file with embedded assets.

### Building a single-file package

The packaging tool requires Python 3.12 or newer (independently of the
launcher's runtime requirements). Generate a standalone file with:

```bash
python3 tools/package_single_file.py --out dist/slopbro_packed.py
```

Then run it directly (no `wwwroot` required):

```bash
python3 dist/slopbro_packed.py 192.168.1.50
```

You can also explicitly specify where it should look for assets
(`embedded`, `dir`):

```bash
python3 dist/slopbro_packed.py --asset-source embedded 192.168.1.50
```

By default (`auto` mode), embedded assets are preferred over files if both
are present.

## Tests

Run the CLI and HTTP handler regression tests without connecting to a TV:

```bash
python3 -m unittest discover -s tests -v
```

The optional offline JavaScript payload fixture requires Node.js:

```bash
node tests/test_payload_lifetime.cjs
```

## Troubleshooting

- `slopbro.py` guesses what the local IP address is and might get it wrong.
  If you don't see any connections back to the HTTP server, try manually
  specifying the IP address with `--local-ip`.

- Make sure there are no weird network issues between your TV and wherever
  you're running SlopBro. Remember that connections need to work in both
  directions.

- Use `--test-server simple` to check basic HTTP connectivity from the TV's
  browser without needing SSAP pairing to work first.

## Credits

IDK, Claude Sonnet 4.6?

(`dangbei-overlay` from [dangbro](https://github.com/azoffshowy/dangbro);
jsserver vulnerability first publicly disclosed in
[jsbro-autoroot](https://github.com/raws0kil/jsbro-autoroot).)

## License

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along
with this program. If not, see <https://www.gnu.org/licenses/>.

See `COPYING` for details.

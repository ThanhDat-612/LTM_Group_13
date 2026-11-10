# Security module

The project uses one shared security implementation: `server/security.py` wraps
`server/validator.py`. The TCP upload handler imports this same implementation,
so the standalone checker and live server apply the same filename, size and
SHA-256 rules.

## Protection performed by the server

1. Limits request header length and requires a valid UTF-8 JSON `UPLOAD_REQ`.
2. Rejects empty/unsafe filenames, path separators, traversal strings and
   unsupported filename characters.
3. Rejects invalid, negative or over-limit file sizes before receiving payload.
4. Validates SHA-256 format before accepting the upload.
5. Limits concurrent upload connections and applies a socket timeout.
6. Writes to a temporary `.part` file, checks exact received size and SHA-256,
   then atomically renames the file only after successful verification.
7. Deletes temporary data after a failed or interrupted upload.

## Standalone security checker

Run commands from the `CODE` directory:

```bash
# Run built-in policy tests
python -m server.security --self-test

# Check a local file's filename and size and calculate SHA-256
python -m server.security --scan "../sample.pdf"

# Use a custom maximum file size
python -m server.security --scan "../sample.pdf" --max-size-mb 100
```

## Run an end-to-end upload test

Terminal 1:

```bash
python -m server.main
```

Terminal 2:

```bash
python -m client.upload_cli "../sample.pdf" --host 127.0.0.1 --port 5000
```

The upload client sends a JSON header terminated by newline, followed by exactly
the number of raw file bytes declared in `size`. The server replies with
`UPLOAD_ACK`, then a final `RESULT` containing success/failure and SHA-256.

## Scope and limitations

This is upload validation and integrity checking, not antivirus scanning. A
matching SHA-256 proves that received bytes match the checksum supplied in the
request; it does not prove that the file is safe or that the sender is trusted.
The current protocol does not provide authentication, encryption/TLS, malware
signatures, or protection against a malicious trusted client that can choose
its own checksum. Deploy on a trusted network until authentication and TLS are
implemented. The existing desktop GUI currently checks TCP connectivity; the
new CLI is the reference file-upload client for this protocol.

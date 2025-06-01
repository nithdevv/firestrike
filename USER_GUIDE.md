# FireStrike User Guide

## Installation

1. Make sure you have TOR installed:
   ```bash
   # Ubuntu/Debian
   sudo apt install tor
   
   # Windows
   # Download and install TOR Browser from https://www.torproject.org/
   ```

2. Install FireStrike:
   ```bash
   # Clone repository
   git clone https://github.com/yourusername/firestrike.git
   cd firestrike

   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows

   # Install dependencies
   pip install -r requirements.txt
   ```

## Basic Usage

### Upload File

To share a file:
```bash
python -m firestrike upload path/to/your/file.txt
```

After upload completes, you'll receive a magnet link like:
```
firestrike://5d41402abc4b2a76b9719d911017c592#YourEncryptionKey
```
Share this link with people you want to share the file with.

Options:
- `--temp` - delete file after upload
- `--port PORT` - use custom port (default: 8789)

### Download File

To download a shared file:
```bash
python -m firestrike download "firestrike://5d41402abc4b2a76b9719d911017c592#YourEncryptionKey"
```

Options:
- `--output PATH` - specify output location
- `--temp` - delete encrypted file after download
- `--port PORT` - use custom port

### View Network Status

To see active peers in the network:
```bash
python -m firestrike peers
```

## Advanced Usage

### Running as Background Service

Create a systemd service (Linux):
```ini
[Unit]
Description=FireStrike Node
After=network.target tor.service

[Service]
Type=simple
User=youruser
ExecStart=/path/to/venv/bin/python -m firestrike node
Restart=always

[Install]
WantedBy=multi-user.target
```

### Custom Port Configuration

If default ports are blocked, edit config:
```bash
python -m firestrike upload --port 8790 file.txt
python -m firestrike download --port 8790 "magnet:link"
```

## Security Tips

1. Always use secure channels to share magnet links
2. Don't share the same files repeatedly from one node
3. Use `--temp` flag to automatically delete sensitive files
4. Run node behind VPN for additional security
5. Don't expose your node's port to the internet

## Troubleshooting

### Common Issues

1. "TOR not running":
   ```bash
   # Start TOR service
   sudo service tor start
   ```

2. "Port already in use":
   ```bash
   # Use different port
   python -m firestrike upload --port 8790 file.txt
   ```

3. "No peers found":
   - Check your internet connection
   - Make sure TOR is running
   - Wait a few minutes for network discovery

4. "Upload/Download stuck":
   - Check TOR connection
   - Try restarting the node
   - Use `--port` to change ports

### Logs

Check logs for detailed error information:
```bash
tail -f ~/.firestrike/node.log
```

## Network Participation

Your node automatically participates in the network by:
- Storing and forwarding files
- Maintaining peer connections
- Contributing to network resilience

The more nodes run continuously, the more reliable the network becomes.

## Best Practices

1. Running a Node:
   - Use stable internet connection
   - Keep enough disk space
   - Run 24/7 if possible

2. File Sharing:
   - Use descriptive filenames
   - Share magnet links securely
   - Keep files available

3. Security:
   - Update regularly
   - Use strong passwords
   - Monitor system resources

## Support

For help and discussions:
- GitHub Issues
- Project Wiki
- Community Forums

Remember: FireStrike is designed for legal file sharing. Users are responsible for the content they share. 
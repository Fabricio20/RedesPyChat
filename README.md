## Python Chat Service

IPv6-only auto-discovery chat service written in Python.
Proof of Concept for my network engineering class.

#### Usage:

**Warning**: Requires Python 3+ and (at least local) IPv6 connectivity.

To start the server:
```
python server.py
```

To start the client:
```
python client.py
```

#### Protocol:

The protocol is JSON-based.

| OP | Field(s)       | Sent-By | Description                           |                           
|----|----------------|---------|---------------------------------------|
| -1 | message        | server  | Closes the connection due to an error |
| 0  |                | client  | Graceful exit                         |
| 1  | name           | client  | Defines the client's nickname         |
| 2  | name?, message | both    | Sends a broadcast message             |

#### Authors:
- Fabricio Winter

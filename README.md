## Python Chat Service

IPv6-only auto-discovery chat service written in Python.
Proof of Concept for my network engineering class.

### Features:
- IPv6 Only (ready for the future of the internet?!)
- Service discovery (client finds the server via multicast announcements!)
- Basically IRC (complex protocol)
- Channels, DMs, Admins, Kicks, (Network Splits?)

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

The protocol is JSON-based. Hash field is used to track RPC between servers.

| OP 		 | Arguments                         | Description                                                        |
|------------|-----------------------------------|--------------------------------------------------------------------|
| DISCONNECT | message?                          | Closes the connection, message indicates an error                  |
| ERROR      | message                           | Sends an error to the client                                       |
| LOGIN      | name, hash?                       | Defines a nickname                                                 |
| MESSAGE    | target, message, username?, hash? | Sends a message. (* for all, & for all in server)                  |
| JOIN       | channel, username, password?      | Join a channel (or create), with a possible password               |
| PART       | channel, username                 | Leaves a channel                                                   |
| ADMIN      | channel, username                 | Promotes a user to channel admin                                   |
| KICK       | channel, username, message?       | Kicks a user from a channel                                        |
| USERS      | userList, hash, channel?          | Lists all users, optionally filter by channel                      |
| ACK        | success, hash                     | ACK between servers                                                |
| CHANNELS   | channelList?                      | Syncs all channels between servers, could be used to list channels |

#### Authors:
- Fabricio Winter
- Protocol co-developed with [SchneiderrBR](https://github.com/SchneiderrBR/)

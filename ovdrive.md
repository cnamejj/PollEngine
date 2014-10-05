ovdrive.py
==========

Python "server" that can be used to drive an OpenVPN client.  As written is
uses a static passoword appended with a "one time password" to authenticate.
The specific OTP used in the code included here is compatible with Google
Authenticator.  But if you have an algorithm for another OTP you could just
plug it into the code to adapt to the code your VPN server expects.

So the real benefit in using this software is to make sure OpenVPN tunnels can
automatically re-authenticate when an SSL session key times out.  On it's own
OpenVPN clients can store credentials in memory and re-use them as needed.
But when the authentication model called for an OTP to be included, then
storing the credentials used initially doesn't work.

Using a password for a VPN connection that's a concatenation of a static
password and an OTP is common multi-factor authentication is required and when
Radius is part of the mix on the server side.

## Setting things up: Install OpenVPN

First, you need to get OpenVPN working.  On Linux systems getting the software
installed it simple enough using "yum", "apt-get", etc...

For MacOS I ended up downloading the source for OpenVPN and compiling it.
That proved to be very easy since the code compiled cleanly and just worked
after it was installed.  The only peculiar thing is that the default location
for the complied programs is "/usr/local/sbin/" which isn't in the default
PATH for MacOS.  So you'll need to either run it by specifying the full path
to the "openvpn" command or tweak you PATH environment variable in your
favorite Bash startup script, meaning ".bash_profile", ".bashrc", etc...

## Setting things up: Configure your OpenVPN client

How you get the config file needed to connect to your VPN server is
installation dependent so you'll have to follow the instructions given to you
by the people that setup your VPN server.

But however you get the specifics, you'll wind up with a configuration file
OpenVPN can read when it starts.  It will identify hostnames or IP's of the
VPN server, include an SSL certificate(s), described encrytion options to use,
etc...

Whatever's in there, just get it working as delivered first.  Meaning get to
the point where you can enter the following command:

```
$ sudo openvpn --config name-of-config-file
```

and establish a VPN connection by manually entering your usename and password,
meaning the static password plus the OTP you get from the Google Authenticator
app.  Once that works, then you're ready to try driving the connection process with the
"ovdrive.py" code include here.

### Practice controlling the "ovdrive.py" server

When you start "ovdrive.py" it will listen on two ports on the "localhost" interface on your system.  The ports are defined in these lines of code:

```
ADMIN_PORT = 7778
OVDRIVE_PORT = 7777
```

and they can be changed to any values you prefer.  The "OVDRIVE_PORT" is the
server your OpenVPN client will communicate with as it needs authentication
credentials.  The "ADMIN_PORT" is the server you will use to provide the
username, static password, and "secret" needed to generate one-time-password.

The reason for a admin server is simple, to avoid storing credentials in plain
text in a Python script.  Instead, when the code is started it just waits for
you to connect and supply the info it needs to construct the credentials the
OpenVPN client will need.

So before changing your OpenVPN configuration to point to the "ovrdive.py"
server, you can start up the server and practice using the administrative
interface.  To do that, if you changed the "ADMIN_PORT" remember that and
replace "7778" in the examples with the port you picked.

To start the server, just run

```
ovdrive.py
```

in a terminal window.

Then in a different terminal window, connect to the server and try the "show",
"user", "pass", "seed", "otp" and "drop" commands.

```
telnet localhost 7778
Trying 127.0.0.1...
Connected to localhost.
Escape character is '^]'.
show
User: NoUser
Pass: NoPassword
Seed: NoOTPSeed
user whoever
User set to whoever
pass StatPass123
Password for whoever set
seed URUYUTBMEOFDIUZS
OTP seed for whoever set
otp
OTP for 14/10/04-19:32:18 is StatPass123848032
drop
Connection closed by foreign host.
$
```

The commands recognized by the admin server are very straightforward.

|user XXX|stores the username used for the VPN connection to "XXX"|
|pass XXX|stores the static component of the compound VPN password|
|seed XXX|stores the "secret" used in the OTP algorithm|
|otp| generates the current compound VPN password (static + OTP)|
|drop|directs the admin server to drop the connection|
|quit| stops the "ovdrive.py" server, which will terminate any VPN tunnel|

You can connect back to the server as you like and re-issue commands.  The
credentials you supply are retained in RAM.  So if connect back to the admin
port 10 minutes later and send another "otp" command it will re-use the
information you supplied to generate the VPN password.

Back on the terminal where you started the "ovdrive" server, the console will
log messages showing connections and commands received.  It will look
something like this.

```
$ ./ovdrive.py
14/10/04-19:26:34 Got a new admin client on port 7778
14/10/04-19:26:37 Admin: show current settings
14/10/04-19:27:37 Timeout #1, wait again...
14/10/04-19:28:48 Admin: set user to whoever
14/10/04-19:28:54 Admin: set password for whoever
14/10/04-19:29:15 Admin: drop client connection
14/10/04-19:30:15 Timeout #1, wait again...
14/10/04-19:31:15 Timeout #2, wait again...
14/10/04-19:32:12 Got a new admin client on port 7778
14/10/04-19:32:13 Admin: show current settings
14/10/04-19:32:16 Admin: set OTP seed for whoever
14/10/04-19:32:18 Admin: Generate OTP *PW-MASKED*848032
14/10/04-19:32:30 Admin: drop client connection
```

Once that works, you're ready to connect the OpenVPN client to your "ovdrive"
server.

### Connecting OpenVPN to "ovdrive"

The OpenVPN software provides a simple mechanism for connecting a VPN client
to an external process which can supply credentials.  In fact that external
connection mechanism can completely control the VPN client.  The "ovdrive"
server only makes use a tiny part of the API, for lack of a better word.

To connect the two processes, you just need to add the following configuration
lines to the OpenVPN configuration file.

Just remember to change "7777" to whatever you used if you decided to change
the "OVDRIVE_PORT" in the "ovdrive.py" script.

```
auth-user-pass
auth-nocache
auth-retry interact

management-hold
management-query-passwords

management 127.0.0.1 7777
```

You can check the man page for "openvpn" for a description of what each of
those configuration options does.  The overall effect is that the OpenVPN
client will block whenever it needs credentials and ask the "ovdrive" server
running on port "7777" for advice on how to proceed.

In response to the status information sent by the OpenVPN client, the
"ovdrive" server will send back commands to the OpenVPN client.  The
communications between the OpenVPN client and the "ovdrive" server will be
logged to the console of the window where you're running "ovdrive".  And
depending on how verbosely you've configured your OpenVPN client, it may be
logged in that terminal window as well.


#!/usr/bin/env python
"""
Driver for OpenVPN client
"""

import time
import base64
import hashlib
import struct
import hmac
import pollengine

# ---

class OVDriveData:
    """OpenVPN authentication data"""

    def __init__( self ):
        self.user = NO_USER
        self.pass_pref = NO_PASS
        self.otp_seed = NO_SEED

# ---

class ShellOVDrive:
    """Driver for OpenVPN client"""

    def __init__( self ):
#        PE.displaymsg( 'dbg:: Shell_OVDrive init' )
        self.ovdata = OVDriveData()
        return

    def set_ovdata( self, ovdata ):
        """Record a data structure"""

        self.ovdata = ovdata

    def process_request( self, conn ):
        """Handle requests received from the client"""

#        PE.displaymsg( 'Received {size} bytes "{req}"'.format(size=len(
#                conn.inp_queue), req=conn.inp_queue) )
        __continue = True

        __lines = conn.inp_queue.split( '\n' )
        for __req in __lines:
            if __req != '':
                PE.displaymsg( __req )
            try:
                __template = NEED[__req]

                PE.displaymsg( 'Response: {out}'.format(out=__template.format(
                        user=self.ovdata.user, pw=MASKED_PW)) )
                conn.queue_response( __template.format(user=self.ovdata.user,
                        pw=gen_otp(self.ovdata)) )

            except KeyError:
                pass

        conn.inp_queue = ''
        conn.inp_lines = ''

        return True

    def get_name( self ):
        """Return a description of the class"""

        return 'Shell_OVDrive'

# ---

class ShellAdmin:
    """Driver for admin shell object"""

    def __init__( self ):
#        PE.displaymsg( 'dbg:: Shell_Admin init' )
        self.ovdata = OVDriveData()

    def set_ovdata( self, ovdata ):
        """Record a data structure"""

        self.ovdata = ovdata

    def process_request( self, conn ):
        """Handle requests received from the client"""

#        PE.displaymsg( 'Received {size} bytes "{req}"'.format(
#                size=len(conn.inp_queue), req=conn.inp_queue) )
        __continue = True

        __lines = conn.inp_queue.split( '\n' )
        for __req in __lines:
            __words = __req.split( ' ' )

#            PE.displaymsg( 'dbg:: line "{line}" words {nw}'.format(line=__req,
#                    nw=len(__words)) )
            if len(__words) > 0:
                __comm = __words[0]

                if __comm == '':
                    continue

                if __comm == ACR_USER:
                    if len(__words) == 2:
                        self.ovdata.user = __words[1]
                        PE.displaymsg( 'Admin: set user to {user}'.
                                format(user=self.ovdata.user) )
                        conn.queue_response( 'User set to {user}'.
                                format(user=self.ovdata.user) )
                    else:
                        conn.queue_response(
                                'The "user" command takes one argument' )

                elif __comm == ACR_PASS:
                    if len(__words) == 2:
                        self.ovdata.pass_pref = __words[1]
                        PE.displaymsg( 'Admin: set password for {user}'.
                                format(user=self.ovdata.user) )
                        conn.queue_response( 'Password for {user} set'.
                                format(user=self.ovdata.user) )
                    else:
                        conn.queue_response(
                                'The "pass" command takes one argument' )

                elif __comm == ACR_SEED:
                    if len(__words) == 2:
                        self.ovdata.otp_seed = __words[1]

                        PE.displaymsg( 'Admin: set OTP seed for {user}'.
                                format(user=self.ovdata.user) )
                        conn.queue_response( 'OTP seed for {user} set'.
                                format(user=self.ovdata.user) )
                    else:
                        conn.queue_response(
                               'The "seed" command takes one argument' )

                elif __comm == ACR_SHOW:
                    PE.displaymsg( 'Admin: show current settings' )
                    conn.queue_response( SHOW_TEMPLATE.format(
                            user=self.ovdata.user, pw=self.ovdata.pass_pref,
                            seed=self.ovdata.otp_seed) )

                elif __comm == ACR_OTP:
                    __otp = gen_otp(self.ovdata)
                    PE.displaymsg( 'Admin: Generate OTP {pwmask}{otp}'.format(
                            otp=__otp[-6:], pwmask=MASKED_PW) )
                    conn.queue_response( 'OTP for {now} is {otp}'.format(
                            now=time.strftime('%y/%m/%d-%H:%M:%S'), otp=__otp) )

                elif __comm == ACR_DROP:
                    PE.displaymsg( 'Admin: drop client connection' )
                    conn.close()

                elif __comm == ACR_QUIT:
                    PE.displaymsg( 'Admin: stop OVDriver' )
                    __continue = False

                else:

                    PE.displaymsg( 'Admin: unrecognized command "{comm}"'.
                            format(comm=__comm) )
                    conn.queue_response( 'Command "{comm}" unrecognized'.
                            format(comm=__comm) )

#        conn.queue_response( 'Got {nl} lines, {size} bytes\n'.format(
#                size=len(conn.inp_queue), nl=len(__lines)) )
        conn.inp_lines = ''
        conn.inp_queue = ''

        return __continue

    def get_name( self ):
        """Return a description of the class"""

        return 'Shell_Admin'

# ---

def gen_otp( ovdata ):
    """Generate the current one-time-password"""

    try:
        __n_interval = time.time() // OTP_INTERVAL
        __key = base64.b32decode( ovdata.otp_seed, casefold=OTP_COLLAPSE )
        __msg = struct.pack( '>Q', __n_interval )
        __hdig = hmac.new( __key, __msg, OTP_DIGEST_METH ).digest()
        __ob_low = ord( __hdig[19] ) & 15
        __fulltoken = struct.unpack( '>I', __hdig[__ob_low:__ob_low + 4])
        __token = (__fulltoken[0] & OTP_TOKEN_MASK) % (10 ** OTP_TOKEN_LEN)

        __result = '{pref}{token:06d}'.format(pref=ovdata.pass_pref,
                token=__token)
    except TypeError:

        __result = '{pref}{failed}'.format(pref=ovdata.pass_pref,
                failed=OTP_ERROR)


#    PE.displaymsg( 'dbg:: Generate OTP {otp}'.format(otp=__result) )
    return( __result )

# ---

def request_status( conn_list ):
    """Callback routine to periodically check server status"""

    for __conn in conn_list:

#        PE.displaymsg( 'dbg:: port {port} type {ct}'.format(ct=__conn.type,
#            port=__conn.server_port) )
        if __conn.server_port == OVDRIVE_PORT and __conn.type == IS_SESSION:
#            PE.displaymsg( 'dbg:: Found an OVDrive session' )
            __conn.queue_response( STATUS_CHECK ) 

    return

# ---

ADMIN_PORT = 7778
OVDRIVE_PORT = 7777
MASKED_PW = '*PW-MASKED*'

IS_LISTEN = 0
IS_SESSION = 1

NO_USER = 'NoUser'
NO_PASS = 'NoPassword'
NO_SEED = 'NoOTPSeed'

OTP_INTERVAL = 30
OTP_TOKEN_LEN = 6
OTP_DIGEST_METH = hashlib.sha1
OTP_COLLAPSE = True
OTP_TOKEN_MASK = 0x7fffffff
OTP_ERROR = 'OTP-Failed'

ACR_USER = 'user'
ACR_PASS = 'pass'
ACR_SEED = 'seed'
ACR_SHOW = 'show'
ACR_QUIT = 'quit'
ACR_OTP = 'otp'
ACR_DROP = 'drop'

STATUS_CHECK = 'load-stats'

REQ_RELEASE = ">HOLD:Waiting for hold release"
REQ_AUTH = ">PASSWORD:Need 'Auth' username/password"
REQ_PASS = "SUCCESS: 'Auth' username entered, but not yet verified"
REQ_SETSTATE = "SUCCESS: 'Auth' password entered, but not yet verified"

NEED = dict()
NEED[REQ_RELEASE] = 'hold release'
NEED[REQ_AUTH] = 'username Auth {user}'
NEED[REQ_PASS] = 'password Auth {pw}'
NEED[REQ_SETSTATE] = 'state on'

SERVER_PORT_LIST = ( ADMIN_PORT, OVDRIVE_PORT )

SHOW_TEMPLATE = 'User: {user}\nPass: {pw}\nSeed: {seed}'

# ---

PE = pollengine
ENGINE = PE.Engine( port_list = SERVER_PORT_LIST )

OVDATA = OVDriveData()
OVDATA.user = NO_USER
OVDATA.pass_pref = NO_PASS
OVDATA.otp_seed = NO_SEED

ADMIN_SHELL = ShellAdmin()
ADMIN_SHELL.set_ovdata( OVDATA )

OVDRIVE_SHELL = ShellOVDrive()
OVDRIVE_SHELL.set_ovdata( OVDATA )

ENGINE.config_server( ADMIN_PORT, shell = ADMIN_SHELL, status = request_status )
ENGINE.config_server( OVDRIVE_PORT, shell = OVDRIVE_SHELL )

ENGINE.run()
